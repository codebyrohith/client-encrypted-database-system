from config.database import get_db_connection

def execute_query(query, params=None):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor
    except Exception as e:
        print(f"Database query error: {e}")
        return None
    finally:
        conn.close()

def fetch_one(query, params=None):
    cursor = execute_query(query, params)
    return cursor.fetchone() if cursor else None

def fetch_all(query, params=None):
    cursor = execute_query(query, params)
    return cursor.fetchall() if cursor else []
