import sqlite3
from config import DB_PATHS, ADMIN_ID

def get_connection(role):
    if role == "master":
        db_path = DB_PATHS["psychologist"].parent / "master.db"
    elif role in DB_PATHS:
        db_path = DB_PATHS[role]
    else:
        raise ValueError(f"Неизвестная БД: {role}")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_all_databases():
    master_path = DB_PATHS["psychologist"].parent / "master.db"
    conn_master = sqlite3.connect(master_path, check_same_thread=False)
    cur = conn_master.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
    cur.execute("SELECT * FROM admins WHERE user_id = ?", (ADMIN_ID,))
    if not cur.fetchone():
        cur.execute("INSERT INTO admins (user_id) VALUES (?)", (ADMIN_ID,))
        print(f"Admin {ADMIN_ID} added.")
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (ADMIN_ID, "SuperAdmin"))
    conn_master.commit()
    conn_master.close()
    print("Master DB ready.")

    roles = ["psychologist", "programmer", "adult", "general", "writer", "assistant"]
    for role in roles:
        conn = get_connection(role)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS dialogs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, message_text TEXT, response_text TEXT, rating INTEGER DEFAULT NULL, retry_count INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
        conn.close()
        print(f"DB {role} ready.")

    conn_m = get_connection("madina")
    c_m = conn_m.cursor()
    c_m.execute("CREATE TABLE IF NOT EXISTS training_data (id INTEGER PRIMARY KEY AUTOINCREMENT, source_role TEXT, user_id INTEGER, prompt TEXT, completion TEXT, quality_score INTEGER)")
    conn_m.commit()
    conn_m.close()
    print("Madina DB ready.")
    print("All databases initialized!")
