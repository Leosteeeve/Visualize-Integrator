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


TAG_TRANSLATIONS = {
    "换元法": "Substitution",
    "三角复合函数": "trigonometric composite",
    "分部积分": "integration by parts",
    "三角恒等式": "trigonometric identity",
    "绝对值分段": "absolute value split",
    "原函数": "antiderivative",
    "基本公式": "basic formula",
    "微积分基本定理": "Fundamental Theorem of Calculus",
    "反常积分": "improper integral",
    "极限": "limit",
    "二重积分": "double integral",
    "累次积分": "iterated integral",
    "极坐标面积": "polar area",
    "扇形微元": "sector area element",
    "极坐标二重积分": "polar double integral",
    "雅可比": "Jacobian",
    "降幂公式": "power-reduction identity",
    "积化和差": "product-to-sum identity",
    "幂函数公式": "power rule",
    "逐项积分": "term-by-term integration",
    "基础积分公式": "basic antiderivative formulas",
    "反三角函数公式": "inverse trigonometric formula",
    "重复分部积分": "repeated integration by parts",
}


FORMULA_CARDS = {
    "generic_antiderivative": {
        "zh-CN": [
            ("不定积分结果形式", r"\int f(x)\,dx=F(x)+C", "不定积分和定积分使用同样的求积技巧；区别是这里不代上下限，最后加常数。"),
        ],
        "en-US": [
            ("Indefinite integral form", r"\int f(x)\,dx=F(x)+C", r"Indefinite integrals use the same techniques as definite integrals; no bounds are evaluated, and \(C\) is added."),
        ],
    },
    "power_rule_antiderivative": {
        "zh-CN": [
            ("线性性质", r"\int(af(x)+bg(x))\,dx=a\int f(x)\,dx+b\int g(x)\,dx", "多项式可以拆成一项一项来积。"),
            ("幂函数公式", r"\int x^n\,dx=\frac{x^{n+1}}{n+1}+C\quad(n\ne -1)", "每一项指数加 1，再除以新的指数。"),
        ],
        "en-US": [
            ("Linearity", r"\int(af(x)+bg(x))\,dx=a\int f(x)\,dx+b\int g(x)\,dx", "A polynomial can be integrated term by term."),
            ("Power rule", r"\int x^n\,dx=\frac{x^{n+1}}{n+1}+C\quad(n\ne -1)", "Increase the exponent by 1, then divide by the new exponent."),
        ],
    },
    "basic_antiderivative_formula": {
        "zh-CN": [
            ("基础积分公式", r"\int e^x\,dx=e^x+C,\quad \int\sin x\,dx=-\cos x+C,\quad \int\cos x\,dx=\sin x+C", "先识别表达式属于哪一类基础函数，再直接套公式。"),
            ("不定积分常数", r"+C", "不代入上下限时，所有相差常数的原函数都正确。"),
        ],
        "en-US": [
            ("Basic formulas", r"\int e^x\,dx=e^x+C,\quad \int\sin x\,dx=-\cos x+C,\quad \int\cos x\,dx=\sin x+C", "Identify the basic function type, then apply the matching formula."),
            ("Constant of integration", r"+C", "Without bounds, antiderivatives that differ by a constant are all valid."),
        ],
    },
    "inverse_trig_antiderivative": {
        "zh-CN": [
            ("反三角函数公式", r"\int\frac{1}{1+x^2}\,dx=\arctan x+C", r"分母是 \(1+x^2\) 的有理式会对应反正切函数。"),
        ],
        "en-US": [
            ("Inverse trig formula", r"\int\frac{1}{1+x^2}\,dx=\arctan x+C", r"A denominator of \(1+x^2\) matches the arctangent formula."),
        ],
    },
    "repeated_integration_by_parts": {
        "zh-CN": [
            ("分部积分", r"\int u\,dv=uv-\int v\,du", "指数函数乘三角函数时，分部积分后会回到同类积分。"),
            ("移项求原积分", r"I=A-BI\quad\Rightarrow\quad I=\frac{A}{1+B}", "重复分部积分后把原积分移到同一边解出来。"),
        ],
        "en-US": [
            ("Integration by parts", r"\int u\,dv=uv-\int v\,du", "For exponential times trigonometric functions, integration by parts returns to a related integral."),
            ("Solve for the original integral", r"I=A-BI\quad\Rightarrow\quad I=\frac{A}{1+B}", "After the integral reappears, move it to the same side and solve for it."),
        ],
    },
    "fundamental_theorem": {
        "zh-CN": [
            ("微积分基本定理", r"\int_a^b f(x)\,dx=F(b)-F(a)", "先求原函数，再代入上下限。"),
        ],
        "en-US": [
            ("Fundamental Theorem of Calculus", r"\int_a^b f(x)\,dx=F(b)-F(a)", "First find an antiderivative, then evaluate at the bounds."),
        ],
    },
    "u_sub_cos_power_sin": {
        "zh-CN": [
            ("换元法", r"u=g(x),\quad du=g'(x)\,dx", "当外层函数伴随内层导数出现时，把内层整体设为新变量。"),
            ("三角导数", r"d(\cos x)=-\sin x\,dx", r"这里 \(\sin x\,dx\) 正好能转成 \(-du\)。"),
        ],
        "en-US": [
            ("Substitution", r"u=g(x),\quad du=g'(x)\,dx", "When a composite function appears with the derivative of its inside, replace the inside by a new variable."),
            ("Trig derivative", r"d(\cos x)=-\sin x\,dx", r"Here \(\sin x\,dx\) becomes \(-du\)."),
        ],
    },
    "u_sub_sin_power_cos": {
        "zh-CN": [
            ("换元法", r"u=g(x),\quad du=g'(x)\,dx", "当外层函数伴随内层导数出现时，把内层整体设为新变量。"),
            ("三角导数", r"d(\sin x)=\cos x\,dx", r"这里 \(\cos x\,dx\) 正好能转成 \(du\)。"),
        ],
        "en-US": [
            ("Substitution", r"u=g(x),\quad du=g'(x)\,dx", "When a composite function appears with the derivative of its inside, replace the inside by a new variable."),
            ("Trig derivative", r"d(\sin x)=\cos x\,dx", r"Here \(\cos x\,dx\) becomes \(du\)."),
        ],
    },
    "trig_power_reduction": {
        "zh-CN": [
            ("降幂公式", r"\sin^2x=\frac{1-\cos 2x}{2}", "偶次三角幂通常先降幂，再逐项积分。"),
            ("降幂公式", r"\cos^2x=\frac{1+\cos 2x}{2}", "平方项不能直接当作普通幂函数积分。"),
        ],
        "en-US": [
            ("Power-reduction identity", r"\sin^2x=\frac{1-\cos 2x}{2}", "Even powers of trig functions are usually reduced before integrating."),
            ("Power-reduction identity", r"\cos^2x=\frac{1+\cos 2x}{2}", "A squared trig function is not integrated like an ordinary power."),
        ],
    },
    "trig_product_to_sum": {
        "zh-CN": [
            ("积化和差", r"\sin A\cos B=\frac12[\sin(A+B)+\sin(A-B)]", "不同角度的三角函数相乘时，先化成和差更容易积分。"),
            ("积化和差", r"\sin A\sin B=\frac12[\cos(A-B)-\cos(A+B)]", "乘积变成和差后可以逐项积分。"),
            ("积化和差", r"\cos A\cos B=\frac12[\cos(A-B)+\cos(A+B)]", "乘积变成和差后可以逐项积分。"),
        ],
        "en-US": [
            ("Product-to-sum", r"\sin A\cos B=\frac12[\sin(A+B)+\sin(A-B)]", "Products with different angles are easier after converting to sums."),
            ("Product-to-sum", r"\sin A\sin B=\frac12[\cos(A-B)-\cos(A+B)]", "After conversion, integrate term by term."),
            ("Product-to-sum", r"\cos A\cos B=\frac12[\cos(A-B)+\cos(A+B)]", "After conversion, integrate term by term."),
        ],
    },
    "integration_by_parts": {
        "zh-CN": [
            ("分部积分", r"\int u\,dv=uv-\int v\,du", r"乘积型函数常把会变简单的部分选作 \(u\)。"),
        ],
        "en-US": [
            ("Integration by parts", r"\int u\,dv=uv-\int v\,du", r"For products, choose \(u\) as the part that becomes simpler after differentiating."),
        ],
    },
    "trig_identity_abs_piecewise": {
        "zh-CN": [
            ("平方恒等式", r"1-\sin^2x=\cos^2x", "先把根号内因式分解，再用恒等式化成平方。"),
            ("绝对值", r"\sqrt{\cos^2x}=|\cos x|", "开平方后必须保留绝对值，再按区间判断符号。"),
        ],
        "en-US": [
            ("Pythagorean identity", r"1-\sin^2x=\cos^2x", "Factor inside the radical first, then turn the remaining factor into a square."),
            ("Absolute value", r"\sqrt{\cos^2x}=|\cos x|", "Taking the square root creates an absolute value, so split by sign."),
        ],
    },
    "improper_limit": {
        "zh-CN": [("反常积分定义", r"\int_a^\infty f(x)\,dx=\lim_{B\to\infty}\int_a^B f(x)\,dx", "无穷上下限必须先写成极限。")],
        "en-US": [("Improper integral definition", r"\int_a^\infty f(x)\,dx=\lim_{B\to\infty}\int_a^B f(x)\,dx", "Infinite bounds must be handled with limits.")],
    },
    "rectangular_double_integral": {
        "zh-CN": [("累次积分", r"\iint_R f(x,y)\,dA=\int_a^b\int_c^d f(x,y)\,dy\,dx", "矩形区域可以先沿一个方向积分，再沿另一个方向累加。")],
        "en-US": [("Iterated integral", r"\iint_R f(x,y)\,dA=\int_a^b\int_c^d f(x,y)\,dy\,dx", "On a rectangle, integrate in one direction and then accumulate in the other.")],
    },
    "polar_area_formula": {
        "zh-CN": [("极坐标面积", r"A=\frac12\int_\alpha^\beta(r_{out}^2-r_{in}^2)\,d\theta", r"小扇形面积给出 \(\frac12r^2d\theta\)。")],
        "en-US": [("Polar area", r"A=\frac12\int_\alpha^\beta(r_{out}^2-r_{in}^2)\,d\theta", r"A thin sector contributes \(\frac12r^2d\theta\).")],
    },
    "polar_double_jacobian": {
        "zh-CN": [("极坐标雅可比", r"dA=r\,dr\,d\theta", r"离原点越远，同样角度扫出的弧越长，所以多出因子 \(r\)。")],
        "en-US": [("Polar Jacobian", r"dA=r\,dr\,d\theta", r"Farther from the origin, the same angle sweeps a longer arc, creating the factor \(r\).")],
    },
}


REASONING_STEPS = {
    "generic_antiderivative": {
        "zh-CN": ["这是不定积分，但技巧仍然和定积分一样：先判断被积函数结构，再求原函数。", r"区别只是不代入上下限，最后加 \(C\)。"],
        "en-US": ["This is an indefinite integral, but the technique is the same as for definite integrals: identify the integrand structure first.", r"The only difference is that no bounds are evaluated, and \(C\) is added."],
    },
    "power_rule_antiderivative": {
        "zh-CN": ["识别到多项式或幂函数组合。", "用线性性质拆开每一项，再逐项使用幂函数积分公式。", r"这是定积分里求 \(F(x)\) 的同一个步骤，只是不计算 \(F(b)-F(a)\)。"],
        "en-US": ["We see a polynomial or a combination of powers.", "Use linearity to split the terms, then apply the power rule term by term.", r"This is the same step used before evaluating \(F(b)-F(a)\) in a definite integral."],
    },
    "basic_antiderivative_formula": {
        "zh-CN": ["识别到基础指数、三角、对数或根式积分。", "直接套对应的基础积分公式；如果有常数倍，用线性性质提到积分外。", r"因为没有上下限，最后保留 \(+C\)。"],
        "en-US": ["We see a basic exponential, trigonometric, logarithmic, or radical integral.", "Apply the matching basic formula; constant factors stay outside by linearity.", r"Because there are no bounds, keep \(+C\) at the end."],
    },
    "inverse_trig_antiderivative": {
        "zh-CN": [r"识别到 \(\frac{1}{1+x^2}\) 型结构。", r"这个结构对应 \(\arctan x\) 的导数，所以用反三角函数公式。"],
        "en-US": [r"We recognize the \(\frac{1}{1+x^2}\) pattern.", r"This is the derivative pattern for \(\arctan x\), so use the inverse trigonometric formula."],
    },
    "repeated_integration_by_parts": {
        "zh-CN": ["识别到指数函数和三角函数相乘。", "这类题用分部积分一次后还会出现另一个指数三角积分。", "第二次分部积分后原积分重新出现，把它移到等式同一边求解。"],
        "en-US": ["We see an exponential function multiplied by a trigonometric function.", "One integration by parts creates the companion exponential-trig integral.", "A second integration by parts makes the original integral reappear; move it to one side and solve."],
    },
    "fundamental_theorem": {
        "zh-CN": ["这是有限区间上的定积分。", r"先找原函数 \(F\)，再用 \(F(b)-F(a)\) 表示从 \(a\) 到 \(b\) 的净累积量。"],
        "en-US": ["This is a definite integral on a finite interval.", r"Find an antiderivative \(F\), then compute the net accumulation \(F(b)-F(a)\)."],
    },
    "u_sub_cos_power_sin": {
        "zh-CN": [r"识别到 \(\cos x\) 的幂，同时旁边有 \(\sin x\,dx\)。", r"因为 \(d(\cos x)=-\sin x\,dx\)，所以令 \(u=\cos x\) 后积分变成幂函数积分。"],
        "en-US": [r"We see a power of \(\cos x\) together with \(\sin x\,dx\).", r"Since \(d(\cos x)=-\sin x\,dx\), setting \(u=\cos x\) turns the integral into a power integral."],
    },
    "u_sub_sin_power_cos": {
        "zh-CN": [r"识别到 \(\sin x\) 的幂，同时旁边有 \(\cos x\,dx\)。", r"因为 \(d(\sin x)=\cos x\,dx\)，所以令 \(u=\sin x\)。"],
        "en-US": [r"We see a power of \(\sin x\) together with \(\cos x\,dx\).", r"Since \(d(\sin x)=\cos x\,dx\), set \(u=\sin x\)."],
    },
    "trig_power_reduction": {
        "zh-CN": ["识别到偶次三角幂。", "偶次幂不容易直接换元，先用降幂公式把平方变成常数项和二倍角项。"],
        "en-US": ["We see an even power of a trig function.", "Even powers are not direct substitutions, so first use a power-reduction identity."],
    },
    "trig_product_to_sum": {
        "zh-CN": ["识别到两个三角函数相乘。", "用积化和差公式把乘积改写成几个可以直接积分的三角函数。"],
        "en-US": ["We see a product of two trig functions.", "Use a product-to-sum identity to rewrite it as terms that integrate directly."],
    },
    "trig_identity_abs_piecewise": {
        "zh-CN": ["先因式分解根号内表达式。", r"用 \(1-\sin^2x=\cos^2x\) 化简后会出现 \(|\cos x|\)。", r"因为 \(\cos x\) 在区间内变号，所以必须按符号分段。"],
        "en-US": ["First factor the expression inside the radical.", r"Using \(1-\sin^2x=\cos^2x\) creates \(|\cos x|\).", r"Because \(\cos x\) changes sign on the interval, split the integral by sign."],
    },
    "integration_by_parts": {
        "zh-CN": ["识别到乘积型表达式。", r"选择求导后更简单的部分作为 \(u\)，把另一部分作为 \(dv\)，再套用分部积分公式。"],
        "en-US": ["We see a product of functions.", r"Choose the part that simplifies after differentiating as \(u\), put the other part in \(dv\), then apply integration by parts."],
    },
    "improper_limit": {
        "zh-CN": ["反常积分的无穷端点不能直接代入。", "先把无穷端点替换成有限变量边界，再取极限判断是否收敛。"],
        "en-US": ["An infinite endpoint cannot be substituted directly.", "Replace it by a finite variable bound first, then take a limit to decide convergence."],
    },
    "rectangular_double_integral": {
        "zh-CN": ["区域是矩形，所以可以写成累次积分。", "先固定外层变量，对内层变量累积高度，再对外层变量继续累积。"],
        "en-US": ["The region is rectangular, so the double integral can be written as an iterated integral.", "Hold the outer variable fixed, integrate in the inner direction, then accumulate in the outer direction."],
    },
    "polar_area_formula": {
        "zh-CN": ["极坐标区域天然按角度切成薄扇形。", r"每个薄扇形的面积近似为 \(\frac12r^2d\theta\)，有内半径时用外半径平方减内半径平方。"],
        "en-US": ["A polar region is naturally sliced into thin sectors by angle.", r"Each sector has area \(\frac12r^2d\theta\); with an inner radius, subtract the inner radius squared from the outer radius squared."],
    },
    "polar_double_jacobian": {
        "zh-CN": ["极坐标二重积分仍然是在平面区域上累积函数值。", r"从直角坐标换到极坐标时，面积微元变成 \(dA=r\,dr\,d\theta\)，所以被积函数必须乘 \(r\)。"],
        "en-US": ["A polar double integral still accumulates a function over a planar region.", r"Changing from Cartesian to polar coordinates gives \(dA=r\,dr\,d\theta\), so the integrand must be multiplied by \(r\)."],
    },
}


def formula_cards(recipe_id: str, language: str) -> list[dict[str, str]]:
    cards = FORMULA_CARDS.get(recipe_id, {})
    selected = cards.get(language) or cards.get("zh-CN") or []
    return [{"title": title, "latex": latex, "explanation": explanation} for title, latex, explanation in selected]


def reasoning_steps(recipe_id: str, language: str) -> list[str]:
    steps = REASONING_STEPS.get(recipe_id, {})
    return list(steps.get(language) or steps.get("zh-CN") or [])


def translate_tags(tags: list[str], language: str) -> list[str]:
    if language != "en-US":
        return tags
    return [TAG_TRANSLATIONS.get(tag, tag) for tag in tags]


def localize_response(payload: dict[str, Any], language: str) -> dict[str, Any]:
    payload["language"] = language
    payload["method_tags"] = translate_tags(payload.get("method_tags", []), language)
    payload["formula_cards"] = formula_cards(payload.get("recipe_id", ""), language)
    payload["reasoning_steps"] = reasoning_steps(payload.get("recipe_id", ""), language)
    if language == "en-US" and not payload.get("available"):
        payload["reason"] = "This problem type cannot yet be explained with a reliable full algebraic derivation; the system kept the answer, numerical check, and graph for verification."
    if language == "en-US" and payload.get("recipe_id") == "trig_identity_abs_piecewise":
        payload["notes"] = [
            r"On \(0\le x\le \frac\pi2\), \(|\cos x|=\cos x\).",
            r"On \(\frac\pi2\le x\le \pi\), \(|\cos x|=-\cos x\).",
        ]
    return payload


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
        recipe_id = "generic_antiderivative"
        method_tags = ["基本公式"]
        extra_lines: list[str] = []
        if expr.is_polynomial(x):
            recipe_id = "power_rule_antiderivative"
            method_tags = ["幂函数公式", "逐项积分"]
            expanded = sp.expand(expr)
            if expanded != expr:
                extra_lines.append(rf"{safe_latex(expr)} &= {safe_latex(expanded)}")
        else:
            arctan_pattern = 1 / (1 + x**2)
            arctan_coeff = sp.simplify(expr / arctan_pattern)
            if not arctan_coeff.has(x) and is_zero(expr - arctan_coeff * arctan_pattern):
                recipe_id = "inverse_trig_antiderivative"
                method_tags = ["反三角函数公式", "基础积分公式"]
            elif expr.has(sp.sin, sp.cos, sp.exp, sp.log) or expr.has(x ** sp.Rational(1, 2)):
                recipe_id = "basic_antiderivative_formula"
                method_tags = ["基础积分公式", "逐项积分"]
        return response(
            available=True,
            explainability="full",
            recipe_id=recipe_id,
            method_tags=method_tags,
            lines=extra_lines + [
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
                rf"{statement_latex} &= {coefficient_prefix(-coeff)}\int u^{{{power}}}\,du",
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


def build_trig_power_reduction(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    if mode not in {"definite", "indefinite"}:
        return None
    candidates = [
        (sp.sin(x) ** 2, r"\sin^2x", r"\frac{1-\cos 2x}{2}", sp.Rational(1, 2) * (1 - sp.cos(2 * x))),
        (sp.cos(x) ** 2, r"\cos^2x", r"\frac{1+\cos 2x}{2}", sp.Rational(1, 2) * (1 + sp.cos(2 * x))),
    ]
    for pattern, trig_latex, reduced_latex, reduced_expr in candidates:
        coeff = sp.simplify(expr / pattern)
        if coeff.has(x) or not is_zero(expr - coeff * pattern):
            continue
        coeff_prefix = coefficient_prefix(coeff)
        reduced_with_coeff = sp.simplify(coeff * reduced_expr)
        anti = sp.integrate(reduced_with_coeff, x)
        if anti.has(sp.Integral):
            return None
        if mode == "indefinite":
            return response(
                available=True,
                explainability="full",
                recipe_id="trig_power_reduction",
                method_tags=["降幂公式", "三角恒等式"],
                lines=[
                    rf"{trig_latex} &= {reduced_latex}",
                    rf"{statement_latex} &= \int {safe_latex(reduced_with_coeff)}\,dx",
                    rf"&= {safe_latex(sp.simplify(anti))}+C",
                ],
                verified=final_is_verified(integration),
            )
        bounds = integration.get("bounds", {})
        lower = bounds.get("lower_latex", "a")
        upper = bounds.get("upper_latex", "b")
        return response(
            available=True,
            explainability="full",
            recipe_id="trig_power_reduction",
            method_tags=["降幂公式", "三角恒等式"],
            lines=[
                rf"{trig_latex} &= {reduced_latex}",
                rf"{statement_latex} &= \int_{{{lower}}}^{{{upper}}}{safe_latex(reduced_with_coeff)}\,dx",
                rf"&= \left[{safe_latex(sp.simplify(anti))}\right]_{{{lower}}}^{{{upper}}}",
                rf"&= {final_latex}",
            ],
            verified=final_is_verified(integration),
        )
    return None


def build_product_to_sum(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    if mode not in {"definite", "indefinite"}:
        return None
    candidates: list[tuple[sp.Expr, str, sp.Expr]] = []
    for a in range(1, 7):
        for b in range(1, 7):
            candidates.extend(
                [
                    (
                        sp.sin(a * x) * sp.cos(b * x),
                        rf"\sin({a}x)\cos({b}x)=\frac12\left[\sin({a + b}x)+\sin({a - b}x)\right]",
                        sp.Rational(1, 2) * (sp.sin((a + b) * x) + sp.sin((a - b) * x)),
                    ),
                    (
                        sp.sin(a * x) * sp.sin(b * x),
                        rf"\sin({a}x)\sin({b}x)=\frac12\left[\cos({a - b}x)-\cos({a + b}x)\right]",
                        sp.Rational(1, 2) * (sp.cos((a - b) * x) - sp.cos((a + b) * x)),
                    ),
                    (
                        sp.cos(a * x) * sp.cos(b * x),
                        rf"\cos({a}x)\cos({b}x)=\frac12\left[\cos({a - b}x)+\cos({a + b}x)\right]",
                        sp.Rational(1, 2) * (sp.cos((a - b) * x) + sp.cos((a + b) * x)),
                    ),
                ]
            )
    for pattern, identity_latex, expanded in candidates:
        coeff = sp.simplify(expr / pattern)
        if coeff.has(x) or not is_zero(expr - coeff * pattern):
            continue
        transformed = sp.simplify(coeff * expanded)
        anti = sp.integrate(transformed, x)
        if anti.has(sp.Integral):
            return None
        if mode == "indefinite":
            return response(
                available=True,
                explainability="full",
                recipe_id="trig_product_to_sum",
                method_tags=["积化和差", "三角恒等式"],
                lines=[
                    identity_latex,
                    rf"{statement_latex} &= \int {safe_latex(transformed)}\,dx",
                    rf"&= {safe_latex(sp.simplify(anti))}+C",
                ],
                verified=final_is_verified(integration),
            )
        bounds = integration.get("bounds", {})
        lower = bounds.get("lower_latex", "a")
        upper = bounds.get("upper_latex", "b")
        return response(
            available=True,
            explainability="full",
            recipe_id="trig_product_to_sum",
            method_tags=["积化和差", "三角恒等式"],
            lines=[
                identity_latex,
                rf"{statement_latex} &= \int_{{{lower}}}^{{{upper}}}{safe_latex(transformed)}\,dx",
                rf"&= \left[{safe_latex(sp.simplify(anti))}\right]_{{{lower}}}^{{{upper}}}",
                rf"&= {final_latex}",
            ],
            verified=final_is_verified(integration),
        )
    return None


def build_exp_trig_repeated_parts(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    if mode not in {"definite", "indefinite"}:
        return None

    candidates: list[tuple[sp.Expr, str, int, int, sp.Expr]] = []
    for a in range(1, 7):
        for b in range(1, 7):
            candidates.append(
                (
                    sp.exp(a * x) * sp.sin(b * x),
                    "sin",
                    a,
                    b,
                    sp.exp(a * x) * (a * sp.sin(b * x) - b * sp.cos(b * x)) / (a**2 + b**2),
                )
            )
            candidates.append(
                (
                    sp.exp(a * x) * sp.cos(b * x),
                    "cos",
                    a,
                    b,
                    sp.exp(a * x) * (a * sp.cos(b * x) + b * sp.sin(b * x)) / (a**2 + b**2),
                )
            )

    for pattern, trig_kind, a, b, anti_base in candidates:
        coeff = sp.simplify(expr / pattern)
        if coeff.has(x) or not is_zero(expr - coeff * pattern):
            continue

        exp_latex = safe_latex(sp.exp(a * x))
        sin_latex = safe_latex(sp.sin(b * x))
        cos_latex = safe_latex(sp.cos(b * x))
        denominator = a**2 + b**2
        anti_expr = sp.simplify(coeff * anti_base)
        coeff_text = coefficient_prefix(coeff)

        if trig_kind == "sin":
            setup_lines = [
                rf"I &= \int {exp_latex}{sin_latex}\,dx,\quad J=\int {exp_latex}{cos_latex}\,dx",
                rf"I &= \frac{{{exp_latex}{sin_latex}}}{{{a}}}-\frac{{{b}}}{{{a}}}J",
                rf"J &= \frac{{{exp_latex}{cos_latex}}}{{{a}}}+\frac{{{b}}}{{{a}}}I",
                rf"I &= \frac{{{exp_latex}\left({a}{sin_latex}-{b}{cos_latex}\right)}}{{{denominator}}}",
            ]
        else:
            setup_lines = [
                rf"I &= \int {exp_latex}{cos_latex}\,dx,\quad J=\int {exp_latex}{sin_latex}\,dx",
                rf"I &= \frac{{{exp_latex}{cos_latex}}}{{{a}}}+\frac{{{b}}}{{{a}}}J",
                rf"J &= \frac{{{exp_latex}{sin_latex}}}{{{a}}}-\frac{{{b}}}{{{a}}}I",
                rf"I &= \frac{{{exp_latex}\left({a}{cos_latex}+{b}{sin_latex}\right)}}{{{denominator}}}",
            ]

        if mode == "indefinite":
            lines = setup_lines + [
                rf"{statement_latex} &= {coeff_text}I",
                rf"&= {safe_latex(anti_expr)}+C",
            ]
            return response(
                available=True,
                explainability="full",
                recipe_id="repeated_integration_by_parts",
                method_tags=["分部积分", "重复分部积分"],
                lines=lines,
                verified=final_is_verified(integration),
            )

        bounds = integration.get("bounds", {})
        lower = bounds.get("lower_latex", "a")
        upper = bounds.get("upper_latex", "b")
        lines = setup_lines + [
            rf"{statement_latex} &= \left[{safe_latex(anti_expr)}\right]_{{{lower}}}^{{{upper}}}",
            rf"&= {final_latex}",
        ]
        return response(
            available=True,
            explainability="full",
            recipe_id="repeated_integration_by_parts",
            method_tags=["分部积分", "重复分部积分"],
            lines=lines,
            verified=final_is_verified(integration),
        )

    return None


def build_parts(
    mode: str,
    expr: sp.Expr,
    integration: dict[str, Any],
    statement_latex: str,
    final_latex: str,
    x: sp.Symbol,
) -> dict[str, Any] | None:
    candidates: list[tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr, sp.Expr, sp.Expr]] = [
        (sp.log(x), sp.log(x), 1, 1 / x, x, x * sp.log(x) - x),
        (x * sp.log(x), sp.log(x), x, 1 / x, x**2 / 2, x**2 * sp.log(x) / 2 - x**2 / 4),
        (sp.log(x) ** 2, sp.log(x) ** 2, 1, 2 * sp.log(x) / x, x, x * sp.log(x) ** 2 - 2 * x * sp.log(x) + 2 * x),
    ]
    for k in range(1, 7):
        candidates.extend(
            [
                (
                    x * sp.exp(k * x),
                    x,
                    sp.exp(k * x),
                    1,
                    sp.exp(k * x) / k,
                    x * sp.exp(k * x) / k - sp.exp(k * x) / k**2,
                ),
                (
                    x * sp.sin(k * x),
                    x,
                    sp.sin(k * x),
                    1,
                    -sp.cos(k * x) / k,
                    -x * sp.cos(k * x) / k + sp.sin(k * x) / k**2,
                ),
                (
                    x * sp.cos(k * x),
                    x,
                    sp.cos(k * x),
                    1,
                    sp.sin(k * x) / k,
                    x * sp.sin(k * x) / k + sp.cos(k * x) / k**2,
                ),
            ]
        )
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
            build_trig_power_reduction,
            build_product_to_sum,
            build_exp_trig_repeated_parts,
            build_parts,
            build_generic_single_variable,
        ]
        for builder in builders:
            built = builder(mode, expr, integration, statement_latex, final_latex, x)
            if built:
                if requested_recipe != "auto":
                    built["source_recipe_id"] = requested_recipe
                return localize_response(built, str(request.get("language", "zh-CN")))
    elif mode == "improper":
        built = build_improper(expr, integration, statement_latex, final_latex, x)
        if built:
            return localize_response(built, str(request.get("language", "zh-CN")))
    elif mode == "double":
        built = build_double(expr, integration, statement_latex, final_latex, x, y)
        if built:
            return localize_response(built, str(request.get("language", "zh-CN")))
    elif mode == "polar_area":
        built = build_polar_area(integration, statement_latex, final_latex)
        if built:
            return localize_response(built, str(request.get("language", "zh-CN")))
    elif mode == "polar_double":
        built = build_polar_double(expr, integration, statement_latex, final_latex, r, theta)
        if built:
            return localize_response(built, str(request.get("language", "zh-CN")))

    return localize_response(response(
        available=False,
        explainability="result-only",
        recipe_id=requested_recipe,
        reason="这个题型暂时不能可靠生成完整代数推导；系统已保留答案、数值校验和图像用于核验。",
        verified=final_is_verified(integration),
        method_tags=recipe.get("method_tags", []),
    ), str(request.get("language", "zh-CN")))
