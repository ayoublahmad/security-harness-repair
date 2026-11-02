## Target A versus Target B reconciliation

| Case | Target A | Target B | Interpretation |
|---|---|---|---|
| C01 | pass | pass | Legitimate red access preserved |
| C02 | pass | fail | Target B introduces a blue-access regression |
| C03 | fail | pass | Target B fixes the cross-tenant read issue |
| C04 | pass | pass | Anonymous access behavior preserved |
| C05 | pass | pass | Unknown-session behavior preserved |
| C06 | pass | pass | Missing-report behavior preserved |
| C07 | fail | fail | Unauthorized write state mutation remains in both |
| C08 | pass | fail | Target B introduces another legitimate blue-access regression |
| C09 | error | error | Exception behavior remains unresolved |
| C10 | not-run | not-run | Deliberately unselected in both runs |

Target B fixes the cross-tenant read failure observed in Target A at C03.
However, it introduces regressions at C02 and C08 by denying legitimate blue
tenant access. The unauthorized-write state mutation at C07 remains in both
targets, and both targets still produce an unexpected error at C09.

## Finding register

| ID | Case | Target | Severity | Finding | Status |
|---|---|---|---|---|---|
| F-01 | C03 | A | High | Cross-tenant read returns `200` instead of `403` | Confirmed |
| F-02 | C07 | A and B | High | Denied write changes report state | Confirmed |
| F-03 | C02, C08 | B | High | Legitimate blue-reader access is denied | Regression |
| F-04 | C09 | A and B | Medium | Exception probe crashes instead of returning `400/Unknown` | Error-handling defect |

## F-01 — Cross-tenant read

A red session requests the blue report. The contract requires `403 Denied`,
but Target A returns the blue report with status `200`.

This violates R6 and is detected by exact response comparison under R1.

Target B returns the expected denial for this case.

## F-02 — Denied write mutates state

The red session attempts to write to the blue report. The response is `403
Denied`, but the report value changes to `DEMO-tampered`.

This violates R1 and R6 because denied writes must leave all state unchanged.
The repaired runner detects this by comparing `snapshot()` with the expected
state.
The issue remains in both targets.

## F-03 — Target B legitimate-access regression

Target B denies C02 and C08, although blue-reader is accessing its own blue
report and the expected response is `200`.

This violates R6. Target B must not be accepted as a complete fix because it
removes legitimate access while addressing C03.

## F-04 — Unexpected exception

C09 intentionally sends the `explode` operation. Both targets raise
`RuntimeError: DEMO-storage-failure` instead of returning the expected
`400/Unknown`.

This is a fault-injection probe exposing an error-handling defect. It is not
classified as an authorization vulnerability.

## Decision

Target B should not be accepted as a complete replacement. It improves C03,
but introduces legitimate blue-access regressions and retains the C07 state
mutation and C09 exception behavior.