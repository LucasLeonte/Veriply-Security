"""
Secrets Management Utilities
============================

Provides:
- ``SecretValue``: A string wrapper that redacts its value in ``repr()``, logs,
  and Sentry events, preventing accidental credential leakage.
- ``validate_secrets()``: Startup validator that asserts all required secrets
  meet minimum-length and minimum-entropy requirements.
- ``get_secret_age_days()``: Optional helper that reads ``SECRET_LAST_ROTATED_AT``
  and warns if secrets are overdue for rotation (> 90 days).

Usage::

    from app.core.secrets import SecretValue, validate_secrets

    # In settings.py:
    JWT_SECRET: SecretValue = SecretValue("")

    # On startup:
    validate_secrets(settings)
"""

from __future__ import annotations

import math
import logging
import os
from collections import Counter
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SecretValue — opaque string wrapper
# ---------------------------------------------------------------------------

class SecretValue(str):
    """
    An opaque string subclass for secret values.

    - ``repr()`` and ``str()`` both return ``"**REDACTED**"`` so that
      accidental printing, logging, or Sentry capture never exposes the value.
    - The real value is still accessible via ``get_secret_value()``.
    - Compatible with Pydantic ``BaseSettings`` (it is a plain ``str``
      subclass, so no custom validator is needed).

    Examples::

        s = SecretValue("my-super-secret")
        print(s)           # **REDACTED**
        repr(s)            # "SecretValue(**REDACTED**)"
        s.get_secret_value()  # "my-super-secret"
        len(s)             # 15  (len still works on the real value)
    """

    def __repr__(self) -> str:
        return "SecretValue(**REDACTED**)"

    def __str__(self) -> str:
        return "**REDACTED**"

    def get_secret_value(self) -> str:
        """Return the actual secret string."""
        return str.__str__(self)

    def __bool__(self) -> bool:
        return bool(str.__str__(self))

    def __len__(self) -> int:
        return str.__len__(self)


# ---------------------------------------------------------------------------
# Entropy helper
# ---------------------------------------------------------------------------

def _shannon_entropy(value: str) -> float:
    """Calculate Shannon entropy (bits per character) of *value*."""
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _is_placeholder(value: str) -> bool:
    """Return True if the value looks like an unfilled placeholder."""
    placeholder_patterns = (
        "CHANGE_ME",
        "changeme",
        "your_secret_here",
        "replace_me",
        "TODO",
        "FIXME",
        "",
    )
    lower = value.lower().strip()
    return any(p.lower() in lower for p in placeholder_patterns) or not lower


# ---------------------------------------------------------------------------
# Secret requirements registry
# ---------------------------------------------------------------------------

# Each entry: (env_var_name, min_length, min_entropy, required_in_prod)
_SECRET_REQUIREMENTS: list[tuple[str, int, float, bool]] = [
    ("JWT_SECRET",                 32, 3.5, True),
    ("NEXTAUTH_SECRET",            32, 3.5, True),
    ("REDIS_PASSWORD",             16, 3.0, True),
    ("EMAIL_TOKEN_ENCRYPTION_KEY", 32, 3.5, True),
    ("GOOGLE_CLIENT_SECRET",       20, 3.0, False),  # optional in dev
    ("SMTP_PASSWORD",              8,  2.0, False),   # optional in dev
]


# ---------------------------------------------------------------------------
# validate_secrets()
# ---------------------------------------------------------------------------

def validate_secrets(settings: Any, *, strict: bool | None = None) -> None:
    """
    Validate all required secrets against minimum length and entropy.

    Args:
        settings: The ``Settings`` instance (``app.core.settings.settings``).
        strict:   If ``True``, treat optional-in-dev secrets as required too.
                  Defaults to ``True`` when ``ENVIRONMENT=production``.

    Raises:
        ValueError: If one or more required secrets are missing or too weak.
    """
    is_prod = getattr(settings, "is_production", False)
    if strict is None:
        strict = is_prod

    errors: list[str] = []

    for var_name, min_len, min_entropy, required_in_prod in _SECRET_REQUIREMENTS:
        is_required = required_in_prod or strict
        raw_value: str = str.__str__(getattr(settings, var_name, "") or "")

        if _is_placeholder(raw_value):
            if is_required:
                errors.append(
                    f"  * {var_name}: not set or still a placeholder. "
                    f"Run `python scripts/secrets.py generate` to create it."
                )
            else:
                logger.warning(
                    "[secrets] %s is not configured -- optional in dev but required in production.",
                    var_name,
                )
            continue

        if len(raw_value) < min_len:
            errors.append(
                f"  * {var_name}: too short ({len(raw_value)} chars, minimum {min_len}). "
                "Use a longer, randomly generated value."
            )

        entropy = _shannon_entropy(raw_value)
        if entropy < min_entropy:
            errors.append(
                f"  * {var_name}: entropy too low ({entropy:.2f} bits/char, minimum {min_entropy:.1f}). "
                "Use a randomly generated value -- avoid dictionary words or repeated patterns."
            )

    if errors:
        bullet_list = "\n".join(errors)
        raise ValueError(
            f"\n\n{'=' * 70}\n"
            f"STARTUP FAILED -- Secret configuration errors:\n"
            f"{bullet_list}\n\n"
            f"Fix these issues in your .env file and restart.\n"
            f"Quick fix: python scripts/secrets.py generate\n"
            f"{'=' * 70}\n"
        )

    logger.info("[secrets] All required secrets validated successfully.")


# ---------------------------------------------------------------------------
# get_secret_age_days()  -- optional rotation reminder
# ---------------------------------------------------------------------------

def get_secret_age_days() -> int | None:
    """
    Return the age (in days) of secrets since their last rotation, or ``None``
    if ``SECRET_LAST_ROTATED_AT`` is not set.

    Set ``SECRET_LAST_ROTATED_AT=YYYY-MM-DD`` in your ``.env`` to enable
    rotation age tracking.
    """
    raw = os.environ.get("SECRET_LAST_ROTATED_AT", "").strip()
    if not raw:
        return None
    try:
        rotated_at = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        delta = datetime.now(tz=timezone.utc) - rotated_at
        return delta.days
    except ValueError:
        logger.warning(
            "[secrets] SECRET_LAST_ROTATED_AT has invalid format '%s'. "
            "Expected YYYY-MM-DD.",
            raw,
        )
        return None


def warn_if_rotation_overdue(rotation_reminder_days: int = 90) -> None:
    """Log a warning if secrets are overdue for rotation."""
    age = get_secret_age_days()
    if age is None:
        logger.info(
            "[secrets] Secret rotation age unknown. "
            "Set SECRET_LAST_ROTATED_AT=YYYY-MM-DD in .env to track rotation."
        )
        return
    if age > rotation_reminder_days:
        logger.warning(
            "[secrets] Secrets were last rotated %d days ago "
            "(recommended maximum: %d days). "
            "Run `python scripts/secrets.py rotate` for each secret.",
            age,
            rotation_reminder_days,
        )
    else:
        logger.info("[secrets] Secret rotation is current (%d days old).", age)
