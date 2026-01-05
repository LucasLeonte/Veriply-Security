"""Add missing columns to confidence_logs table and create indexes."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
print('Connecting to database...')

conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

# Add missing columns
columns_to_add = [
    ('user_id', 'UUID REFERENCES users(id)'),
    ('hitl_resolved', 'BOOLEAN DEFAULT FALSE'),
    ('resolution_user_id', 'UUID REFERENCES users(id)'),
    ('resolution_timestamp', 'TIMESTAMP WITH TIME ZONE'),
    ('metadata', 'JSONB'),
]

for col_name, col_type in columns_to_add:
    try:
        cur.execute(f'ALTER TABLE confidence_logs ADD COLUMN {col_name} {col_type};')
        print(f'Added column: {col_name}')
    except Exception as e:
        if 'already exists' in str(e):
            print(f'Column {col_name} already exists')
        else:
            print(f'Error adding {col_name}: {e}')

# Create all indexes
print('Creating indexes...')
cur.execute('CREATE INDEX IF NOT EXISTS ix_confidence_logs_tenant_id ON confidence_logs(tenant_id);')
cur.execute('CREATE INDEX IF NOT EXISTS ix_confidence_logs_bot_id ON confidence_logs(bot_id);')
cur.execute('CREATE INDEX IF NOT EXISTS ix_confidence_logs_query_id ON confidence_logs(query_id);')
cur.execute('CREATE INDEX IF NOT EXISTS ix_confidence_logs_routing ON confidence_logs(routing_decision);')

# Check if hitl_resolved column exists now
cur.execute("""
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'confidence_logs' AND column_name = 'hitl_resolved';
""")
if cur.fetchone():
    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_confidence_logs_hitl_pending 
    ON confidence_logs(routing_decision, hitl_resolved) 
    WHERE routing_decision = 'HITL' AND hitl_resolved = FALSE;
    """)
    print('Created HITL pending index')

# Show final schema
cur.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'confidence_logs' 
ORDER BY ordinal_position;
""")
print('Final confidence_logs schema:')
for col in cur.fetchall():
    print(f'  {col[0]}: {col[1]}')

# Show indexes
cur.execute("""
SELECT indexname FROM pg_indexes WHERE tablename = 'confidence_logs';
""")
print('Indexes:')
for idx in cur.fetchall():
    print(f'  {idx[0]}')

cur.close()
conn.close()
print('DONE')
