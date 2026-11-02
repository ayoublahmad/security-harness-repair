# Decision and Work Log

## Prioritization

I prioritized repairing the evidence workflow before assessing the targets.

After repair, the highest-priority target issue was the cross-tenant read in C03,
because Target A exposes one tenant's report to another tenant. The denied-write
state mutation in C07 was also prioritized because a request reported as denied
still modified protected data.

## Implementation decision

I repaired only `inputs/harness.py`. I preserved the following supplied files
unchanged:

- `inputs/target_a.py`
- `inputs/target_b.py`
- `inputs/cases.json`

The repaired runner performs exact response and state comparisons, creates fresh
target state for each selected case, copies requests, reports four result states,
continues after errors, records provenance, and returns truthful exit statuses.

## Validation obstacle and response

The first state-mutation meta-test used an incomplete expected observed state. The
synthetic target initialized both reports and modified only `r-blue`, so the
observed state correctly contained both `r-red` and modified `r-blue`.

I corrected the test expectation to match the complete snapshot and reran the
meta-tests successfully.

## Meta-test validation

The meta-tests cover:

- an all-pass contract target;
- a known-bad target;
- an always-success response;
- unexpected exceptions;
- continued execution after errors;
- unselected cases;
- state mutation;
- fresh state per case;
- order independence;
- request preservation.

The original runner was tested before repair and exposed false-green behavior and
request mutation. The repaired runner was then tested with the same meta-test
suite.

## Target comparison decision

Target B improves the C03 cross-tenant read result, but it introduces failures
for legitimate blue-reader access in C02 and C08. It also retains the C07
denied-write state mutation and the C09 exception behavior.

I therefore decided that Target B must not be accepted as a complete replacement.

## Limitations

The supplied application is a fictional in-memory model. The evidence does not
cover real network behavior, browser execution, database transactions,
concurrency, persistence, deployment configuration, or cases outside the
provided finite suite.

C09 is a fault-injection/error-handling probe, not proof of an authorization
vulnerability. C10 is intentionally unselected and provides no observed target
behavior.

## Next verification step

Correct Target B so that it preserves legitimate blue access while denying
cross-tenant access. Move authorization checks before any state mutation and
define the required handling for the injected exception.

Then rerun the unchanged cases with the repaired runner and add regression cases
for each correction.