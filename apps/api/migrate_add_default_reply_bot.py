"""
Migration script to add default_reply_bot_id column to email_integrations.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as session:
        try:
            # Add default_reply_bot_id column if it doesn't exist
            await session.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='email_integrations' 
                        AND column_name='default_reply_bot_id'
                    ) THEN
                        ALTER TABLE email_integrations 
                        ADD COLUMN default_reply_bot_id UUID REFERENCES bots(id);
                    END IF;
                END $$;
            """))
            await session.commit()
            print("✓ Migration complete: default_reply_bot_id added to email_integrations")
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(main())
