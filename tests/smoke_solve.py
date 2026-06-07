from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import server  # noqa: E402


def check(name, payload, predicate):
    result = server.solve_payload(payload)
    if not predicate(result):
        raise AssertionError(f"{name} failed: {result}")
    print(f"ok - {name}")


def main():
    check(
        "definite power",
        {"mode": "definite", "expression": "x^2", "lower": "0", "upper": "1"},
        lambda r: r["ok"]
        and r["result_latex"] == r"\frac{1}{3}"
        and len(r["steps"]) >= 3
        and r["algebra_steps"]["available"],
    )
    check(
        "algebra u substitution",
        {"mode": "definite", "expression": "cos(x)^5*sin(x)", "lower": "0", "upper": "pi/2"},
        lambda r: r["ok"]
        and r["algebra_steps"]["available"]
        and r["algebra_steps"]["recipe_id"] == "u_sub_cos_power_sin"
        and len(r["algebra_steps"]["formula_cards"]) >= 2
        and len(r["algebra_steps"]["reasoning_steps"]) >= 2
        and r"\int_{0}^{1}u^{5}" in r["algebra_steps"]["latex"]
        and r["result_latex"] == r"\frac{1}{6}",
    )
    check(
        "algebra trig power reduction",
        {"mode": "definite", "expression": "sin(x)^2", "lower": "0", "upper": "pi"},
        lambda r: r["ok"]
        and r["algebra_steps"]["available"]
        and r["algebra_steps"]["recipe_id"] == "trig_power_reduction"
        and any(r"\sin^2x" in card["latex"] for card in r["algebra_steps"]["formula_cards"])
        and r["result_latex"] == r"\frac{\pi}{2}",
    )
    check(
        "algebra product to sum",
        {"mode": "definite", "expression": "sin(2*x)*cos(3*x)", "lower": "0", "upper": "pi"},
        lambda r: r["ok"]
        and r["algebra_steps"]["available"]
        and r["algebra_steps"]["recipe_id"] == "trig_product_to_sum"
        and len(r["algebra_steps"]["formula_cards"]) >= 3,
    )
    check(
        "algebra trig absolute split",
        {"mode": "definite", "expression": "sqrt(sin(x)^3-sin(x)^5)", "lower": "0", "upper": "pi"},
        lambda r: r["ok"]
        and r["algebra_steps"]["available"]
        and r["algebra_steps"]["recipe_id"] == "trig_identity_abs_piecewise"
        and any("Absolute value" in card["title"] or "绝对值" in card["title"] for card in r["algebra_steps"]["formula_cards"])
        and r"\frac45" in r["algebra_steps"]["latex"]
        and len(r["algebra_steps"]["notes"]) == 2,
    )
    check(
        "method aligns with integration by parts",
        {"mode": "definite", "expression": "x*log(x)", "lower": "1", "upper": "3"},
        lambda r: r["ok"]
        and r["method"] == "分部积分"
        and r["algebra_steps"]["recipe_id"] == "integration_by_parts"
        and "微积分基本定理" not in r["method"]
        and any("分部积分" in card["title"] for card in r["algebra_steps"]["formula_cards"]),
    )
    check(
        "indefinite exp trig uses repeated parts",
        {"mode": "indefinite", "expression": "exp(x)*sin(x)"},
        lambda r: r["ok"]
        and r["method"] == "重复分部积分"
        and r["algebra_steps"]["recipe_id"] == "repeated_integration_by_parts"
        and "I" in r["algebra_steps"]["latex"]
        and "+C" in r["algebra_steps"]["latex"],
    )
    check(
        "indefinite polynomial uses power rule",
        {"mode": "indefinite", "expression": "x^3 + 2*x"},
        lambda r: r["ok"]
        and r["method"] == "幂函数公式 + 逐项积分"
        and r["algebra_steps"]["recipe_id"] == "power_rule_antiderivative"
        and any("幂函数公式" in card["title"] for card in r["algebra_steps"]["formula_cards"]),
    )
    check(
        "indefinite inverse trig formula",
        {"mode": "indefinite", "expression": "1/(1+x^2)"},
        lambda r: r["ok"]
        and r["method"] == "反三角函数公式"
        and r["algebra_steps"]["recipe_id"] == "inverse_trig_antiderivative",
    )
    check(
        "scaled trig parts stays aligned",
        {"mode": "definite", "expression": "x*sin(3*x)", "lower": "0", "upper": "pi"},
        lambda r: r["ok"]
        and r["method"] == "分部积分"
        and r["algebra_steps"]["recipe_id"] == "integration_by_parts"
        and any("分部积分" in step for step in r["steps"]),
    )
    check(
        "fallback method follows algebra recipe",
        {"mode": "definite", "expression": "1/(1+x^2)", "lower": "0", "upper": "1"},
        lambda r: r["ok"]
        and r["algebra_steps"]["recipe_id"] == "fundamental_theorem"
        and r["method"] == "微积分基本定理"
        and "分部积分" not in r["method"],
    )
    check(
        "english solve localization",
        {
            "mode": "definite",
            "expression": "cos(x)^5*sin(x)",
            "lower": "0",
            "upper": "pi/2",
            "language": "en-US",
        },
        lambda r: r["ok"]
        and r["language"] == "en-US"
        and r["method"] == "Substitution"
        and r["algebra_steps"]["language"] == "en-US"
        and r["algebra_steps"]["formula_cards"][0]["title"] == "Substitution"
        and "换元" not in r["method"],
    )
    check(
        "improper convergent",
        {"mode": "improper", "expression": "1/x^2", "lower": "1", "upper": "oo"},
        lambda r: r["ok"] and r.get("improper", {}).get("status") == "convergent" and r["result_latex"] == "1",
    )
    check(
        "improper divergent",
        {"mode": "improper", "expression": "1/x", "lower": "1", "upper": "oo"},
        lambda r: r["ok"] and r.get("improper", {}).get("status") == "divergent" and r["result_latex"] == r"\infty",
    )
    check(
        "double rectangle",
        {
            "mode": "double",
            "expression": "x*y",
            "x_lower": "0",
            "x_upper": "1",
            "y_lower": "0",
            "y_upper": "1",
        },
        lambda r: r["ok"] and r["result_latex"] == r"\frac{1}{4}" and r["plot"]["kind"] == "surface",
    )
    check(
        "polar circle area",
        {"mode": "polar_area", "expression": "1", "thetaLower": "0", "thetaUpper": "2*pi"},
        lambda r: r["ok"] and r["result_latex"] == r"\pi" and r["plot"]["kind"] == "polar_area",
    )
    check(
        "polar sine circle area",
        {"mode": "polar_area", "expression": "2*sin(theta)", "thetaLower": "0", "thetaUpper": "pi"},
        lambda r: r["ok"] and r["result_latex"] == r"\pi",
    )
    check(
        "polar annular sector",
        {
            "mode": "polar_area",
            "expression": "2",
            "innerExpression": "1",
            "thetaLower": "0",
            "thetaUpper": "pi",
        },
        lambda r: r["ok"] and r["result_latex"] == r"\frac{3 \pi}{2}",
    )
    check(
        "polar double unit disk",
        {
            "mode": "polar_double",
            "expression": "1",
            "rLower": "0",
            "rUpper": "1",
            "thetaLower": "0",
            "thetaUpper": "2*pi",
        },
        lambda r: r["ok"] and r["result_latex"] == r"\pi" and r["plot"]["kind"] == "polar_surface",
    )
    check(
        "polar double radial square",
        {
            "mode": "polar_double",
            "expression": "r^2",
            "rLower": "0",
            "rUpper": "1",
            "thetaLower": "0",
            "thetaUpper": "2*pi",
        },
        lambda r: r["ok"] and r["result_latex"] == r"\frac{\pi}{2}",
    )
    check(
        "solid washer x",
        {"mode": "solid_revolution", "solidPreset": "washer_x", "expression": "x", "innerExpression": "0", "lower": "0", "upper": "1"},
        lambda r: r["ok"] and r["result_latex"] == r"\frac{\pi}{3}" and r["plot"]["kind"] == "solid_revolution" and r["algebra_steps"]["recipe_id"] == "solid_washer",
    )
    check(
        "solid annular washer",
        {"mode": "solid_revolution", "solidPreset": "washer_x", "expression": "2", "innerExpression": "1", "lower": "0", "upper": "3"},
        lambda r: r["ok"] and r["result_latex"] == r"9 \pi" and r["algebra_steps"]["recipe_id"] == "solid_washer",
    )
    check(
        "solid shell y",
        {"mode": "solid_revolution", "solidPreset": "shell_y", "expression": "1-x", "innerExpression": "0", "lower": "0", "upper": "1"},
        lambda r: r["ok"] and r["result_latex"] == r"\frac{\pi}{3}" and r["algebra_steps"]["recipe_id"] == "solid_shell",
    )
    check(
        "solid washer y",
        {"mode": "solid_revolution", "solidPreset": "washer_y", "expression": "y", "innerExpression": "0", "lower": "0", "upper": "1"},
        lambda r: r["ok"] and r["result_latex"] == r"\frac{\pi}{3}" and r["algebra_steps"]["recipe_id"] == "solid_washer",
    )
    check(
        "raw definite input",
        {"raw": "\u222b_0^1 x^2 dx"},
        lambda r: r["ok"] and r["mode"] == "definite" and r["result_latex"] == r"\frac{1}{3}",
    )
    check(
        "raw polar input",
        {"raw": "r=2*sin(theta), theta=0..pi"},
        lambda r: r["ok"] and r["mode"] == "polar_area" and r["result_latex"] == r"\pi",
    )
    check(
        "bad input",
        {"mode": "definite", "expression": "bad(", "lower": "0", "upper": "1"},
        lambda r: not r["ok"] and bool(r["error"]),
    )


if __name__ == "__main__":
    main()
