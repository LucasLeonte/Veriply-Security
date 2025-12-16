from sqlalchemy import text, create_engine

engine = create_engine('postgresql://postgres:DarioDML@10.2.160.214:5432/vector_db')

with engine.connect() as conn:
    # Add mime column
    conn.execute(text("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='mime') THEN
                ALTER TABLE documents ADD COLUMN mime VARCHAR(100);
            END IF;
        END $$;
    """))
    
    # Add size column
    conn.execute(text("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='size') THEN
                ALTER TABLE documents ADD COLUMN size INTEGER;
            END IF;
        END $$;
    """))
    
    # Add storage_path column
    conn.execute(text("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='storage_path') THEN
                ALTER TABLE documents ADD COLUMN storage_path TEXT;
            END IF;
        END $$;
    """))
    
    # Add uploaded_by column
    conn.execute(text("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='uploaded_by') THEN
                ALTER TABLE documents ADD COLUMN uploaded_by UUID REFERENCES users(id);
            END IF;
        END $$;
    """))
    
    conn.commit()
    print("✓ Missing columns added successfully")

# Verify the changes
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position"))
    rows = result.fetchall()
    print('\nUpdated Documents table columns:')
    for row in rows:
        print(f'  {row[0]}: {row[1]}')
