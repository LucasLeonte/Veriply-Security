"""Fix the status of Q&A documents in the knowledge base from 'failed' to 'ready'."""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:DarioDML@10.2.160.214:5432/vector_db"
    )
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        # Update Q&A documents from 'failed' or 'uploaded' to 'ready'
        # These are documents with titles like "Verified Q&A:..."
        result = await session.execute(
            text("""
                UPDATE documents 
                SET status = 'ready', updated_at = NOW()
                WHERE (title LIKE 'Verified Q&A:%' OR title LIKE 'HITL-%')
                  AND status IN ('failed', 'uploaded')
                RETURNING id, title, status
            """)
        )
        updated = result.fetchall()
        
        if updated:
            print(f"✓ Updated {len(updated)} Q&A documents to 'ready' status:")
            for row in updated:
                print(f"  - {str(row[0])[:8]}... | {row[1][:50]}...")
        else:
            print("No Q&A documents needed updating (already ready or none exist)")
        
        await session.commit()
        
        # Verify the update
        print("\n" + "=" * 80)
        print("Current Q&A Document Statuses:")
        print("=" * 80)
        result2 = await session.execute(
            text("""
                SELECT id, title, status, created_at 
                FROM documents 
                WHERE title LIKE 'Verified Q&A:%' OR title LIKE 'HITL-%'
                ORDER BY created_at DESC 
                LIMIT 10
            """)
        )
        rows = result2.fetchall()
        for row in rows:
            doc_id = str(row[0])[:8]
            title = row[1][:45] if row[1] else "No title"
            status = row[2]
            created = row[3]
            print(f"ID: {doc_id}... | Status: {status:10} | {title}...")
    
    await engine.dispose()
    print("\n✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
