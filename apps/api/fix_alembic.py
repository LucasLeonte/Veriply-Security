import os
from sqlalchemy import create_engine, text

# Use the actual database URL from .env
database_url = 'postgresql://postgres:DarioDML@10.2.160.214:5432/vector_db'

engine = create_engine(database_url)
with engine.connect() as conn:
    # Remove any bad merge_heads_manual entry
    conn.execute(text("DELETE FROM alembic_version WHERE version_num = 'merge_heads_manual'"))
    conn.commit()
    
    # Show current versions
    result = conn.execute(text('SELECT * FROM alembic_version'))
    print("Current alembic versions in database:")
    for row in result:
        print(f"  - {row[0]}")
