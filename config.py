import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'puneeth-vehicle-secret-key-fallback-2026')
    
    # MySQL Database Config - Primary reads from MYSQL_* environment variables
    MYSQL_HOST = os.getenv('MYSQL_HOST', os.getenv('DB_HOST', '127.0.0.1'))
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', os.getenv('DB_PORT', 3306)))
    MYSQL_USER = os.getenv('MYSQL_USER', os.getenv('DB_USER', 'root'))
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', os.getenv('DB_PASSWORD', 'puneeth@mysql'))
    MYSQL_DB = os.getenv('MYSQL_DATABASE', os.getenv('DB_NAME', 'puneeth_vehicle_services'))
    
    # Aliases
    DB_HOST = MYSQL_HOST
    DB_PORT = MYSQL_PORT
    DB_USER = MYSQL_USER
    DB_PASSWORD = MYSQL_PASSWORD
    DB_NAME = MYSQL_DB
    
    # Upload Folder for Hero Image & Media
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
