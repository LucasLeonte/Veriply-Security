"""Test the verified-qa API endpoint."""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.verified_qa import VerifiedQA
from app.schemas.verified_qa import VerifiedQAResponse
from sqlalchemy import select
from uuid import UUID

async def test_endpoint():
    async with AsyncSessionLocal() as db:
        # Simulate what the endpoint does
        tenant_id = UUID("b8e9bd23-ad0b-4e17-868c-c7bb232b45a0")  # From the test above
        group_id = None  # We'll get entries for the tenant
        
        stmt = select(VerifiedQA).where(
            VerifiedQA.tenant_id == tenant_id,
            VerifiedQA.deleted_at.is_(None),
        ).limit(10).offset(0)
        
        result = await db.execute(stmt)
        entries = result.scalars().all()
        print(f"Found {len(entries)} verified QA entries")
        
        # Try to convert them
        responses = []
        for entry in entries:
            try:
                resp = VerifiedQAResponse.from_orm(entry)
                responses.append(resp)
                print(f"[OK] Converted: {entry.question_text[:30]}...")
            except Exception as e:
                print(f"[ERROR] Failed to convert: {e}")
        
        print(f"\nSuccessfully converted {len(responses)}/{len(entries)} entries")
        return len(responses) == len(entries)

result = asyncio.run(test_endpoint())
print(f"\nTest {'PASSED' if result else 'FAILED'}")
