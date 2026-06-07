import json
import os
from urllib import request


BASE_URL = os.environ.get("CALCULUS_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.environ.get("CALCULUS_HTTP_TIMEOUT", "60"))


def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def expect(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"ok - {name}")


def main():
    with request.urlopen(BASE_URL + "/", timeout=TIMEOUT) as response:
        html = response.read().decode("utf-8")

    for marker in [
        'id="lessonTabs"',
        'id="practiceKind"',
        'id="qaRaw"',
        'id="plot"',
        'id="threePlot"',
        'id="polarBoundsGrid"',
        'id="solidBoundsGrid"',
        'id="languageToggle"',
        'i18n/en-US.js',
    ]:
        expect(f"page marker {marker}", marker in html)

    definite = post_json(
        "/api/solve",
        {"mode": "definite", "expression": "x^2", "lower": "0", "upper": "1"},
    )
    expect(
        "http definite solve",
        definite["ok"] and definite["result_latex"] == r"\frac{1}{3}" and definite["algebra_steps"]["available"],
    )

    english = post_json(
        "/api/solve",
        {
            "mode": "definite",
            "expression": "cos(x)^5*sin(x)",
            "lower": "0",
            "upper": "pi/2",
            "language": "en-US",
        },
    )
    expect(
        "http english solve",
        english["ok"]
        and english["language"] == "en-US"
        and english["method"] == "Substitution"
        and english["algebra_steps"]["formula_cards"][0]["title"] == "Substitution",
    )

    parts = post_json(
        "/api/solve",
        {"mode": "definite", "expression": "x*log(x)", "lower": "1", "upper": "3"},
    )
    expect(
        "http parts method aligned",
        parts["ok"]
        and parts["method"] == "分部积分"
        and parts["algebra_steps"]["recipe_id"] == "integration_by_parts",
    )

    indefinite_exp_trig = post_json(
        "/api/solve",
        {"mode": "indefinite", "expression": "exp(x)*sin(x)"},
    )
    expect(
        "http indefinite exp trig method aligned",
        indefinite_exp_trig["ok"]
        and indefinite_exp_trig["method"] == "重复分部积分"
        and indefinite_exp_trig["algebra_steps"]["recipe_id"] == "repeated_integration_by_parts",
    )

    double = post_json(
        "/api/solve",
        {
            "mode": "double",
            "expression": "x*y",
            "x_lower": "0",
            "x_upper": "1",
            "y_lower": "0",
            "y_upper": "1",
        },
    )
    expect("http double solve", double["ok"] and double["plot"]["kind"] == "surface")

    raw = post_json("/api/solve", {"raw": "\u222b_1^oo 1/x^2 dx"})
    expect("http raw improper solve", raw["ok"] and raw.get("improper", {}).get("status") == "convergent")

    polar = post_json(
        "/api/solve",
        {"mode": "polar_area", "expression": "1", "thetaLower": "0", "thetaUpper": "2*pi"},
    )
    expect("http polar solve", polar["ok"] and polar["result_latex"] == r"\pi")

    solid = post_json(
        "/api/solve",
        {"mode": "solid_revolution", "solidPreset": "washer_x", "expression": "x", "innerExpression": "0", "lower": "0", "upper": "1"},
    )
    expect("http solid solve", solid["ok"] and solid["result_latex"] == r"\frac{\pi}{3}" and solid["plot"]["kind"] == "solid_revolution")

    practice = post_json(
        "/api/practice/generate",
        {"kind": "definite", "level": "easy", "seed": "http-practice", "language": "en-US"},
    )
    expect(
        "http practice generate",
        practice["ok"]
        and practice["solution"]["ok"]
        and practice["solution"]["language"] == "en-US"
        and practice["signature"]
        and "algebra_steps" in practice["solution"],
    )

    practice_next = post_json(
        "/api/practice/generate",
        {
            "kind": "definite",
            "level": "easy",
            "seed": "http-practice",
            "avoid_signatures": [practice["signature"]],
        },
    )
    expect("http practice avoid", practice_next["ok"] and practice_next["signature"] != practice["signature"])

    polar_practice = post_json(
        "/api/practice/generate",
        {"kind": "polar", "level": "ap", "seed": "http-polar-practice"},
    )
    expect("http polar practice generate", polar_practice["ok"] and polar_practice["solution"]["ok"])

    solid_practice = post_json(
        "/api/practice/generate",
        {"kind": "solid", "level": "ap", "seed": "http-solid-practice"},
    )
    expect("http solid practice generate", solid_practice["ok"] and solid_practice["solution"]["ok"])

    bad = post_json(
        "/api/solve",
        {"mode": "definite", "expression": "bad(", "lower": "0", "upper": "1"},
    )
    expect("http bad input", not bad["ok"] and bool(bad["error"]) and bool(bad["steps"]))


if __name__ == "__main__":
    main()
