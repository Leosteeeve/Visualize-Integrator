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

    per_pair = 100 if os.environ.get("CALCULUS_GENERATOR_STRESS") else 2
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

    bad = server.generate_practice_payload({"kind": "vector", "level": "easy"})
    expect("invalid kind handled", not bad["ok"] and bool(bad["error"]))
    print(f"generated signatures checked: {len(seen)}")


if __name__ == "__main__":
    main()
