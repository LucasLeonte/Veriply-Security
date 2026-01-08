"""Test the verified-qa API endpoint with the actual route logic."""
import asyncio
from uuid import UUID
from app.core.database import AsyncSessionLocal, get_db
from app.models.verified_qa import VerifiedQA
from app.schemas.verified_qa import VerifiedQAResponse
from app.services.verified_qa import list_verified_qa
from sqlalchemy import select

async def test_list_endpoint():
    """Test the list_entries endpoint logic."""
    async with AsyncSessionLocal() as db:
        # Use the same tenant from the database
        tenant_id = UUID("b8e9bd23-ad0b-4e17-868c-c7bb232b45a0")
        group_id = UUID("83d1a9fd-0733-432a-b7d4-66256f606f0f")
        
        print(f"Testing list_verified_qa service with:")
        print(f"  tenant_id: {tenant_id}")
        print(f"  group_id: {group_id}")
        
        try:
            entries, total = await list_verified_qa(
                db=db,
                tenant_id=tenant_id,
                group_id=group_id,
                limit=10,
                offset=0,
            )
            
            print(f"Found {len(entries)} entries (total: {total})")
            
            # Convert to response objects
            responses = [VerifiedQAResponse.from_orm(entry) for entry in entries]
            print(f"Successfully converted all {len(responses)} entries to response schema")
            
            # Print sample response
            if responses:
                print(f"\nSample response:")
                print(f"  ID: {responses[0].id}")
                print(f"  Question: {responses[0].question_text[:50]}...")
                print(f"  Answer: {responses[0].answer_text[:50]}...")
                print(f"  Approved at: {responses[0].approved_at}")
                print(f"  Updated by: {responses[0].updated_by_user_id}")
                print(f"  Deleted at: {responses[0].deleted_at}")
            
            return True
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

result = asyncio.run(test_list_endpoint())
print(f"\nTest {'PASSED' if result else 'FAILED'}")
