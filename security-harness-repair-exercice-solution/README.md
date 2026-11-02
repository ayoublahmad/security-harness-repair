# Repair an unreliable security regression harness

The fictional HeatherCheck team reports green security checks, while a teammate still observes forbidden report access. Repair the evidence workflow so it can distinguish a target defect from a runner defect. Both targets are **deliberately vulnerable training models**, entirely in memory; no server or network. Preserve their code and the original evidence. All facts are fictional.

## Inputs and setup

- [Runner](inputs/harness.py): deliberately unreliable starter; repair this file or provide a compatible replacement.
- [Target A](inputs/target_a.py): original implementation.
- [Target B](inputs/target_b.py): proposed replacement, not an approved fix.
- [Cases](inputs/cases.json): eight contract probes and two legitimate controls, with selection flags and complete expected objects.
- [Policy](inputs/harness-policy.md): authoritative R1–R6, four result states, API, exit and provenance contracts.

Baseline skills: short Python scripts, assertions, request/response, authorization and mutable state. Python 3.10+ standard library only; no installation. From exported `candidate/` run:

```sh
python3 -B inputs/harness.py --target inputs/target_a.py --cases inputs/cases.json
python3 -B inputs/harness.py --target inputs/target_b.py --cases inputs/cases.json
```

The starter prints 10 pass results and exits 0 for each target. These are symptoms to investigate, not a trustworthy security result.

## Core work

1. Capture both starter runs, exit statuses and source hashes. Explain misleading results with case IDs, policy clauses and code locations; distinguish runner defects, target failures and fault injection.
2. Build a reusable repaired runner implementing R1–R5: exact response/state assertions, isolated state, four result states, continued execution, truthful exit status and provenance. Keep `--target`/`--cases`; do not edit target behavior or expected objects to obtain green.
3. Add runnable meta-tests demonstrating an all-pass contract target, a known-bad target, unexpected exceptions and unselected cases. Show each runner defect rejected before repair and checked afterward; verify order independence and input preservation. An always-success response must not fool your tests.
4. Apply the same repaired runner and cases unchanged to B. Reconcile fixed, newly failing and remaining failures against A; record any runner refinement and rerun A. Keep original and repaired captures separate.
5. Provide a concise evidence handoff and reusable workflow checklist: exact commands, failure interpretation, what remains untested, and the next verification step. Include the log, AI-use note and walkthrough below.

Acceptance: one command per target reproduces observed values, counts, provenance and exits; every case has a result. A selected crash is not a pass; an unselected case remains unknown. A passing finite suite proves only its documented cases. Repairing this harness does not repair either target. No external actions or real application assessment.

## Submission, AI and timing

Submit an archive or repository containing runnable artifacts, source/evidence references, captured verification output and a concise walkthrough (up to five minutes recording **or equivalent accessible text**). Include exact commands and tool versions. Add a short decision/work log recording prioritization, one obstacle and response, one validation/refinement, limits and next step. Add an AI-use note with one accepted, corrected or rejected output and how you checked it; if no AI was used, say so. Never fabricate an AI failure.

No AI tool is provided: you may use any AI tool you already have. AI is allowed and encouraged for coding, drafting, research, automation and critique. Verify AI output. Tool choice is not graded; free/offline tools are supported, no purchases or personal account access are needed. Synthetic fixtures are the authoritative universe; outside research is optional and cannot affect marks.

Your 24 hours start when you click **Start** on the link in your invitation email; the exercise zip becomes available at that moment. Send your submission back within 24 hours of clicking Start. You are not expected to work for the full 24 hours: organize your own working time and breaks within the window. There are no surprise messages or overnight availability requirements, and hours worked are not scored. The clock tests bounded execution, follow-through and verification, not willingness to sacrifice sleep. Do only this assigned exercise. Full marks are possible on core alone: usable result **40**, accuracy/verification **25**, prioritization **20**, communication/handoff **15**. No AI-detector, writing-volume or prose-polish scoring. Work is an exercise submission, not a company deliverable: no external targets, outreach, production actions or public deployment.
