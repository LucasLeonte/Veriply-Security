"""Tests for folder service."""
import pytest
from app.services.folder_service import FolderService


@pytest.mark.asyncio
async def test_create_folder(db_session, test_tenant, test_group, test_user):
    """Test creating a folder."""
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Test Folder",
        created_by=test_user.id
    )
    
    assert folder.id is not None
    assert folder.name == "Test Folder"
    assert folder.tenant_id == test_tenant.id
    assert folder.group_id == test_group.id
    assert folder.created_by == test_user.id


@pytest.mark.asyncio
async def test_create_duplicate_folder_fails(db_session, test_tenant, test_group, test_user):
    """Test that creating a folder with duplicate name fails."""
    await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Duplicate",
        created_by=test_user.id
    )
    await db_session.commit()
    
    with pytest.raises(ValueError, match="already exists"):
        await FolderService.create_folder(
            db=db_session,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            name="Duplicate",
            created_by=test_user.id
        )


@pytest.mark.asyncio
async def test_list_group_folders(db_session, test_tenant, test_group, test_user):
    """Test listing folders in a group."""
    await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Folder 1",
        created_by=test_user.id
    )
    await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Folder 2",
        created_by=test_user.id
    )
    await db_session.commit()
    
    folders = await FolderService.list_group_folders(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert len(folders) == 2
    assert folders[0].name == "Folder 1"
    assert folders[1].name == "Folder 2"


@pytest.mark.asyncio
async def test_update_folder(db_session, test_tenant, test_group, test_user):
    """Test updating folder name."""
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Old Name",
        created_by=test_user.id
    )
    await db_session.commit()
    
    updated = await FolderService.update_folder(
        db=db_session,
        folder_id=folder.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="New Name"
    )
    
    assert updated.name == "New Name"


@pytest.mark.asyncio
async def test_soft_delete_folder(db_session, test_tenant, test_group, test_user):
    """Test soft-deleting a folder."""
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="To Delete",
        created_by=test_user.id
    )
    await db_session.commit()
    
    deleted = await FolderService.soft_delete_folder(
        db=db_session,
        folder_id=folder.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert deleted.deleted_at is not None


@pytest.mark.asyncio
async def test_get_folder_stats(db_session, test_tenant, test_group, test_user, test_document):
    """Test getting folder statistics."""
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Stats Folder",
        created_by=test_user.id
    )
    await db_session.commit()
    
    # Associate document with folder (would be done through document service)
    test_document.folder_id = folder.id
    await db_session.commit()
    
    stats = await FolderService.get_folder_stats(
        db=db_session,
        folder_id=folder.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert stats["doc_count"] == 1
