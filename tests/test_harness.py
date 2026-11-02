import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "inputs" / "harness.py"

spec = importlib.util.spec_from_file_location("harness_under_test", HARNESS_PATH)
harness = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness
spec.loader.exec_module(harness)


def make_case(
    case_id,
    request,
    expected_response,
    expected_state,
    selected=True,
):
    return {
        "id": case_id,
        "selected": selected,
        "request": request,
        "expected_response": expected_response,
        "expected_state": expected_state,
    }


def result_by_id(results):
    return {result["id"]: result for result in results}

# Synthetic targets isolate runner behavior from the supplied vulnerable targets.
class GoodTarget:
    def __init__(self):
        self.reports = {
            "r-red": "DEMO-red",
            "r-blue": "DEMO-blue",
        }

    def snapshot(self):
        return dict(self.reports)

    def respond(self, request):
        if request["op"] == "read":
            if request["session"] == "red-reader":
                if request["report"] == "r-red":
                    return {"status": 200, "body": "DEMO-red"}
                return {"status": 403, "body": "Denied"}

            if request["session"] == "blue-reader":
                if request["report"] == "r-blue":
                    return {"status": 200, "body": "DEMO-blue"}
                return {"status": 403, "body": "Denied"}

            return {"status": 401, "body": "Sign in"}

        return {"status": 400, "body": "Unknown"}


class AlwaysSuccessTarget:
    def __init__(self):
        self.reports = {
            "r-red": "DEMO-red",
            "r-blue": "DEMO-blue",
        }

    def snapshot(self):
        return dict(self.reports)

    def respond(self, request):
        return {"status": 200, "body": "OK"}


class KnownBadTarget:
    def __init__(self):
        self.reports = {
            "r-red": "DEMO-red",
            "r-blue": "DEMO-blue",
        }

    def snapshot(self):
        return dict(self.reports)

    def respond(self, request):
        return {"status": 200, "body": "DEMO-blue"}


class ExceptionTarget:
    def __init__(self):
        self.reports = {
            "r-red": "DEMO-red",
            "r-blue": "DEMO-blue",
        }

    def snapshot(self):
        return dict(self.reports)

    def respond(self, request):
        if request["op"] == "explode":
            raise RuntimeError("synthetic failure")
        return {"status": 200, "body": "DEMO-red"}


class MutationTarget:
    def __init__(self):
        self.reports = {
            "r-red": "DEMO-red",
            "r-blue": "DEMO-blue",
        }

    def snapshot(self):
        return dict(self.reports)

    def respond(self, request):
        self.reports["r-blue"] = "DEMO-tampered"
        return {"status": 403, "body": "Denied"}


class CountingTarget:
    def __init__(self):
        self.calls = 0

    def snapshot(self):
        return {"calls": self.calls}

    def respond(self, request):
        self.calls += 1
        return {"status": 200, "body": "OK"}


class MutatingRequestTarget:
    def __init__(self):
        self.reports = {}

    def snapshot(self):
        return {}

    def respond(self, request):
        request["mutated"] = True
        return {"status": 200, "body": "OK"}


class HarnessTests(unittest.TestCase):
    # Run cases directly through the harness without starting a subprocess.
    def run_suite(self, target_class, cases):
        module = SimpleNamespace(Target=target_class)
        return harness.run(module, {"suite": "META", "cases": cases})

    def test_all_pass_contract_target(self):
        cases = [
            make_case(
                "PASS-1",
                {
                    "op": "read",
                    "session": "red-reader",
                    "report": "r-red",
                },
                {"status": 200, "body": "DEMO-red"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            ),
            make_case(
                "PASS-2",
                {
                    "op": "read",
                    "session": "blue-reader",
                    "report": "r-blue",
                },
                {"status": 200, "body": "DEMO-blue"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            ),
        ]

        results, counts = self.run_suite(GoodTarget, cases)

        self.assertEqual(counts, {
            "pass": 2,
            "fail": 0,
            "error": 0,
            "not-run": 0,
        })
        self.assertTrue(all(result["result"] == "pass" for result in results))

    def test_known_bad_target_is_rejected(self):
        cases = [
            make_case(
                "BAD-1",
                {
                    "op": "read",
                    "session": "red-reader",
                    "report": "r-blue",
                },
                {"status": 403, "body": "Denied"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            )
        ]

        results, counts = self.run_suite(KnownBadTarget, cases)

        self.assertEqual(counts["fail"], 1)
        self.assertEqual(result_by_id(results)["BAD-1"]["result"], "fail")
        self.assertEqual(
            result_by_id(results)["BAD-1"]["observed_response"],
            {"status": 200, "body": "DEMO-blue"},
        )

    def test_always_success_response_does_not_pass(self):
        cases = [
            make_case(
                "WRONG-RESPONSE",
                {"op": "read"},
                {"status": 403, "body": "Denied"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            )
        ]

        results, counts = self.run_suite(AlwaysSuccessTarget, cases)

        self.assertEqual(counts["fail"], 1)
        self.assertEqual(
            result_by_id(results)["WRONG-RESPONSE"]["result"],
            "fail",
        )
   # Errors must be reported without preventing later cases from running.
    def test_exception_is_error_and_execution_continues(self):
        cases = [
            make_case(
                "ERROR-1",
                {"op": "explode"},
                {"status": 400, "body": "Unknown"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            ),
            make_case(
                "AFTER-ERROR",
                {"op": "read"},
                {"status": 200, "body": "DEMO-red"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            ),
        ]

        results, counts = self.run_suite(ExceptionTarget, cases)
        by_id = result_by_id(results)

        self.assertEqual(counts["error"], 1)
        self.assertEqual(by_id["ERROR-1"]["result"], "error")
        self.assertEqual(
            by_id["ERROR-1"]["error"],
            {
                "type": "RuntimeError",
                "message": "synthetic failure",
            },
        )
        self.assertEqual(by_id["AFTER-ERROR"]["result"], "pass")
# Unselected cases are unknown evidence, not successful tests.
    def test_unselected_case_is_not_run(self):
        cases = [
            make_case(
                "UNSELECTED",
                {"op": "must-not-run"},
                {"status": 200, "body": "OK"},
                {},
                selected=False,
            ),
            make_case(
                "SELECTED",
                {"op": "run"},
                {"status": 200, "body": "OK"},
                {"calls": 1},
            ),
        ]

        results, counts = self.run_suite(CountingTarget, cases)
        by_id = result_by_id(results)

        self.assertEqual(counts["not-run"], 1)
        self.assertEqual(by_id["UNSELECTED"]["result"], "not-run")
        self.assertNotIn("observed_response", by_id["UNSELECTED"])
        self.assertNotIn("observed_state", by_id["UNSELECTED"])
        self.assertEqual(by_id["SELECTED"]["result"], "pass")
# A correct denial response is insufficient if internal state was modified.
    def test_state_mutation_is_detected(self):
        cases = [
            make_case(
                "STATE-CHANGE",
                {"op": "write"},
                {"status": 403, "body": "Denied"},
                {
                    "r-red": "DEMO-red",
                    "r-blue": "DEMO-blue",
                },
            )
        ]

        results, counts = self.run_suite(MutationTarget, cases)

        self.assertEqual(counts["fail"], 1)
        self.assertEqual(
            result_by_id(results)["STATE-CHANGE"]["observed_state"],
            {
                 "r-red": "DEMO-red",
                 "r-blue": "DEMO-tampered",
            },
        )
# Each selected case must receive a newly initialized target.
    def test_fresh_state_is_used_for_each_case(self):
        cases = [
            make_case(
                "FRESH-1",
                {"op": "run"},
                {"status": 200, "body": "OK"},
                {"calls": 1},
            ),
            make_case(
                "FRESH-2",
                {"op": "run"},
                {"status": 200, "body": "OK"},
                {"calls": 1},
            ),
        ]

        results, counts = self.run_suite(CountingTarget, cases)

        self.assertEqual(counts, {
            "pass": 2,
            "fail": 0,
            "error": 0,
            "not-run": 0,
        })
        self.assertTrue(all(result["result"] == "pass" for result in results))
# Results must remain tied to case IDs, regardless of execution order.
    def test_order_independence(self):
        cases = [
            make_case(
                "ORDER-1",
                {"op": "run", "value": 1},
                {"status": 200, "body": "OK"},
                {"calls": 1},
            ),
            make_case(
                "ORDER-2",
                {"op": "run", "value": 2},
                {"status": 200, "body": "OK"},
                {"calls": 1},
            ),
        ]

        original_results, original_counts = self.run_suite(
            CountingTarget,
            cases,
        )
        reversed_results, reversed_counts = self.run_suite(
            CountingTarget,
            list(reversed(cases)),
        )

        original_by_id = result_by_id(original_results)
        reversed_by_id = result_by_id(reversed_results)

        self.assertEqual(original_counts, reversed_counts)

        for case_id in original_by_id:
            self.assertEqual(
                original_by_id[case_id]["result"],
                reversed_by_id[case_id]["result"],
            )
            self.assertEqual(
                original_by_id[case_id]["observed_response"],
                reversed_by_id[case_id]["observed_response"],
            )
            self.assertEqual(
                original_by_id[case_id]["observed_state"],
                reversed_by_id[case_id]["observed_state"],
            )
# The target receives a copy so supplied test inputs remain unchanged.
    def test_requests_are_not_mutated(self):
        request = {
            "op": "run",
            "nested": {
                "value": "original",
            },
        }
        original_request = copy.deepcopy(request)

        cases = [
            make_case(
                "INPUT-1",
                request,
                {"status": 200, "body": "OK"},
                {},
            )
        ]

        self.run_suite(MutatingRequestTarget, cases)

        self.assertEqual(request, original_request)
        self.assertNotIn("mutated", request)


if __name__ == "__main__":
    unittest.main(verbosity=2)