"""Simple semantic search API endpoint for testing embeddings."""
import asyncio
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import aiohttp

app = FastAPI(title="Veriply Search API")

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:DarioDML@10.2.160.214:5432/vector_db"
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

# Ollama config
OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
EMBEDDING_MODEL = "bge-m3"


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SearchResult(BaseModel):
    text: str
    metadata: dict
    similarity: float


async def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama."""
    async with aiohttp.ClientSession() as session:
        payload = {"model": EMBEDDING_MODEL, "input": text}
        async with session.post(OLLAMA_URL, json=payload, timeout=30) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Failed to generate embedding")
            data = await resp.json()
            if "embeddings" in data and len(data["embeddings"]) > 0:
                return data["embeddings"][0]
            raise HTTPException(status_code=500, detail="Invalid embedding response")


@app.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """Semantic search over document embeddings."""
    try:
        # Generate query embedding
        query_embedding = await get_embedding(request.query)
        
        # Search database
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT 
                        text,
                        metadata,
                        1 - (embedding <=> :query_vec::vector) as similarity
                    FROM embeddings
                    ORDER BY embedding <=> :query_vec::vector
                    LIMIT :limit
                """),
                {"query_vec": query_embedding, "limit": request.limit}
            )
            
            results = []
            for row in result:
                import json
                results.append(SearchResult(
                    text=row.text,
                    metadata=json.loads(row.metadata),
                    similarity=float(row.similarity)
                ))
            
            return results
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model": EMBEDDING_MODEL}


if __name__ == "__main__":
    import uvicorn
    print("Starting Veriply Search API on http://localhost:8000")
    print("Docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
