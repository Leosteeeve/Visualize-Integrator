import json
from urllib import request


BASE_URL = "http://127.0.0.1:8000"


def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def expect(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"ok - {name}")


def main():
    with request.urlopen(BASE_URL + "/", timeout=10) as response:
        html = response.read().decode("utf-8")

    for marker in ['id="lessonTabs"', 'id="practiceKind"', 'id="qaRaw"', 'id="plot"']:
        expect(f"page marker {marker}", marker in html)

    definite = post_json(
        "/api/solve",
        {"mode": "definite", "expression": "x^2", "lower": "0", "upper": "1"},
    )
    expect("http definite solve", definite["ok"] and definite["result_latex"] == r"\frac{1}{3}")

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

    bad = post_json(
        "/api/solve",
        {"mode": "definite", "expression": "bad(", "lower": "0", "upper": "1"},
    )
    expect("http bad input", not bad["ok"] and bool(bad["error"]) and bool(bad["steps"]))


if __name__ == "__main__":
    main()
