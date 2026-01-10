"""
Test different credential combinations for PostgreSQL
"""
import asyncio
import asyncpg

async def test_credentials(user, password, host, port, database):
    """Test a specific set of credentials."""
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            timeout=5
        )
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        return True, result
    except Exception as e:
        return False, str(e)

async def main():
    host = "10.2.160.214"
    port = 5432
    
    # Test different combinations
    credentials = [
        ("Veriply", "Student1", "vector_db"),
        ("veriply", "Student1", "vector_db"),
        ("postgres", "Student1", "vector_db"),
        ("Veriply", "Student1", "postgres"),  # Default database
        ("veriply", "Student1", "postgres"),
        ("postgres", "Student1", "postgres"),
    ]
    
    print("=" * 70)
    print("TESTING DIFFERENT CREDENTIAL COMBINATIONS")
    print("=" * 70)
    print(f"\nHost: {host}:{port}")
    print("\nTesting...\n")
    
    for user, password, database in credentials:
        print(f"Testing: user='{user}', password='***', db='{database}'")
        success, result = await test_credentials(user, password, host, port, database)
        
        if success:
            print(f"  ✓ SUCCESS!")
            print(f"  PostgreSQL: {result.split(',')[0]}")
            print("\n" + "=" * 70)
            print("WORKING CREDENTIALS FOUND!")
            print("=" * 70)
            print(f"User: {user}")
            print(f"Password: {password}")
            print(f"Database: {database}")
            print(f"\nConnection string:")
            print(f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}")
            return
        else:
            print(f"  ✗ Failed: {result}\n")
    
    print("\n" + "=" * 70)
    print("NO WORKING CREDENTIALS FOUND")
    print("=" * 70)
    print("\nPossible issues:")
    print("1. Password is incorrect")
    print("2. User doesn't exist")
    print("3. Database doesn't exist")
    print("4. PostgreSQL is not running")
    print("5. Firewall is blocking connection")
    print("6. PostgreSQL pg_hba.conf not configured for remote connections")

if __name__ == "__main__":
    asyncio.run(main())
