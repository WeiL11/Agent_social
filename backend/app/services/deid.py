"""Lightweight regex de-identification. This is the MVP scrubber; production
should layer Microsoft Presidio on top for NER-based PII (names, locations)."""

import re

_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b(?:\+?\d[\d\s-]{7,}\d)\b"), "[PHONE]"),
    (re.compile(r"\b(?:sk-|ghp_|xox[baprs]-)[A-Za-z0-9_-]{8,}\b"), "[SECRET]"),
    (re.compile(r"\b\d{1,5}\s+\w+(?:\s\w+)*\s(?:St|Street|Ave|Avenue|Rd|Road)\b", re.I), "[ADDRESS]"),
]


def scrub(text: str | None) -> str | None:
    if not text:
        return text
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
