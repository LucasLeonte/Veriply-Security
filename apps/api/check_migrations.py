"""Check alembic_version table"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@10.2.160.214:5432/vector_db')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num'))
    versions = [r[0] for r in result]
    print('Applied migrations:')
    for v in versions:
        print(f'  - {v}')
