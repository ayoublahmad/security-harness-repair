# HC policy (authoritative, fictional)

R1 Target API: `Target()` creates fresh report state; `respond(request)` returns a response; `snapshot()` returns report state. Never modify either target. Compare complete response and state with each case's expected objects using exact JSON structure/types/values (object key order irrelevant). Controls C01/C02 prove legitimate access. An expected object is a contract, not proof it was observed.

R2 Fresh state: instantiate one Target per selected case; copy its request before calling. Never carry state across cases. Preserve suite order and inputs. Results for a given ID must be independent of order.

R3 Four states: selected, normally returned, both objects equal => `pass`; selected, normally returned, either differs => `fail`; any unexpected exception creating/calling/snapshotting => `error` with exception type/message. Continue after errors. An unselected case is `not-run`, with no target call and no observed data; never a pass. C09 is fault injection, not evidence of an authorization vulnerability.

R4 Output JSON: one result per case with ID/result, observed response/state for normal returns, or error details. Include all four counts. Exit 1 if any fail/error; otherwise exit 2 if any not-run; otherwise exit 0. Setup/input errors exit 3, not green. Inputs are well-formed supplied fixtures; no general schema framework required.

R5 Provenance: report actual target filename, VERSION and SHA-256 of target bytes, cases bytes and runner bytes. Preserve original captures and hashes; never relabel A output as B. Rerun after changes. `--target` and `--cases` remain supported; document any added test command.

R6 Target behavior: known sessions may read only their own reports; unknown sessions get 401, missing IDs 404. Denied writes get 403 and leave all state unchanged. Read success returns 200 and stored text. The exception probe expects 400/Unknown but both supplied targets crash. All requests, state and error strings are synthetic; no network or filesystem application behavior is modeled.
