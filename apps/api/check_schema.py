from sqlalchemy import text, create_engine

engine = create_engine('postgresql://postgres:DarioDML@10.2.160.214:5432/vector_db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position"))
    rows = result.fetchall()
    print('Documents table columns:')
    for row in rows:
        print(f'  {row[0]}: {row[1]}')
