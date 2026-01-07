import os
import sys
import psycopg2

# Ensure 'app' package is importable when running as a script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.settings import settings

statements = [
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS is_paused boolean NOT NULL DEFAULT false;",
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS last_poll_at timestamp NULL;",
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS last_success_at timestamp NULL;",
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS last_error_at timestamp NULL;",
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS last_error_message text NULL;",
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS next_poll_at timestamp NULL;",
    "ALTER TABLE email_integrations ADD COLUMN IF NOT EXISTS error_count integer NOT NULL DEFAULT 0;",
    # Remove defaults so application-level defaults apply
    "ALTER TABLE email_integrations ALTER COLUMN is_paused DROP DEFAULT;",
    "ALTER TABLE email_integrations ALTER COLUMN error_count DROP DEFAULT;",
]

print("Connecting to DB...")
conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
cur = conn.cursor()
for stmt in statements:
    try:
        print("Executing:", stmt)
        cur.execute(stmt)
    except Exception as e:
        print("WARN:", e)
conn.commit()
cur.close()
conn.close()
print("Done.")
