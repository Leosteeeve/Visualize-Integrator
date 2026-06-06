from __future__ import annotations

import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import traceback
import warnings as warning_tools
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import sympy as sp
from sympy.calculus.singularities import singularities
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

try:
    from scipy import integrate as scipy_integrate
except Exception:  # pragma: no cover - SciPy is optional at runtime.
    scipy_integrate = None

import algebra_steps
import problem_generator


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
CPP_SOURCE = ROOT / "cpp" / "integrator.cpp"
CPP_EXE = ROOT / "cpp" / ("integrator.exe" if os.name == "nt" else "integrator")
DEFAULT_PORT = 8000

x = sp.Symbol("x", real=True)
y = sp.Symbol("y", real=True)
theta = sp.Symbol("theta", real=True)
r = sp.Symbol("r", real=True)
TRANSFORMS = standard_transformations + (convert_xor, implicit_multiplication_application)

PARSE_GLOBALS = {
    "__builtins__": {},
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
}

PARSE_LOCALS = {
    "x": x,
    "y": y,
    "r": r,
    "theta": theta,
    "t": theta,
    "θ": theta,
    "pi": sp.pi,
    "π": sp.pi,
    "oo": sp.oo,
    "inf": sp.oo,
    "infinity": sp.oo,
    "∞": sp.oo,
    "e": sp.E,
    "E": sp.E,
    "I": sp.I,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "arcsin": sp.asin,
    "arccos": sp.acos,
    "arctan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "Abs": sp.Abs,
}


def normalize_math_text(value: str) -> str:
    replacements = {
        "−": "-",
        "–": "-",
        "—": "-",
        "×": "*",
        "·": "*",
        "÷": "/",
        "π": "pi",
        "∞": "oo",
        "√": "sqrt",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value.strip()


def parse_math(value: str) -> sp.Expr:
    text = normalize_math_text(value)
    if not text:
        raise ValueError("Expression is empty")
    return parse_expr(
        text,
        local_dict=dict(PARSE_LOCALS),
        global_dict=dict(PARSE_GLOBALS),
        transformations=TRANSFORMS,
        evaluate=True,
    )


def expr_to_cpp(expr: sp.Expr) -> str:
    text = str(sp.simplify(expr))
    return text.replace("**", "^")


def finite_float(expr: sp.Expr) -> float:
    value = float(sp.N(expr, 17))
    if not math.isfinite(value):
        raise ValueError("Bound is not finite")
    return value


def bound_float(expr: sp.Expr) -> float:
    simplified = sp.simplify(expr)
    if simplified == sp.oo:
        return math.inf
    if simplified == -sp.oo:
        return -math.inf
    return finite_float(simplified)


def json_float(value: float) -> float | None:
    return value if math.isfinite(value) else None


def has_unevaluated_integral(value: sp.Expr) -> bool:
    return bool(value.has(sp.Integral))


def safe_latex(value: sp.Expr) -> str:
    try:
        return sp.latex(value)
    except Exception:
        return str(value)


def safe_numeric_value(value: sp.Expr) -> float | None:
    try:
        if value is sp.nan or value.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
            return None
        numeric = float(sp.N(value, 17))
        return numeric if math.isfinite(numeric) else None
    except Exception:
        return None


def classify_integral_result(value: sp.Expr) -> tuple[str, str]:
    if has_unevaluated_integral(value):
        return "unknown", "符号引擎暂时没有解析出这个反常积分的闭式结果。"
    if value is sp.nan or value.has(sp.nan):
        return "divergent", "左右极限不能合成为有限值，反常积分发散。"
    if value.has(sp.zoo) or value.has(sp.oo, -sp.oo) or value.is_finite is False:
        return "divergent", "积分极限趋于无穷或不存在有限极限。"
    if value.is_finite is True or safe_numeric_value(value) is not None:
        return "convergent", "反常积分存在有限值，判定为收敛。"
    return "unknown", "暂时无法仅凭符号结果证明收敛或发散。"


def find_singular_points(expr: sp.Expr, lower: float, upper: float) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    found: list[dict[str, Any]] = []
    try:
        raw = singularities(expr, x)
    except Exception as exc:
        return [], [f"暂时无法自动分析奇点: {exc}"]

    if raw in (sp.EmptySet, sp.S.EmptySet):
        return [], []
    if not isinstance(raw, sp.FiniteSet):
        notes.append("当前阶段还不能完全枚举这类符号奇点。")
        return [], notes

    for item in raw:
        simplified = sp.simplify(item)
        numeric = safe_numeric_value(simplified)
        if numeric is None or not math.isfinite(numeric):
            continue
        if numeric < lower - 1e-12 or numeric > upper + 1e-12:
            continue

        if math.isfinite(lower) and math.isclose(numeric, lower, rel_tol=1e-10, abs_tol=1e-10):
            location = "left_endpoint"
        elif math.isfinite(upper) and math.isclose(numeric, upper, rel_tol=1e-10, abs_tol=1e-10):
            location = "right_endpoint"
        else:
            location = "internal"

        found.append(
            {
                "value": simplified,
                "text": str(simplified),
                "latex": safe_latex(simplified),
                "float": numeric,
                "location": location,
            }
        )

    found.sort(key=lambda item: item["float"])
    return found, notes


def find_gpp() -> str | None:
    candidates = [
        shutil.which("g++"),
        r"E:\MinGW\bin\g++.exe",
        r"C:\mingw64\bin\g++.exe",
        r"D:\MSYS2\ucrt64\bin\g++.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def ensure_cpp_integrator(warnings: list[str]) -> bool:
    if CPP_EXE.exists() and CPP_EXE.stat().st_mtime >= CPP_SOURCE.stat().st_mtime:
        return True

    gpp = find_gpp()
    if not gpp:
        warnings.append("C++ compiler was not found; using SciPy numeric fallback.")
        return False

    cmd = [gpp, "-O3", "-std=c++17", str(CPP_SOURCE), "-o", str(CPP_EXE)]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown compiler error").strip()
        warnings.append(f"C++ compiler failed; using SciPy fallback. {detail[:240]}")
        return False

    return True


def numeric_with_cpp(expr: sp.Expr, lower: float, upper: float, eps: float, warnings: list[str]) -> dict[str, Any] | None:
    if not ensure_cpp_integrator(warnings):
        return None

    cpp_expr = expr_to_cpp(expr)
    try:
        completed = subprocess.run(
            [str(CPP_EXE), cpp_expr, repr(lower), repr(upper), repr(eps)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        warnings.append(f"C++ engine could not run; using SciPy fallback. {exc}")
        return None

    try:
        payload = json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError:
        warnings.append("C++ engine returned an unreadable response; using SciPy fallback.")
        return None

    if completed.returncode != 0 or not payload.get("ok"):
        warnings.append(f"C++ engine declined this expression; using SciPy fallback. {payload.get('error', 'unknown error')}")
        return None

    return payload


def numeric_double_with_cpp(
    expr: sp.Expr,
    x_lower: float,
    x_upper: float,
    y_lower: float,
    y_upper: float,
    eps: float,
    warnings: list[str],
) -> dict[str, Any] | None:
    if not ensure_cpp_integrator(warnings):
        return None

    cpp_expr = expr_to_cpp(expr)
    try:
        completed = subprocess.run(
            [
                str(CPP_EXE),
                "--double",
                cpp_expr,
                repr(x_lower),
                repr(x_upper),
                repr(y_lower),
                repr(y_upper),
                repr(eps),
            ],
            capture_output=True,
            text=True,
            timeout=12,
        )
    except Exception as exc:
        warnings.append(f"C++ double engine could not run; using SciPy fallback. {exc}")
        return None

    try:
        payload = json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError:
        warnings.append("C++ double engine returned an unreadable response; using SciPy fallback.")
        return None

    if completed.returncode != 0 or not payload.get("ok"):
        warnings.append(f"C++ double engine declined this expression; using SciPy fallback. {payload.get('error', 'unknown error')}")
        return None

    return payload


def numeric_with_scipy(
    expr: sp.Expr,
    lower: float,
    upper: float,
    eps: float,
    split_points: list[float] | None = None,
) -> dict[str, Any]:
    if scipy_integrate is None:
        raise RuntimeError("Neither the C++ engine nor SciPy is available for numeric integration")

    sign = 1.0
    if upper < lower:
        lower, upper = upper, lower
        sign = -1.0

    fn = sp.lambdify(x, expr, modules=["math"])

    def wrapped(value: float) -> float:
        result = fn(value)
        if isinstance(result, complex):
            if abs(result.imag) > 1e-10:
                raise ValueError("Function returned a complex value")
            result = result.real
        result = float(result)
        if not math.isfinite(result):
            raise ValueError("Function returned a non-finite value")
        return result

    sorted_points = sorted(
        point for point in (split_points or []) if math.isfinite(point) and lower < point < upper
    )
    bounds = [lower, *sorted_points, upper]
    total_value = 0.0
    total_error = 0.0
    captured_warnings: list[str] = []

    for left, right in zip(bounds, bounds[1:]):
        with warning_tools.catch_warnings(record=True) as caught:
            warning_tools.simplefilter("always")
            value, error = scipy_integrate.quad(
                wrapped,
                left,
                right,
                epsabs=eps / max(1, len(bounds) - 1),
                epsrel=eps,
                limit=240,
            )
        total_value += value
        total_error += abs(error)
        captured_warnings.extend(str(item.message) for item in caught)

    method = "quad_scipy_improper" if split_points or not (math.isfinite(lower) and math.isfinite(upper)) else "quad_scipy"
    return {
        "ok": True,
        "value": sign * total_value,
        "estimated_error": total_error,
        "evaluations": None,
        "method": method,
        "engine": "python_scipy",
        "integration_warnings": captured_warnings[:3],
    }


def numeric_double_with_scipy(
    expr: sp.Expr,
    x_lower: float,
    x_upper: float,
    y_lower: float,
    y_upper: float,
    eps: float,
) -> dict[str, Any]:
    if scipy_integrate is None:
        raise RuntimeError("Neither the C++ engine nor SciPy is available for double integration")

    sign = 1.0
    if x_upper < x_lower:
        x_lower, x_upper = x_upper, x_lower
        sign *= -1.0
    if y_upper < y_lower:
        y_lower, y_upper = y_upper, y_lower
        sign *= -1.0

    fn = sp.lambdify((x, y), expr, modules=["math"])

    def wrapped(y_value: float, x_value: float) -> float:
        result = fn(x_value, y_value)
        if isinstance(result, complex):
            if abs(result.imag) > 1e-10:
                raise ValueError("Function returned a complex value")
            result = result.real
        result = float(result)
        if not math.isfinite(result):
            raise ValueError("Function returned a non-finite value")
        return result

    value, error = scipy_integrate.dblquad(
        wrapped,
        x_lower,
        x_upper,
        lambda _x: y_lower,
        lambda _x: y_upper,
        epsabs=eps,
        epsrel=eps,
    )
    return {
        "ok": True,
        "value": sign * value,
        "estimated_error": abs(error),
        "evaluations": None,
        "method": "dblquad_scipy",
        "engine": "python_scipy",
    }


def numeric_polar_double_with_scipy(
    integrand: sp.Expr,
    r_lower_expr: sp.Expr,
    r_upper_expr: sp.Expr,
    theta_lower: float,
    theta_upper: float,
    eps: float,
) -> dict[str, Any]:
    if scipy_integrate is None:
        raise RuntimeError("SciPy is required for polar integration with variable radial bounds")

    theta_sign = 1.0
    if theta_upper < theta_lower:
        theta_lower, theta_upper = theta_upper, theta_lower
        theta_sign *= -1.0

    integrand_fn = sp.lambdify((r, theta), integrand, modules=["math"])
    r_lower_fn = sp.lambdify(theta, r_lower_expr, modules=["math"])
    r_upper_fn = sp.lambdify(theta, r_upper_expr, modules=["math"])

    def clean(value: Any, name: str) -> float:
        if isinstance(value, complex):
            if abs(value.imag) > 1e-10:
                raise ValueError(f"{name} returned a complex value")
            value = value.real
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{name} returned a non-finite value")
        return numeric

    def wrapped(r_value: float, theta_value: float) -> float:
        return clean(integrand_fn(r_value, theta_value), "Integrand")

    def lower(theta_value: float) -> float:
        return clean(r_lower_fn(theta_value), "Lower radius")

    def upper(theta_value: float) -> float:
        return clean(r_upper_fn(theta_value), "Upper radius")

    value, error = scipy_integrate.dblquad(
        wrapped,
        theta_lower,
        theta_upper,
        lower,
        upper,
        epsabs=eps,
        epsrel=eps,
    )
    return {
        "ok": True,
        "value": theta_sign * value,
        "estimated_error": abs(error),
        "evaluations": None,
        "method": "polar_dblquad_scipy",
        "engine": "python_scipy",
    }


def sample_polar_area(
    outer_expr: sp.Expr,
    inner_expr: sp.Expr,
    theta_lower: float,
    theta_upper: float,
) -> dict[str, Any]:
    outer_fn = sp.lambdify(theta, outer_expr, modules=["math"])
    inner_fn = sp.lambdify(theta, inner_expr, modules=["math"])
    theta_min, theta_max = sorted((theta_lower, theta_upper))
    if theta_min == theta_max:
        theta_max = theta_min + 2 * math.pi

    count = 420
    outer_points: list[dict[str, float | None]] = []
    inner_points: list[dict[str, float | None]] = []
    finite_radii: list[float] = []

    def sample_radius(fn: Any, angle: float) -> tuple[float | None, float | None, float | None]:
        try:
            raw = fn(angle)
            if isinstance(raw, complex):
                raw = raw.real if abs(raw.imag) <= 1e-10 else math.nan
            radius = float(raw)
            if not math.isfinite(radius):
                return None, None, None
            finite_radii.append(abs(radius))
            return radius, radius * math.cos(angle), radius * math.sin(angle)
        except Exception:
            return None, None, None

    for index in range(count):
        portion = index / (count - 1)
        angle = theta_min + (theta_max - theta_min) * portion
        outer_radius, outer_x, outer_y = sample_radius(outer_fn, angle)
        inner_radius, inner_x, inner_y = sample_radius(inner_fn, angle)
        outer_points.append({"theta": angle, "r": outer_radius, "x": outer_x, "y": outer_y})
        inner_points.append({"theta": angle, "r": inner_radius, "x": inner_x, "y": inner_y})

    r_max = max(finite_radii) if finite_radii else 1.0
    if r_max <= 0:
        r_max = 1.0

    return {
        "kind": "polar_area",
        "thetaMin": theta_min,
        "thetaMax": theta_max,
        "rMax": r_max,
        "outer": outer_points,
        "inner": inner_points,
    }


def sample_polar_surface(
    expr: sp.Expr,
    r_lower_expr: sp.Expr,
    r_upper_expr: sp.Expr,
    theta_lower: float,
    theta_upper: float,
) -> dict[str, Any]:
    base = sample_polar_area(r_upper_expr, r_lower_expr, theta_lower, theta_upper)
    expr_fn = sp.lambdify((r, theta), expr, modules=["math"])
    lower_fn = sp.lambdify(theta, r_lower_expr, modules=["math"])
    upper_fn = sp.lambdify(theta, r_upper_expr, modules=["math"])
    theta_min, theta_max = base["thetaMin"], base["thetaMax"]

    rows: list[list[dict[str, float | None]]] = []
    finite_z: list[float] = []
    theta_count = 32
    r_count = 22
    for ti in range(theta_count):
        theta_portion = ti / (theta_count - 1)
        angle = theta_min + (theta_max - theta_min) * theta_portion
        try:
            r_low = float(lower_fn(angle))
            r_high = float(upper_fn(angle))
        except Exception:
            r_low, r_high = 0.0, 0.0
        row: list[dict[str, float | None]] = []
        for ri in range(r_count):
            r_portion = ri / (r_count - 1)
            radius = r_low + (r_high - r_low) * r_portion
            try:
                raw = expr_fn(radius, angle)
                if isinstance(raw, complex):
                    raw = raw.real if abs(raw.imag) <= 1e-10 else math.nan
                z_value = float(raw)
                z_value = z_value if math.isfinite(z_value) else None
            except Exception:
                z_value = None
            if z_value is not None:
                finite_z.append(z_value)
            row.append(
                {
                    "theta": angle,
                    "r": radius,
                    "x": radius * math.cos(angle),
                    "y": radius * math.sin(angle),
                    "z": z_value,
                }
            )
        rows.append(row)

    if finite_z:
        z_min, z_max = min(finite_z), max(finite_z)
        if z_min == z_max:
            z_min -= 1.0
            z_max += 1.0
    else:
        z_min, z_max = -1.0, 1.0

    return {
        **base,
        "kind": "polar_surface",
        "rows": rows,
        "zMin": z_min,
        "zMax": z_max,
    }


def sample_function(expr: sp.Expr, lower: float | None, upper: float | None) -> dict[str, Any]:
    fn = sp.lambdify(x, expr, modules=["math"])
    left_tail = False
    right_tail = False

    if lower is None or upper is None or lower == upper:
        lower, upper = -5.0, 5.0
    elif math.isfinite(lower) and math.isfinite(upper):
        pass
    elif math.isfinite(lower) and upper == math.inf:
        right_tail = True
        width = max(10.0, abs(lower) * 0.35 + 8.0)
        upper = lower + width
    elif lower == -math.inf and math.isfinite(upper):
        left_tail = True
        width = max(10.0, abs(upper) * 0.35 + 8.0)
        lower = upper - width
    else:
        left_tail = True
        right_tail = True
        lower, upper = -8.0, 8.0

    if upper < lower:
        lower, upper = upper, lower

    span = upper - lower
    padding = span * 0.2 if span > 0 else 1.0
    start = lower - padding
    end = upper + padding
    count = 360
    points: list[dict[str, float | None]] = []
    finite_y: list[float] = []

    for index in range(count):
        t = index / (count - 1)
        xv = start + (end - start) * t
        yv: float | None
        try:
            raw = fn(xv)
            if isinstance(raw, complex):
                raw = raw.real if abs(raw.imag) <= 1e-10 else math.nan
            candidate = float(raw)
            yv = candidate if math.isfinite(candidate) else None
        except Exception:
            yv = None

        if yv is not None:
            finite_y.append(yv)
        points.append({"x": xv, "y": yv})

    if finite_y:
        finite_y.sort()
        low_index = max(0, int(len(finite_y) * 0.02) - 1)
        high_index = min(len(finite_y) - 1, int(len(finite_y) * 0.98))
        y_min = finite_y[low_index]
        y_max = finite_y[high_index]
        if y_min == y_max:
            y_min -= 1.0
            y_max += 1.0
        y_pad = (y_max - y_min) * 0.18
        y_min -= y_pad
        y_max += y_pad
    else:
        y_min, y_max = -1.0, 1.0

    return {
        "points": points,
        "xMin": start,
        "xMax": end,
        "yMin": y_min,
        "yMax": y_max,
        "shadeMin": lower,
        "shadeMax": upper,
        "leftTail": left_tail,
        "rightTail": right_tail,
    }


def sample_surface(
    expr: sp.Expr,
    x_lower: float,
    x_upper: float,
    y_lower: float,
    y_upper: float,
) -> dict[str, Any]:
    fn = sp.lambdify((x, y), expr, modules=["math"])
    x_min, x_max = sorted((x_lower, x_upper))
    y_min, y_max = sorted((y_lower, y_upper))
    if x_min == x_max:
        x_min -= 1.0
        x_max += 1.0
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0

    size = 35
    rows: list[list[dict[str, float | None]]] = []
    finite_z: list[float] = []
    for yi in range(size):
        ty = yi / (size - 1)
        yv = y_min + (y_max - y_min) * ty
        row: list[dict[str, float | None]] = []
        for xi in range(size):
            tx = xi / (size - 1)
            xv = x_min + (x_max - x_min) * tx
            zv: float | None
            try:
                raw = fn(xv, yv)
                if isinstance(raw, complex):
                    raw = raw.real if abs(raw.imag) <= 1e-10 else math.nan
                candidate = float(raw)
                zv = candidate if math.isfinite(candidate) else None
            except Exception:
                zv = None

            if zv is not None:
                finite_z.append(zv)
            row.append({"x": xv, "y": yv, "z": zv})
        rows.append(row)

    if finite_z:
        finite_z.sort()
        low_index = max(0, int(len(finite_z) * 0.02) - 1)
        high_index = min(len(finite_z) - 1, int(len(finite_z) * 0.98))
        z_min = min(0.0, finite_z[low_index])
        z_max = max(0.0, finite_z[high_index])
        if z_min == z_max:
            z_min -= 1.0
            z_max += 1.0
        z_pad = (z_max - z_min) * 0.16
        z_min -= z_pad
        z_max += z_pad
    else:
        z_min, z_max = -1.0, 1.0

    return {
        "kind": "surface",
        "rows": rows,
        "xMin": x_min,
        "xMax": x_max,
        "yMin": y_min,
        "yMax": y_max,
        "zMin": z_min,
        "zMax": z_max,
    }


def integrate_double_payload(
    expr: sp.Expr,
    request: dict[str, Any],
    warnings: list[str],
    response: dict[str, Any],
) -> dict[str, Any]:
    x_lower_expr = parse_math(str(request.get("xLower", request.get("lower", "0"))))
    x_upper_expr = parse_math(str(request.get("xUpper", request.get("upper", "1"))))
    y_lower_expr = parse_math(str(request.get("yLower", "0")))
    y_upper_expr = parse_math(str(request.get("yUpper", "1")))

    x_lower = finite_float(x_lower_expr)
    x_upper = finite_float(x_upper_expr)
    y_lower = finite_float(y_lower_expr)
    y_upper = finite_float(y_upper_expr)
    eps = float(request.get("epsilon", 1e-8))

    response["bounds"] = {
        "x_lower": str(x_lower_expr),
        "x_upper": str(x_upper_expr),
        "y_lower": str(y_lower_expr),
        "y_upper": str(y_upper_expr),
        "x_lower_latex": safe_latex(x_lower_expr),
        "x_upper_latex": safe_latex(x_upper_expr),
        "y_lower_latex": safe_latex(y_lower_expr),
        "y_upper_latex": safe_latex(y_upper_expr),
        "x_lower_float": x_lower,
        "x_upper_float": x_upper,
        "y_lower_float": y_lower,
        "y_upper_float": y_upper,
    }

    response["double"] = {
        "region_type": "rectangular",
        "region_text": f"x in [{x_lower_expr}, {x_upper_expr}], y in [{y_lower_expr}, {y_upper_expr}]",
    }
    response["antiderivative"] = {"available": False}

    exact = sp.integrate(expr, (y, y_lower_expr, y_upper_expr), (x, x_lower_expr, x_upper_expr))
    if not has_unevaluated_integral(exact):
        exact = sp.simplify(exact)
        response["exact"] = {
            "available": True,
            "text": str(exact),
            "latex": safe_latex(exact),
            "numeric": safe_numeric_value(exact) if exact.is_real is not False else None,
        }
    else:
        response["exact"] = {"available": False}

    numeric = numeric_double_with_cpp(expr, x_lower, x_upper, y_lower, y_upper, eps, warnings)
    if numeric is None:
        numeric = numeric_double_with_scipy(expr, x_lower, x_upper, y_lower, y_upper, eps)
    response["numeric"] = numeric
    response["plot"] = sample_surface(expr, x_lower, x_upper, y_lower, y_upper)
    return response


def ensure_symbols(expr: sp.Expr, allowed: set[sp.Symbol], label: str) -> None:
    extra = expr.free_symbols - allowed
    if extra:
        names = ", ".join(sorted(str(symbol) for symbol in extra))
        allowed_names = ", ".join(sorted(str(symbol) for symbol in allowed))
        raise ValueError(f"{label} only supports variables {allowed_names}. Unknown: {names}")


def integrate_polar_area_payload(
    outer_expr: sp.Expr,
    request: dict[str, Any],
    warnings: list[str],
    response: dict[str, Any],
) -> dict[str, Any]:
    ensure_symbols(outer_expr, {theta}, "Polar radius")
    inner_expr = parse_math(str(request.get("innerExpression", request.get("inner", "0")) or "0"))
    ensure_symbols(inner_expr, {theta}, "Inner polar radius")

    theta_lower_expr = parse_math(str(request.get("thetaLower", request.get("lower", "0"))))
    theta_upper_expr = parse_math(str(request.get("thetaUpper", request.get("upper", "2*pi"))))
    theta_lower = finite_float(theta_lower_expr)
    theta_upper = finite_float(theta_upper_expr)
    eps = float(request.get("epsilon", 1e-8))

    area_integrand = sp.simplify(sp.Rational(1, 2) * (outer_expr**2 - inner_expr**2))
    response["bounds"] = {
        "theta_lower": str(theta_lower_expr),
        "theta_upper": str(theta_upper_expr),
        "theta_lower_latex": safe_latex(theta_lower_expr),
        "theta_upper_latex": safe_latex(theta_upper_expr),
        "theta_lower_float": theta_lower,
        "theta_upper_float": theta_upper,
    }
    response["polar"] = {
        "type": "area",
        "outer": str(outer_expr),
        "inner": str(inner_expr),
        "outer_latex": safe_latex(outer_expr),
        "inner_latex": safe_latex(inner_expr),
        "integrand": str(area_integrand),
        "integrand_latex": safe_latex(area_integrand),
        "region_text": f"theta in [{theta_lower_expr}, {theta_upper_expr}], r between {inner_expr} and {outer_expr}",
    }

    antiderivative = sp.integrate(area_integrand, theta)
    if not has_unevaluated_integral(antiderivative):
        antiderivative = sp.simplify(antiderivative)
        response["antiderivative"] = {
            "available": True,
            "text": str(antiderivative),
            "latex": safe_latex(antiderivative),
            "verified": sp.simplify(sp.diff(antiderivative, theta) - area_integrand) == 0,
        }
    else:
        response["antiderivative"] = {"available": False}

    exact = sp.integrate(area_integrand, (theta, theta_lower_expr, theta_upper_expr))
    if not has_unevaluated_integral(exact):
        exact = sp.simplify(exact)
        response["exact"] = {
            "available": True,
            "text": str(exact),
            "latex": safe_latex(exact),
            "numeric": safe_numeric_value(exact) if exact.is_real is not False else None,
        }
    else:
        response["exact"] = {"available": False}

    numeric = numeric_with_cpp(area_integrand.subs(theta, x), theta_lower, theta_upper, eps, warnings)
    if numeric is None:
        numeric = numeric_with_scipy(area_integrand.subs(theta, x), theta_lower, theta_upper, eps, [])
        if numeric.get("integration_warnings"):
            warnings.extend(numeric["integration_warnings"])
    response["numeric"] = numeric
    response["plot"] = sample_polar_area(outer_expr, inner_expr, theta_lower, theta_upper)
    return response


def integrate_polar_double_payload(
    expr: sp.Expr,
    request: dict[str, Any],
    warnings: list[str],
    response: dict[str, Any],
) -> dict[str, Any]:
    ensure_symbols(expr, {r, theta}, "Polar integrand")
    r_lower_expr = parse_math(str(request.get("rLower", "0")))
    r_upper_expr = parse_math(str(request.get("rUpper", "1")))
    ensure_symbols(r_lower_expr, {theta}, "Lower polar radius")
    ensure_symbols(r_upper_expr, {theta}, "Upper polar radius")

    theta_lower_expr = parse_math(str(request.get("thetaLower", request.get("lower", "0"))))
    theta_upper_expr = parse_math(str(request.get("thetaUpper", request.get("upper", "2*pi"))))
    theta_lower = finite_float(theta_lower_expr)
    theta_upper = finite_float(theta_upper_expr)
    eps = float(request.get("epsilon", 1e-8))
    integrand = sp.simplify(expr * r)

    response["bounds"] = {
        "theta_lower": str(theta_lower_expr),
        "theta_upper": str(theta_upper_expr),
        "r_lower": str(r_lower_expr),
        "r_upper": str(r_upper_expr),
        "theta_lower_latex": safe_latex(theta_lower_expr),
        "theta_upper_latex": safe_latex(theta_upper_expr),
        "r_lower_latex": safe_latex(r_lower_expr),
        "r_upper_latex": safe_latex(r_upper_expr),
        "theta_lower_float": theta_lower,
        "theta_upper_float": theta_upper,
    }
    response["polar"] = {
        "type": "double",
        "integrand_without_jacobian": str(expr),
        "integrand_with_jacobian": str(integrand),
        "integrand_with_jacobian_latex": safe_latex(integrand),
        "region_text": f"theta in [{theta_lower_expr}, {theta_upper_expr}], r in [{r_lower_expr}, {r_upper_expr}]",
        "jacobian": "r",
    }
    response["antiderivative"] = {"available": False}

    exact = sp.integrate(integrand, (r, r_lower_expr, r_upper_expr), (theta, theta_lower_expr, theta_upper_expr))
    if not has_unevaluated_integral(exact):
        exact = sp.simplify(exact)
        response["exact"] = {
            "available": True,
            "text": str(exact),
            "latex": safe_latex(exact),
            "numeric": safe_numeric_value(exact) if exact.is_real is not False else None,
        }
    else:
        response["exact"] = {"available": False}

    numeric = None
    if not r_lower_expr.has(theta) and not r_upper_expr.has(theta):
        try:
            r_lower_float = finite_float(r_lower_expr)
            r_upper_float = finite_float(r_upper_expr)
            numeric = numeric_double_with_cpp(
                integrand.subs({theta: x, r: y}),
                theta_lower,
                theta_upper,
                r_lower_float,
                r_upper_float,
                eps,
                warnings,
            )
        except Exception as exc:
            warnings.append(f"Polar C++ numeric path skipped: {exc}")
    if numeric is None:
        numeric = numeric_polar_double_with_scipy(integrand, r_lower_expr, r_upper_expr, theta_lower, theta_upper, eps)
    response["numeric"] = numeric
    response["plot"] = sample_polar_surface(expr, r_lower_expr, r_upper_expr, theta_lower, theta_upper)
    return response


def integrate_payload(request: dict[str, Any]) -> dict[str, Any]:
    mode = str(request.get("mode", "definite"))
    expr = parse_math(str(request.get("expression", "")))
    free_symbols = expr.free_symbols
    if mode == "double":
        allowed_symbols = {x, y}
    elif mode == "polar_area":
        allowed_symbols = {theta}
    elif mode == "polar_double":
        allowed_symbols = {r, theta}
    else:
        allowed_symbols = {x}
    if free_symbols - allowed_symbols:
        names = ", ".join(sorted(str(symbol) for symbol in free_symbols - allowed_symbols))
        if mode == "double":
            allowed_names = "x and y"
        elif mode == "polar_area":
            allowed_names = "theta"
        elif mode == "polar_double":
            allowed_names = "r and theta"
        else:
            allowed_names = "x"
        raise ValueError(f"Only the variable {allowed_names} is supported in this mode. Unknown: {names}")

    warnings: list[str] = []
    response: dict[str, Any] = {
        "ok": True,
        "mode": mode,
        "expression": str(expr),
        "expression_latex": safe_latex(expr),
        "warnings": warnings,
    }

    if mode == "double":
        return integrate_double_payload(expr, request, warnings, response)
    if mode == "polar_area":
        return integrate_polar_area_payload(expr, request, warnings, response)
    if mode == "polar_double":
        return integrate_polar_double_payload(expr, request, warnings, response)

    antiderivative = sp.integrate(expr, x)
    if not has_unevaluated_integral(antiderivative):
        simplified_antiderivative = sp.simplify(antiderivative)
        verification = sp.simplify(sp.diff(simplified_antiderivative, x) - expr)
        response["antiderivative"] = {
            "available": True,
            "text": str(simplified_antiderivative),
            "latex": safe_latex(simplified_antiderivative),
            "verified": verification == 0,
        }
    else:
        response["antiderivative"] = {"available": False}

    if mode == "indefinite":
        response["plot"] = sample_function(expr, None, None)
        return response

    lower_expr = parse_math(str(request.get("lower", "0")))
    upper_expr = parse_math(str(request.get("upper", "1")))
    lower = bound_float(lower_expr) if mode == "improper" else finite_float(lower_expr)
    upper = bound_float(upper_expr) if mode == "improper" else finite_float(upper_expr)
    eps = float(request.get("epsilon", 1e-8))
    lower_order = min(lower, upper)
    upper_order = max(lower, upper)
    singular_points, singular_notes = find_singular_points(expr, lower_order, upper_order)
    warnings.extend(singular_notes)

    response["bounds"] = {
        "lower": str(lower_expr),
        "upper": str(upper_expr),
        "lower_latex": safe_latex(lower_expr),
        "upper_latex": safe_latex(upper_expr),
        "lower_float": json_float(lower),
        "upper_float": json_float(upper),
        "lower_infinite": not math.isfinite(lower),
        "upper_infinite": not math.isfinite(upper),
    }

    exact = sp.integrate(expr, (x, lower_expr, upper_expr))
    if not has_unevaluated_integral(exact):
        exact = sp.simplify(exact)
        response["exact"] = {
            "available": True,
            "text": str(exact),
            "latex": safe_latex(exact),
            "numeric": safe_numeric_value(exact) if exact.is_real is not False else None,
        }
    else:
        response["exact"] = {"available": False}

    if mode == "improper":
        status, reason = classify_integral_result(exact)
        response["improper"] = {
            "status": status,
            "reason": reason,
            "has_infinite_bound": not math.isfinite(lower) or not math.isfinite(upper),
            "singularities": [
                {
                    "text": item["text"],
                    "latex": item["latex"],
                    "float": item["float"],
                    "location": item["location"],
                }
                for item in singular_points
            ],
        }

        split_points = [item["float"] for item in singular_points if item["location"] == "internal"]
        if status == "divergent":
            response["numeric"] = {
                "ok": False,
                "value": None,
                "estimated_error": None,
                "evaluations": None,
                "method": "not_run_divergent",
                "engine": "symbolic_check",
            }
        else:
            numeric = numeric_with_scipy(expr, lower, upper, eps, split_points)
            if numeric.get("integration_warnings"):
                warnings.extend(numeric["integration_warnings"])
            response["numeric"] = numeric
    else:
        numeric = numeric_with_cpp(expr, lower, upper, eps, warnings)
        if numeric is None:
            split_points = [item["float"] for item in singular_points if item["location"] == "internal"]
            numeric = numeric_with_scipy(expr, lower, upper, eps, split_points)
            if numeric.get("integration_warnings"):
                warnings.extend(numeric["integration_warnings"])
        response["numeric"] = numeric

    response["plot"] = sample_function(expr, lower, upper)
    return response


def normalize_raw_integral(raw: str) -> str:
    return (
        raw.strip()
        .replace("∞", "oo")
        .replace("π", "pi")
        .replace("−", "-")
        .replace("×", "*")
        .replace("·", "*")
    )


def apply_raw_integral(request: dict[str, Any]) -> dict[str, Any]:
    raw = normalize_raw_integral(str(request.get("raw", "")))
    if not raw:
        return request

    polar_match = re.match(
        r"^r\s*=\s*(.+?)\s*,\s*theta\s*=\s*(.+?)\.\.(.+)$",
        raw.strip(),
        flags=re.IGNORECASE,
    )
    if polar_match:
        radius_text, lower_text, upper_text = polar_match.groups()
        updated = dict(request)
        updated["mode"] = "polar_area"
        updated["expression"] = radius_text
        updated["thetaLower"] = lower_text
        updated["thetaUpper"] = upper_text
        updated.setdefault("innerExpression", "0")
        return updated

    spaced_single = re.match(r"^∫_([^\^]+)\^([^\s]+)\s+(.+?)\s*dx$", raw)
    if spaced_single:
        lower_text, upper_text, expression_text = spaced_single.groups()
        updated = dict(request)
        updated["expression"] = expression_text
        updated["lower"] = lower_text
        updated["upper"] = upper_text
        if upper_text in {"oo", "+oo", "infty", "infinity"} or lower_text in {"-oo", "-infty", "-infinity"}:
            updated["mode"] = "improper"
        else:
            updated.setdefault("mode", "definite")
        return updated

    compact = re.sub(r"\s+", "", raw)
    double_match = re.match(r"^∫∫(.+?)(?:dA|dxdy|dydx)$", compact)
    if double_match:
        updated = dict(request)
        updated["mode"] = "double"
        updated["expression"] = double_match.group(1)
        updated.setdefault("xLower", "0")
        updated.setdefault("xUpper", "1")
        updated.setdefault("yLower", "0")
        updated.setdefault("yUpper", "1")
        return updated

    single_match = re.match(r"^∫_([^\^]+)\^(-?oo|\+?oo|-?infty|\+?infty|pi|-?\d+(?:\.\d+)?)(.+)dx$", compact)
    if single_match:
        lower_text, upper_text, expression_text = single_match.groups()
        updated = dict(request)
        updated["expression"] = expression_text
        updated["lower"] = lower_text
        updated["upper"] = upper_text
        if upper_text in {"oo", "+oo", "infty", "infinity"} or lower_text in {"-oo", "-infty", "-infinity"}:
            updated["mode"] = "improper"
        else:
            updated.setdefault("mode", "definite")
        return updated

    return request


def solve_statement_latex(request: dict[str, Any], integration: dict[str, Any]) -> str:
    mode = integration.get("mode")
    expr_latex = integration.get("expression_latex", str(request.get("expression", "")))
    bounds = integration.get("bounds", {})
    if mode == "indefinite":
        return f"\\int {expr_latex}\\,dx"
    if mode == "polar_area":
        polar = integration.get("polar", {})
        outer = polar.get("outer_latex", expr_latex)
        inner = polar.get("inner_latex", "0")
        return (
            "\\frac12\\int_{"
            + bounds.get("theta_lower_latex", "\\alpha")
            + "}^{"
            + bounds.get("theta_upper_latex", "\\beta")
            + "}\\left(("
            + outer
            + ")^2-("
            + inner
            + ")^2\\right)\\,d\\theta"
        )
    if mode == "polar_double":
        return (
            "\\int_{"
            + bounds.get("theta_lower_latex", "\\alpha")
            + "}^{"
            + bounds.get("theta_upper_latex", "\\beta")
            + "}\\int_{"
            + bounds.get("r_lower_latex", "a")
            + "}^{"
            + bounds.get("r_upper_latex", "b")
            + "} "
            + expr_latex
            + "\\,r\\,dr\\,d\\theta"
        )
    if mode == "double":
        return (
            "\\int_{"
            + bounds.get("x_lower_latex", "a")
            + "}^{"
            + bounds.get("x_upper_latex", "b")
            + "}\\int_{"
            + bounds.get("y_lower_latex", "c")
            + "}^{"
            + bounds.get("y_upper_latex", "d")
            + "}"
            + expr_latex
            + "\\,dy\\,dx"
        )
    return (
        "\\int_{"
        + bounds.get("lower_latex", "a")
        + "}^{"
        + bounds.get("upper_latex", "b")
        + "}"
        + expr_latex
        + "\\,dx"
    )


def result_latex(integration: dict[str, Any]) -> str:
    exact = integration.get("exact", {})
    if exact.get("available") and exact.get("latex"):
        return exact["latex"]
    antiderivative = integration.get("antiderivative", {})
    if antiderivative.get("available") and antiderivative.get("latex"):
        return antiderivative["latex"] + "+C"
    numeric = integration.get("numeric", {})
    if numeric.get("ok") is False:
        return "\\text{发散或无有限值}"
    value = numeric.get("value")
    if value is not None:
        return str(value)
    return "\\text{暂无法给出闭式结果}"


def is_simple_u_sub(expr: sp.Expr) -> bool:
    return bool(expr.has(sp.cos(x**2), sp.sin(x**2), sp.exp(x**2))) and bool(expr.has(x))


def is_parts_candidate(expr: sp.Expr) -> bool:
    return bool(
        expr.has(x * sp.exp(x))
        or expr.has(x * sp.sin(x))
        or expr.has(x * sp.cos(x))
        or expr.has(sp.log(x))
    )


def is_separable_xy(expr: sp.Expr) -> bool:
    if not expr.has(x) or not expr.has(y):
        return False
    factors = sp.Mul.make_args(sp.factor(expr))
    has_x_factor = any(free <= {x} and free for free in (factor.free_symbols for factor in factors))
    has_y_factor = any(free <= {y} and free for free in (factor.free_symbols for factor in factors))
    return has_x_factor and has_y_factor


def normalize_language(request: dict[str, Any]) -> str:
    return "en-US" if str(request.get("language", "zh-CN")).lower().startswith("en") else "zh-CN"


METHOD_ENGLISH = {
    "u_sub_cos_power_sin": ("Substitution", "The integrand contains a power of cosine and the differential of cosine, so substitution turns it into a power integral."),
    "u_sub_sin_power_cos": ("Substitution", "The integrand contains a power of sine and the differential of sine, so substitution turns it into a power integral."),
    "trig_power_reduction": ("Trigonometric power reduction", "An even trigonometric power is rewritten with a power-reduction identity before integrating."),
    "trig_product_to_sum": ("Product-to-sum identity", "A product of trigonometric functions is rewritten as a sum so each term can be integrated directly."),
    "integration_by_parts": ("Integration by parts", "For a product, choose one factor to differentiate and the other to integrate, then apply the integration-by-parts formula."),
    "trig_identity_abs_piecewise": ("Trigonometric identity and sign split", "Factor the radical, use a Pythagorean identity, then split the absolute value where the sign changes."),
    "improper_limit": ("Improper integral: limit definition", "Rewrite the infinite or singular endpoint as a limit before evaluating."),
    "rectangular_double_integral": ("Double integral over a rectangle", "Compute the iterated integral one variable at a time."),
    "polar_area_formula": ("Polar area formula", "Use the thin-sector area element for a polar curve."),
    "polar_double_jacobian": ("Polar double integral: Jacobian factor", r"In polar coordinates the area element is multiplied by the Jacobian factor \(r\)."),
    "fundamental_theorem": ("Definite integral: Fundamental Theorem of Calculus", "Find an antiderivative first, then evaluate it at the upper and lower bounds."),
    "generic_antiderivative": ("Indefinite integral: antiderivative", "Find a function whose derivative is the integrand, then add the constant of integration."),
}


CONCEPT_ENGLISH = {
    "基本原函数": "basic antiderivatives",
    "逐项积分": "term-by-term integration",
    "换元法": "substitution",
    "链式法则逆用": "reverse chain rule",
    "分部积分": "integration by parts",
    "恒等变形": "identity transformation",
    "有理函数": "rational functions",
    "特殊函数": "special functions",
    "多步骤技巧": "multi-step techniques",
    "微积分基本定理": "Fundamental Theorem of Calculus",
    "有向面积": "signed area",
    "对称性": "symmetry",
    "三角恒等式": "trigonometric identities",
    "部分分式": "partial fractions",
    "技巧综合": "combined techniques",
    "数值校验": "numerical check",
    "挑战积分": "challenge integral",
    "极限定义": "limit definition",
    "p 型积分": "p-integral",
    "收敛判别": "convergence test",
    "端点奇异": "endpoint singularity",
    "指数尾部": "exponential tail",
    "比较判别": "comparison test",
    "对数换元": "log substitution",
    "双重反常": "two-sided improper integral",
    "条件收敛": "conditional convergence",
    "高精度数值": "high-precision numeric check",
    "矩形区域": "rectangular region",
    "曲面体积": "surface volume",
    "累次积分": "iterated integral",
    "可分离函数": "separable function",
    "二重积分技巧": "double-integral techniques",
    "耦合曲面": "coupled surface",
    "可分离结构": "separable structure",
    "数值曲面体积": "numeric surface volume",
    "振荡曲面": "oscillating surface",
    "极坐标面积": "polar area",
    "扇形微元": "sector element",
    "心形线": "cardioid",
    "玫瑰线": "rose curve",
    "夹层面积": "area between curves",
    "极坐标二重积分": "polar double integral",
    "雅可比因子": "Jacobian factor",
    "变量边界": "variable bounds",
    "数值极坐标": "numeric polar integral",
    "复杂边界": "complex bounds",
}


PROBLEM_TITLE_ENGLISH = {
    "definite": "Definite integral practice",
    "indefinite": "Indefinite integral practice",
    "improper": "Improper integral practice",
    "double": "Double integral practice",
    "polar_area": "Polar area practice",
    "polar_double": "Polar double integral practice",
}


PROBLEM_TARGET_ENGLISH = {
    "definite": "Choose a reliable integration technique, show the algebra, and check the answer.",
    "indefinite": "Find an antiderivative and verify it by differentiation.",
    "improper": "Rewrite the problem as a limit and decide whether it converges.",
    "double": "Evaluate the iterated integral over the given region.",
    "polar_area": "Use the polar area formula and show the radius-square step.",
    "polar_double": r"Use the polar Jacobian \(r\) and evaluate the iterated integral.",
}


def english_steps(
    integration: dict[str, Any],
    statement: str,
    final: str,
    method: str,
    algebra: dict[str, Any],
) -> list[str]:
    steps = [f"Write the problem as \\({statement}\\).", f"Method choice: {method}."]
    steps.extend(algebra.get("reasoning_steps", []))
    exact = integration.get("exact", {})
    numeric = integration.get("numeric", {})
    if exact.get("available"):
        steps.append(f"Exact result: \\({exact.get('latex')}\\).")
    if numeric.get("value") is not None:
        steps.append(f"Numerical check: \\({numeric.get('value')}\\), estimated error \\({numeric.get('estimated_error')}\\).")
    steps.append(f"Final answer: \\({final}\\).")
    return steps


def localize_solution_payload(payload: dict[str, Any], language: str) -> dict[str, Any]:
    payload["language"] = language
    if language != "en-US":
        return payload
    algebra = payload.get("algebra_steps", {})
    recipe_id = algebra.get("recipe_id", "")
    method, explanation = METHOD_ENGLISH.get(
        recipe_id,
        ("Symbolic computation with numerical verification", "The system can compute the answer, but this expression is not yet matched to a reliable full derivation template."),
    )
    payload["method"] = method
    payload["method_explanation"] = explanation
    if payload.get("ok"):
        payload["steps"] = english_steps(payload, payload.get("statement_latex", ""), payload.get("result_latex", ""), method, algebra)
    else:
        payload["method"] = "Unable to identify a reliable method"
        payload["method_explanation"] = "The expression or bounds could not be parsed. Please check the input."
        payload["steps"] = ["The problem was not parsed successfully, so no calculation steps were generated."]
    return payload


def localize_problem_item(problem_item: dict[str, Any], language: str) -> dict[str, Any]:
    if language != "en-US":
        return problem_item
    localized = dict(problem_item)
    mode = str(localized.get("mode", "definite"))
    localized["title"] = PROBLEM_TITLE_ENGLISH.get(mode, "Integral practice")
    localized["target"] = PROBLEM_TARGET_ENGLISH.get(mode, "Solve the integral and verify the result.")
    localized["kindLabel"] = {
        "definite": "Definite integral",
        "indefinite": "Indefinite integral",
        "improper": "Improper integral",
        "double": "Double integral",
        "polar": "Polar integral",
    }.get(str(localized.get("kind")), str(localized.get("kindLabel", "")))
    localized["levelLabel"] = {
        "easy": "Easy",
        "ap": "AP",
        "advanced": "Advanced techniques",
        "mit": "MIT / Challenge",
    }.get(str(localized.get("level")), str(localized.get("levelLabel", "")))
    localized["concepts"] = [CONCEPT_ENGLISH.get(item, item) for item in localized.get("concepts", [])]
    localized["methodTags"] = [CONCEPT_ENGLISH.get(item, item) for item in localized.get("methodTags", [])]
    return localized


def identify_solution_method(request: dict[str, Any], expr: sp.Expr, integration: dict[str, Any]) -> tuple[str, str]:
    mode = integration.get("mode")
    if mode == "polar_area":
        return "极坐标面积公式", "把极坐标曲线围成的区域看成许多很薄的扇形，面积微元是 \\(\\frac12 r^2\\,d\\theta\\)。若有内外半径，就用外半径平方减内半径平方。"
    if mode == "polar_double":
        return "极坐标二重积分：雅可比因子 r", "把平面微元从 \\(dx\\,dy\\) 换成极坐标时，面积微元变成 \\(r\\,dr\\,d\\theta\\)，所以被积函数必须乘上 \\(r\\)。"
    if mode == "double":
        if is_separable_xy(expr):
            return "矩形区域二重积分：可分离函数", "把曲面高度写成 x 部分和 y 部分的乘积，再把二重积分拆成两个一元积分。"
        if expr.is_polynomial(x, y):
            return "矩形区域二重积分：累次积分", "先固定 x 对 y 积分，再对 x 积分；也可以理解为曲面下的有向体积。"
        return "矩形区域二重积分：数值与符号结合", "在矩形区域上累积曲面高度，优先给精确结果，必要时用数值积分核验。"
    if mode == "improper":
        return "反常积分：极限定义", "先把无穷端点或奇异端点改写成极限，再判断极限是否有限。"
    if mode == "indefinite":
        if expr.is_polynomial(x):
            return "不定积分：幂函数公式", "逐项使用幂函数积分公式，并加上常数 C。"
        if is_parts_candidate(expr):
            return "不定积分：分部积分候选", "这是乘积型表达式，优先考虑分部积分；若规则不完全匹配，则用符号引擎核验。"
        return "不定积分：寻找原函数", "目标是找到一个求导后等于原函数的 F(x)。"
    if expr.is_polynomial(x):
        return "定积分：幂函数公式 + 微积分基本定理", "先求原函数，再代入上下限得到有向面积。"
    if is_simple_u_sub(expr):
        return "定积分：换元法", "识别内层函数和它的导数，把复杂复合函数化成更简单的一元积分。"
    if is_parts_candidate(expr):
        return "定积分：分部积分", "乘积型函数通常考虑分部积分，然后用上下限代入。"
    if expr.has(sp.sin, sp.cos, sp.tan):
        return "定积分：三角函数基本积分", "先用基础三角函数原函数，再通过图像检查正负面积。"
    return "定积分：符号计算 + 数值核验", "先尝试精确积分，再用数值积分和图像检查答案大小。"


def solve_steps(request: dict[str, Any], expr: sp.Expr, integration: dict[str, Any], method: str) -> list[str]:
    mode = integration.get("mode")
    statement = solve_statement_latex(request, integration)
    final = result_latex(integration)
    steps: list[str] = [f"题目写作：\\({statement}\\)。", f"方法判断：{method}。"]

    if mode == "polar_area":
        bounds = integration.get("bounds", {})
        polar = integration.get("polar", {})
        steps.append(
            "极坐标面积来自扇形面积微元："
            "\\(dA=\\frac12 r^2\\,d\\theta\\)。"
        )
        steps.append(
            "本题角度范围是 "
            f"\\(\\theta\\in[{bounds.get('theta_lower_latex','\\alpha')},{bounds.get('theta_upper_latex','\\beta')}]\\)，"
            f"外半径 \\(r_{{out}}={polar.get('outer_latex','r(\\theta)')}\\)，"
            f"内半径 \\(r_{{in}}={polar.get('inner_latex','0')}\\)。"
        )
        steps.append(
            "代入公式："
            f"\\(A=\\frac12\\int (r_{{out}}^2-r_{{in}}^2)\\,d\\theta"
            f"=\\int {polar.get('integrand_latex','')}\\,d\\theta\\)。"
        )
    elif mode == "polar_double":
        bounds = integration.get("bounds", {})
        polar = integration.get("polar", {})
        steps.append(
            "极坐标二重积分的面积微元是 "
            "\\(dA=r\\,dr\\,d\\theta\\)，这个 \\(r\\) 是坐标变换的雅可比因子。"
        )
        steps.append(
            "积分区域写作 "
            f"\\(\\theta\\in[{bounds.get('theta_lower_latex','\\alpha')},{bounds.get('theta_upper_latex','\\beta')}],"
            f"r\\in[{bounds.get('r_lower_latex','a')},{bounds.get('r_upper_latex','b')}]\\)。"
        )
        steps.append(
            "所以实际计算的被积函数是 "
            f"\\({polar.get('integrand_with_jacobian_latex','f(r,\\theta)r')}\\)。"
        )
    elif mode == "double":
        bounds = integration.get("bounds", {})
        steps.append(
            "区域是矩形："
            f"\\(x\\in[{bounds.get('x_lower_latex','a')},{bounds.get('x_upper_latex','b')}],"
            f"y\\in[{bounds.get('y_lower_latex','c')},{bounds.get('y_upper_latex','d')}]\\)。"
        )
        if is_separable_xy(expr):
            steps.append("因为函数可分离，矩形区域上的二重积分可以拆成 x 积分与 y 积分的乘积。")
        else:
            steps.append("按累次积分理解：先对内层变量积分，再对外层变量积分。")
        steps.append("图像中底面矩形是积分区域，曲面 \\(z=f(x,y)\\) 的高度累积成体积。")
    elif mode == "improper":
        improper = integration.get("improper", {})
        steps.append("反常积分不能直接把无穷或奇点当普通数字代入，必须先写成极限。")
        if improper.get("singularities"):
            points = ", ".join(item.get("text", "?") for item in improper["singularities"])
            steps.append(f"检测到奇点：\\({points}\\)，需要用单侧极限分段处理。")
        if improper.get("status"):
            status_text = {"convergent": "收敛", "divergent": "发散", "unknown": "待判定"}.get(improper["status"], improper["status"])
            steps.append(f"符号判定结果：{status_text}。{improper.get('reason', '')}")
    elif mode == "indefinite":
        antiderivative = integration.get("antiderivative", {})
        if antiderivative.get("available"):
            steps.append(f"找到原函数：\\(F(x)={antiderivative.get('latex')}\\)。")
            steps.append("不定积分答案要加常数 \\(C\\)，因为常数求导后为 0。")
        else:
            steps.append("符号引擎暂时没有找到可靠闭式原函数，可以保留为数值或特殊函数形式。")
    else:
        antiderivative = integration.get("antiderivative", {})
        if antiderivative.get("available"):
            bounds = integration.get("bounds", {})
            steps.append(f"先求原函数：\\(F(x)={antiderivative.get('latex')}\\)。")
            steps.append(
                "使用微积分基本定理："
                f"\\(\\int_{{{bounds.get('lower_latex','a')}}}^{{{bounds.get('upper_latex','b')}}}f(x)\\,dx="
                f"F({bounds.get('upper_latex','b')})-F({bounds.get('lower_latex','a')})\\)。"
            )
        else:
            steps.append("没有可靠闭式原函数时，使用自适应数值积分并用图像检查面积大小。")

    exact = integration.get("exact", {})
    numeric = integration.get("numeric", {})
    if exact.get("available"):
        steps.append(f"精确结果：\\({exact.get('latex')}\\)。")
    if numeric.get("value") is not None:
        steps.append(f"数值核验：\\({numeric.get('value')}\\)，误差估计约为 \\({numeric.get('estimated_error')}\\)。")
    steps.append(f"最终答案：\\({final}\\)。")
    return steps


def solve_payload(request: dict[str, Any]) -> dict[str, Any]:
    try:
        language = normalize_language(request)
        request = apply_raw_integral(request)
        request["language"] = language
        integration = integrate_payload(request)
        if not integration.get("ok"):
            return localize_solution_payload({
                **integration,
                "problem_type": integration.get("mode", request.get("mode")),
                "method": "无法可靠识别方法",
                "method_explanation": "题目格式或表达式暂时无法解析，请检查函数、变量和上下限。",
                "statement_latex": "",
                "result_latex": "",
                "steps": [
                    "题目没有成功解析，因此没有生成计算步骤。",
                    f"错误信息：{integration.get('error', '未知错误')}",
                ],
                "algebra_steps": algebra_steps.build_algebra_steps(
                    request=request,
                    expr=sp.Integer(0),
                    integration=integration,
                    statement_latex="",
                    final_latex="",
                    x=x,
                    y=y,
                    r=r,
                    theta=theta,
                ),
            }, language)

        expr = parse_math(str(request.get("expression", "")))
        method, explanation = identify_solution_method(request, expr, integration)
        statement = solve_statement_latex(request, integration)
        algebra = algebra_steps.build_algebra_steps(
            request=request,
            expr=expr,
            integration=integration,
            statement_latex=statement,
            final_latex=result_latex(integration),
            x=x,
            y=y,
            r=r,
            theta=theta,
        )
        return localize_solution_payload({
            **integration,
            "problem_type": integration.get("mode"),
            "method": method,
            "method_explanation": explanation,
            "statement_latex": statement,
            "result_latex": result_latex(integration),
            "steps": solve_steps(request, expr, integration, method),
            "algebra_steps": algebra,
        }, language)
    except Exception as exc:
        language = normalize_language(request)
        return localize_solution_payload({
            **make_error_response(exc),
            "problem_type": request.get("mode"),
            "method": "无法可靠识别方法",
            "method_explanation": "题目格式或表达式暂时无法解析，请检查函数、变量和上下限。",
            "statement_latex": "",
            "result_latex": "",
            "steps": [
                "题目没有成功解析，因此没有生成计算步骤。",
                f"错误信息：{exc}",
            ],
        }, language)


def make_error_response(exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "error": str(exc),
        "trace": traceback.format_exc(limit=2) if os.environ.get("CALCULUS_DEBUG") else None,
    }


def is_practice_solution_usable(solution: dict[str, Any]) -> bool:
    if not solution.get("ok"):
        return False
    if not solution.get("result_latex"):
        return False

    mode = solution.get("mode")
    if mode == "indefinite":
        return bool(solution.get("antiderivative", {}).get("available"))
    if mode == "improper":
        status = solution.get("improper", {}).get("status")
        if status == "divergent":
            return True
        return bool(solution.get("exact", {}).get("available") or solution.get("numeric", {}).get("value") is not None)
    if mode in {"definite", "double", "polar_area", "polar_double"}:
        return bool(solution.get("exact", {}).get("available") or solution.get("numeric", {}).get("value") is not None)
    return False


def generate_practice_payload(request: dict[str, Any]) -> dict[str, Any]:
    try:
        language = normalize_language(request)
        kind = str(request.get("kind", "definite"))
        level = str(request.get("level", "easy"))
        seed = problem_generator.make_seed(request.get("seed"))
        rng = problem_generator.make_rng(seed)
        raw_avoid = request.get("avoid_signatures", [])
        avoid_signatures = {str(item) for item in raw_avoid if item}
        max_attempts = min(max(int(request.get("max_attempts", 120)), 1), 500)
        last_error = ""

        for attempt in range(1, max_attempts + 1):
            candidate = problem_generator.generate_candidate(kind, level, rng)
            if candidate["signature"] in avoid_signatures:
                last_error = "generated duplicate signature"
                continue

            candidate["payload"]["language"] = language
            solution = solve_payload(candidate["payload"])
            if not is_practice_solution_usable(solution):
                last_error = solution.get("error") or "solution did not pass practice validation"
                continue
            wants_full_algebra = (
                candidate["problem"].get("explainability") == "full"
                and level in {"easy", "ap", "advanced"}
            )
            if wants_full_algebra and not solution.get("algebra_steps", {}).get("available"):
                last_error = "generated problem did not have reliable algebra steps"
                continue

            problem_item = {
                **candidate["problem"],
                "signature": candidate["signature"],
                "familyId": candidate["family_id"],
                "concepts": candidate["concepts"],
            }
            problem_item = localize_problem_item(problem_item, language)
            return {
                "ok": True,
                "problem": problem_item,
                "solution": solution,
                "signature": candidate["signature"],
                "family_id": candidate["family_id"],
                "concepts": candidate["concepts"],
                "seed": seed,
                "attempts": attempt,
                "capacity_estimate": problem_generator.total_capacity(kind, level),
                "source": "local-generator",
            }

        return {
            "ok": False,
            "error": f"Could not generate a validated practice problem after {max_attempts} attempts. Last error: {last_error}",
            "kind": kind,
            "level": level,
            "seed": seed,
        }
    except Exception as exc:
        return make_error_response(exc)


class CalculusHandler(BaseHTTPRequestHandler):
    server_version = "CalculusMVP/0.1"

    def send_cors_headers(self) -> None:
        origin = os.environ.get("CALCULUS_CORS_ORIGIN", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if origin != "*":
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        requested = unquote(parsed.path)
        if requested in {"/api/health", "/healthz"}:
            self.send_json(200, {"ok": True, "service": "calculus-studio"})
            return
        if requested == "/":
            requested = "/index.html"

        file_path = (WEB_ROOT / requested.lstrip("/")).resolve()
        try:
            file_path.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self.send_error(403)
            return

        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/integrate", "/api/solve", "/api/practice/generate"}:
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            request = json.loads(body.decode("utf-8"))
            if parsed.path == "/api/solve":
                response = solve_payload(request)
            elif parsed.path == "/api/practice/generate":
                response = generate_practice_payload(request)
            else:
                response = integrate_payload(request)
            self.send_json(200, response)
        except Exception as exc:
            self.send_json(400, make_error_response(exc))

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main() -> None:
    port_value = os.environ.get("PORT") or os.environ.get("CALCULUS_PORT") or (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PORT)
    port = int(port_value)
    host = os.environ.get("CALCULUS_HOST") or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    server = ThreadingHTTPServer((host, port), CalculusHandler)
    print(f"Calculus MVP running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
