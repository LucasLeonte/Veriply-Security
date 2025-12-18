"""Quick fix for confidence_logs table - add missing columns."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')

conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

# Add missing columns quickly
sqls = [
    "ALTER TABLE confidence_logs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);",
    "ALTER TABLE confidence_logs ADD COLUMN IF NOT EXISTS hitl_resolved BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE confidence_logs ADD COLUMN IF NOT EXISTS resolution_user_id UUID REFERENCES users(id);",
    "ALTER TABLE confidence_logs ADD COLUMN IF NOT EXISTS resolution_timestamp TIMESTAMP WITH TIME ZONE;",
    "ALTER TABLE confidence_logs ADD COLUMN IF NOT EXISTS metadata JSONB;",
    "CREATE INDEX IF NOT EXISTS ix_confidence_logs_tenant_id ON confidence_logs(tenant_id);",
    "CREATE INDEX IF NOT EXISTS ix_confidence_logs_bot_id ON confidence_logs(bot_id);",
    "CREATE INDEX IF NOT EXISTS ix_confidence_logs_query_id ON confidence_logs(query_id);",
    "CREATE INDEX IF NOT EXISTS ix_confidence_logs_routing ON confidence_logs(routing_decision);",
]

for sql in sqls:
    try:
        cur.execute(sql)
        print(f"✓ {sql[:60]}")
    except Exception as e:
        print(f"✗ {sql[:60]} - {e}")

# HITL index (may fail if column doesn't exist yet)
try:
    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_confidence_logs_hitl_pending 
    ON confidence_logs(routing_decision, hitl_resolved) 
    WHERE routing_decision = 'HITL' AND hitl_resolved = FALSE;
    """)
    print("✓ HITL pending index created")
except Exception as e:
    print(f"✗ HITL index: {e}")

print("\n✅ Done!")
cur.close()
conn.close()
