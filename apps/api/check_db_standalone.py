import asyncio
import os
from sqlalchemy import Column, String, Boolean, DateTime, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid

# Define Base and Model inline to avoid import issues
Base = declarative_base()

class EmailIntegration(Base):
    __tablename__ = "email_integrations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    provider = Column(String, nullable=False)
    encrypted_refresh_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

# Connection string from typical .env or default (adjust if needed)
# Using the standard local connection string for the project
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/veriply"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        try:
            result = await session.execute(select(EmailIntegration))
            integrations = result.scalars().all()
            print(f"Found {len(integrations)} integrations")
            for i in integrations:
                print(f"ID: {i.id}")
                print(f"Provider: {i.provider}")
                print(f"User: {i.user_id}")
                print(f"Active: {i.is_active}")
                print(f"Has Refresh Token: {i.encrypted_refresh_token is not None}")
                if i.encrypted_refresh_token is None:
                     print("  -> WARNING: Refresh token is MISSING!")
                print("-" * 20)
        except Exception as e:
            print(f"Error querying database: {e}")
        finally:
            await session.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
