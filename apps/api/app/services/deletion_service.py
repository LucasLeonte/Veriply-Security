"""Document deletion service with async storage cleanup.

Handles background cleanup of document files from storage (S3 or local filesystem)
after document records are deleted from the database.
"""
import asyncio
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


def enqueue_storage_cleanup(storage_path: str) -> bool:
    """Enqueue async cleanup job for a single document's storage.
    
    Args:
        storage_path: Path to the file in storage (S3 key or local path)
        
    Returns:
        bool: True if cleanup was queued successfully
    """
    async def _cleanup():
        try:
            await cleanup_storage(storage_path)
        except Exception as e:
            logger.exception(f"Storage cleanup failed for {storage_path}: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_cleanup())
        return True
    except RuntimeError:
        # No running loop — run synchronously
        try:
            asyncio.run(_cleanup())
            return True
        except Exception as e:
            logger.exception(f"Synchronous storage cleanup failed for {storage_path}: {e}")
            return False


def enqueue_bulk_storage_cleanup(storage_paths: List[str]) -> int:
    """Enqueue async cleanup jobs for multiple documents' storage.
    
    Args:
        storage_paths: List of paths to files in storage
        
    Returns:
        int: Number of cleanup jobs successfully queued
    """
    async def _bulk_cleanup():
        tasks = [cleanup_storage(path) for path in storage_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count
        
        if error_count > 0:
            logger.warning(f"Bulk storage cleanup: {success_count} succeeded, {error_count} failed")
        else:
            logger.info(f"Bulk storage cleanup: all {success_count} files cleaned successfully")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_bulk_cleanup())
        return len(storage_paths)
    except RuntimeError:
        # No running loop — run synchronously
        try:
            asyncio.run(_bulk_cleanup())
            return len(storage_paths)
        except Exception as e:
            logger.exception(f"Synchronous bulk storage cleanup failed: {e}")
            return 0


async def cleanup_storage(storage_path: str) -> None:
    """Clean up a document file from storage.
    
    This function handles both S3 and local filesystem storage.
    
    Args:
        storage_path: Path to the file in storage
        
    Raises:
        Exception: If cleanup fails (logged but not propagated in async context)
    """
    if not storage_path:
        logger.warning("Cannot cleanup: storage_path is empty")
        return
    
    # Check if using S3
    if storage_path.startswith("s3://"):
        await cleanup_s3(storage_path)
    else:
        # Local filesystem
        await cleanup_local(storage_path)


async def cleanup_s3(s3_path: str) -> None:
    """Delete a file from S3 storage.
    
    Args:
        s3_path: S3 URI (e.g., s3://bucket-name/path/to/file)
    """
    try:
        # Parse S3 path
        # Format: s3://bucket-name/key/path
        parts = s3_path.replace("s3://", "").split("/", 1)
        if len(parts) != 2:
            logger.error(f"Invalid S3 path format: {s3_path}")
            return
        
        bucket_name, key = parts
        
        # Import boto3 only if needed
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            logger.error("boto3 not installed, cannot cleanup S3 files")
            return
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Delete the object
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=key)
            logger.info(f"Deleted S3 object: {s3_path}")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # File doesn't exist, that's ok
                logger.info(f"S3 object already deleted or doesn't exist: {s3_path}")
            else:
                raise
                
    except Exception as e:
        logger.error(f"Failed to cleanup S3 file {s3_path}: {e}")
        raise


async def cleanup_local(file_path: str) -> None:
    """Delete a file from local filesystem storage.
    
    Args:
        file_path: Local filesystem path
    """
    try:
        path = Path(file_path)
        
        if path.exists():
            path.unlink()
            logger.info(f"Deleted local file: {file_path}")
        else:
            # File doesn't exist, that's ok
            logger.info(f"Local file already deleted or doesn't exist: {file_path}")
            
    except Exception as e:
        logger.error(f"Failed to cleanup local file {file_path}: {e}")
        raise


async def cleanup_document_embeddings(document_id: str) -> int:
    """Clean up embeddings associated with a document.
    
    This is called as part of the deletion process to remove vectors from pgvector.
    In most cases, this is handled by CASCADE DELETE on the chunks table,
    but this function can be used for explicit cleanup or verification.
    
    Args:
        document_id: UUID of the document
        
    Returns:
        int: Number of embeddings deleted
    """
    from app.core.database import AsyncSessionLocal
    from app.models.chunk import Chunk
    from sqlalchemy import select, delete
    from uuid import UUID
    
    try:
        doc_uuid = UUID(document_id)
        
        async with AsyncSessionLocal() as session:
            # Count chunks first
            count_query = select(Chunk).where(Chunk.document_id == doc_uuid)
            result = await session.execute(count_query)
            chunk_count = len(result.scalars().all())
            
            if chunk_count == 0:
                logger.info(f"No chunks found for document {document_id}")
                return 0
            
            # Delete all chunks (and their embeddings via CASCADE)
            delete_query = delete(Chunk).where(Chunk.document_id == doc_uuid)
            await session.execute(delete_query)
            await session.commit()
            
            logger.info(f"Deleted {chunk_count} chunks/embeddings for document {document_id}")
            return chunk_count
            
    except Exception as e:
        logger.error(f"Failed to cleanup embeddings for document {document_id}: {e}")
        return 0
