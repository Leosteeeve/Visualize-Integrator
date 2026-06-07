from __future__ import annotations

import hashlib
import random
import secrets
from dataclasses import dataclass
from typing import Any, Callable


KINDS = ("definite", "indefinite", "improper", "double", "polar", "solid")
LEVELS = ("easy", "ap", "advanced", "mit")

KIND_LABELS = {
    "definite": "定积分",
    "indefinite": "不定积分",
    "improper": "反常积分",
    "double": "二重积分",
    "polar": "极坐标积分",
    "solid": "立体几何积分",
}

LEVEL_LABELS = {
    "easy": "简单",
    "ap": "AP",
    "advanced": "高等技巧",
    "mit": "MIT/挑战",
}


@dataclass(frozen=True)
class Family:
    family_id: str
    kind: str
    level: str
    concepts: tuple[str, ...]
    make: Callable[[random.Random], dict[str, Any]]
    capacity: int = 2000


def make_seed(seed: Any | None = None) -> str:
    if seed is None or seed == "":
        return secrets.token_hex(8)
    return str(seed)


def make_rng(seed: Any | None = None) -> random.Random:
    return random.Random(make_seed(seed))


def rand_int(rng: random.Random, low: int, high: int, *, nonzero: bool = False) -> int:
    value = rng.randint(low, high)
    while nonzero and value == 0:
        value = rng.randint(low, high)
    return value


def pick(rng: random.Random, values: list[Any] | tuple[Any, ...]) -> Any:
    return values[rng.randrange(len(values))]


def coeff(rng: random.Random, low: int = 1, high: int = 6, *, signed: bool = False) -> int:
    value = rand_int(rng, low, high)
    return value if not signed or rng.random() < 0.5 else -value


def term(c: int, body: str) -> str:
    if c == 1:
        return body
    if c == -1:
        return f"-{body}"
    return f"{c}*{body}"


def add_terms(*items: str) -> str:
    return " + ".join(item for item in items if item)


def tex_expr(expr: str) -> str:
    text = expr.replace("*", " ")
    replacements = {
        "sqrt": r"\sqrt",
        "sin": r"\sin",
        "cos": r"\cos",
        "tan": r"\tan",
        "exp": r"\exp",
        "log": r"\log",
        "oo": r"\infty",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def tex_bound(bound: str | None) -> str:
    if bound is None:
        return ""
    return tex_expr(str(bound)).replace("-\\infty", r"-\infty")


def statement_for(problem: dict[str, Any]) -> str:
    expr = tex_expr(problem["expression"])
    if problem["mode"] == "indefinite":
        return rf"\int {expr}\,dx"
    if problem["mode"] == "polar_area":
        inner = tex_expr(problem.get("innerExpression", "0"))
        return (
            rf"\frac12\int_{{{tex_bound(problem['thetaLower'])}}}^{{{tex_bound(problem['thetaUpper'])}}}"
            rf"\left(({expr})^2-({inner})^2\right)\,d\theta"
        )
    if problem["mode"] == "polar_double":
        return (
            rf"\int_{{{tex_bound(problem['thetaLower'])}}}^{{{tex_bound(problem['thetaUpper'])}}}"
            rf"\int_{{{tex_bound(problem['rLower'])}}}^{{{tex_bound(problem['rUpper'])}}}"
            rf"{expr}\,r\,dr\,d\theta"
        )
    if problem["mode"] == "double":
        return (
            rf"\int_{{{tex_bound(problem['xLower'])}}}^{{{tex_bound(problem['xUpper'])}}}"
            rf"\int_{{{tex_bound(problem['yLower'])}}}^{{{tex_bound(problem['yUpper'])}}}"
            rf"{expr}\,dy\,dx"
        )
    if problem["mode"] == "solid_revolution":
        inner = tex_expr(problem.get("innerExpression", "0"))
        variable = "y" if problem.get("solidPreset") in {"washer_y", "shell_x"} else "x"
        lower = tex_bound(problem["lower"])
        upper = tex_bound(problem["upper"])
        if problem.get("solidPreset") in {"washer_x", "washer_y"}:
            return (
                rf"\pi\int_{{{lower}}}^{{{upper}}}"
                rf"\left(({expr})^2-({inner})^2\right)\,d{variable}"
            )
        return (
            rf"2\pi\int_{{{lower}}}^{{{upper}}}"
            rf"{variable}\left(({expr})-({inner})\right)\,d{variable}"
        )
    return rf"\int_{{{tex_bound(problem['lower'])}}}^{{{tex_bound(problem['upper'])}}}{expr}\,dx"


def problem(
    title: str,
    mode: str,
    expression: str,
    *,
    lower: str | None = None,
    upper: str | None = None,
    x_lower: str | None = None,
    x_upper: str | None = None,
    y_lower: str | None = None,
    y_upper: str | None = None,
    inner_expression: str | None = None,
    theta_lower: str | None = None,
    theta_upper: str | None = None,
    r_lower: str | None = None,
    r_upper: str | None = None,
    solid_preset: str | None = None,
    target: str,
    recipe_id: str = "auto",
    recipe_params: dict[str, Any] | None = None,
    method_tags: list[str] | None = None,
    explainability: str | None = None,
) -> dict[str, Any]:
    if explainability is None:
        target_text = target + " " + expression
        explainability = "partial" if any(word in target_text for word in ("特殊函数", "数值", "挑战", "非初等")) else "full"
    item: dict[str, Any] = {
        "title": title,
        "mode": mode,
        "expression": expression,
        "target": target,
        "recipe": {
            "recipe_id": recipe_id,
            "recipe_params": recipe_params or {},
            "method_tags": method_tags or [],
            "explainability": explainability,
        },
        "recipeId": recipe_id,
        "methodTags": method_tags or [],
        "explainability": explainability,
    }
    if mode == "double":
        item.update(
            {
                "xLower": x_lower or "0",
                "xUpper": x_upper or "1",
                "yLower": y_lower or "0",
                "yUpper": y_upper or "1",
            }
        )
    elif mode == "polar_area":
        item.update(
            {
                "innerExpression": inner_expression or "0",
                "thetaLower": theta_lower or "0",
                "thetaUpper": theta_upper or "2*pi",
            }
        )
    elif mode == "polar_double":
        item.update(
            {
                "rLower": r_lower or "0",
                "rUpper": r_upper or "1",
                "thetaLower": theta_lower or "0",
                "thetaUpper": theta_upper or "2*pi",
            }
        )
    elif mode == "solid_revolution":
        item.update(
            {
                "solidPreset": solid_preset or "washer_x",
                "innerExpression": inner_expression or "0",
                "lower": lower or "0",
                "upper": upper or "1",
            }
        )
    elif mode != "indefinite":
        item.update({"lower": lower or "0", "upper": upper or "1"})
    item["statement"] = statement_for(item)
    return item


def payload_for(problem_item: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "mode": problem_item["mode"],
        "expression": problem_item["expression"],
        "epsilon": 1e-8,
        "recipe": problem_item.get("recipe", {}),
    }
    if problem_item["mode"] == "double":
        payload.update(
            {
                "xLower": problem_item["xLower"],
                "xUpper": problem_item["xUpper"],
                "yLower": problem_item["yLower"],
                "yUpper": problem_item["yUpper"],
            }
        )
    elif problem_item["mode"] == "polar_area":
        payload.update(
            {
                "innerExpression": problem_item.get("innerExpression", "0"),
                "thetaLower": problem_item["thetaLower"],
                "thetaUpper": problem_item["thetaUpper"],
            }
        )
    elif problem_item["mode"] == "polar_double":
        payload.update(
            {
                "rLower": problem_item["rLower"],
                "rUpper": problem_item["rUpper"],
                "thetaLower": problem_item["thetaLower"],
                "thetaUpper": problem_item["thetaUpper"],
            }
        )
    elif problem_item["mode"] == "solid_revolution":
        payload.update(
            {
                "solidPreset": problem_item.get("solidPreset", "washer_x"),
                "innerExpression": problem_item.get("innerExpression", "0"),
                "lower": problem_item["lower"],
                "upper": problem_item["upper"],
            }
        )
    elif problem_item["mode"] != "indefinite":
        payload.update({"lower": problem_item["lower"], "upper": problem_item["upper"]})
    return payload


def signature_for(problem_item: dict[str, Any], kind: str, level: str) -> str:
    parts = [
        kind,
        level,
        problem_item["mode"],
        problem_item["expression"].replace(" ", ""),
        problem_item.get("lower", ""),
        problem_item.get("upper", ""),
        problem_item.get("xLower", ""),
        problem_item.get("xUpper", ""),
        problem_item.get("yLower", ""),
        problem_item.get("yUpper", ""),
        problem_item.get("innerExpression", ""),
        problem_item.get("thetaLower", ""),
        problem_item.get("thetaUpper", ""),
        problem_item.get("rLower", ""),
        problem_item.get("rUpper", ""),
        problem_item.get("solidPreset", ""),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def generate_candidate(kind: str, level: str, rng: random.Random) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"Unsupported practice kind: {kind}")
    if level not in LEVELS:
        raise ValueError(f"Unsupported practice level: {level}")
    family = pick(rng, FAMILIES_BY_KEY[(kind, level)])
    problem_item = family.make(rng)
    problem_item.update(
        {
            "kind": kind,
            "level": level,
            "kindLabel": KIND_LABELS[kind],
            "levelLabel": LEVEL_LABELS[level],
        }
    )
    problem_item.setdefault("recipe", {}).update({"family_id": family.family_id, "kind": kind, "level": level})
    signature = signature_for(problem_item, kind, level)
    return {
        "problem": problem_item,
        "payload": payload_for(problem_item),
        "signature": signature,
        "family_id": family.family_id,
        "concepts": list(family.concepts),
        "capacity": family.capacity,
    }


def total_capacity(kind: str | None = None, level: str | None = None) -> int:
    families = [
        family
        for family in FAMILIES
        if (kind is None or family.kind == kind) and (level is None or family.level == level)
    ]
    return sum(family.capacity for family in families)


def _family(kind: str, level: str, index: int, concepts: tuple[str, ...], maker: Callable[[random.Random, int], dict[str, Any]]) -> Family:
    return Family(
        family_id=f"{kind}.{level}.{index:02d}",
        kind=kind,
        level=level,
        concepts=concepts,
        make=lambda rng, i=index: maker(rng, i),
    )


def make_indefinite_easy(rng: random.Random, index: int) -> dict[str, Any]:
    a = coeff(rng)
    b = coeff(rng)
    n = rand_int(rng, 1, 8)
    k = rand_int(rng, 1, 5)
    if index == 0:
        expr = term(a, f"x^{n}")
        title = "幂函数原函数"
    elif index == 1:
        expr = add_terms(term(a, f"x^{n}"), term(b, f"x^{rand_int(rng, 0, 5)}"))
        title = "多项式逐项积分"
    elif index == 2:
        expr = add_terms(term(a, f"x^{n}"), str(b))
        title = "幂函数与常数"
    elif index == 3:
        expr = term(a, "sin(x)")
        title = "正弦函数原函数"
    elif index == 4:
        expr = term(a, "cos(x)")
        title = "余弦函数原函数"
    elif index == 5:
        expr = term(a, "exp(x)")
        title = "指数函数原函数"
    elif index == 6:
        expr = term(a, "1/x")
        title = "对数型原函数"
    elif index == 7:
        expr = term(a, "sqrt(x)")
        title = "根式幂函数"
    elif index == 8:
        expr = term(a, f"sin({k}*x)")
        title = "线性角三角函数"
    else:
        expr = add_terms(term(a, f"x^{n}"), term(b, f"cos({k}*x)"))
        title = "基础函数线性组合"
    return problem(title, "indefinite", expr, target="直接套用基本原函数表。")


def make_indefinite_ap(rng: random.Random, index: int) -> dict[str, Any]:
    a = coeff(rng, 2, 6)
    b = rand_int(rng, -5, 5)
    n = rand_int(rng, 2, 6)
    k = rand_int(rng, 2, 6)
    inner = f"{a}*x + {b}"
    if index == 0:
        expr = term(a * n, f"({inner})^{n - 1}")
        title = "线性换元幂函数"
    elif index == 1:
        expr = term(a, f"cos({inner})")
        title = "余弦换元"
    elif index == 2:
        expr = term(a, f"sin({inner})")
        title = "正弦换元"
    elif index == 3:
        expr = term(a, f"exp({inner})")
        title = "指数换元"
    elif index == 4:
        expr = f"{a}/({inner})"
        title = "对数换元"
    elif index == 5:
        expr = f"{a}/(2*sqrt({inner}))"
        title = "根式换元"
    elif index == 6:
        expr = f"2*x*(x^2 + {rand_int(rng, 1, 6)})^{n}"
        title = "二次内层换元"
    elif index == 7:
        expr = term(k, f"exp({k}*x)")
        title = "指数线性换元"
    elif index == 8:
        expr = add_terms(term(a, f"cos({a}*x)"), term(k, f"x^{n}"))
        title = "换元与幂函数组合"
    else:
        expr = f"{2 * k}*x/(1 + {k}*x^2)"
        title = "有理换元"
    return problem(title, "indefinite", expr, target="识别内层函数及其导数。")


def make_indefinite_advanced(rng: random.Random, index: int) -> dict[str, Any]:
    a = coeff(rng, 1, 4)
    k = rand_int(rng, 1, 4)
    if index == 0:
        expr = f"x*exp({k}*x)"
        title = "分部积分：x 与指数"
    elif index == 1:
        expr = f"x*sin({k}*x)"
        title = "分部积分：x 与正弦"
    elif index == 2:
        expr = f"x*cos({k}*x)"
        title = "分部积分：x 与余弦"
    elif index == 3:
        expr = "log(x)"
        title = "分部积分：对数函数"
    elif index == 4:
        expr = "x*log(x)"
        title = "分部积分：x log x"
    elif index == 5:
        expr = "1/(1+x^2)"
        title = "反三角函数原函数"
    elif index == 6:
        p, q = rand_int(rng, 1, 4), rand_int(rng, 5, 8)
        expr = f"1/(x + {p}) + 1/(x + {q})"
        title = "简单部分分式"
    elif index == 7:
        expr = "sin(x)^2"
        title = "三角恒等变形"
    elif index == 8:
        expr = "cos(x)^2"
        title = "余弦平方恒等式"
    else:
        expr = term(a, "exp(x)*sin(x)")
        title = "指数与三角乘积"
    return problem(title, "indefinite", expr, target="根据乘积、恒等式或有理式结构选择技巧。")


def make_indefinite_mit(rng: random.Random, index: int) -> dict[str, Any]:
    n = rand_int(rng, 2, 4)
    k = rand_int(rng, 1, 4)
    if index == 0:
        expr = f"exp(-{k}*x^2)"
        title = "误差函数型原函数"
    elif index == 1:
        expr = f"exp({k}*x^2)"
        title = "虚误差函数型原函数"
    elif index == 2:
        expr = "sin(x)/x"
        title = "特殊函数型原函数"
    elif index == 3:
        expr = "log(x)^2"
        title = "对数平方分部积分"
    elif index == 4:
        expr = "log(x)/x"
        title = "对数换元挑战"
    elif index == 5:
        expr = "1/(x*log(x))"
        title = "双层对数换元"
    elif index == 6:
        expr = f"x^{n}*exp(x)"
        title = "多次分部积分"
    elif index == 7:
        expr = f"x^{n}*sin(x)"
        title = "多项式乘三角函数"
    elif index == 8:
        expr = "sin(x)^3"
        title = "奇次三角幂"
    else:
        expr = "1/(1+x^4)"
        title = "高阶有理函数"
    return problem(title, "indefinite", expr, target="允许出现特殊函数或多步骤技巧。")


def make_definite_easy(rng: random.Random, index: int) -> dict[str, Any]:
    a, b = coeff(rng), rand_int(rng, 1, 5)
    n = rand_int(rng, 1, 6)
    if index == 0:
        expr, lower, upper, title = term(a, f"x^{n}"), "0", str(b), "幂函数面积"
    elif index == 1:
        expr, lower, upper, title = add_terms(term(a, f"x^{n}"), term(coeff(rng), f"x^{rand_int(rng, 0, 4)}")), "0", str(b), "多项式定积分"
    elif index == 2:
        expr, lower, upper, title = str(a), str(rand_int(rng, -3, 1)), str(rand_int(rng, 2, 6)), "常数函数面积"
    elif index == 3:
        expr, lower, upper, title = term(a, "sin(x)"), "0", "pi", "正弦半波面积"
    elif index == 4:
        expr, lower, upper, title = term(a, "cos(x)"), "0", "pi/2", "余弦四分之一波"
    elif index == 5:
        expr, lower, upper, title = term(a, "exp(x)"), "0", "1", "指数函数累积"
    elif index == 6:
        expr, lower, upper, title = term(a, "1/x"), "1", str(rand_int(rng, 2, 6)), "对数面积"
    elif index == 7:
        expr, lower, upper, title = term(a, "sqrt(x)"), "0", str(b), "根式曲线面积"
    elif index == 8:
        expr, lower, upper, title = term(a, f"x^{2 * rand_int(rng, 1, 3)}"), f"-{b}", str(b), "偶函数对称面积"
    else:
        expr, lower, upper, title = add_terms(term(a, "x"), str(coeff(rng))), str(rand_int(rng, -3, 0)), str(rand_int(rng, 1, 5)), "一次函数有向面积"
    return problem(title, "definite", expr, lower=lower, upper=upper, target="先求原函数，再代入上下限。")


def make_definite_ap(rng: random.Random, index: int) -> dict[str, Any]:
    a = coeff(rng, 2, 5)
    n = rand_int(rng, 2, 6)
    b = rand_int(rng, 1, 4)
    if index == 0:
        expr, lower, upper, title = f"{a*n}*({a}*x + {b})^{n-1}", "0", "1", "换元法幂函数"
    elif index == 1:
        expr, lower, upper, title = "2*x*cos(x^2)", "0", str(b), "二次换元余弦"
    elif index == 2:
        expr, lower, upper, title = f"{a}*exp({a}*x)", "0", "1", "指数换元定积分"
    elif index == 3:
        expr, lower, upper, title = f"{a}/({a}*x + {b})", "0", "2", "对数换元定积分"
    elif index == 4:
        expr, lower, upper, title = f"{2*b}*x/(1 + {b}*x^2)", "0", "1", "有理函数换元"
    elif index == 5:
        expr, lower, upper, title = "sin(x)^2", "0", "pi", "三角平方面积"
    elif index == 6:
        expr, lower, upper, title = "cos(x)^2", "0", "pi", "余弦平方面积"
    elif index == 7:
        expr, lower, upper, title = add_terms(term(coeff(rng), "x^3"), term(coeff(rng), "x")), f"-{b}", str(b), "奇函数对称性"
    elif index == 8:
        expr, lower, upper, title = f"x/sqrt(x^2 + {b})", "0", "2", "根式换元"
    else:
        expr, lower, upper, title = f"sin({a}*x)", "0", f"pi/{a}", "线性角三角积分"
    return problem(title, "definite", expr, lower=lower, upper=upper, target="识别换元、对称性或三角恒等式。")


def make_definite_advanced(rng: random.Random, index: int) -> dict[str, Any]:
    b = rand_int(rng, 1, 4)
    k = rand_int(rng, 1, 4)
    if index == 0:
        expr, lower, upper, title = "x*exp(x)", "0", str(b), "分部积分定积分"
    elif index == 1:
        expr, lower, upper, title = f"x*sin({k}*x)", "0", "pi", "分部积分与正弦"
    elif index == 2:
        expr, lower, upper, title = f"x*cos({k}*x)", "0", "pi", "分部积分与余弦"
    elif index == 3:
        expr, lower, upper, title = "log(x)", "1", str(rand_int(rng, 2, 6)), "对数分部积分"
    elif index == 4:
        expr, lower, upper, title = "1/(1+x^2)", "0", str(b), "反三角函数定积分"
    elif index == 5:
        expr, lower, upper, title = add_terms(term(coeff(rng), "x^4"), term(coeff(rng), "x^2")), f"-{b}", str(b), "偶函数对称性"
    elif index == 6:
        p, q = rand_int(rng, 1, 3), rand_int(rng, 4, 7)
        expr, lower, upper, title = f"1/((x + {p})*(x + {q}))", "0", "1", "部分分式定积分"
    elif index == 7:
        expr, lower, upper, title = "exp(x)*sin(x)", "0", "pi", "指数三角乘积"
    elif index == 8:
        expr, lower, upper, title = "sin(x)^3", "0", "pi", "奇次三角幂"
    else:
        expr, lower, upper, title = "x*log(x)", "1", str(rand_int(rng, 2, 5)), "乘积型对数积分"
    return problem(title, "definite", expr, lower=lower, upper=upper, target="综合使用分部积分、恒等式和对称性。")


def make_definite_mit(rng: random.Random, index: int) -> dict[str, Any]:
    b = rand_int(rng, 1, 3)
    k = rand_int(rng, 1, 4)
    if index == 0:
        expr, lower, upper, title = f"exp(-{k}*x^2)", f"-{b}", str(b), "高斯型有限窗口"
    elif index == 1:
        expr, lower, upper, title = "sin(x^2)", "0", str(b), "菲涅耳型积分"
    elif index == 2:
        expr, lower, upper, title = "cos(x^2)", "0", str(b), "振荡相位积分"
    elif index == 3:
        expr, lower, upper, title = "log(x)^2", "1", str(rand_int(rng, 2, 5)), "对数平方积分"
    elif index == 4:
        expr, lower, upper, title = "1/(1+x^4)", "0", "1", "高阶有理定积分"
    elif index == 5:
        expr, lower, upper, title = "sin(x)/x", "1", str(rand_int(rng, 2, 6)), "振荡商函数"
    elif index == 6:
        expr, lower, upper, title = f"x^{rand_int(rng, 2, 4)}*exp(-x)", "0", str(rand_int(rng, 2, 6)), "伽马型有限截断"
    elif index == 7:
        expr, lower, upper, title = "sqrt(1+x^4)", "0", "1", "非初等闭式曲线面积"
    elif index == 8:
        expr, lower, upper, title = "exp(-x^2)*cos(x)", "0", str(b), "高斯调制振荡"
    else:
        expr, lower, upper, title = "log(1+x^2)/(1+x^2)", "0", str(b), "反三角换元挑战"
    return problem(title, "definite", expr, lower=lower, upper=upper, target="允许用特殊函数或高精度数值校验。")


def make_improper_easy(rng: random.Random, index: int) -> dict[str, Any]:
    p = rand_int(rng, 2, 5)
    a = rand_int(rng, 1, 4)
    if index == 0:
        expr, lower, upper, title = "1/sqrt(x)", "0", "1", "端点奇异收敛"
    elif index == 1:
        expr, lower, upper, title = "1/sqrt(1-x)", "0", "1", "右端点奇异"
    elif index == 2:
        expr, lower, upper, title = f"1/x^{p}", "1", "oo", "p 型尾部收敛"
    elif index == 3:
        expr, lower, upper, title = "1/x", "1", "oo", "调和尾部发散"
    elif index == 4:
        expr, lower, upper, title = f"exp(-{a}*x)", "0", "oo", "指数尾部"
    elif index == 5:
        expr, lower, upper, title = f"1/(x^2 + {a})", "0", "oo", "反三角尾部"
    elif index == 6:
        expr, lower, upper, title = "log(x)", "0", "1", "对数端点"
    elif index == 7:
        expr, lower, upper, title = "1/(x^(1/3))", "0", "1", "弱端点奇异"
    elif index == 8:
        expr, lower, upper, title = "1/(x^(3/2))", "1", "oo", "幂函数尾部"
    else:
        expr, lower, upper, title = f"{a}/(1 + x)^2", "0", "oo", "平移 p 型尾部"
    return problem(title, "improper", expr, lower=lower, upper=upper, target="把无穷或端点奇异改写成极限。")


def make_improper_ap(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 5)
    p = rand_int(rng, 2, 6)
    if index == 0:
        expr, lower, upper, title = f"1/x^{p}", "1", "oo", "p 判别法收敛"
    elif index == 1:
        expr, lower, upper, title = "1/sqrt(x)", "1", "oo", "p 判别法发散"
    elif index == 2:
        expr, lower, upper, title = f"1/(x^(1/{p}))", "0", "1", "端点 p 判别收敛"
    elif index == 3:
        expr, lower, upper, title = f"1/(x^({p}/2))", "0", "1", "端点 p 判别发散"
    elif index == 4:
        expr, lower, upper, title = f"x*exp(-{a}*x)", "0", "oo", "指数压制多项式"
    elif index == 5:
        expr, lower, upper, title = f"1/(x*log(x)^{p})", "e", "oo", "对数 p 型收敛"
    elif index == 6:
        expr, lower, upper, title = "1/(x*log(x))", "e", "oo", "对数尾部发散"
    elif index == 7:
        expr, lower, upper, title = "1/(sqrt(x)*(1+x))", "0", "oo", "双端收敛"
    elif index == 8:
        expr, lower, upper, title = f"1/(x^2 + {a}^2)", "-oo", "oo", "全实线反三角尾部"
    else:
        expr, lower, upper, title = "exp(-x)*sin(x)", "0", "oo", "指数衰减振荡"
    return problem(title, "improper", expr, lower=lower, upper=upper, target="判断 p 型、对数型或指数尾部。")


def make_improper_advanced(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 4)
    n = rand_int(rng, 1, 4)
    if index == 0:
        expr, lower, upper, title = f"x^{n}*exp(-{a}*x)", "0", "oo", "伽马型尾部"
    elif index == 1:
        expr, lower, upper, title = f"log(x)/x^{n + 1}", "1", "oo", "对数慢增长比较"
    elif index == 2:
        expr, lower, upper, title = "1/(sqrt(x)*(1+x))", "0", "oo", "端点与无穷双重反常"
    elif index == 3:
        expr, lower, upper, title = "log(x)/(1+x^2)", "0", "oo", "对称对数权重"
    elif index == 4:
        expr, lower, upper, title = f"1/(x^2 + {a}*x + {a + 2})", "0", "oo", "二次分母比较"
    elif index == 5:
        expr, lower, upper, title = "1/(x*log(x)^2)", "e", "oo", "对数换元收敛"
    elif index == 6:
        expr, lower, upper, title = "1/(x*sqrt(log(x)))", "e", "oo", "对数换元发散"
    elif index == 7:
        expr, lower, upper, title = "sin(x)/x^2", "1", "oo", "振荡绝对收敛"
    elif index == 8:
        expr, lower, upper, title = "1/sqrt(1-x^2)", "0", "1", "三角换元端点"
    else:
        expr, lower, upper, title = f"exp(-x)*cos({a}*x)", "0", "oo", "指数衰减余弦"
    return problem(title, "improper", expr, lower=lower, upper=upper, target="综合比较、换元和收敛判别。")


def make_improper_mit(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 4)
    n = rand_int(rng, 0, 3)
    if index == 0:
        expr, lower, upper, title = f"exp(-{a}*x^2)", "-oo", "oo", "高斯全实线"
    elif index == 1:
        expr, lower, upper, title = f"x^{n}*exp(-x)", "0", "oo", "伽马函数型"
    elif index == 2:
        expr, lower, upper, title = "sin(x)/x", "0", "oo", "狄利克雷型积分"
    elif index == 3:
        expr, lower, upper, title = "1/(1+x^2)", "-oo", "oo", "柯西核面积"
    elif index == 4:
        expr, lower, upper, title = "1/(sqrt(x)*(1+x))", "0", "oo", "贝塔函数型"
    elif index == 5:
        expr, lower, upper, title = "log(x)/(1+x^2)", "0", "oo", "对称抵消型"
    elif index == 6:
        expr, lower, upper, title = "exp(-x^2)*cos(x)", "-oo", "oo", "傅里叶高斯型"
    elif index == 7:
        expr, lower, upper, title = "1/(1+x^4)", "0", "oo", "高阶有理反常积分"
    elif index == 8:
        expr, lower, upper, title = "log(x)^2*exp(-x)", "0", "oo", "对数矩型积分"
    else:
        expr, lower, upper, title = "sin(x^2)", "0", "oo", "菲涅耳反常积分"
    return problem(title, "improper", expr, lower=lower, upper=upper, target="允许特殊函数、条件收敛或高精度数值校验。")


def make_double_easy(rng: random.Random, index: int) -> dict[str, Any]:
    a, b, c = coeff(rng), coeff(rng), coeff(rng)
    x0, x1 = 0, rand_int(rng, 1, 4)
    y0, y1 = 0, rand_int(rng, 1, 4)
    if index == 0:
        expr, title = str(a), "常数曲面体积"
    elif index == 1:
        expr, title = add_terms(term(a, "x"), term(b, "y"), str(c)), "平面曲面体积"
    elif index == 2:
        expr, title = "x*y", "双线性曲面"
    elif index == 3:
        expr, title = add_terms(term(a, "x^2"), term(b, "y")), "抛物柱面"
    elif index == 4:
        expr, title = add_terms(term(a, "x"), term(b, "y^2")), "横纵平方组合"
    elif index == 5:
        expr, title = f"x^{rand_int(rng, 1, 3)}*y^{rand_int(rng, 1, 3)}", "单项式曲面"
    elif index == 6:
        expr, title = f"({a}*x + {b})*({rand_int(rng, 1, 4)}*y + {c})", "可分离一次乘积"
    elif index == 7:
        expr, title = "sin(x)", "只随 x 变化的波面"
    elif index == 8:
        expr, title = "cos(y)", "只随 y 变化的波面"
    else:
        expr, title = "x^2 + y^2", "抛物面窗口"
    return problem(title, "double", expr, x_lower=str(x0), x_upper=str(x1), y_lower=str(y0), y_upper=str(y1), target="在矩形区域上累加曲面高度。")


def make_double_ap(rng: random.Random, index: int) -> dict[str, Any]:
    b = rand_int(rng, 1, 3)
    if index == 0:
        expr, bounds, title = "sin(x)*cos(y)", ("0", "pi", "0", "pi/2"), "可分离三角曲面"
    elif index == 1:
        expr, bounds, title = "exp(x)*exp(y)", ("0", "1", "0", "1"), "可分离指数曲面"
    elif index == 2:
        expr, bounds, title = "x^3 + x*y^2", (f"-{b}", str(b), "0", "1"), "x 方向奇函数抵消"
    elif index == 3:
        expr, bounds, title = "x^2*y + y", ("0", "1", f"-{b}", str(b)), "y 方向奇函数抵消"
    elif index == 4:
        expr, bounds, title = "x^2 + y^2", (f"-{b}", str(b), f"-{b}", str(b)), "对称抛物面"
    elif index == 5:
        expr, bounds, title = f"(x + {b})*(y^2 + 1)", ("0", "2", "0", "1"), "可分离多项式"
    elif index == 6:
        expr, bounds, title = "cos(x)*sin(y)", ("0", "pi/2", "0", "pi"), "三角乘积"
    elif index == 7:
        expr, bounds, title = "x*y + x + y", ("0", "1", "0", "1"), "双线性加平面"
    elif index == 8:
        expr, bounds, title = "sqrt(x) + sqrt(y)", ("0", str(rand_int(rng, 1, 4)), "0", str(rand_int(rng, 1, 4))), "根式曲面"
    else:
        expr, bounds, title = "1/(1+x^2+y^2)", ("0", "1", "0", "1"), "平滑数值曲面"
    return problem(title, "double", expr, x_lower=bounds[0], x_upper=bounds[1], y_lower=bounds[2], y_upper=bounds[3], target="用累次积分和矩形区域结构简化。")


def make_double_advanced(rng: random.Random, index: int) -> dict[str, Any]:
    b = rand_int(rng, 1, 3)
    if index == 0:
        expr, bounds, title = "sin(x)^2*cos(y)^2", ("0", "pi", "0", "pi/2"), "三角平方可分离"
    elif index == 1:
        expr, bounds, title = "exp(-x)*cos(y)", ("0", "2", "0", "pi/2"), "指数三角可分离"
    elif index == 2:
        expr, bounds, title = "x*y + x^2*y^2", ("0", "1", "0", "1"), "多项式混合曲面"
    elif index == 3:
        expr, bounds, title = "x^3*y^2 + y^4", (f"-{b}", str(b), "0", "1"), "奇偶性与多项式"
    elif index == 4:
        expr, bounds, title = "log(1+x)*y", ("0", "1", "0", "2"), "对数曲面"
    elif index == 5:
        expr, bounds, title = "1/(1+x^2)*1/(1+y^2)", ("0", "1", "0", "1"), "有理可分离曲面"
    elif index == 6:
        expr, bounds, title = "x*exp(y) + y*exp(x)", ("0", "1", "0", "1"), "指数多项式混合"
    elif index == 7:
        expr, bounds, title = "sqrt(1+x^2) + sqrt(1+y^2)", ("0", "1", "0", "1"), "根式曲面"
    elif index == 8:
        expr, bounds, title = "sin(x+y)", ("0", "pi/2", "0", "pi/2"), "变量耦合波面"
    else:
        expr, bounds, title = "x^2/(1+y^2)", ("0", "2", "0", "1"), "可分离有理曲面"
    return problem(title, "double", expr, x_lower=bounds[0], x_upper=bounds[1], y_lower=bounds[2], y_upper=bounds[3], target="结合可分离、对称性和累次积分。")


def make_double_mit(rng: random.Random, index: int) -> dict[str, Any]:
    b = rand_int(rng, 1, 2)
    if index == 0:
        expr, bounds, title = "exp(-(x^2+y^2))", (f"-{b}", str(b), f"-{b}", str(b)), "高斯曲面窗口"
    elif index == 1:
        expr, bounds, title = "sin(x*y)", ("0", "1", "0", "pi"), "耦合振荡曲面"
    elif index == 2:
        expr, bounds, title = "cos(x^2+y^2)", ("0", "1", "0", "1"), "径向振荡窗口"
    elif index == 3:
        expr, bounds, title = "1/(1+x^2+y^2)", (f"-{b}", str(b), f"-{b}", str(b)), "有理径向曲面"
    elif index == 4:
        expr, bounds, title = "log(1+x*y)", ("0", "1", "0", "1"), "对数耦合曲面"
    elif index == 5:
        expr, bounds, title = "sqrt(1+x^2+y^2)", ("0", "1", "0", "1"), "根式体积挑战"
    elif index == 6:
        expr, bounds, title = "exp(-x^2)*cos(y)", ("0", "2", "0", "pi"), "高斯与三角可分离"
    elif index == 7:
        expr, bounds, title = "x*y/(1+x^2+y^2)", ("0", "2", "0", "2"), "有理耦合曲面"
    elif index == 8:
        expr, bounds, title = "sin(x^2)*cos(y^2)", ("0", "1", "0", "1"), "菲涅耳乘积曲面"
    else:
        expr, bounds, title = "exp(-x)*sin(y)", ("0", "2", "0", "pi"), "衰减波面窗口"
    return problem(title, "double", expr, x_lower=bounds[0], x_upper=bounds[1], y_lower=bounds[2], y_upper=bounds[3], target="允许数值型曲面体积和特殊函数结果。")


def make_polar_easy(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 6)
    b = rand_int(rng, 1, max(1, a - 1))
    if index == 0:
        return problem("极坐标圆面积", "polar_area", str(a), theta_lower="0", theta_upper="2*pi", target="使用 \\(A=\\frac12\\int r^2d\\theta\\)。")
    if index == 1:
        return problem("扇形面积", "polar_area", str(a), theta_lower="0", theta_upper=f"pi/{rand_int(rng, 2, 6)}", target="把常半径曲线看成扇形。")
    if index == 2:
        return problem("上半圆面积", "polar_area", f"{a}*sin(theta)", theta_lower="0", theta_upper="pi", target="识别 \\(r=a\\sin\\theta\\) 的圆。")
    if index == 3:
        return problem("右半圆面积", "polar_area", f"{a}*cos(theta)", theta_lower="-pi/2", theta_upper="pi/2", target="识别 \\(r=a\\cos\\theta\\) 的圆。")
    if index == 4:
        return problem("环形扇区", "polar_area", str(a), inner_expression=str(b), theta_lower="0", theta_upper="pi/2", target="用外半径平方减内半径平方。")
    if index == 5:
        return problem("整圆内的四分之一扇形", "polar_area", str(a), theta_lower="0", theta_upper="pi/2", target="常半径时面积等于扇形面积。")
    if index == 6:
        return problem("基础正弦瓣", "polar_area", f"{a}*sin(theta)", theta_lower="0", theta_upper="pi/2", target="在给定角度区间上套极坐标面积公式。")
    if index == 7:
        return problem("基础余弦瓣", "polar_area", f"{a}*cos(theta)", theta_lower="0", theta_upper="pi/2", target="画出第一象限内的极坐标曲线。")
    if index == 8:
        return problem("阿基米德螺线小扇区", "polar_area", f"{a}*theta", theta_lower="0", theta_upper="pi/2", target="半径随角度线性增长。")
    return problem("常数外半径夹层", "polar_area", str(a + b), inner_expression=str(b), theta_lower="0", theta_upper="pi", target="夹层面积只需要处理两个半径平方。")


def make_polar_ap(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 4)
    n = rand_int(rng, 2, 5)
    if index == 0:
        return problem("心形线面积", "polar_area", f"{a}*(1+cos(theta))", theta_lower="0", theta_upper="2*pi", target="心形线面积常用全周期积分。")
    if index == 1:
        return problem("内凹心形线面积", "polar_area", f"{a}*(1-sin(theta))", theta_lower="0", theta_upper="2*pi", target="平方后积分，负号影响形状但不影响公式结构。")
    if index == 2:
        return problem("玫瑰线单瓣", "polar_area", f"{a}*sin({n}*theta)", theta_lower="0", theta_upper=f"pi/{n}", target="先确定单瓣角度范围，再用面积公式。")
    if index == 3:
        return problem("余弦玫瑰单瓣", "polar_area", f"{a}*cos({n}*theta)", theta_lower=f"-pi/{2*n}", theta_upper=f"pi/{2*n}", target="单瓣常以对称区间计算。")
    if index == 4:
        return problem("圆与同心小圆夹层", "polar_area", str(a + 2), inner_expression=str(a), theta_lower="0", theta_upper="2*pi", target="环形区域可直接用半径平方差。")
    if index == 5:
        return problem("极坐标曲线夹层", "polar_area", f"{a+2}", inner_expression=f"{a}*sin(theta)", theta_lower="0", theta_upper="pi", target="外半径减内半径时保持角度范围一致。")
    if index == 6:
        return problem("螺线面积", "polar_area", f"{a}*theta", theta_lower="0", theta_upper="pi", target="半径依赖角度，直接对 \\(\\theta\\) 积分。")
    if index == 7:
        return problem("平方根极径", "polar_area", f"sqrt({a}*theta)", theta_lower="0", theta_upper="pi", target="根式极径平方后会明显简化。")
    if index == 8:
        return problem("对称极坐标瓣", "polar_area", f"{a}*sin(2*theta)", theta_lower="0", theta_upper="pi/2", target="利用单瓣区间理解图像。")
    return problem("平移圆瓣面积", "polar_area", f"{a}*(1+sin(theta))", theta_lower="0", theta_upper="pi", target="先看图像，再确认积分区间。")


def make_polar_advanced(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 4)
    if index == 0:
        return problem("极坐标单位圆二重积分", "polar_double", "1", r_lower="0", r_upper=str(a), theta_lower="0", theta_upper="2*pi", target="用雅可比 \\(r\\) 计算圆盘面积。")
    if index == 1:
        return problem("极坐标径向二重积分", "polar_double", "r", r_lower="0", r_upper=str(a), theta_lower="0", theta_upper="2*pi", target="被积函数乘雅可比后变成 \\(r^2\\)。")
    if index == 2:
        return problem("径向平方曲面体积", "polar_double", "r^2", r_lower="0", r_upper=str(a), theta_lower="0", theta_upper="2*pi", target="适合圆盘上的径向函数。")
    if index == 3:
        return problem("环形扇区二重积分", "polar_double", "1", r_lower=str(a), r_upper=str(a + rand_int(rng, 1, 3)), theta_lower="0", theta_upper="pi/2", target="环形扇区必须保留内外半径。")
    if index == 4:
        return problem("变量半径圆盘", "polar_double", "1", r_lower="0", r_upper=f"{a}*sin(theta)", theta_lower="0", theta_upper="pi", target="半径边界依赖角度时更能体现极坐标优势。")
    if index == 5:
        return problem("变量半径加权面积", "polar_double", "r", r_lower="0", r_upper=f"{a}*cos(theta)", theta_lower="-pi/2", theta_upper="pi/2", target="先写区域，再乘雅可比。")
    if index == 6:
        return problem("角向权重二重积分", "polar_double", "sin(theta)", r_lower="0", r_upper=str(a), theta_lower="0", theta_upper="pi", target="角向函数在极坐标中直接积分。")
    if index == 7:
        return problem("径向指数曲面", "polar_double", "exp(-r)", r_lower="0", r_upper=str(a), theta_lower="0", theta_upper="2*pi", target="圆盘上的径向衰减函数。")
    if index == 8:
        return problem("极坐标夹层二重积分", "polar_double", "1", r_lower=f"{a}", r_upper=f"{a}+sin(theta)", theta_lower="0", theta_upper="pi", target="变量外半径和常数内半径形成夹层。")
    return problem("极坐标面积再解释", "polar_area", f"{a}*(1+cos(theta))", inner_expression=str(a), theta_lower="0", theta_upper="pi", target="曲线夹层可以先用面积公式训练，再连接二重积分。")


def make_polar_mit(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 3)
    n = rand_int(rng, 2, 5)
    if index == 0:
        return problem("振荡极径面积", "polar_area", f"{a}+sin({n}*theta)", theta_lower="0", theta_upper="2*pi", target="振荡半径适合用数值和图像共同校验。")
    if index == 1:
        return problem("指数极径面积", "polar_area", f"exp(sin(theta))", theta_lower="0", theta_upper="2*pi", target="允许出现非初等闭式结果。")
    if index == 2:
        return problem("复杂玫瑰线瓣", "polar_area", f"{a}*sin({n}*theta)", theta_lower="0", theta_upper=f"2*pi/{n}", target="用图像确认瓣的范围。")
    if index == 3:
        return problem("高斯径向圆盘", "polar_double", "exp(-r^2)", r_lower="0", r_upper=str(a + 1), theta_lower="0", theta_upper="2*pi", target="高斯型函数在极坐标下很自然。")
    if index == 4:
        return problem("耦合振荡极坐标曲面", "polar_double", "sin(r*theta)", r_lower="0", r_upper="1", theta_lower="0", theta_upper="pi", target="数值曲面体积挑战。")
    if index == 5:
        return problem("角向指数权重", "polar_double", "exp(cos(theta))", r_lower="0", r_upper=str(a), theta_lower="0", theta_upper="2*pi", target="角向非初等积分适合数值校验。")
    if index == 6:
        return problem("变量半径高斯窗口", "polar_double", "exp(-r^2)", r_lower="0", r_upper=f"{a}*(1+cos(theta))", theta_lower="0", theta_upper="2*pi", target="变量边界和径向函数结合。")
    if index == 7:
        return problem("复杂夹层面积", "polar_area", f"{a}+cos(2*theta)", inner_expression=f"{a}/2", theta_lower="0", theta_upper="2*pi", target="夹层面积用图像帮助理解。")
    if index == 8:
        return problem("径向有理曲面", "polar_double", "1/(1+r^2)", r_lower="0", r_upper=str(a + 1), theta_lower="0", theta_upper="2*pi", target="有理径向函数通常比直角坐标更简洁。")
    return problem("极坐标螺线加权", "polar_double", "r^2", r_lower="0", r_upper=f"{a}*theta", theta_lower="0", theta_upper="pi", target="半径边界随角度增长，适合观察区域形状。")


def make_solid_easy(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 5)
    b = rand_int(rng, 1, 4)
    if index == 0:
        return problem("圆盘法：直线绕 x 轴", "solid_revolution", f"{a}*x", inner_expression="0", lower="0", upper=str(b), solid_preset="washer_x", target="垂直于 x 轴切片，每片是圆盘。", recipe_id="solid_washer")
    if index == 1:
        return problem("圆柱体体积", "solid_revolution", str(a), inner_expression="0", lower="0", upper=str(b), solid_preset="washer_x", target="常半径圆盘累积成圆柱。", recipe_id="solid_washer")
    if index == 2:
        return problem("垫片法：常半径夹层", "solid_revolution", str(a + 2), inner_expression=str(a), lower="0", upper=str(b), solid_preset="washer_x", target="外圆盘减内圆盘得到垫片截面。", recipe_id="solid_washer")
    if index == 3:
        return problem("绕 y 轴的圆盘", "solid_revolution", f"{a}*y", inner_expression="0", lower="0", upper=str(b), solid_preset="washer_y", target="把 y 当作积分变量，截面垂直于 y 轴。", recipe_id="solid_washer")
    if index == 4:
        return problem("柱壳法：三角形绕 y 轴", "solid_revolution", f"{a}-x", inner_expression="0", lower="0", upper=str(a), solid_preset="shell_y", target="竖条绕 y 轴形成柱壳。", recipe_id="solid_shell")
    if index == 5:
        return problem("柱壳法：横条绕 x 轴", "solid_revolution", f"{a}-y", inner_expression="0", lower="0", upper=str(a), solid_preset="shell_x", target="横条绕 x 轴形成柱壳。", recipe_id="solid_shell")
    if index == 6:
        return problem("抛物线圆盘", "solid_revolution", f"{a}*x^2", inner_expression="0", lower="0", upper="1", solid_preset="washer_x", target="幂函数半径用圆盘法。", recipe_id="solid_washer")
    if index == 7:
        return problem("线性垫片", "solid_revolution", f"{a}+x", inner_expression=str(a), lower="0", upper=str(b), solid_preset="washer_x", target="外半径随 x 增长，内半径保持常数。", recipe_id="solid_washer")
    if index == 8:
        return problem("绕 y 轴常半径垫片", "solid_revolution", str(a + b), inner_expression=str(a), lower="0", upper=str(b), solid_preset="washer_y", target="y 方向累积同样可以形成垫片。", recipe_id="solid_washer")
    return problem("柱壳法：矩形绕 y 轴", "solid_revolution", str(a), inner_expression="0", lower="0", upper=str(b), solid_preset="shell_y", target="常高度竖条绕 y 轴形成柱壳。", recipe_id="solid_shell")


def make_solid_ap(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 4)
    b = rand_int(rng, 2, 5)
    if index == 0:
        return problem("垫片法：两条直线之间", "solid_revolution", f"{b}", inner_expression=f"{a}*x", lower="0", upper="1", solid_preset="washer_x", target="先找外半径和内半径，再平方相减。", recipe_id="solid_washer")
    if index == 1:
        return problem("圆盘法：根式轮廓", "solid_revolution", f"sqrt({a}*x)", inner_expression="0", lower="0", upper=str(b), solid_preset="washer_x", target="根式半径平方后会简化。", recipe_id="solid_washer")
    if index == 2:
        return problem("柱壳法：抛物线高度", "solid_revolution", f"{b}-x^2", inner_expression="0", lower="0", upper="1", solid_preset="shell_y", target="半径是 x，高度来自上曲线减下曲线。", recipe_id="solid_shell")
    if index == 3:
        return problem("柱壳法：y 变量", "solid_revolution", f"{b}-y^2", inner_expression="0", lower="0", upper="1", solid_preset="shell_x", target="绕 x 轴时横条半径是 y。", recipe_id="solid_shell")
    if index == 4:
        return problem("绕 y 轴的垫片", "solid_revolution", f"{a}+y", inner_expression=str(a), lower="0", upper=str(b), solid_preset="washer_y", target="把半径写成 y 的函数。", recipe_id="solid_washer")
    if index == 5:
        return problem("圆盘法：半圆轮廓", "solid_revolution", f"sqrt({a}^2-x^2)", inner_expression="0", lower="0", upper=str(a), solid_preset="washer_x", target="平方后得到二次多项式。", recipe_id="solid_washer")
    if index == 6:
        return problem("壳层法：夹层高度", "solid_revolution", f"{b}", inner_expression="x", lower="0", upper=str(a), solid_preset="shell_y", target="高度是外函数减内函数。", recipe_id="solid_shell")
    if index == 7:
        return problem("垫片法：抛物线内孔", "solid_revolution", str(b), inner_expression="x^2", lower="0", upper="1", solid_preset="washer_x", target="内半径也要平方，不能只相减半径。", recipe_id="solid_washer")
    if index == 8:
        return problem("柱壳法：线性夹层", "solid_revolution", f"{a}+x", inner_expression="x", lower="0", upper=str(b), solid_preset="shell_y", target="柱壳高度来自两条曲线差。", recipe_id="solid_shell")
    return problem("绕 x 轴柱壳：线性夹层", "solid_revolution", f"{a}+y", inner_expression="y", lower="0", upper=str(b), solid_preset="shell_x", target="横向柱壳同样用半径乘高度。", recipe_id="solid_shell")


def make_solid_advanced(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 3)
    if index == 0:
        return problem("三角轮廓绕 x 轴", "solid_revolution", f"{a}*sin(x)", inner_expression="0", lower="0", upper="pi", solid_preset="washer_x", target="三角半径平方后需要用降幂公式。", recipe_id="solid_washer")
    if index == 1:
        return problem("余弦轮廓垫片", "solid_revolution", f"{a}+cos(x)", inner_expression=str(a), lower="0", upper="pi/2", solid_preset="washer_x", target="外半径平方会产生三角项。", recipe_id="solid_washer")
    if index == 2:
        return problem("指数衰减旋转体", "solid_revolution", "exp(-x)", inner_expression="0", lower="0", upper=str(a + 1), solid_preset="washer_x", target="指数半径平方后仍可精确积分。", recipe_id="solid_washer")
    if index == 3:
        return problem("柱壳法：指数高度", "solid_revolution", "exp(-x)", inner_expression="0", lower="0", upper=str(a + 1), solid_preset="shell_y", target="柱壳法会出现 x 乘指数函数。", recipe_id="solid_shell")
    if index == 4:
        return problem("绕 y 轴的根式垫片", "solid_revolution", f"sqrt({a}*y)", inner_expression="0", lower="0", upper=str(a + 1), solid_preset="washer_y", target="用 y 变量进行垫片法。", recipe_id="solid_washer")
    if index == 5:
        return problem("柱壳法：三角高度", "solid_revolution", "sin(x)", inner_expression="0", lower="0", upper="pi", solid_preset="shell_y", target="半径乘三角高度，适合观察壳层。", recipe_id="solid_shell")
    if index == 6:
        return problem("垫片法：有内孔三角体", "solid_revolution", f"{a}+sin(x)", inner_expression=str(a), lower="0", upper="pi", solid_preset="washer_x", target="先平方再相减，内半径不能漏掉。", recipe_id="solid_washer")
    if index == 7:
        return problem("绕 x 轴柱壳：三角高度", "solid_revolution", "sin(y)", inner_expression="0", lower="0", upper="pi", solid_preset="shell_x", target="横向壳层训练变量切换。", recipe_id="solid_shell")
    if index == 8:
        return problem("多项式夹层旋转体", "solid_revolution", f"{a}+x^2", inner_expression="x", lower="0", upper="1", solid_preset="washer_x", target="综合使用平方展开和逐项积分。", recipe_id="solid_washer")
    return problem("柱壳法：多项式夹层", "solid_revolution", f"{a}+x^2", inner_expression="x", lower="0", upper="1", solid_preset="shell_y", target="高度先相减，再乘半径。", recipe_id="solid_shell")


def make_solid_mit(rng: random.Random, index: int) -> dict[str, Any]:
    a = rand_int(rng, 1, 3)
    if index == 0:
        return problem("高斯轮廓旋转体", "solid_revolution", "exp(-x^2)", inner_expression="0", lower="0", upper=str(a), solid_preset="washer_x", target="允许出现特殊函数或数值型校验。", recipe_id="solid_washer")
    if index == 1:
        return problem("振荡轮廓旋转体", "solid_revolution", f"{a}+sin(3*x)", inner_expression=str(a), lower="0", upper="2*pi", solid_preset="washer_x", target="振荡半径适合用 3D 图检查。", recipe_id="solid_washer")
    if index == 2:
        return problem("柱壳法挑战：高斯高度", "solid_revolution", "exp(-x^2)", inner_expression="0", lower="0", upper=str(a), solid_preset="shell_y", target="数值和特殊函数共同校验。", recipe_id="solid_shell")
    if index == 3:
        return problem("有理轮廓旋转体", "solid_revolution", "1/(1+x^2)", inner_expression="0", lower="0", upper=str(a + 1), solid_preset="washer_x", target="有理函数平方后可用精确或数值校验。", recipe_id="solid_washer")
    if index == 4:
        return problem("复杂垫片体积", "solid_revolution", f"{a}+cos(2*x)", inner_expression=str(a), lower="0", upper="pi", solid_preset="washer_x", target="三角展开较长，图像辅助理解。", recipe_id="solid_washer")
    if index == 5:
        return problem("绕 y 轴指数垫片", "solid_revolution", "exp(-y)", inner_expression="0", lower="0", upper=str(a + 1), solid_preset="washer_y", target="使用 y 变量的指数旋转体。", recipe_id="solid_washer")
    if index == 6:
        return problem("绕 x 轴柱壳挑战", "solid_revolution", "exp(-y^2)", inner_expression="0", lower="0", upper=str(a), solid_preset="shell_x", target="横向壳层的数值型挑战。", recipe_id="solid_shell")
    if index == 7:
        return problem("根式夹层挑战", "solid_revolution", "sqrt(1+x)", inner_expression="sqrt(x)", lower="0", upper="1", solid_preset="washer_x", target="根式夹层先平方再相减。", recipe_id="solid_washer")
    if index == 8:
        return problem("对数高度柱壳", "solid_revolution", "log(1+x)", inner_expression="0", lower="0", upper=str(a + 1), solid_preset="shell_y", target="壳层法结合对数积分。", recipe_id="solid_shell")
    return problem("特殊函数垫片", "solid_revolution", "exp(-x^2)+1", inner_expression="1", lower="0", upper=str(a), solid_preset="washer_x", target="非初等轮廓用数值和图像共同校验。", recipe_id="solid_washer")


MAKERS: dict[tuple[str, str], Callable[[random.Random, int], dict[str, Any]]] = {
    ("indefinite", "easy"): make_indefinite_easy,
    ("indefinite", "ap"): make_indefinite_ap,
    ("indefinite", "advanced"): make_indefinite_advanced,
    ("indefinite", "mit"): make_indefinite_mit,
    ("definite", "easy"): make_definite_easy,
    ("definite", "ap"): make_definite_ap,
    ("definite", "advanced"): make_definite_advanced,
    ("definite", "mit"): make_definite_mit,
    ("improper", "easy"): make_improper_easy,
    ("improper", "ap"): make_improper_ap,
    ("improper", "advanced"): make_improper_advanced,
    ("improper", "mit"): make_improper_mit,
    ("double", "easy"): make_double_easy,
    ("double", "ap"): make_double_ap,
    ("double", "advanced"): make_double_advanced,
    ("double", "mit"): make_double_mit,
    ("polar", "easy"): make_polar_easy,
    ("polar", "ap"): make_polar_ap,
    ("polar", "advanced"): make_polar_advanced,
    ("polar", "mit"): make_polar_mit,
    ("solid", "easy"): make_solid_easy,
    ("solid", "ap"): make_solid_ap,
    ("solid", "advanced"): make_solid_advanced,
    ("solid", "mit"): make_solid_mit,
}

CONCEPTS: dict[tuple[str, str], tuple[str, ...]] = {
    ("indefinite", "easy"): ("基本原函数", "逐项积分"),
    ("indefinite", "ap"): ("换元法", "链式法则逆用"),
    ("indefinite", "advanced"): ("分部积分", "恒等变形", "有理函数"),
    ("indefinite", "mit"): ("特殊函数", "多步骤技巧"),
    ("definite", "easy"): ("微积分基本定理", "有向面积"),
    ("definite", "ap"): ("换元法", "对称性", "三角恒等式"),
    ("definite", "advanced"): ("分部积分", "部分分式", "技巧综合"),
    ("definite", "mit"): ("特殊函数", "数值校验", "挑战积分"),
    ("improper", "easy"): ("极限定义", "p 型积分"),
    ("improper", "ap"): ("收敛判别", "端点奇异", "指数尾部"),
    ("improper", "advanced"): ("比较判别", "对数换元", "双重反常"),
    ("improper", "mit"): ("特殊函数", "条件收敛", "高精度数值"),
    ("double", "easy"): ("矩形区域", "曲面体积"),
    ("double", "ap"): ("累次积分", "可分离函数", "对称性"),
    ("double", "advanced"): ("二重积分技巧", "耦合曲面", "可分离结构"),
    ("double", "mit"): ("数值曲面体积", "特殊函数", "振荡曲面"),
    ("polar", "easy"): ("极坐标面积", "扇形微元"),
    ("polar", "ap"): ("心形线", "玫瑰线", "夹层面积"),
    ("polar", "advanced"): ("极坐标二重积分", "雅可比因子", "变量边界"),
    ("polar", "mit"): ("数值极坐标", "复杂边界", "特殊函数"),
    ("solid", "easy"): ("旋转体", "圆盘法", "垫片法"),
    ("solid", "ap"): ("旋转体", "柱壳法", "方法选择"),
    ("solid", "advanced"): ("体积积分", "垫片法", "柱壳法"),
    ("solid", "mit"): ("数值旋转体", "特殊函数", "3D 校验"),
}


FAMILIES: list[Family] = []
for (family_kind, family_level), maker in MAKERS.items():
    for family_index in range(10):
        FAMILIES.append(_family(family_kind, family_level, family_index, CONCEPTS[(family_kind, family_level)], maker))

FAMILIES_BY_KEY: dict[tuple[str, str], list[Family]] = {
    (family_kind, family_level): [
        family for family in FAMILIES if family.kind == family_kind and family.level == family_level
    ]
    for family_kind in KINDS
    for family_level in LEVELS
}

for key, families in FAMILIES_BY_KEY.items():
    if len(families) < 10:
        raise RuntimeError(f"Practice generator key {key} has fewer than 10 families")
