#!/usr/bin/env python3
"""
Migration: Add security fields to audit_logs table
====================================================

Adds new columns to support structured security event logging:
    - event_type    VARCHAR      SecurityEvent enum value
    - severity      VARCHAR      DEBUG / INFO / WARNING / CRITICAL
    - outcome       VARCHAR      SUCCESS / FAILURE / BLOCKED
    - ip_address    VARCHAR(45)  Client IPv4 or IPv6
    - user_agent    VARCHAR(512) Browser / client UA string
    - http_method   VARCHAR(10)  GET, POST, etc.
    - http_path     VARCHAR(512) Request URL path
    - http_status   INTEGER      HTTP response status code
    - request_id    VARCHAR(36)  Per-request correlation UUID

Also:
    - Makes tenant_id and actor_id NULLABLE (unauthenticated events
      have no associated user/tenant)

Run from the apps/api directory:
    python migrate_add_security_fields.py
"""
import asyncio
import sys
from pathlib import Path

# Allow importing app modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text
from app.core.database import engine


ADD_COLUMNS_SQL = """
-- Make existing NOT NULL FKs nullable (for unauthenticated events)
ALTER TABLE audit_logs
    ALTER COLUMN tenant_id DROP NOT NULL,
    ALTER COLUMN actor_id  DROP NOT NULL;

-- Remove legacy target_user_id if it exists (superseded by actor_id + event_type)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'audit_logs' AND column_name = 'target_user_id'
    ) THEN
        ALTER TABLE audit_logs DROP COLUMN target_user_id;
    END IF;
END $$;

-- Add new security event columns (idempotent: skip if already present)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'event_type') THEN
        ALTER TABLE audit_logs ADD COLUMN event_type   VARCHAR;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'severity') THEN
        ALTER TABLE audit_logs ADD COLUMN severity     VARCHAR;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'outcome') THEN
        ALTER TABLE audit_logs ADD COLUMN outcome      VARCHAR;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'ip_address') THEN
        ALTER TABLE audit_logs ADD COLUMN ip_address   VARCHAR(45);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'user_agent') THEN
        ALTER TABLE audit_logs ADD COLUMN user_agent   VARCHAR(512);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'http_method') THEN
        ALTER TABLE audit_logs ADD COLUMN http_method  VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'http_path') THEN
        ALTER TABLE audit_logs ADD COLUMN http_path    VARCHAR(512);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'http_status') THEN
        ALTER TABLE audit_logs ADD COLUMN http_status  INTEGER;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'request_id') THEN
        ALTER TABLE audit_logs ADD COLUMN request_id   VARCHAR(36);
    END IF;
END $$;

-- Performance index: look up events by IP (brute-force queries)
CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address   ON audit_logs(ip_address);
-- Performance index: filter by event type
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type   ON audit_logs(event_type);
-- Performance index: filter by severity
CREATE INDEX IF NOT EXISTS idx_audit_logs_severity     ON audit_logs(severity);
-- Performance index: tenant-scoped admin queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id    ON audit_logs(tenant_id);
-- Performance index: chronological queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at   ON audit_logs(created_at DESC);
"""


async def run_migration() -> None:
    print("Running migration: add security fields to audit_logs ...")
    async with engine.begin() as conn:
        await conn.execute(text(ADD_COLUMNS_SQL))
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(run_migration())
