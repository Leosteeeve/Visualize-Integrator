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


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
CPP_SOURCE = ROOT / "cpp" / "integrator.cpp"
CPP_EXE = ROOT / "cpp" / ("integrator.exe" if os.name == "nt" else "integrator")
DEFAULT_PORT = 8000

x = sp.Symbol("x", real=True)
y = sp.Symbol("y", real=True)
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


def integrate_payload(request: dict[str, Any]) -> dict[str, Any]:
    mode = str(request.get("mode", "definite"))
    expr = parse_math(str(request.get("expression", "")))
    free_symbols = expr.free_symbols
    allowed_symbols = {x, y} if mode == "double" else {x}
    if free_symbols - allowed_symbols:
        names = ", ".join(sorted(str(symbol) for symbol in free_symbols - allowed_symbols))
        allowed_names = "x and y" if mode == "double" else "x"
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


def identify_solution_method(request: dict[str, Any], expr: sp.Expr, integration: dict[str, Any]) -> tuple[str, str]:
    mode = integration.get("mode")
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

    if mode == "double":
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
        request = apply_raw_integral(request)
        integration = integrate_payload(request)
        if not integration.get("ok"):
            return {
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
            }

        expr = parse_math(str(request.get("expression", "")))
        method, explanation = identify_solution_method(request, expr, integration)
        statement = solve_statement_latex(request, integration)
        return {
            **integration,
            "problem_type": integration.get("mode"),
            "method": method,
            "method_explanation": explanation,
            "statement_latex": statement,
            "result_latex": result_latex(integration),
            "steps": solve_steps(request, expr, integration, method),
        }
    except Exception as exc:
        return {
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
        }


def make_error_response(exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "error": str(exc),
        "trace": traceback.format_exc(limit=2) if os.environ.get("CALCULUS_DEBUG") else None,
    }


class CalculusHandler(BaseHTTPRequestHandler):
    server_version = "CalculusMVP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        requested = unquote(parsed.path)
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
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/integrate", "/api/solve"}:
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            request = json.loads(body.decode("utf-8"))
            response = solve_payload(request) if parsed.path == "/api/solve" else integrate_payload(request)
            self.send_json(200, response)
        except Exception as exc:
            self.send_json(400, make_error_response(exc))

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main() -> None:
    port = int(os.environ.get("CALCULUS_PORT", sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PORT))
    server = ThreadingHTTPServer(("127.0.0.1", port), CalculusHandler)
    print(f"Calculus MVP running at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
