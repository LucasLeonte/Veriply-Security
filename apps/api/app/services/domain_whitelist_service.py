"""Domain whitelist validation and matching helpers for widget security."""

from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import Request

DOMAIN_REGEX = re.compile(r"^(\*\.)?[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$")
LOCALHOST_REGEX = re.compile(r"^(localhost|127\.0\.0\.1)$")
MAX_DOMAINS = 50


def _strip_port(domain: str) -> str:
    if ":" in domain:
        return domain.split(":", 1)[0]
    return domain


def normalize_domain(domain: str) -> str:
    """Normalize a domain string (strip protocol/port, lowercase)."""
    candidate = domain.strip().lower()

    if candidate.startswith("http://") or candidate.startswith("https://"):
        parsed = urlparse(candidate)
        candidate = parsed.netloc or parsed.path
    candidate = candidate.rstrip("/")
    candidate = _strip_port(candidate)
    return candidate


def is_valid_domain(domain: str) -> bool:
    candidate = normalize_domain(domain)
    if not candidate:
        return False
    return bool(DOMAIN_REGEX.match(candidate) or LOCALHOST_REGEX.match(candidate))


def validate_domain_list(domains: List[str]) -> List[str]:
    if len(domains) > MAX_DOMAINS:
        raise ValueError(f"Maximum {MAX_DOMAINS} domains allowed")

    normalized: list[str] = []
    seen: set[str] = set()

    for raw in domains:
        if not isinstance(raw, str):
            raise ValueError("Domain must be a string")

        candidate = normalize_domain(raw)
        if not is_valid_domain(candidate):
            raise ValueError("Invalid domain format")
        if candidate in seen:
            raise ValueError("Domain already in whitelist")

        seen.add(candidate)
        normalized.append(candidate)

    return normalized


def extract_request_origin(request: Request) -> Optional[str]:
    """Extract embedding origin from custom header, Origin, or Referer."""
    header_order = ["x-embed-origin", "origin", "referer"]
    for header_name in header_order:
        raw = request.headers.get(header_name)
        if not raw:
            continue
        candidate = normalize_domain(raw)
        if candidate:
            return candidate
    return None


def matches_whitelist(origin: Optional[str], allowed_domains: List[str]) -> bool:
    """Check whether the given origin matches the whitelist (supports wildcards)."""
    if not allowed_domains:
        return True
    if not origin:
        return False

    domain = normalize_domain(origin)
    for allowed in allowed_domains:
        normalized_allowed = normalize_domain(allowed)
        if normalized_allowed.startswith("*."):
            base = normalized_allowed[2:]
            if domain.endswith(f".{base}"):
                return True
            continue
        if domain == normalized_allowed:
            return True
    return False
