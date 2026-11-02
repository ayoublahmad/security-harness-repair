
# HeatherCheck Harness Repair Walkthrough

## Executive summary

The supplied starter harness produced false-green security results. It marked
unselected cases and unexpected exceptions as passes, accepted any non-empty
response, did not compare internal state, reused target state between cases,
always exited successfully, and reported inaccurate provenance.

I repaired the runner without changing either target or the supplied cases. The
repaired runner now performs exact response and state comparisons, creates fresh
target state for each selected case, preserves requests, reports `pass`, `fail`,
`error`, and `not-run`, continues after errors, reports provenance, and returns
truthful exit statuses.

## 2. Baseline investigation

I first ran the original starter runner against both targets:

```powershell
python -B inputs\harness.py --target inputs\target_a.py --cases inputs\cases.json
python -B inputs\harness.py --target inputs\target_b.py --cases inputs\cases.json
```

The starter runner reported all cases as `pass` and exited successfully. This was
false-green evidence.

The runner was unreliable because it:

- accepted any non-empty response;
- did not compare expected responses;
- never inspected target state with `snapshot()`;
- converted all exceptions into `pass`;
- reported unselected cases as `pass`;
- reused one target instance across cases;
- always returned exit code `0`;
- reported false target provenance.

The complete and detailled inestagation and analysis is in `docs/baseline-analysis.md`

The original outputs, commands, exit codes, and hashes are preserved in the
`evidence/` directory.

## 3. Runner repair

I repaired `inputs\harness.py` without modifying:

- `inputs\target_a.py`;
- `inputs\target_b.py`;
- `inputs\cases.json`.

The repaired runner now:

- compares complete responses and states;
- creates a fresh target for each selected case;
- passes a deep copy of each request;
- reports `pass`, `fail`, `error`, and `not-run`;
- records observed response and state;
- records exception type and message;
- continues after errors;
- reports counts for all four result states;
- includes target, version, and SHA-256 provenance;
- returns truthful exit codes.

The command-line interface remains unchanged:

```powershell
python -B inputs\harness.py --target inputs\target_a.py --cases inputs\cases.json
python -B inputs\harness.py --target inputs\target_b.py --cases inputs\cases.json
```

## 4. Runner validation

I added runnable meta-tests in `tests\test_harness.py`:

```powershell
python -B -m unittest discover -s tests -v
```

The tests cover:

- an all-pass contract target;
- a known-bad target;
- an always-success response;
- unexpected exceptions;
- continued execution after errors;
- unselected cases;
- state mutation;
- fresh state per case;
- order independence;
- input preservation.

The tests were first run against the original runner. They exposed the
incompatible result behavior and request mutation problem. After the repair, the
same tests passed.

The always-success synthetic target was important because it returned a
non-empty `200` response for every request. The repaired runner correctly
rejected incorrect responses instead of treating them as passes.

## 5. Target A results

I applied the repaired runner to Target A:

```powershell
python -B inputs\harness.py --target inputs\target_a.py --cases inputs\cases.json
```

Target A has these important results:

- `C03` fails because a red session can read the blue report;
- `C07` fails because a denied write changes report state;
- `C09` is an error because the target raises `RuntimeError`;
- `C10` is `not-run` because it is unselected.

The valid controls and expected authentication/error responses pass.

The C03 result confirms a cross-tenant authorization defect. The C07 result
confirms an integrity defect that would have been missed by checking only the
`403` response that i why make a comparison between states in my reppaired runner.

## 6. Target B results

I then applied the identical repaired runner and unchanged cases to Target B:

```powershell
python -B inputs\harness.py --target inputs\target_b.py --cases inputs\cases.json
```


Target B improves the C03 cross-tenant read behavior, but it introduces
regressions:

- `C02` fails because legitimate blue access is denied;
- `C08` fails for the same reason;
- `C07` still fails because denied writes mutate state;
- `C09` remains an error;
- `C10` remains `not-run`.

Therefore, Target B is not a complete or acceptable replacement.

## 7. Final security assessment

The main confirmed findings are:

1. Target A permits cross-tenant report access.
2. Both targets mutate protected state after a denied write.
3. Target B denies legitimate blue-reader access.
4. Both targets fail the injected exception-handling probe.

C09 is a deliberate fault-injection case. It demonstrates unexpected error
handling, but it is not evidence of an authorization vulnerability.

C10 is not evidence of success because it was deliberately unselected.

## 8. Limitations and next steps

This exercise uses a finite, fictional, in-memory model. It does not test a real
HTTP server, browser behavior, database transactions, concurrency, persistence,
deployment configuration, or behavior outside the supplied cases.

The next engineering step is to correct Target B so that it:

- preserves legitimate blue access;
- denies cross-tenant access;
- checks authorization before modifying state;
- handles the injected failure according to the contract.

After those changes, the unchanged cases should be rerun with the repaired runner,
and additional regression cases should be added for each corrected behavior.

## 9. Evidence location

Raw baseline and repaired captures are stored under `evidence/`. The finding
register, decision log, and AI-use note are stored under `docs/`.

The final conclusion is that the repaired harness now provides trustworthy,
reproducible evidence, while neither supplied target should be considered fully
secure.
