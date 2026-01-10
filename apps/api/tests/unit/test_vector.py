import psycopg2
from pgvector.psycopg2 import register_vector

# --- CONFIGURATION ---
DB_HOST = "10.2.160.214"  # <--- Make sure this is still your IP
DB_NAME = "vector_db"
DB_USER = "postgres"
DB_PASS = "DarioDML"      # <--- Make sure this is your password
# ---------------------

try:
    # 1. Connect to the database
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    conn.autocommit = True
    
    # 2. Register the vector extension so Python understands it
    register_vector(conn)
    cur = conn.cursor()

    print("✅ Connected successfully!")

    # 3. Create a table with a 3-dimensional vector
    cur.execute("DROP TABLE IF EXISTS python_test;")
    cur.execute("CREATE TABLE python_test (id bigserial PRIMARY KEY, embedding vector(3));")
    print("✅ Table created.")

    # 4. Insert some dummy vectors
    cur.execute("INSERT INTO python_test (embedding) VALUES (%s), (%s)", ([1, 2, 3], [4, 5, 6]))
    print("✅ Data inserted.")

    # 5. Query: Find the nearest neighbor to [1, 2, 3]
    # We added ::vector so Postgres knows how to treat the input
    query_vec = [1, 2, 3]
    cur.execute("SELECT * FROM python_test ORDER BY embedding <-> %s::vector LIMIT 1;", (query_vec,))
    row = cur.fetchone()

    print(f"✅ Nearest neighbor found: ID={row[0]}, Vector={row[1]}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")