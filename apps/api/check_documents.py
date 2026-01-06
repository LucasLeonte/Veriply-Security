import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_documents():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            """
            SELECT 
                id, 
                title,
                status,
                storage_path
            FROM documents 
            WHERE title LIKE 'Verified Q&A%'
            ORDER BY created_at DESC 
            LIMIT 5
            """
        ))
        
        rows = result.fetchall()
        
        if not rows:
            print("\n❌ No Verified Q&A documents found!")
        else:
            print(f"\n✅ Found {len(rows)} Verified Q&A documents:\n")
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Title: {row[1]}")
                print(f"Status: {row[2]}")
                print(f"Storage Path: {row[3]}")
                
                # Check if file exists
                if row[3]:
                    if row[3].startswith("file://"):
                        import os
                        local_path = row[3][7:]  # Remove "file://"
                        exists = os.path.exists(local_path)
                        print(f"File exists: {exists}")
                        if not exists:
                            print(f"  → File not found at: {local_path}")
                print()

if __name__ == "__main__":
    asyncio.run(check_documents())
