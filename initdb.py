# from db import init_db

# init_db()
# # print("✅ All tables ensured!")

from db import get_conn
# --- DB Connection ---
conn = get_conn()
cursor = conn.cursor()
# cursor.execute("DELETE FROM vendors WHERE name ='tile'")
# conn.commit()


# cursor.execute("SELECT id , name, value FROM config")
# config = dict(cursor.fetchall())
# print(config)