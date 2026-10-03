# Validation record

Scope: Mutable FROM references, remote ADD and missing non-root final USER.

Local checks to rerun:

```sh
python -m unittest discover -s tests -v
python cli.py --help
python -m compileall -q review.py cli.py tests
```

Check the exact public GitHub commit and its workflow run separately after publishing. Tests use synthetic input; no production system or external target is exercised. This is a line-oriented Dockerfile review; ARG expansion, build graph behavior, image contents and runtime privileges are not resolved.

## Current source result (2026-10-02)

- Python 3.14.6: 8/8 unit and CLI integration tests passed.
- Tests include the specific malformed-input, incomplete-review and declaration cases added during the source audit.
- Stage aliases inherit known USER declarations. UID 0 remains root regardless of its group. Valid SHA-256 image digests are distinguished from malformed pins. Escape directives and common heredoc bodies are parsed without executing them; build variables and ONBUILD behavior remain review prompts.
- Test input is synthetic. No external target, live credential or production cluster is exercised.
- The public commit and its corresponding GitHub workflow must be verified separately after this update.
