"""Ingestion worker: chunk documents, generate embeddings, and insert into Postgres+pgvector.

Usage examples:

  # Run with mock embeddings for local testing
  python ingest_worker.py --source docs --provider mock --batch-size 64

  # Run with Ollama (self-hosted) - requires Ollama HTTP API available
  python ingest_worker.py --source docs --provider ollama --model bge-m3 --batch-size 32

Environment:
  Set `DATABASE_URL` to your asyncpg SQLAlchemy URL, e.g.
    postgresql+asyncpg://user:password@localhost:5432/veriply

This is a scaffold: the `ollama` provider attempts to call a local Ollama HTTP endpoint
and will print an error if unavailable. The `mock` provider produces deterministic
vectors and is useful for testing the ingestion pipeline and validating DB insert logic.
"""

import argparse
import asyncio
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import List

import aiohttp
from langchain_text_splitters import CharacterTextSplitter
from sqlalchemy import (Column, Integer, MetaData, String, Table, Text,
                        func)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import insert

from pgvector.sqlalchemy import Vector

# bge-m3 produces 1024-dimensional embeddings
DEFAULT_DIM = 1024


def deterministic_vector(text: str, dim: int = DEFAULT_DIM) -> List[float]:
    """Create a deterministic pseudo-embedding from text for testing.
    Not a real embedding; useful for pipeline tests.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Expand to dim floats by repeated hashing
    out = []
    counter = 0
    while len(out) < dim:
        m = hashlib.sha256(h + counter.to_bytes(4, "little")).digest()
        for i in range(0, len(m), 4):
            if len(out) >= dim:
                break
            v = int.from_bytes(m[i : i + 4], "little") / 2 ** 32
            out.append(v)
        counter += 1
    return out[:dim]


async def ollama_embed(texts: List[str], model: str = "bge-m3") -> List[List[float]]:
    """Attempt to call a local Ollama HTTP embedding endpoint.

    This function assumes an HTTP server at http://127.0.0.1:11434 that accepts
    POST /api/embed or similar. The exact endpoint varies by Ollama version; this
    scaffold tries common patterns and raises a helpful error if none work.
    """
    url_candidates = [
        "http://127.0.0.1:11434/embed",
        "http://127.0.0.1:11434/embeddings",
        "http://127.0.0.1:11434/api/embed",
        "http://127.0.0.1:11434/api/embeddings",
    ]

    payload = {"model": model, "input": texts}

    async with aiohttp.ClientSession() as session:
        last_err = None
        for url in url_candidates:
            try:
                async with session.post(url, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Accept multiple shapes: {'data': [{'embedding': [...]}, ...]} or list of vectors
                        if isinstance(data, dict) and "data" in data:
                            return [item.get("embedding") for item in data["data"]]
                        if isinstance(data, list) and all(isinstance(x, list) for x in data):
                            return data
                        # Fallback: try to extract embeddings key
                        if isinstance(data, dict) and "embeddings" in data:
                            return data["embeddings"]
                        raise RuntimeError(f"Unexpected response shape from {url}: {data}")
                    else:
                        last_err = f"{url} returned status {resp.status}"
            except Exception as e:
                last_err = str(e)
        raise RuntimeError(
            "Could not contact Ollama embedding endpoint. Tried: "
            + ", ".join(url_candidates)
            + ". Last error: "
            + str(last_err)
        )


def collect_text_files(source: Path) -> List[Path]:
    exts = {".md", ".txt", ".html", ".json"}
    files = [p for p in source.rglob("*") if p.suffix.lower() in exts]
    files.sort()
    return files


def make_table(metadata: MetaData) -> Table:
    return Table(
        "embeddings",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column("tenant_id", UUID(as_uuid=True), nullable=True),
        Column("bot_id", UUID(as_uuid=True)),
        Column("doc_id", UUID(as_uuid=True)),
        Column("chunk_id", Integer),
        Column("embedding", Vector(dim=DEFAULT_DIM)),
        Column("text", Text),
        Column("metadata", String),
        Column("created_at", String, server_default=func.now()),
    )


async def ingest_folder(
    source: Path,
    database_url: str,
    provider: str = "mock",
    model: str = "bge-m3",
    batch_size: int = 64,
):
    engine = create_async_engine(database_url, future=True)
    metadata = MetaData()
    embeddings_table = make_table(metadata)

    async with engine.begin() as conn:
        # Ensure table exists (create if not)
        await conn.run_sync(metadata.create_all)

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    files = collect_text_files(source)
    print(f"Found {len(files)} files under {source}")

    rows = []
    async with engine.begin() as conn:
        for file in files:
            text = file.read_text(encoding="utf-8")
            chunks = splitter.split_text(text)
            for idx, chunk in enumerate(chunks):
                rows.append((str(file), idx, chunk))

                if len(rows) >= batch_size:
                    texts = [r[2] for r in rows]
                    if provider == "mock":
                        embeddings = [deterministic_vector(t) for t in texts]
                    else:
                        embeddings = await ollama_embed(texts, model=model)

                    # Build insert payloads
                    # Using a dummy test tenant for ingestion scaffold
                    test_tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
                    payloads = []
                    for (path, chunk_id, txt), emb in zip(rows, embeddings):
                        payloads.append(
                            {
                                "id": uuid.uuid4(),
                                "tenant_id": test_tenant_id,
                                "bot_id": None,
                                "doc_id": None,
                                "chunk_id": chunk_id,
                                "embedding": emb,
                                "text": txt,
                                "metadata": json.dumps({"source": path}),
                            }
                        )

                    await conn.execute(insert(embeddings_table).values(payloads))
                    print(f"Inserted batch of {len(payloads)} chunks")
                    rows = []

        # flush remaining
        if rows:
            texts = [r[2] for r in rows]
            if provider == "mock":
                embeddings = [deterministic_vector(t) for t in texts]
            else:
                embeddings = await ollama_embed(texts, model=model)

            # Using a dummy test tenant for ingestion scaffold
            test_tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            payloads = []
            for (path, chunk_id, txt), emb in zip(rows, embeddings):
                payloads.append(
                    {
                        "id": uuid.uuid4(),
                        "tenant_id": test_tenant_id,
                        "bot_id": None,
                        "doc_id": None,
                        "chunk_id": chunk_id,
                        "embedding": emb,
                        "text": txt,
                        "metadata": json.dumps({"source": path}),
                    }
                )

            await conn.execute(insert(embeddings_table).values(payloads))
            print(f"Inserted final batch of {len(payloads)} chunks")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="docs", help="Source folder to ingest")
    p.add_argument("--provider", choices=["mock", "ollama"], default="mock")
    p.add_argument("--model", default="bge-m3")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:DarioDML@10.2.160.214:5432/vector_db"),
    )
    return p.parse_args()


def main():
    args = parse_args()
    source = Path(args.source)
    if not source.exists():
        print(f"Source folder {source} not found")
        return
    asyncio.run(
        ingest_folder(
            source=source,
            database_url=args.database_url,
            provider=args.provider,
            model=args.model,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
