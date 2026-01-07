from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class EmailSample:
    subject: str
    body: str
    sender: Optional[str] = None
    folder: Optional[str] = None  # e.g., "INBOX", "Support"
    labels: Optional[List[str]] = None  # Gmail-style labels


def _normalize(s: Optional[str]) -> str:
    return (s or "").lower()


def _matches_keywords(text: str, keywords: Optional[List[str]]) -> bool:
    if not keywords:
        return True
    t = text.lower()
    for kw in keywords:
        if kw and kw.lower() in t:
            return True
    return False


def _excludes_keywords(text: str, keywords: Optional[List[str]]) -> bool:
    if not keywords:
        return False
    t = text.lower()
    for kw in keywords:
        if kw and kw.lower() in t:
            return True
    return False


def _folder_or_label_match(sample: EmailSample, rule_folders: Optional[List[str]]) -> bool:
    if not rule_folders:
        return True

    target = set([_normalize(sample.folder)]) if sample.folder else set()
    if sample.labels:
        target.update([_normalize(l) for l in sample.labels])

    normalized_rules = set([_normalize(f) for f in rule_folders])
    return len(target.intersection(normalized_rules)) > 0


def match_email_to_rules(email: EmailSample, rules: List[Dict[str, Any]]):
    """
    Evaluate rules in ascending priority (lower number is higher priority).
    Each rule is a dict containing keys: folder_labels, include_keywords, exclude_keywords, priority, is_active
    Returns first matching rule dict or None.
    """
    # Sort by priority ascending
    ordered = sorted([r for r in rules if r.get("is_active", True)], key=lambda r: r.get("priority", 100))

    combined_text = f"{email.subject}\n{email.body}".lower()

    for rule in ordered:
        if not _folder_or_label_match(email, rule.get("folder_labels")):
            continue
        if not _matches_keywords(combined_text, rule.get("include_keywords")):
            continue
        if _excludes_keywords(combined_text, rule.get("exclude_keywords")):
            continue
        return rule

    return None
