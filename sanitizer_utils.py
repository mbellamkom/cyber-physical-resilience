import re

# V-05: Robust regex patterns for normalization
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"system\s+prompt",
    r"you\s+are\s+(now\s+)?(no\s+longer|an?\s+)(ai|assistant|large language model)",
    r"developer\s+mode",
    r"bypass\s+(all\s+)?restrictions?",
    r"disregard\s+(all\s+)?previous",
    r"new\s+instructions?\s*:",
    r"<\s*/?system\s*>",   # XML/tag-based injection attempts
]

# Pre-compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(p) for p in SUSPICIOUS_PATTERNS]

def normalize_text(text):
    """V-05: Standardize whitespace and casing for reliable scanning."""
    if not text: return ""
    return re.sub(r'\s+', ' ', text.lower()).strip()

def scan_text(text: str) -> tuple[bool, str]:
    """Scans raw text against suspicious patterns. Returns (is_safe, trigger_pattern)."""
    if not text:
        return True, None

    content = normalize_text(text)
    for pattern in COMPILED_PATTERNS:
        if pattern.search(content):
            return False, pattern.pattern
    return True, None
