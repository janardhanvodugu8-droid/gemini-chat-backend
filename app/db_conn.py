import psycopg2
from app.config import DATABASE_URL  # import your DATABASE_URL from config.py

def get_conn():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL is not set in environment variables")
    
    conn = psycopg2.connect(DATABASE_URL)
    # Ensure autocommit is off for explicit transaction control
    conn.autocommit = False
    return conn

