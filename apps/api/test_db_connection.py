"""
Quick Database Connection Test

This script verifies that:
1. Settings load correctly from .env
2. DATABASE_URL is constructed properly
3. Database connection can be established
4. PostgreSQL version can be queried

Run from project root: python apps/api/test_db_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add apps/api to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.settings import settings
from app.core.database import engine
from sqlalchemy import text


async def test_connection():
    """Test database connection and configuration."""
    
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    
    # Step 1: Verify settings loaded
    print("\n1. Settings Configuration:")
    print(f"   DB_HOST: {settings.DB_HOST}")
    print(f"   DB_PORT: {settings.DB_PORT}")
    print(f"   DB_NAME: {settings.DB_NAME}")
    print(f"   DB_USER: {settings.DB_USER}")
    print(f"   DB_PASSWORD: {'*' * len(settings.DB_PASSWORD) if settings.DB_PASSWORD else '(not set)'}")
    db_url = settings.get_database_url()
    # Hide password in output
    if '@' in db_url:
        parts = db_url.split('@')
        user_pass = parts[0].split('://')[-1]
        if ':' in user_pass:
            user = user_pass.split(':')[0]
            masked_url = db_url.replace(user_pass, f"{user}:***")
        else:
            masked_url = db_url
    else:
        masked_url = db_url
    print(f"\n   DATABASE_URL: {masked_url}")
    
    # Step 2: Test connection
    print("\n2. Testing Connection...")
    try:
        async with engine.connect() as conn:
            # Query PostgreSQL version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            print("   ✓ Connection successful!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            
            # Check if pgvector extension is available
            result = await conn.execute(
                text("SELECT COUNT(*) FROM pg_available_extensions WHERE name = 'vector'")
            )
            has_pgvector = result.scalar() > 0
            
            if has_pgvector:
                # Check if pgvector is enabled
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
                )
                is_enabled = result.scalar() > 0
                
                if is_enabled:
                    print("   ✓ pgvector extension is INSTALLED and ENABLED")
                else:
                    print("   ⚠ pgvector extension is available but NOT ENABLED")
                    print("     Run: CREATE EXTENSION vector;")
            else:
                print("   ✗ pgvector extension NOT available")
                print("     Install with: apt-get install postgresql-16-pgvector")
            
            # Test simple query
            result = await conn.execute(text("SELECT 1 as test"))
            test_val = result.scalar()
            assert test_val == 1
            print("   ✓ Simple query works")
            
    except Exception as e:
        print("   ✗ Connection FAILED!")
        print(f"   Error: {e}")
        print("\n   Troubleshooting:")
        print("   - Verify DB_HOST is correct in .env")
        print("   - Check if PostgreSQL is running")
        print("   - Verify DB_USER and DB_PASSWORD are correct")
        print(f"   - Check firewall allows port {settings.DB_PORT}")
        return False
    
    # Step 3: Connection pool info
    print("\n3. Connection Pool Configuration:")
    print(f"   Pool Size: {settings.DB_POOL_SIZE}")
    print(f"   Max Overflow: {settings.DB_MAX_OVERFLOW}")
    print(f"   Total Max Connections: {settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW}")
    print(f"   Pool Timeout: {settings.DB_POOL_TIMEOUT}s")
    print(f"   Pool Recycle: {settings.DB_POOL_RECYCLE}s")
    
    print("\n" + "=" * 70)
    print("✓ ALL CHECKS PASSED - Database is ready!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
