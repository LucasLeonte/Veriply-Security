"""Tests for bot access service."""
import pytest
from uuid import uuid4
from app.services.bot_access_service import BotAccessService


@pytest.mark.asyncio
async def test_set_document_access(db_session, test_tenant, test_group, test_bot, test_document):
    """Test setting explicit document access."""
    access = await BotAccessService.set_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert access.bot_id == test_bot.id
    assert access.document_id == test_document.id
    assert access.is_allowed is True


@pytest.mark.asyncio
async def test_set_folder_access(db_session, test_tenant, test_group, test_bot, test_user):
    """Test setting folder access."""
    from app.services.folder_service import FolderService
    
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Test Folder",
        created_by=test_user.id
    )
    await db_session.commit()
    
    access = await BotAccessService.set_folder_access(
        db=db_session,
        bot_id=test_bot.id,
        folder_id=folder.id,
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert access.bot_id == test_bot.id
    assert access.folder_id == folder.id
    assert access.is_allowed is True


@pytest.mark.asyncio
async def test_check_document_access_explicit(db_session, test_tenant, test_group, test_bot, test_document):
    """Test checking document access with explicit access record."""
    # Set explicit document access
    await BotAccessService.set_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    await db_session.commit()
    
    # Check access
    has_access = await BotAccessService.check_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert has_access is True


@pytest.mark.asyncio
async def test_check_document_access_via_folder(db_session, test_tenant, test_group, test_bot, test_document, test_user):
    """Test checking document access via folder access."""
    from app.services.folder_service import FolderService
    
    # Create folder
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Allowed Folder",
        created_by=test_user.id
    )
    await db_session.commit()
    
    # Associate document with folder
    test_document.folder_id = folder.id
    await db_session.commit()
    
    # Set folder access
    await BotAccessService.set_folder_access(
        db=db_session,
        bot_id=test_bot.id,
        folder_id=folder.id,
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    await db_session.commit()
    
    # Check document access (should inherit from folder)
    has_access = await BotAccessService.check_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert has_access is True


@pytest.mark.asyncio
async def test_document_override_folder_access(db_session, test_tenant, test_group, test_bot, test_document, test_user):
    """Test that explicit document access overrides folder access."""
    from app.services.folder_service import FolderService
    
    # Create folder
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Denied Folder",
        created_by=test_user.id
    )
    await db_session.commit()
    
    # Associate document with folder
    test_document.folder_id = folder.id
    await db_session.commit()
    
    # Set folder access to denied
    await BotAccessService.set_folder_access(
        db=db_session,
        bot_id=test_bot.id,
        folder_id=folder.id,
        is_allowed=False,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    # Set explicit document access to allowed (overrides folder)
    await BotAccessService.set_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    await db_session.commit()
    
    # Check document access (should be allowed despite folder denial)
    has_access = await BotAccessService.check_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert has_access is True


@pytest.mark.asyncio
async def test_default_deny_access(db_session, test_tenant, test_group, test_bot, test_document):
    """Test that default access is deny when no rules exist."""
    has_access = await BotAccessService.check_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert has_access is False


@pytest.mark.asyncio
async def test_bulk_set_access(db_session, test_tenant, test_group, test_bot, test_document, test_user):
    """Test bulk setting access for multiple documents/folders."""
    from app.services.folder_service import FolderService
    from app.models.document import Document
    
    # Create another document
    doc2 = Document(
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        title="Document 2",
        uploader_id=test_user.id,
        status="ready"
    )
    db_session.add(doc2)
    
    # Create folder
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Bulk Folder",
        created_by=test_user.id
    )
    await db_session.commit()
    
    # Bulk set access
    result = await BotAccessService.bulk_set_access(
        db=db_session,
        bot_id=test_bot.id,
        document_ids=[test_document.id, doc2.id],
        folder_ids=[folder.id],
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert result["documents_updated"] == 2
    assert result["folders_updated"] == 1


@pytest.mark.asyncio
async def test_get_access_summary(db_session, test_tenant, test_group, test_bot, test_document, test_user):
    """Test getting access summary for a bot."""
    from app.services.folder_service import FolderService
    
    # Create folder
    folder = await FolderService.create_folder(
        db=db_session,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Summary Folder",
        created_by=test_user.id
    )
    
    # Set access
    await BotAccessService.set_folder_access(
        db=db_session,
        bot_id=test_bot.id,
        folder_id=folder.id,
        is_allowed=True,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    await BotAccessService.set_document_access(
        db=db_session,
        bot_id=test_bot.id,
        document_id=test_document.id,
        is_allowed=False,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    await db_session.commit()
    
    # Get summary
    summary = await BotAccessService.get_access_summary(
        db=db_session,
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert len(summary["folders"]) == 1
    assert summary["folders"][0]["allowed"] is True
    assert len(summary["documents"]) == 1
    assert summary["documents"][0]["allowed"] is False
