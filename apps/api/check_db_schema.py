import os
from sqlalchemy import create_engine, text, inspect

database_url = 'postgresql://postgres:DarioDML@10.2.160.214:5432/vector_db'

engine = create_engine(database_url)
inspector = inspect(engine)

print("=== Tables in database ===")
tables = inspector.get_table_names()
for table in sorted(tables):
    print(f"  - {table}")

print("\n=== Checking specific columns ===")
if 'bots' in tables:
    columns = [col['name'] for col in inspector.get_columns('bots')]
    print(f"Bots columns: {', '.join(columns)}")
    print(f"  - Has welcome_message: {'welcome_message' in columns}")
    print(f"  - Has primary_color: {'primary_color' in columns}")
    
if 'widget_configs' in tables:
    columns = [col['name'] for col in inspector.get_columns('widget_configs')]
    print(f"\nWidget_configs columns: {', '.join(columns)}")
    print(f"  - Has welcome_message: {'welcome_message' in columns}")
    print(f"  - Has primary_color: {'primary_color' in columns}")
