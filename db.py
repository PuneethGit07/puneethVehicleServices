import os
import pymysql
import pymysql.cursors
from config import Config

def init_db():
    """
    Ensures the MySQL database 'puneeth_vehicle_services' exists,
    and runs database.sql schema if tables are missing.
    """
    # 1. Connect to MySQL server without database specified
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset='utf8mb4',
        autocommit=True
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    finally:
        conn.close()

    # 2. Check if main tables exist in the database
    conn_db = get_db_connection()
    try:
        with conn_db.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tables = [list(r.values())[0] for r in cur.fetchall()]
            
        required_tables = ['customers', 'vehicles', 'services', 'payments', 'users']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.sql')
            if os.path.exists(sql_file):
                with open(sql_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # Execute multi-statements schema
                conn_multi = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
                )
                try:
                    with conn_multi.cursor() as cur:
                        cur.execute(schema_sql)
                    conn_multi.commit()
                finally:
                    conn_multi.close()
    finally:
        conn_db.close()

def get_db_connection():
    """
    Establish a connection to the MySQL database.
    Uses DictCursor so results are returned as python dictionaries.
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

def query_db(query, args=(), one=False):
    """
    Execute a read query and return dictionary results.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            result = cursor.fetchall()
            return (result[0] if result else None) if one else result
    finally:
        conn.close()

def execute_db(query, args=(), return_id=False):
    """
    Execute an INSERT, UPDATE, or DELETE query.
    Commits transaction and returns affected rows or lastrowid.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            last_id = cursor.lastrowid
            affected = cursor.rowcount
        conn.commit()
        return last_id if return_id else affected
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def check_db_connection():
    """
    Check if MySQL is reachable and tables exist.
    """
    try:
        init_db()
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.execute("SHOW TABLES;")
            tables = [list(r.values())[0] for r in cursor.fetchall()]
        conn.close()
        return True, f"Connected to MySQL! Found {len(tables)} tables: {', '.join(tables)}"
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    print("----------------------------------------------------------")
    print("Testing MySQL Server Connection...")
    print(f"Host: {Config.MYSQL_HOST}")
    print(f"Port: {Config.MYSQL_PORT}")
    print(f"User: {Config.MYSQL_USER}")
    print(f"Database: {Config.MYSQL_DB}")
    print("Password read from environment variable: MYSQL_PASSWORD")
    print("----------------------------------------------------------")
    
    ok, msg = check_db_connection()
    if ok:
        print("[SUCCESS]", msg)
        # Check record counts
        for t in ['customers', 'vehicles', 'services', 'payments', 'users']:
            try:
                cnt = query_db(f"SELECT COUNT(*) AS c FROM {t}", one=True)['c']
                print(f" - Table '{t}': {cnt} records")
            except Exception as e:
                print(f" - Table '{t}': error ({e})")
    else:
        print("[FAILED]", msg)
