from __future__ import annotations

from typing import Any

import sympy as sp


def safe_latex(value: Any) -> str:
    try:
        return sp.latex(value)
    except Exception:
        return str(value)


def as_latex_bound(value: Any, fallback: str = "?") -> str:
    if value is None:
        return fallback
    try:
        return safe_latex(value)
    except Exception:
        return str(value)


def aligned(lines: list[str]) -> str:
    return "\\begin{aligned}\n" + "\\\\\n".join(lines) + "\n\\end{aligned}"


def coefficient_prefix(value: sp.Expr) -> str:
    value = sp.simplify(value)
    if value == 1:
        return ""
    if value == -1:
        return "-"
    return safe_latex(value)


def response(
    *,
    available: bool,
    explainability: str,
    recipe_id: str,
    lines: list[str] | None = None,
    notes: list[str] | None = None,
    reason: str = "",
    verified: bool = False,
    method_tags: list[str] | None = None,
) -> dict[str, Any]:
    step_lines = lines or []
    return {
        "available": available,
        "explainability": explainability,
        "recipe_id": recipe_id,
        "method_tags": method_tags or [],
        "lines": step_lines,
        "latex": aligned(step_lines) if step_lines else "",
        "notes": notes or [],
        "reason": reason,
        "verified": verified,
    }


def final_is_verified(integration: dict[str, Any]) -> bool:
    exact = integration.get("exact", {})
    antiderivative = integration.get("antiderivative", {})
    numeric = integration.get("numeric", {})
    return bool(
        exact.get("available")
        or antiderivative.get("verified")
        or (numeric.get("ok") is True and numeric.get("value") is not None)
    )


def result_latex(integration: dict[str, Any], fallback: str = "?") -> str:
    exact = integration.get("exact", {})
    if exact.get("available") and exact.get("latex"):
        return str(exact["latex"])
    antiderivative = integration.get("antiderivative", {})
    if antiderivative.get("available") and antiderivative.get("latex"):
        return str(antiderivative["latex"]) + "+C"
    improper = integration.get("improper", {})
    if improper.get("status") == "divergent":
        return r"\text{发散}"
    numeric = integration.get("numeric", {})
    if numeric.get("value") is not None:
        return safe_latex(sp.N(numeric["value"], 10))
    return fallback


def is_zero(expr: sp.Expr) -> bool:
    try:
        return sp.simplify(expr) == 0
    except Exception:
        return False


def get_bound(integration: dict[str, Any], key: str, symbol: sp.Symbol) -> sp.Expr | None:
    bounds = integration.get("bounds", {})
    value = bounds.get(key)
    if value is None:
        return None
    try:
        return sp.sympify(value)
    except Exception:
        text = bounds.get(f"{key}_latex")
        return sp.sympify(text) if text else None


def antiderivative_line(expr: sp.Expr, variable: sp.Symbol) -> sp.Expr | None:
    anti = sp.integrate(expr, variable)
    if anti.has(sp.Integral):
        return None
    return sp.simplify(anti)


def build_generic_single_variable(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    anti = integration.get("antiderivative", {})
    if not anti.get("available") or not anti.get("latex"):
        return None
    anti_latex = anti["latex"]
    if mode == "indefinite":
        return response(
            available=True,
            explainability="full",
            recipe_id="generic_antiderivative",
            method_tags=["原函数", "基本公式"],
            lines=[
                rf"{statement_latex} &= {anti_latex}+C",
            ],
            verified=bool(anti.get("verified")),
        )

    bounds = integration.get("bounds", {})
    lower = bounds.get("lower_latex", "a")
    upper = bounds.get("upper_latex", "b")
    return response(
        available=True,
        explainability="full",
        recipe_id="fundamental_theorem",
        method_tags=["原函数", "微积分基本定理"],
        lines=[
            rf"{statement_latex} &= \left[{anti_latex}\right]_{{{lower}}}^{{{upper}}}",
            rf"&= {final_latex}",
        ],
        verified=final_is_verified(integration),
    )


def match_cos_power_sin(expr: sp.Expr, x: sp.Symbol) -> tuple[sp.Expr, int] | None:
    for power in range(1, 13):
        base = sp.sin(x) * sp.cos(x) ** power
        coeff = sp.simplify(expr / base)
        if not coeff.has(x) and is_zero(expr - coeff * base):
            return coeff, power
    return None


def match_sin_power_cos(expr: sp.Expr, x: sp.Symbol) -> tuple[sp.Expr, sp.Rational] | None:
    for numerator in range(1, 17):
        for denominator in (1, 2, 3, 4):
            power = sp.Rational(numerator, denominator)
            base = sp.sin(x) ** power * sp.cos(x)
            coeff = sp.simplify(expr / base)
            if not coeff.has(x) and is_zero(expr - coeff * base):
                return coeff, power
    return None


def build_cos_power_sin(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    matched = match_cos_power_sin(expr, x)
    if not matched:
        return None
    coeff, power = matched
    coeff_latex = safe_latex(coeff)
    anti_coeff = sp.simplify(-coeff / (power + 1))
    anti_latex = safe_latex(anti_coeff * sp.Symbol("u") ** (power + 1))
    if mode == "indefinite":
        return response(
            available=True,
            explainability="full",
            recipe_id="u_sub_cos_power_sin",
            method_tags=["换元法", "三角复合函数"],
            lines=[
                rf"u &= \cos x,\quad du=-\sin x\,dx",
                rf"{statement_latex} &= {-sp.latex(coeff)}\int u^{{{power}}}\,du",
                rf"&= {anti_latex}+C",
                rf"&= {safe_latex(anti_coeff * sp.cos(x) ** (power + 1))}+C",
            ],
            verified=final_is_verified(integration),
        )

    bounds = integration.get("bounds", {})
    lower_expr = sp.sympify(bounds.get("lower", "0"))
    upper_expr = sp.sympify(bounds.get("upper", "0"))
    u_lower = sp.simplify(sp.cos(lower_expr))
    u_upper = sp.simplify(sp.cos(upper_expr))
    flipped = sp.simplify(-coeff)
    lines = [
        rf"u &= \cos x,\quad du=-\sin x\,dx",
        rf"{statement_latex} &= {coefficient_prefix(flipped)}\int_{{{safe_latex(u_lower)}}}^{{{safe_latex(u_upper)}}}u^{{{power}}}\,du",
    ]
    try:
        should_flip_bounds = bool(sp.N(u_lower) > sp.N(u_upper))
    except Exception:
        should_flip_bounds = False
    if u_lower != u_upper and should_flip_bounds:
        lines.append(rf"&= {coefficient_prefix(coeff)}\int_{{{safe_latex(u_upper)}}}^{{{safe_latex(u_lower)}}}u^{{{power}}}\,du")
        lines.append(rf"&= {coefficient_prefix(coeff)}\left[\frac{{u^{{{power + 1}}}}}{{{power + 1}}}\right]_{{{safe_latex(u_upper)}}}^{{{safe_latex(u_lower)}}}")
    else:
        lines.append(
            rf"&= {coefficient_prefix(flipped)}\left[\frac{{u^{{{power + 1}}}}}{{{power + 1}}}\right]_{{{safe_latex(u_lower)}}}^{{{safe_latex(u_upper)}}}"
        )
    lines.append(rf"&= {final_latex}")
    return response(
        available=True,
        explainability="full",
        recipe_id="u_sub_cos_power_sin",
        method_tags=["换元法", "三角复合函数"],
        lines=lines,
        verified=final_is_verified(integration),
    )


def build_sin_power_cos(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    matched = match_sin_power_cos(expr, x)
    if not matched:
        return None
    coeff, power = matched
    next_power = sp.simplify(power + 1)
    if mode == "indefinite":
        return response(
            available=True,
            explainability="full",
            recipe_id="u_sub_sin_power_cos",
            method_tags=["换元法", "三角复合函数"],
            lines=[
                rf"u &= \sin x,\quad du=\cos x\,dx",
                rf"{statement_latex} &= {safe_latex(coeff)}\int u^{{{safe_latex(power)}}}\,du",
                rf"&= {safe_latex(coeff / next_power)}u^{{{safe_latex(next_power)}}}+C",
                rf"&= {safe_latex(coeff / next_power * sp.sin(x) ** next_power)}+C",
            ],
            verified=final_is_verified(integration),
        )
    bounds = integration.get("bounds", {})
    lower_expr = sp.sympify(bounds.get("lower", "0"))
    upper_expr = sp.sympify(bounds.get("upper", "0"))
    u_lower = sp.simplify(sp.sin(lower_expr))
    u_upper = sp.simplify(sp.sin(upper_expr))
    return response(
        available=True,
        explainability="full",
        recipe_id="u_sub_sin_power_cos",
        method_tags=["换元法", "三角复合函数"],
        lines=[
            rf"u &= \sin x,\quad du=\cos x\,dx",
            rf"{statement_latex} &= {safe_latex(coeff)}\int_{{{safe_latex(u_lower)}}}^{{{safe_latex(u_upper)}}}u^{{{safe_latex(power)}}}\,du",
            rf"&= {safe_latex(coeff / next_power)}\left[u^{{{safe_latex(next_power)}}}\right]_{{{safe_latex(u_lower)}}}^{{{safe_latex(u_upper)}}}",
            rf"&= {final_latex}",
        ],
        verified=final_is_verified(integration),
    )


def build_parts(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    candidates = [
        (x * sp.exp(x), x, sp.exp(x), sp.exp(x), sp.exp(x), (x - 1) * sp.exp(x)),
        (x * sp.sin(x), x, sp.sin(x), 1, -sp.cos(x), sp.sin(x) - x * sp.cos(x)),
        (x * sp.cos(x), x, sp.cos(x), 1, sp.sin(x), x * sp.sin(x) + sp.cos(x)),
        (sp.log(x), sp.log(x), 1, 1 / x, x, x * sp.log(x) - x),
    ]
    for pattern, u_expr, dv_expr, du_expr, v_expr, anti_expr in candidates:
        coeff = sp.simplify(expr / pattern)
        if coeff.has(x) or not is_zero(expr - coeff * pattern):
            continue
        anti_expr = sp.simplify(coeff * anti_expr)
        if mode == "indefinite":
            return response(
                available=True,
                explainability="full",
                recipe_id="integration_by_parts",
                method_tags=["分部积分"],
                lines=[
                    rf"u &= {safe_latex(u_expr)},\quad dv={safe_latex(dv_expr)}\,dx,\quad du={safe_latex(du_expr)}\,dx,\quad v={safe_latex(v_expr)}",
                    rf"{statement_latex} &= {safe_latex(coeff)}\left({safe_latex(u_expr * v_expr)}-\int {safe_latex(v_expr * du_expr)}\,dx\right)",
                    rf"&= {safe_latex(anti_expr)}+C",
                ],
                verified=final_is_verified(integration),
            )
        bounds = integration.get("bounds", {})
        lower = bounds.get("lower_latex", "a")
        upper = bounds.get("upper_latex", "b")
        return response(
            available=True,
            explainability="full",
            recipe_id="integration_by_parts",
            method_tags=["分部积分"],
            lines=[
                rf"u &= {safe_latex(u_expr)},\quad dv={safe_latex(dv_expr)}\,dx",
                rf"{statement_latex} &= {safe_latex(coeff)}\left(\left[{safe_latex(u_expr * v_expr)}\right]_{{{lower}}}^{{{upper}}}-\int_{{{lower}}}^{{{upper}}}{safe_latex(v_expr * du_expr)}\,dx\right)",
                rf"&= \left[{safe_latex(anti_expr)}\right]_{{{lower}}}^{{{upper}}}",
                rf"&= {final_latex}",
            ],
            verified=final_is_verified(integration),
        )
    return None


def build_abs_trig_piecewise(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    target = sp.sqrt(sp.sin(x) ** 3 - sp.sin(x) ** 5)
    if mode not in {"definite", "improper"} or not is_zero(expr - target):
        return None
    bounds = integration.get("bounds", {})
    lower = bounds.get("lower_latex", "0")
    upper = bounds.get("upper_latex", r"\pi")
    if lower != "0" or upper != r"\pi":
        return None
    return response(
        available=True,
        explainability="full",
        recipe_id="trig_identity_abs_piecewise",
        method_tags=["三角恒等式", "绝对值分段", "换元法"],
        lines=[
            r"\sqrt{\sin^3 x-\sin^5 x} &= \sqrt{\sin^3x(1-\sin^2x)}",
            r"&= \sin^{\frac32}x\,|\cos x|",
            r"\int_0^\pi \sqrt{\sin^3x-\sin^5x}\,dx &= \int_0^{\frac\pi2}\sin^{\frac32}x\cos x\,dx+\int_{\frac\pi2}^{\pi}\sin^{\frac32}x(-\cos x)\,dx",
            r"&= \int_0^{\frac\pi2}\sin^{\frac32}x\,d(\sin x)-\int_{\frac\pi2}^{\pi}\sin^{\frac32}x\,d(\sin x)",
            r"&= \left[\frac25\sin^{\frac52}x\right]_0^{\frac\pi2}-\left[\frac25\sin^{\frac52}x\right]_{\frac\pi2}^{\pi}",
            r"&= \frac45",
        ],
        notes=[
            r"在 \(0\le x\le \frac\pi2\) 上，\(|\cos x|=\cos x\)。",
            r"在 \(\frac\pi2\le x\le \pi\) 上，\(|\cos x|=-\cos x\)。",
        ],
        verified=final_is_verified(integration),
    )


def build_improper(
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    bounds = integration.get("bounds", {})
    lower = bounds.get("lower_latex", "a")
    upper = bounds.get("upper_latex", "b")
    lower_inf = bounds.get("lower_infinite")
    upper_inf = bounds.get("upper_infinite")
    anti = integration.get("antiderivative", {})
    anti_latex = anti.get("latex")
    if not anti_latex:
        return None
    if upper_inf:
        lines = [
            rf"{statement_latex} &= \lim_{{B\to\infty}}\int_{{{lower}}}^B {safe_latex(expr)}\,dx",
            rf"&= \lim_{{B\to\infty}}\left[{anti_latex}\right]_{{{lower}}}^B",
            rf"&= {final_latex}",
        ]
    elif lower_inf:
        lines = [
            rf"{statement_latex} &= \lim_{{A\to-\infty}}\int_A^{{{upper}}} {safe_latex(expr)}\,dx",
            rf"&= \lim_{{A\to-\infty}}\left[{anti_latex}\right]_A^{{{upper}}}",
            rf"&= {final_latex}",
        ]
    else:
        return None
    return response(
        available=True,
        explainability="full",
        recipe_id="improper_limit",
        method_tags=["反常积分", "极限"],
        lines=lines,
        verified=final_is_verified(integration),
    )


def build_double(
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
    y: sp.Symbol,
) -> dict[str, Any] | None:
    bounds = integration.get("bounds", {})
    x_lower = sp.sympify(bounds.get("x_lower", "0"))
    x_upper = sp.sympify(bounds.get("x_upper", "1"))
    y_lower = sp.sympify(bounds.get("y_lower", "0"))
    y_upper = sp.sympify(bounds.get("y_upper", "1"))
    inner = sp.integrate(expr, (y, y_lower, y_upper))
    if inner.has(sp.Integral):
        return None
    outer_anti = sp.integrate(inner, x)
    if outer_anti.has(sp.Integral):
        return None
    return response(
        available=True,
        explainability="full",
        recipe_id="rectangular_double_integral",
        method_tags=["二重积分", "累次积分"],
        lines=[
            rf"{statement_latex} &= \int_{{{safe_latex(x_lower)}}}^{{{safe_latex(x_upper)}}}\left(\int_{{{safe_latex(y_lower)}}}^{{{safe_latex(y_upper)}}}{safe_latex(expr)}\,dy\right)dx",
            rf"&= \int_{{{safe_latex(x_lower)}}}^{{{safe_latex(x_upper)}}}{safe_latex(sp.simplify(inner))}\,dx",
            rf"&= \left[{safe_latex(sp.simplify(outer_anti))}\right]_{{{safe_latex(x_lower)}}}^{{{safe_latex(x_upper)}}}",
            rf"&= {final_latex}",
        ],
        verified=final_is_verified(integration),
    )


def build_polar_area(
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
) -> dict[str, Any] | None:
    bounds = integration.get("bounds", {})
    polar = integration.get("polar", {})
    lower = bounds.get("theta_lower_latex", r"\alpha")
    upper = bounds.get("theta_upper_latex", r"\beta")
    outer = polar.get("outer_latex", r"r_{out}")
    inner = polar.get("inner_latex", "0")
    integrand = polar.get("integrand_latex")
    if not integrand:
        return None
    return response(
        available=True,
        explainability="full",
        recipe_id="polar_area_formula",
        method_tags=["极坐标面积", "扇形微元"],
        lines=[
            rf"{statement_latex} &= \frac12\int_{{{lower}}}^{{{upper}}}\left(({outer})^2-({inner})^2\right)d\theta",
            rf"&= \int_{{{lower}}}^{{{upper}}}{integrand}\,d\theta",
            rf"&= {final_latex}",
        ],
        verified=final_is_verified(integration),
    )


def build_polar_double(
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    r: sp.Symbol,
    theta: sp.Symbol,
) -> dict[str, Any] | None:
    bounds = integration.get("bounds", {})
    r_lower = sp.sympify(bounds.get("r_lower", "0"))
    r_upper = sp.sympify(bounds.get("r_upper", "1"))
    theta_lower = sp.sympify(bounds.get("theta_lower", "0"))
    theta_upper = sp.sympify(bounds.get("theta_upper", "2*pi"))
    jacobian_integrand = sp.simplify(expr * r)
    inner = sp.integrate(jacobian_integrand, (r, r_lower, r_upper))
    if inner.has(sp.Integral):
        return None
    outer = sp.integrate(inner, theta)
    if outer.has(sp.Integral):
        return None
    return response(
        available=True,
        explainability="full",
        recipe_id="polar_double_jacobian",
        method_tags=["极坐标二重积分", "雅可比"],
        lines=[
            rf"dA &= r\,dr\,d\theta",
            rf"{statement_latex} &= \int_{{{safe_latex(theta_lower)}}}^{{{safe_latex(theta_upper)}}}\int_{{{safe_latex(r_lower)}}}^{{{safe_latex(r_upper)}}}{safe_latex(jacobian_integrand)}\,dr\,d\theta",
            rf"&= \int_{{{safe_latex(theta_lower)}}}^{{{safe_latex(theta_upper)}}}{safe_latex(sp.simplify(inner))}\,d\theta",
            rf"&= \left[{safe_latex(sp.simplify(outer))}\right]_{{{safe_latex(theta_lower)}}}^{{{safe_latex(theta_upper)}}}",
            rf"&= {final_latex}",
        ],
        verified=final_is_verified(integration),
    )


def build_algebra_steps(
    *,
    request: dict[str, Any],
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
    y: sp.Symbol,
    r: sp.Symbol,
    theta: sp.Symbol,
) -> dict[str, Any]:
    mode = integration.get("mode") or request.get("mode")
    recipe = request.get("recipe") or {}
    requested_recipe = recipe.get("recipe_id") or "auto"
    builders: list[Any]

    if mode in {"definite", "indefinite"}:
        builders = [
            build_abs_trig_piecewise,
            build_cos_power_sin,
            build_sin_power_cos,
            build_parts,
            build_generic_single_variable,
        ]
        for builder in builders:
            built = builder(mode, expr, integration, statement_latex, final_latex, x)
            if built:
                if requested_recipe != "auto":
                    built["source_recipe_id"] = requested_recipe
                return built
    elif mode == "improper":
        built = build_improper(expr, integration, statement_latex, final_latex, x)
        if built:
            return built
    elif mode == "double":
        built = build_double(expr, integration, statement_latex, final_latex, x, y)
        if built:
            return built
    elif mode == "polar_area":
        built = build_polar_area(integration, statement_latex, final_latex)
        if built:
            return built
    elif mode == "polar_double":
        built = build_polar_double(expr, integration, statement_latex, final_latex, r, theta)
        if built:
            return built

    return response(
        available=False,
        explainability="result-only",
        recipe_id=requested_recipe,
        reason="这个题型暂时不能可靠生成完整代数推导；系统已保留答案、数值校验和图像用于核验。",
        verified=final_is_verified(integration),
        method_tags=recipe.get("method_tags", []),
    )
