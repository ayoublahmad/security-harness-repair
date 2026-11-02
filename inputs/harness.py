"""Local security contract runner."""

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def load_target(path):
    spec = importlib.util.spec_from_file_location("training_target", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load target module: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_equal(actual, expected):
    if type(actual) is not type(expected):
        return False

    if isinstance(actual, dict):
        return (
            actual.keys() == expected.keys()
            and all(
                exact_equal(actual[key], expected[key])
                for key in actual
            )
        )

    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            exact_equal(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected)
        )

    return actual == expected


def run(module, suite):
    results = []

    for case in suite["cases"]:
        case_id = case["id"]

        if not case["selected"]:
            results.append({
                "id": case_id,
                "result": "not-run",
            })
            continue

        try:
            target = module.Target()
            request = copy.deepcopy(case["request"])
            response = target.respond(request)
            state = target.snapshot()
        except Exception as exc:
            results.append({
                "id": case_id,
                "result": "error",
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            })
            continue

        response_matches = exact_equal(
            response,
            case["expected_response"],
        )
        state_matches = exact_equal(
            state,
            case["expected_state"],
        )

        result = "pass" if response_matches and state_matches else "fail"

        result_entry = {
            "id": case_id,
            "result": result,
            "observed_response": response,
            "observed_state": state,
        }

        if result == "fail":
            result_entry["expected_response"] = case["expected_response"]
            result_entry["expected_state"] = case["expected_state"]

        results.append(result_entry)

    counts = {
        "pass": 0,
        "fail": 0,
        "error": 0,
        "not-run": 0,
    }

    for result in results:
        counts[result["result"]] += 1

    return results, counts


def build_report(target_path, cases_path, runner_path):
    suite = json.loads(cases_path.read_text(encoding="utf-8"))
    module = load_target(target_path)

    results, counts = run(module, suite)

    return {
        "provenance": {
            "target": str(target_path),
            "version": getattr(module, "VERSION", None),
            "target_sha256": sha256(target_path),
            "cases": str(cases_path),
            "cases_sha256": sha256(cases_path),
            "runner": str(runner_path),
            "runner_sha256": sha256(runner_path),
        },
        "results": results,
        "counts": counts,
    }


def exit_code(counts):
    if counts["fail"] > 0 or counts["error"] > 0:
        return 1

    if counts["not-run"] > 0:
        return 2

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Replay local HeatherCheck cases."
    )
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = build_report(
            args.target,
            args.cases,
            Path(__file__),
        )
    except Exception as exc:
        print(json.dumps({
            "result": "setup-error",
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }, sort_keys=True))
        return 3

    print(json.dumps(report, sort_keys=True))
    return exit_code(report["counts"])


if __name__ == "__main__":
    raise SystemExit(main())
