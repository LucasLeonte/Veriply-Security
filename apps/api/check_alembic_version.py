import os
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/veriply')

engine = create_engine(database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM alembic_version'))
    print("Current alembic versions in database:")
    for row in result:
        print(f"  - {row[0]}")
