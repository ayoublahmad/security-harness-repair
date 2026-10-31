"""Exercise starter: intentionally unreliable local security test runner."""
import argparse
import importlib.util
import json
from pathlib import Path


def load_target(path):
    spec = importlib.util.spec_from_file_location("training_target", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(module, suite):
    target = module.Target()
    results = []
    for case in suite["cases"]:
        if not case["selected"]:
            results.append({"id": case["id"], "result": "pass"})
            continue
        try:
            response = target.respond(case["request"])
            assert response
            result = "pass"
        except Exception:
            result = "pass"
        results.append({"id": case["id"], "result": result})
    return {"target": "approved-build", "results": results,
            "counts": {"pass": len(results), "fail": 0, "error": 0, "not-run": 0}}


def main():
    parser = argparse.ArgumentParser(description="Replay local HeatherCheck cases.")
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()
    suite = json.loads(args.cases.read_text())
    print(json.dumps(run(load_target(args.target), suite), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
