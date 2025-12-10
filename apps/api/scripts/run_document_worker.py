"""Run the document processor for a single document id (manual testing).

Usage:
  python run_document_worker.py <document-id>

Requires `DATABASE_URL` env var pointing to the async Postgres URL, e.g.
  export DATABASE_URL=postgresql+asyncpg://veriply:change-me@localhost:5432/veriply
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.workers.document_processor import process_document


async def main(document_id: str):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return
    engine = create_async_engine(db_url, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        res = await process_document(document_id, db_session=session)
        print(res)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_document_worker.py <document-id>")
        sys.exit(2)
    asyncio.run(main(sys.argv[1]))
