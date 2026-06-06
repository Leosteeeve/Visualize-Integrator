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
        lambda r: r["ok"] and r["result_latex"] == r"\frac{1}{3}" and len(r["steps"]) >= 3,
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
