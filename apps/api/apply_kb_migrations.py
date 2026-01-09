"""Apply migrations 019, 020, 021 manually"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@10.2.160.214:5432/vector_db')
if not DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)

async def apply_migrations():
    async with engine.begin() as conn:
        print("Creating user_email_history table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_email_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id),
                user_id UUID NOT NULL REFERENCES users(id),
                integration_id UUID NOT NULL REFERENCES email_integrations(id),
                email_id VARCHAR NOT NULL,
                subject VARCHAR,
                body TEXT,
                sent_at TIMESTAMP,
                analyzed BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_email_id_per_integration UNIQUE (integration_id, email_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_email_history_tenant_user 
                ON user_email_history(tenant_id, user_id);
            CREATE INDEX IF NOT EXISTS idx_user_email_history_integration 
                ON user_email_history(integration_id);
            CREATE INDEX IF NOT EXISTS idx_user_email_history_analyzed 
                ON user_email_history(analyzed);
            
            ALTER TABLE user_email_history ENABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS user_email_history_tenant_isolation ON user_email_history;
            CREATE POLICY user_email_history_tenant_isolation
                ON user_email_history
                FOR ALL
                USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
                WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """))
        print("✓ user_email_history created")
        
        print("Creating user_writing_styles table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_writing_styles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id),
                user_id UUID NOT NULL REFERENCES users(id),
                integration_id UUID NOT NULL REFERENCES email_integrations(id),
                tone VARCHAR(20) NOT NULL DEFAULT 'semi_formal',
                greeting_pattern VARCHAR(100),
                closing_pattern VARCHAR(100),
                avg_sentence_length INTEGER,
                avg_email_length INTEGER,
                uses_emojis BOOLEAN NOT NULL DEFAULT FALSE,
                formality_score INTEGER NOT NULL DEFAULT 65,
                custom_preferences JSONB NOT NULL DEFAULT '{}',
                is_manual_override BOOLEAN NOT NULL DEFAULT FALSE,
                sample_count INTEGER NOT NULL DEFAULT 0,
                last_analyzed_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_style_per_integration UNIQUE (user_id, integration_id, tenant_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_writing_style_tenant_user 
                ON user_writing_styles(tenant_id, user_id);
            CREATE INDEX IF NOT EXISTS idx_user_writing_style_integration 
                ON user_writing_styles(integration_id);
            
            ALTER TABLE user_writing_styles ENABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS user_writing_style_tenant_isolation ON user_writing_styles;
            CREATE POLICY user_writing_style_tenant_isolation
                ON user_writing_styles
                FOR ALL
                USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
                WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """))
        print("✓ user_writing_styles created")
        
        print("Creating kb_emails table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kb_emails (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                integration_id UUID NOT NULL REFERENCES email_integrations(id) ON DELETE CASCADE,
                email_id VARCHAR NOT NULL,
                thread_id VARCHAR,
                subject VARCHAR(500),
                from_email VARCHAR(255),
                to_emails TEXT,
                body_text TEXT,
                sent_at TIMESTAMP,
                embedding VECTOR(768),
                email_metadata JSONB,
                status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
                processed_at TIMESTAMP,
                chunk_count VARCHAR,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_kb_emails_tenant_group 
                ON kb_emails(tenant_id, group_id);
            CREATE INDEX IF NOT EXISTS idx_kb_emails_integration 
                ON kb_emails(integration_id);
            CREATE INDEX IF NOT EXISTS idx_kb_emails_status 
                ON kb_emails(status);
            CREATE INDEX IF NOT EXISTS idx_kb_emails_email_id 
                ON kb_emails(email_id);
            CREATE INDEX IF NOT EXISTS idx_kb_emails_sent_at 
                ON kb_emails(sent_at);
        """))
        print("✓ kb_emails table created")
        
        print("Creating vector index...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_kb_emails_embedding 
                ON kb_emails 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
        """))
        print("✓ Vector index created")
        
        print("Enabling RLS on kb_emails...")
        await conn.execute(text("""
            ALTER TABLE kb_emails ENABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS kb_emails_tenant_isolation ON kb_emails;
            CREATE POLICY kb_emails_tenant_isolation
                ON kb_emails
                USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE));
        """))
        print("✓ RLS enabled")
        
        print("\n✅ All migrations applied successfully!")

if __name__ == '__main__':
    asyncio.run(apply_migrations())
