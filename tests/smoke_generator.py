import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import problem_generator  # noqa: E402
import server  # noqa: E402


def expect(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"ok - {name}")


def main():
    expect("family count", len(problem_generator.FAMILIES) == 200)
    expect("capacity estimate", problem_generator.total_capacity() >= 200000)

    for kind in problem_generator.KINDS:
        for level in problem_generator.LEVELS:
            families = problem_generator.FAMILIES_BY_KEY[(kind, level)]
            expect(f"{kind}/{level} family minimum", len(families) >= 10)

    per_pair = 100 if os.environ.get("CALCULUS_GENERATOR_STRESS") else 1
    seen = set()
    for kind in problem_generator.KINDS:
        for level in problem_generator.LEVELS:
            pair_seen = set()
            for index in range(per_pair):
                result = server.generate_practice_payload(
                    {
                        "kind": kind,
                        "level": level,
                        "seed": f"{kind}-{level}-{index}",
                        "avoid_signatures": list(pair_seen),
                    }
                )
                expect(f"{kind}/{level}/{index} generated", result["ok"])
                signature = result["signature"]
                expect(f"{kind}/{level}/{index} unique in pair", signature not in pair_seen)
                expect(f"{kind}/{level}/{index} solution ok", result["solution"]["ok"])
                expect(f"{kind}/{level}/{index} recipe metadata", bool(result["problem"].get("recipe")))
                expect(f"{kind}/{level}/{index} algebra field", "algebra_steps" in result["solution"])
                expected_method, _ = server.method_from_algebra(result["solution"]["algebra_steps"], "zh-CN")
                expect(f"{kind}/{level}/{index} method follows algebra", result["solution"]["method"] == expected_method)
                pair_seen.add(signature)
                seen.add(signature)

    first = server.generate_practice_payload({"kind": "definite", "level": "easy", "seed": "avoid-check"})
    second = server.generate_practice_payload(
        {
            "kind": "definite",
            "level": "easy",
            "seed": "avoid-check",
            "avoid_signatures": [first["signature"]],
        }
    )
    expect("avoid first result", first["ok"])
    expect("avoid second result", second["ok"])
    expect("avoid signature changes", first["signature"] != second["signature"])

    english = server.generate_practice_payload(
        {"kind": "definite", "level": "ap", "seed": "english-practice", "language": "en-US"}
    )
    expect("english practice generated", english["ok"])
    expect("english practice problem localized", english["problem"]["title"] == "Definite integral practice")
    expect("english practice solution localized", english["solution"]["language"] == "en-US")
    expect("english practice algebra localized", english["solution"]["algebra_steps"]["language"] == "en-US")
    expect("english practice concepts localized", all("法" not in item for item in english["problem"].get("concepts", [])))

    for index in (0, 1, 2, 3, 9):
        item = problem_generator.make_definite_advanced(problem_generator.make_rng(f"parts-align-{index}"), index)
        solution = server.solve_payload(problem_generator.payload_for(item))
        expect(f"advanced parts title {index} solution ok", solution["ok"])
        expect(
            f"advanced parts title {index} recipe aligned",
            solution["algebra_steps"]["recipe_id"] == "integration_by_parts",
        )
        expect(f"advanced parts title {index} method aligned", solution["method"] == "分部积分")

    exp_trig = problem_generator.make_indefinite_advanced(problem_generator.make_rng("indefinite-exp-trig"), 9)
    exp_trig_solution = server.solve_payload(problem_generator.payload_for(exp_trig))
    expect("indefinite exp trig generated solution ok", exp_trig_solution["ok"])
    expect("indefinite exp trig recipe aligned", exp_trig_solution["algebra_steps"]["recipe_id"] == "repeated_integration_by_parts")
    expect("indefinite exp trig method aligned", exp_trig_solution["method"] == "重复分部积分")

    bad = server.generate_practice_payload({"kind": "vector", "level": "easy"})
    expect("invalid kind handled", not bad["ok"] and bool(bad["error"]))
    print(f"generated signatures checked: {len(seen)}")


if __name__ == "__main__":
    main()
