# Baseline Analysis: Misleading Results

The baseline captures show that the starter runner reported all cases as `pass` and exited with status `0` for both targets. This result is false-green evidence. The runner did not verify the security contract defined by the harness policy.

## Runner defects in the starter

The original `inputs/harness.py` contains the following defects:

| Code location | Runner defect | Policy violation |
|---|---|---|
| `run()`, target creation | One `Target()` instance is reused for the entire suite | R2 requires fresh state for every selected case |
| Unselected-case branch | Cases with `selected: false` are reported as `pass` | R3 requires `not-run` |
| `assert response` | Only checks that the response is truthy; it does not compare the expected response | R1 requires exact response comparison |
| `except Exception` | Every exception is converted into `pass` | R3 requires `error` with exception details |
| Result counts | All cases are counted as passes, regardless of their actual behavior | R4 requires truthful counts |
| `main()` return value | The runner always exits with status `0` | R4 requires status `1` for failures/errors and status `2` for unselected cases |
| Report metadata | The runner reports `approved-build` instead of the actual target | R5 requires truthful provenance |
| Entire execution flow | `snapshot()` is never called | R1 requires exact state comparison |

## Case analysis

### C03 — Cross-tenant read

C03 sends a request for `red-reader` to read the blue report `r-blue`.

Expected response:

```json
{"status": 403, "body": "Denied"}
```

Target A returns:

```json
{"status": 200, "body": "DEMO-blue"}
```

This is a **target security defect**. Target A checks that the session exists but does not verify that the session tenant owns the requested report.

This violates R6, which requires sessions to read only their own reports. It also demonstrates why R1 requires exact response comparison.

The starter runner incorrectly reports `pass` because the response is non-empty and therefore satisfies only the weak `assert response` check.

Classification:

- Target A: authorization defect
- Starter harness: runner defect because it fails to detect the incorrect response

### C07 — Denied write changes state

C07 attempts to write to the blue report using the red session.

Expected response:

```json
{"status": 403, "body": "Denied"}
```

Expected state:

```json
{
  "r-red": "DEMO-red",
  "r-blue": "DEMO-blue"
}
```

Target A and Target B return `403`, but the write occurs before the ownership check. As a result, `r-blue` becomes `DEMO-tampered`.

This is a **target integrity and authorization defect**. R6 requires denied writes to leave all state unchanged, and R1 requires the harness to compare the complete state using `snapshot()`.

The starter runner incorrectly reports `pass` because:

1. It accepts any truthy response.
2. It never calls `snapshot()`.
3. It cannot detect that the state changed despite the `403` response.

Classification:

- Target A and Target B: unauthorized state mutation
- Starter harness: runner defect because it does not inspect state

### C02 and C08 — Legitimate blue access on Target B

C02 and C08 are legitimate reads by `blue-reader` of `r-blue`.

Expected response:

```json
{"status": 200, "body": "DEMO-blue"}
```

Target B returns:

```json
{"status": 403, "body": "Denied"}
```

This is a **Target B regression**. Although Target B adds an ownership check for reads, it also denies every blue tenant because of the additional `tenant == "blue"` condition.

This violates R6 because legitimate users must be able to access their own reports.

The starter runner incorrectly reports both cases as `pass` because it does not compare the observed response with the expected response.

Classification:

- Target B: legitimate-access regression
- Starter harness: runner defect because it accepts an incorrect non-empty response

### C09 — Exception probe

C09 sends:

```json
{"op": "explode"}
```

The expected contract is:

```json
{"status": 400, "body": "Unknown"}
```

Both targets raise:

```text
RuntimeError: DEMO-storage-failure
```

The request is deliberate **fault injection**. It is designed to test how the target and runner handle an unexpected failure.

The target behavior is an error against the R6 contract because the target crashes instead of returning the expected `400/Unknown` response. However, C09 is not evidence of an authorization vulnerability.

The starter runner hides the problem with:

```python
except Exception:
    result = "pass"
```

Under R3, the correct result is `error`, including the exception type and message.

Classification:

- C09 input: fault injection
- Target A and Target B: unexpected target error
- Starter harness: runner defect because it converts the exception into `pass`

### C10 — Unselected case

C10 has:

```json
"selected": false
```

The starter runner reports:

```json
{"id": "C10", "result": "pass"}
```

However, the target was never called.

Under R3, an unselected case must be reported as:

```json
{"id": "C10", "result": "not-run"}
```

It must not contain observed response or state and must not be used as evidence that the target passed.

Classification:

- No target behavior was observed
- The result is a runner defect
- The correct state is `not-run`, not `pass`

## Summary of classifications

| Case | Target A | Target B | Correct classification |
|---|---|---|---|
| C03 | Cross-tenant read allowed | Ownership check denies the read | Target A security defect; runner hides the result |
| C02/C08 | Legitimate blue reads succeed | Legitimate blue reads denied | Target B regression; runner hides the result |
| C07 | Denied write mutates state | Denied write mutates state | Target defect in both targets; runner misses state change |
| C09 | Runtime exception | Runtime exception | Fault-injection probe exposing target error handling; runner hides the error |
| C10 | Not executed | Not executed | Runner defect because it is reported as `pass` |

## Conclusion

The baseline output cannot be treated as a security result. The starter runner produces false-green evidence because it performs weak response validation, does not inspect state, swallows exceptions, marks unselected cases as passing, reuses mutable target state, and always exits successfully.

