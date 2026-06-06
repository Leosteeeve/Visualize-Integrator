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
        "raw definite input",
        {"raw": "\u222b_0^1 x^2 dx"},
        lambda r: r["ok"] and r["mode"] == "definite" and r["result_latex"] == r"\frac{1}{3}",
    )
    check(
        "bad input",
        {"mode": "definite", "expression": "bad(", "lower": "0", "upper": "1"},
        lambda r: not r["ok"] and bool(r["error"]),
    )


if __name__ == "__main__":
    main()
