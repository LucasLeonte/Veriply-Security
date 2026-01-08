"""Test the delete verified_qa endpoint."""
import asyncio
from uuid import UUID
from app.core.database import AsyncSessionLocal
from app.models.verified_qa import VerifiedQA
from app.services.verified_qa import soft_delete_verified_qa, list_verified_qa
from sqlalchemy import select

async def test_delete():
    """Test soft-delete functionality."""
    async with AsyncSessionLocal() as db:
        tenant_id = UUID("b8e9bd23-ad0b-4e17-868c-c7bb232b45a0")
        
        # Get a verified QA entry to delete
        stmt = select(VerifiedQA).where(
            VerifiedQA.tenant_id == tenant_id,
            VerifiedQA.deleted_at.is_(None),
        ).limit(1)
        
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if not entry:
            print("No entries to delete for testing")
            return False
        
        entry_id = entry.id
        group_id = entry.group_id
        print(f"Testing delete of entry: {entry.question_text[:50]}")
        
        # Delete the entry
        success = await soft_delete_verified_qa(
            db=db,
            verified_qa_id=entry_id,
            tenant_id=tenant_id,
            group_id=group_id,
            deleted_by_user_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
        )
        
        if not success:
            print("Delete returned False")
            return False
        
        await db.commit()
        print("Entry soft-deleted successfully")
        
        # Verify it's deleted
        result = await db.execute(
            select(VerifiedQA).where(VerifiedQA.id == entry_id)
        )
        deleted_entry = result.scalar_one_or_none()
        
        if deleted_entry and deleted_entry.deleted_at:
            print(f"[OK] Entry marked as deleted at: {deleted_entry.deleted_at}")
        else:
            print("[ERROR] Entry not properly marked as deleted")
            return False
        
        # Verify it's excluded from list queries
        entries, total = await list_verified_qa(
            db=db,
            tenant_id=tenant_id,
            group_id=group_id,
            limit=100,
            offset=0,
        )
        
        for e in entries:
            if e.id == entry_id:
                print("[ERROR] Deleted entry still appears in list")
                return False
        
        print("[OK] Deleted entry correctly excluded from list queries")
        return True

result = asyncio.run(test_delete())
print(f"\nTest {'PASSED' if result else 'FAILED'}")
