"""Review a local Dockerfile's final stage and image source declarations."""

from __future__ import annotations
import re


def _instructions(text: str):
    pending = ""
    start = 0
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not pending:
            start = number
        pending += (" " if pending else "") + line.rstrip("\\").rstrip()
        if line.endswith("\\"):
            continue
        parts = pending.split(None, 1)
        if len(parts) == 2:
            yield start, parts[0].upper(), parts[1]
        pending = ""
    if pending:
        raise ValueError("unfinished continuation line")


def review_text(text: str) -> list[dict[str, str]]:
    findings = []
    stages = 0
    final_user = None
    for line, command, value in _instructions(text):
        where = f"line {line}"
        if command == "FROM":
            stages += 1
            final_user = None
            pieces = value.split()
            image = next((part for part in pieces if not part.startswith("--")), "")
            if not image:
                raise ValueError("FROM lacks an image")
            if image != "scratch" and "@sha256:" not in image:
                findings.append({"rule": "mutable-base", "location": where, "note": "Base image is not pinned by digest"})
        elif command == "USER":
            final_user = value.split()[0].lower()
        elif command == "ADD" and re.search(r"\bhttps?://", value, re.IGNORECASE):
            findings.append({"rule": "remote-add", "location": where, "note": "Remote ADD source needs supply-chain review"})
    if stages == 0:
        raise ValueError("no FROM instruction found")
    if final_user in (None, "root", "0", "0:0"):
        findings.append({"rule": "final-root-user", "location": "final stage", "note": "Final stage does not select a non-root user"})
    return findings
