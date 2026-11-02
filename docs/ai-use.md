# AI Use Note

Github copiot was used to explain the exercise policy, help me identify weaknesses in the
starter runner, propose fixes to repaire the runner, and suggest meta-test
scenarios but with the verification of it's output, also i used it in the redaction and the documentation of the handoff .

One AI-suggested meta-test initially expected the mutation target's observed state
to contain only the changed `r-blue` key. I corrected this after running the test:
the target state correctly contained both `r-red` and the modified `r-blue` key.
The test expectation was updated to match the actual `snapshot()` output.

I independently checked the result by running:

```powershell
python -B -m unittest discover -s tests -v