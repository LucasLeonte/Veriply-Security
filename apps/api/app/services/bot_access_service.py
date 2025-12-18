"""Bot document access service for bot-level document/folder access control."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.bot_document_access import BotDocumentAccess
from app.models.document import Document
from app.models.folder import Folder


class BotAccessService:
    """Service for managing bot-level document and folder access."""

    @staticmethod
    async def set_document_access(
        db: AsyncSession,
        bot_id: UUID,
        document_id: UUID,
        is_allowed: bool,
        tenant_id: UUID,
        group_id: UUID
    ) -> BotDocumentAccess:
        """Set explicit document access for a bot.
        
        Args:
            db: Database session
            bot_id: Bot ID
            document_id: Document ID
            is_allowed: Whether bot can access document
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            BotDocumentAccess record
        """
        # Check if access record already exists
        existing = await db.scalar(
            select(BotDocumentAccess).where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.document_id == document_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id
                )
            )
        )
        
        if existing:
            existing.is_allowed = is_allowed
            existing.updated_at = datetime.utcnow()
            await db.flush()
            await db.refresh(existing)
            return existing
        
        # Create new access record
        access = BotDocumentAccess(
            tenant_id=tenant_id,
            group_id=group_id,
            bot_id=bot_id,
            document_id=document_id,
            folder_id=None,
            is_allowed=is_allowed
        )
        db.add(access)
        await db.flush()
        await db.refresh(access)
        return access

    @staticmethod
    async def set_folder_access(
        db: AsyncSession,
        bot_id: UUID,
        folder_id: UUID,
        is_allowed: bool,
        tenant_id: UUID,
        group_id: UUID
    ) -> BotDocumentAccess:
        """Set folder access for a bot.
        
        Args:
            db: Database session
            bot_id: Bot ID
            folder_id: Folder ID
            is_allowed: Whether bot can access folder (and docs in it)
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            BotDocumentAccess record
        """
        # Check if access record already exists
        existing = await db.scalar(
            select(BotDocumentAccess).where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.folder_id == folder_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id
                )
            )
        )
        
        if existing:
            existing.is_allowed = is_allowed
            existing.updated_at = datetime.utcnow()
            await db.flush()
            await db.refresh(existing)
            return existing
        
        # Create new access record
        access = BotDocumentAccess(
            tenant_id=tenant_id,
            group_id=group_id,
            bot_id=bot_id,
            document_id=None,
            folder_id=folder_id,
            is_allowed=is_allowed
        )
        db.add(access)
        await db.flush()
        await db.refresh(access)
        return access

    @staticmethod
    async def check_document_access(
        db: AsyncSession,
        bot_id: UUID,
        document_id: UUID,
        tenant_id: UUID,
        group_id: UUID
    ) -> bool:
        """Check if bot can access a document.
        
        Access resolution:
        1. Check explicit document access (overrides folder)
        2. Check folder access (if document in folder)
        3. Default: deny
        
        Args:
            db: Database session
            bot_id: Bot ID
            document_id: Document ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            True if bot can access document, False otherwise
        """
        # 1. Check explicit document access
        doc_access = await db.scalar(
            select(BotDocumentAccess).where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.document_id == document_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id
                )
            )
        )
        if doc_access:
            return doc_access.is_allowed
        
        # 2. Check folder access
        document = await db.scalar(
            select(Document).where(
                and_(
                    Document.id == document_id,
                    Document.tenant_id == tenant_id,
                    Document.group_id == group_id
                )
            )
        )
        if document and document.folder_id:
            folder_access = await db.scalar(
                select(BotDocumentAccess).where(
                    and_(
                        BotDocumentAccess.bot_id == bot_id,
                        BotDocumentAccess.folder_id == document.folder_id,
                        BotDocumentAccess.tenant_id == tenant_id,
                        BotDocumentAccess.group_id == group_id
                    )
                )
            )
            if folder_access:
                return folder_access.is_allowed
        
        # 3. Default: deny
        return False

    @staticmethod
    async def get_bot_accessible_documents(
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        group_id: UUID
    ) -> List[Document]:
        """Get all documents bot can access based on access rules.
        
        Args:
            db: Database session
            bot_id: Bot ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            List of accessible documents
        """
        # Get all documents in group
        documents = await db.execute(
            select(Document).where(
                and_(
                    Document.tenant_id == tenant_id,
                    Document.group_id == group_id,
                    Document.deleted_at.is_(None)
                )
            )
        )
        all_docs = list(documents.scalars().all())
        
        # Filter by access rules
        accessible = []
        for doc in all_docs:
            if await BotAccessService.check_document_access(
                db, bot_id, doc.id, tenant_id, group_id
            ):
                accessible.append(doc)
        
        return accessible

    @staticmethod
    async def bulk_set_access(
        db: AsyncSession,
        bot_id: UUID,
        document_ids: Optional[List[UUID]],
        folder_ids: Optional[List[UUID]],
        is_allowed: bool,
        tenant_id: UUID,
        group_id: UUID
    ) -> dict:
        """Bulk set access for multiple documents/folders.
        
        Args:
            db: Database session
            bot_id: Bot ID
            document_ids: List of document IDs (optional)
            folder_ids: List of folder IDs (optional)
            is_allowed: Whether bot can access
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            Dict with documents_updated and folders_updated counts
        """
        docs_updated = 0
        folders_updated = 0
        
        if document_ids:
            for doc_id in document_ids:
                await BotAccessService.set_document_access(
                    db, bot_id, doc_id, is_allowed, tenant_id, group_id
                )
                docs_updated += 1
        
        if folder_ids:
            for folder_id in folder_ids:
                await BotAccessService.set_folder_access(
                    db, bot_id, folder_id, is_allowed, tenant_id, group_id
                )
                folders_updated += 1
        
        return {
            "documents_updated": docs_updated,
            "folders_updated": folders_updated
        }

    @staticmethod
    async def get_access_summary(
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        group_id: UUID
    ) -> dict:
        """Get access summary for a bot showing all folders and documents with their access states.
        
        Args:
            db: Database session
            bot_id: Bot ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            Dict with folders and documents lists, each with access info
        """
        # Get all folders
        folders_result = await db.execute(
            select(Folder).where(
                and_(
                    Folder.tenant_id == tenant_id,
                    Folder.group_id == group_id,
                    Folder.deleted_at.is_(None)
                )
            ).order_by(Folder.name)
        )
        folders = list(folders_result.scalars().all())
        
        # Get folder access records
        folder_access_result = await db.execute(
            select(BotDocumentAccess).where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id,
                    BotDocumentAccess.folder_id.isnot(None)
                )
            )
        )
        folder_access_map = {
            acc.folder_id: acc.is_allowed 
            for acc in folder_access_result.scalars().all()
        }
        
        # Get all documents
        documents_result = await db.execute(
            select(Document).where(
                and_(
                    Document.tenant_id == tenant_id,
                    Document.group_id == group_id,
                    Document.deleted_at.is_(None)
                )
            ).order_by(Document.title)
        )
        documents = list(documents_result.scalars().all())
        
        # Get document access records
        doc_access_result = await db.execute(
            select(BotDocumentAccess).where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id,
                    BotDocumentAccess.document_id.isnot(None)
                )
            )
        )
        doc_access_map = {
            acc.document_id: acc.is_allowed 
            for acc in doc_access_result.scalars().all()
        }
        
        # Build folder summary
        folder_summary = []
        for folder in folders:
            # Check if folder has explicit access
            explicit_access = folder_access_map.get(folder.id)
            
            # Check if any documents in folder have overrides
            docs_in_folder = [d for d in documents if d.folder_id == folder.id]
            has_overrides = any(d.id in doc_access_map for d in docs_in_folder)
            
            folder_summary.append({
                "id": str(folder.id),
                "name": folder.name,
                "allowed": explicit_access if explicit_access is not None else False,
                "has_explicit_access": explicit_access is not None,
                "has_doc_overrides": has_overrides
            })
        
        # Build document summary
        document_summary = []
        for doc in documents:
            # Check explicit doc access
            explicit_access = doc_access_map.get(doc.id)
            
            # Determine effective access
            if explicit_access is not None:
                effective_access = explicit_access
            elif doc.folder_id and doc.folder_id in folder_access_map:
                effective_access = folder_access_map[doc.folder_id]
            else:
                effective_access = False
            
            document_summary.append({
                "id": str(doc.id),
                "name": doc.title,
                "folder_id": str(doc.folder_id) if doc.folder_id else None,
                "allowed": effective_access,
                "has_explicit_access": explicit_access is not None,
                "explicit_allowed": explicit_access
            })
        
        return {
            "folders": folder_summary,
            "documents": document_summary
        }
