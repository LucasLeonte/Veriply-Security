"""Check the status of Q&A documents in the knowledge base."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:DarioDML@10.2.160.214:5432/vector_db"
    )
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        # Check Q&A documents
        result = await session.execute(
            text("""
                SELECT id, title, status, created_at 
                FROM documents 
                WHERE title LIKE '%Verified Q&A%' 
                   OR title LIKE '%HITL%'
                ORDER BY created_at DESC 
                LIMIT 10
            """)
        )
        rows = result.fetchall()
        
        print("=" * 80)
        print("Q&A Documents in Knowledge Base:")
        print("=" * 80)
        if rows:
            for row in rows:
                doc_id = str(row[0])[:8]
                title = row[1][:50] if row[1] else "No title"
                status = row[2]
                created = row[3]
                print(f"ID: {doc_id}... | Status: {status:12} | Created: {created} | {title}...")
        else:
            print("No Q&A documents found")
        
        # Also check all recent documents
        print("\n" + "=" * 80)
        print("Recent Documents (last 10):")
        print("=" * 80)
        result2 = await session.execute(
            text("""
                SELECT id, title, status, mime, created_at 
                FROM documents 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
        )
        rows2 = result2.fetchall()
        for row in rows2:
            doc_id = str(row[0])[:8]
            title = row[1][:40] if row[1] else "No title"
            status = row[2]
            mime = row[3]
            created = row[4]
            print(f"ID: {doc_id}... | Status: {status:12} | MIME: {mime:15} | {title}...")
        
        # Check chunks for Q&A docs
        print("\n" + "=" * 80)
        print("Chunks with HITL source:")
        print("=" * 80)
        result3 = await session.execute(
            text("""
                SELECT c.id, c.document_id, d.status, c.created_at
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.metadata_json->>'source' = 'hitl_approval'
                ORDER BY c.created_at DESC
                LIMIT 10
            """)
        )
        rows3 = result3.fetchall()
        if rows3:
            for row in rows3:
                print(f"Chunk: {str(row[0])[:8]}... | Doc: {str(row[1])[:8]}... | Doc Status: {row[2]} | Created: {row[3]}")
        else:
            print("No HITL chunks found")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
