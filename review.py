"""Review Dockerfile image sources and final-stage user declarations."""
from __future__ import annotations
import re

DIGEST = re.compile(r"@sha256:[0-9a-fA-F]{64}$")
HEREDOC = re.compile(r"(?<!<)<<(-?)(?:['\"]([^'\"\s]+)['\"]|([^\s<>'\"]+))")
COMMANDS = set("ADD ARG CMD COPY ENTRYPOINT ENV EXPOSE FROM HEALTHCHECK LABEL MAINTAINER ONBUILD RUN SHELL STOPSIGNAL USER VOLUME WORKDIR".split())


def _outside_quotes(value, offset):
    quote = None
    escaped = False
    for character in value[:offset]:
        if escaped:
            escaped = False
        elif character == "\\" and quote != "'":
            escaped = True
        elif character in ("'", '"'):
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
    return quote is None


def _instructions(text):
    pending = ""
    start = 0
    escape = "\\"
    directive_area = True
    heredocs = []
    for number, raw in enumerate(text.splitlines(), 1):
        if heredocs:
            delimiter, strip_tabs = heredocs[0]
            if (raw.lstrip("\t") if strip_tabs else raw) == delimiter:
                heredocs.pop(0)
            continue
        line = raw.strip()
        if directive_area and line.startswith("#"):
            match = re.fullmatch(r"#\s*escape\s*=\s*([\\`])", line, re.I)
            if match:
                escape = match.group(1)
                continue
            if re.match(r"#\s*(syntax|check)\s*=", line, re.I):
                continue
        if not line or line.startswith("#"):
            directive_area = False
            continue
        directive_area = False
        if not pending:
            start = number
        continued = line.endswith(escape)
        pending += (" " if pending else "") + (line[:-1].rstrip() if continued else line)
        if continued:
            continue
        parts = pending.split(None, 1)
        pending = ""
        if len(parts) != 2 or parts[0].upper() not in COMMANDS:
            raise ValueError(f"unsupported or incomplete Dockerfile instruction on line {start}")
        command, value = parts[0].upper(), parts[1]
        if command in ("RUN", "COPY", "ADD") and not value.startswith("["):
            heredocs = [(match.group(2) or match.group(3), bool(match.group(1))) for match in HEREDOC.finditer(value) if _outside_quotes(value, match.start())]
        yield start, command, value
    if pending or heredocs:
        raise ValueError("unfinished continuation or heredoc")


def review_text(text: str) -> list[dict[str, str]]:
    findings = []
    stages = []
    aliases = {}
    final_user = None
    for line, command, value in _instructions(text):
        where = f"line {line}"
        if command == "FROM":
            pieces = value.split()
            while pieces and pieces[0].startswith("--"):
                if not pieces[0].startswith("--platform="):
                    raise ValueError("unsupported FROM option")
                pieces.pop(0)
            if len(pieces) not in (1, 3) or len(pieces) == 3 and pieces[1].upper() != "AS":
                raise ValueError("invalid FROM declaration")
            image = pieces[0]
            previous = aliases.get(image.lower())
            final_user = stages[previous]["user"] if previous is not None else None
            if previous is None and image != "scratch" and not DIGEST.search(image):
                findings.append({"rule": "mutable-base", "location": where, "note": "External base image lacks a valid SHA-256 digest pin"})
            stages.append({"user": final_user})
            if len(pieces) == 3:
                alias = pieces[2].lower()
                if alias in aliases:
                    raise ValueError("duplicate stage alias")
                aliases[alias] = len(stages) - 1
        elif command == "USER":
            if not stages or len(value.split()) != 1:
                raise ValueError("invalid USER declaration")
            final_user = value
            stages[-1]["user"] = value
        elif not stages and command != "ARG":
            raise ValueError("only ARG may precede the first FROM")
        elif command == "ADD" and re.search(r"(?:https?://|git@|git://|ssh://)", value, re.I):
            findings.append({"rule": "remote-add", "location": where, "note": "Remote ADD source needs supply-chain review"})
        elif command == "ONBUILD":
            findings.append({"rule": "deferred-instruction", "location": where, "note": "ONBUILD behavior needs a downstream build review"})
    if not stages:
        raise ValueError("no FROM instruction found")
    if final_user is None:
        findings.append({"rule": "final-root-user", "location": "final stage", "note": "No explicit non-root user is known for the final stage"})
    elif "$" in final_user:
        findings.append({"rule": "unresolved-user", "location": "final stage", "note": "Final user depends on unresolved build variables"})
    else:
        user = final_user.split(":", 1)[0]
        if user == "root" or user.isdigit() and not user.strip("0"):
            findings.append({"rule": "final-root-user", "location": "final stage", "note": "Final stage explicitly selects root or UID 0"})
    return findings
