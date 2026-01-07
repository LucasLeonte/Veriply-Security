"""
Database Connection Pool Diagnostic and Fix Script

This script helps diagnose and fix the "too many connections" error.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.core.settings import settings
from sqlalchemy import create_engine, text


async def check_connections():
    """Check current PostgreSQL connections."""
    # Use sync engine for this diagnostic
    sync_url = settings.DATABASE_URL_SYNC
    engine = create_engine(sync_url, pool_pre_ping=True)
    
    print("=" * 70)
    print("DATABASE CONNECTION DIAGNOSTICS")
    print("=" * 70)
    print(f"\nDatabase: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"User: {settings.DB_USER}")
    
    try:
        with engine.connect() as conn:
            # Get max connections
            result = conn.execute(text("SHOW max_connections;"))
            max_conn = result.scalar()
            print(f"\nPostgreSQL max_connections: {max_conn}")
            
            # Get current connections
            result = conn.execute(text("""
                SELECT 
                    count(*) as total,
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) FILTER (WHERE state = 'idle') as idle,
                    count(*) FILTER (WHERE application_name LIKE '%veriply%' OR application_name LIKE '%python%') as app_connections
                FROM pg_stat_activity
                WHERE datname = current_database();
            """))
            row = result.fetchone()
            
            print(f"\nCurrent Connections:")
            print(f"  Total: {row[0]}/{max_conn}")
            print(f"  Active: {row[1]}")
            print(f"  Idle: {row[2]}")
            print(f"  From this app: {row[3]}")
            
            # Show connections by application
            result = conn.execute(text("""
                SELECT 
                    application_name,
                    state,
                    count(*) as count
                FROM pg_stat_activity
                WHERE datname = current_database()
                GROUP BY application_name, state
                ORDER BY count DESC
                LIMIT 10;
            """))
            
            print(f"\nConnections by Application:")
            for row in result:
                print(f"  {row[0] or '(unknown)'} - {row[1]}: {row[2]}")
            
            # Calculate recommended pool size
            print(f"\n" + "=" * 70)
            print("CURRENT CONFIGURATION:")
            print("=" * 70)
            print(f"DB_POOL_SIZE: {settings.DB_POOL_SIZE}")
            print(f"DB_MAX_OVERFLOW: {settings.DB_MAX_OVERFLOW}")
            print(f"Total per process: {settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW}")
            
            print(f"\n" + "=" * 70)
            print("RECOMMENDATIONS:")
            print("=" * 70)
            
            if int(max_conn) < 100:
                print(f"⚠️  Your PostgreSQL max_connections ({max_conn}) is LOW")
                print(f"   Consider increasing it in postgresql.conf")
                print(f"   Recommended: max_connections = 100 or more")
            
            print(f"\n✓ Safer connection pool settings for your .env:")
            print(f"  DB_POOL_SIZE=5")
            print(f"  DB_MAX_OVERFLOW=10")
            print(f"  (Total: 15 connections per API process)")
            
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        print(f"\nPossible causes:")
        print(f"  1. Database is full (too many connections)")
        print(f"  2. Database is down")
        print(f"  3. Network issue")
        print(f"  4. Wrong credentials")
        
        return False
    finally:
        engine.dispose()
    
    return True


def show_cleanup_commands():
    """Show commands to clean up connections."""
    print(f"\n" + "=" * 70)
    print("CLEANUP OPTIONS:")
    print("=" * 70)
    print(f"\n1. Restart PostgreSQL (clears all connections):")
    print(f"   On Ubuntu/Linux:")
    print(f"   sudo systemctl restart postgresql")
    print(f"\n2. Kill idle connections (SQL command):")
    print(f"   SELECT pg_terminate_backend(pid)")
    print(f"   FROM pg_stat_activity")
    print(f"   WHERE datname = '{settings.DB_NAME}'")
    print(f"     AND state = 'idle'")
    print(f"     AND pid != pg_backend_pid();")
    print(f"\n3. Stop any running API processes:")
    print(f"   Check for multiple 'uvicorn' or 'python' processes")
    print(f"   On Windows: tasklist | findstr python")
    print(f"   Kill with: taskkill /F /PID <process_id>")


if __name__ == "__main__":
    print("\nChecking database connections...\n")
    
    try:
        result = asyncio.run(check_connections())
        show_cleanup_commands()
        
        if result:
            print(f"\n" + "=" * 70)
            print(f"✓ Successfully connected to database")
            print(f"=" * 70)
        else:
            print(f"\n" + "=" * 70)
            print(f"❌ Could not connect to database")
            print(f"=" * 70)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
