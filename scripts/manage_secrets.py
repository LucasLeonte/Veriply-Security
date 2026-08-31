#!/usr/bin/env python3
"""
Veriply Secrets Management CLI
================================

Usage:
    python scripts/manage_secrets.py generate         # Generate all missing secrets
    python scripts/manage_secrets.py validate         # Validate current .env secrets
    python scripts/manage_secrets.py rotate JWT_SECRET  # Rotate a specific secret
    python scripts/manage_secrets.py audit            # Scan source files for hardcoded secrets

All commands automatically find the project root by walking up from the
script's location until it finds a .env file.
"""
from __future__ import annotations

import argparse
import base64
import math
import os
import re
import secrets as _secrets_stdlib
import sys
from collections import Counter
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"


def _find_project_root() -> Path:
    """Walk up from the script location to find the project root (.env present)."""
    current = Path(__file__).resolve().parent
    for _ in range(6):
        if (current / ".env").exists():
            return current
        current = current.parent
    # Fallback: use cwd
    return Path.cwd()


def _generate_token(length: int = 32) -> str:
    """Generate a URL-safe random token."""
    return _secrets_stdlib.token_urlsafe(length)


def _generate_b64_key(byte_length: int = 32) -> str:
    """Generate a base64-encoded random key."""
    return base64.b64encode(os.urandom(byte_length)).decode()


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _is_placeholder(value: str) -> bool:
    placeholder_patterns = ("CHANGE_ME", "changeme", "your_secret", "replace_me", "TODO")
    lower = value.lower().strip()
    return any(p.lower() in lower for p in placeholder_patterns) or not lower


def _load_env(root: Path) -> dict[str, str]:
    """Parse the .env file into a dict. Does NOT set os.environ."""
    env_file = root / ".env"
    result: dict[str, str] = {}
    if not env_file.exists():
        return result
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # Strip inline comments
        value = value.split(" #")[0].strip().strip('"').strip("'")
        result[key] = value
    return result


# ---------------------------------------------------------------------------
# Secret definitions
# ---------------------------------------------------------------------------

# (env_var, description, generator_fn)
SECRET_SPECS: list[tuple[str, str, callable]] = [
    ("JWT_SECRET",                 "JWT signing secret (min 32 chars)",         lambda: _generate_token(32)),
    ("NEXTAUTH_SECRET",            "NextAuth signing secret (min 32 chars)",     lambda: _generate_token(32)),
    ("REDIS_PASSWORD",             "Redis auth password (min 16 chars)",         lambda: _generate_token(16)),
    ("EMAIL_TOKEN_ENCRYPTION_KEY", "Email OAuth token encryption key (base64)",  lambda: _generate_b64_key(32)),
]

VALIDATION_RULES: list[tuple[str, int, float, bool]] = [
    # (var_name, min_len, min_entropy, required_always)
    ("JWT_SECRET",                 32, 3.5, True),
    ("NEXTAUTH_SECRET",            32, 3.5, True),
    ("REDIS_PASSWORD",             16, 3.0, True),
    ("EMAIL_TOKEN_ENCRYPTION_KEY", 32, 3.5, True),
    ("GOOGLE_CLIENT_SECRET",       20, 3.0, False),
    ("SMTP_PASSWORD",              8,  2.0, False),
]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_generate(args: argparse.Namespace) -> None:
    """Generate all required secrets and print a ready-to-paste .env block."""
    root = _find_project_root()
    current = _load_env(root)

    print(f"\n{BOLD}{CYAN}=== Veriply Secret Generator ==={RESET}\n")
    print("Copy the values below into your .env file.\n")
    print(f"{BOLD}# --- Generated secrets ({len(SECRET_SPECS)}) ---{RESET}")

    for var_name, description, generator in SECRET_SPECS:
        existing = current.get(var_name, "")
        if existing and not _is_placeholder(existing) and not args.force:
            print(f"{GREEN}# {var_name} already set — skipping (use --force to regenerate){RESET}")
            continue
        value = generator()
        print(f"\n# {description}")
        print(f"{BOLD}{var_name}={value}{RESET}")

    print(f"\n{YELLOW}Remember to also set:{RESET}")
    print("  SMTP_USER / SMTP_PASSWORD     (your Gmail address + App Password)")
    print("  GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET  (from Google Cloud Console)")
    print(f"\n{GREEN}After updating .env, run: python scripts/secrets.py validate{RESET}\n")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate current .env secrets against minimum requirements."""
    root = _find_project_root()
    env = _load_env(root)
    is_prod = env.get("ENVIRONMENT", "development").lower() == "production"

    print(f"\n{BOLD}{CYAN}=== Veriply Secret Validator ==={RESET}")
    print(f"Project root: {root}")
    print(f"Environment:  {env.get('ENVIRONMENT', 'development')}\n")

    errors: list[str] = []
    warnings: list[str] = []
    ok_count = 0

    for var_name, min_len, min_entropy, required_always in VALIDATION_RULES:
        is_required = required_always or is_prod
        value = env.get(var_name, "")

        if _is_placeholder(value) or not value:
            if is_required:
                errors.append(f"{var_name}: not set or placeholder. Run `python scripts/secrets.py generate`.")
            else:
                warnings.append(f"{var_name}: not configured (optional in dev, required in prod).")
            continue

        local_errors: list[str] = []
        if len(value) < min_len:
            local_errors.append(f"too short ({len(value)} chars, min {min_len})")
        entropy = _shannon_entropy(value)
        if entropy < min_entropy:
            local_errors.append(f"entropy too low ({entropy:.2f}, min {min_entropy:.1f})")

        if local_errors:
            errors.append(f"{var_name}: " + ", ".join(local_errors))
        else:
            ok_count += 1
            print(f"  {GREEN}OK{RESET}  {var_name} (len={len(value)}, entropy={_shannon_entropy(value):.2f})")

    for w in warnings:
        print(f"  {YELLOW}WARN{RESET} {w}")

    if errors:
        print()
        for e in errors:
            print(f"  {RED}FAIL{RESET} {e}")
        print(f"\n{RED}{BOLD}Validation FAILED — {len(errors)} issue(s) found.{RESET}")
        print(f"Run `python scripts/secrets.py generate` to fix missing secrets.\n")
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}All secrets OK ({ok_count} checked).{RESET}\n")


def cmd_rotate(args: argparse.Namespace) -> None:
    """Regenerate a single named secret."""
    var_name = args.secret_name.upper()

    # Find the spec
    spec = next((s for s in SECRET_SPECS if s[0] == var_name), None)
    if spec is None:
        known = [s[0] for s in SECRET_SPECS]
        print(f"{RED}Unknown secret: {var_name}{RESET}")
        print(f"Rotatable secrets: {', '.join(known)}")
        sys.exit(1)

    _, description, generator = spec
    new_value = generator()

    print(f"\n{BOLD}{CYAN}=== Rotating {var_name} ==={RESET}")
    print(f"Description: {description}\n")
    print(f"{BOLD}New value:{RESET}")
    print(f"  {var_name}={new_value}")
    print(f"\n{YELLOW}Steps:{RESET}")
    print(f"  1. Replace {var_name}=... in your .env with the new value above.")
    print(f"  2. Restart all services (API, workers).")
    print(f"  3. Existing JWTs/sessions will be invalidated — users must log in again.")
    print(f"  4. Update SECRET_LAST_ROTATED_AT={_today_str()} in .env.\n")


def _today_str() -> str:
    return date.today().isoformat()


def cmd_audit(args: argparse.Namespace) -> None:
    """Scan source files for high-entropy strings that may be hardcoded secrets."""
    root = _find_project_root()

    # Extensions to scan; skip known-safe directories
    scan_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".toml"}
    skip_dirs = {
        ".git", "node_modules", ".next", "__pycache__", ".venv", "venv",
        ".env", "dist", "build", "coverage",
    }
    # Patterns that look like real secrets (high entropy, long strings in assignments)
    secret_pattern = re.compile(
        r"""(?:password|secret|token|key|apikey|api_key|auth)\s*[=:]\s*['"]?([A-Za-z0-9+/=_\-]{20,})['"]?""",
        re.IGNORECASE,
    )
    # Minimum entropy to flag
    MIN_ENTROPY = 3.5

    print(f"\n{BOLD}{CYAN}=== Veriply Secret Audit ==={RESET}")
    print(f"Scanning: {root}\n")

    findings: list[tuple[str, int, str, float]] = []

    for path in root.rglob("*"):
        # Skip non-files and excluded dirs
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in skip_dirs):
            continue
        # Only files matching our extension list (but skip .env* files)
        if path.suffix not in scan_extensions:
            continue
        if path.name.startswith(".env"):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for lineno, line in enumerate(content.splitlines(), 1):
            for match in secret_pattern.finditer(line):
                candidate = match.group(1)
                entropy = _shannon_entropy(candidate)
                if entropy >= MIN_ENTROPY:
                    rel = path.relative_to(root)
                    findings.append((str(rel), lineno, candidate[:20] + "...", entropy))

    if not findings:
        print(f"{GREEN}No hardcoded secrets detected.{RESET}\n")
    else:
        print(f"{RED}{BOLD}Potential hardcoded secrets found:{RESET}\n")
        for filepath, lineno, snippet, entropy in findings:
            print(f"  {RED}!{RESET} {filepath}:{lineno}  entropy={entropy:.2f}  value={snippet!r}")
        print(
            f"\n{RED}{BOLD}{len(findings)} potential secret(s) found.{RESET}\n"
            "Review each finding and move any real secrets to .env.\n"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="secrets.py",
        description="Veriply secrets management CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate all required secrets")
    p_gen.add_argument("--force", action="store_true", help="Regenerate even if already set")
    p_gen.set_defaults(func=cmd_generate)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate current .env secrets")
    p_val.set_defaults(func=cmd_validate)

    # rotate
    p_rot = subparsers.add_parser("rotate", help="Rotate a single secret")
    p_rot.add_argument("secret_name", help="Name of the secret to rotate (e.g. JWT_SECRET)")
    p_rot.set_defaults(func=cmd_rotate)

    # audit
    p_aud = subparsers.add_parser("audit", help="Scan source files for hardcoded secrets")
    p_aud.set_defaults(func=cmd_audit)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
