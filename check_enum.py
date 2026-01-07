#!/usr/bin/env python3
"""Check if routingdecision enum exists in the database."""

import os
import sys

# Load from .env file
import re
env_vars = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()

# Database connection parameters
DB_HOST = env_vars.get("DB_HOST", os.getenv("DB_HOST", "localhost"))
DB_PORT = int(env_vars.get("DB_PORT", os.getenv("DB_PORT", "5432")))
DB_NAME = env_vars.get("DB_NAME", os.getenv("DB_NAME", "veriply"))
DB_USER = env_vars.get("DB_USER", os.getenv("DB_USER", "postgres"))
DB_PASSWORD = env_vars.get("DB_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Check if routingdecision enum exists
    cur.execute("""
        SELECT exists (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'confidence_logs'
        ) as confidence_logs_exists;
    """)
    result = cur.fetchone()
    print(f"✓ confidence_logs table exists: {result['confidence_logs_exists']}")
    
    # Check for enum type
    cur.execute("""
        SELECT exists (
            SELECT 1 FROM pg_type 
            WHERE typname = 'routingdecision'
        ) as enum_exists;
    """)
    result = cur.fetchone()
    print(f"✓ routingdecision enum exists: {result['enum_exists']}")
    
    if result['enum_exists']:
        # Show enum values
        cur.execute("""
            SELECT enumlabel FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'routingdecision')
            ORDER BY enumsortorder;
        """)
        values = cur.fetchall()
        print(f"  Enum values: {[v['enumlabel'] for v in values]}")
    else:
        print("\n⚠️  routingdecision enum NOT found! Creating it now...")
        cur.execute("""
            CREATE TYPE routingdecision AS ENUM ('auto_send', 'hitl');
        """)
        conn.commit()
        print("✓ Created routingdecision enum")
    
    cur.close()
    conn.close()
    print("\n✅ Enum check complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
