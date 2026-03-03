import re

PROFANITY_WORDS = {"idiot", "stupid", "moron", "slurword"}
DOXXING_PATTERNS = [
    re.compile(r"\b\+?\d{1,2}[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    re.compile(r"\b\d{1,5}\s+[A-Za-z0-9\s]+\s(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr)\b", re.IGNORECASE),
]


def contains_profanity(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in PROFANITY_WORDS)


def contains_doxxing(text: str) -> bool:
    return any(pattern.search(text) for pattern in DOXXING_PATTERNS)
