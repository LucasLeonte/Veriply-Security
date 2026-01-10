import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import init_db, AsyncSessionLocal
from app.core.settings import settings
from app.services.profile_service import cleanup_inactive_users
from app.workers.retention import run_all_retention_jobs
from app.workers.email_poller import run_periodic as start_email_poller

# Check for new relic or other monitoring hooks if needed

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

async def run_cleanup():
    """Run the inactive users cleanup task."""
    logger.info("Starting inactive users cleanup...")
    async with AsyncSessionLocal() as session:
        await cleanup_inactive_users(session, days=30)
    logger.info("Inactive users cleanup completed.")

async def run_retention():
    """Run all data retention cleanup jobs."""
    logger.info("Starting retention jobs...")
    async with AsyncSessionLocal() as session:
        await run_all_retention_jobs(session)
    logger.info("Retention jobs completed.")

async def main():
    logger.info("Starting Veriply Background Worker...")
    
    # Initialize DB (creates pool) - API handles schema creation
    # await init_db()
    
    # Scheduler for Cron Tasks
    scheduler = AsyncIOScheduler()
    
    # Cleanup Inactive Users: Daily at 2:00 AM UTC
    scheduler.add_job(run_cleanup, "cron", hour=2, minute=0, id="cleanup_inactive_users")
    
    # Retention Jobs: Daily at 2:05 AM UTC
    scheduler.add_job(run_retention, "cron", hour=2, minute=5, id="cleanup_retention_data")
    
    scheduler.start()
    logger.info("Scheduler started with jobs: cleanup_inactive_users, cleanup_context")
    
    # Run Email Poller (Loops forever)
    logger.info("Starting Email Poller...")
    try:
        await start_email_poller(AsyncSessionLocal, settings.EMAIL_POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("Worker cancelled.")
    except Exception as e:
        logger.exception(f"Worker crashed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
