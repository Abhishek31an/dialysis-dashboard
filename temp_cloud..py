import os
import mysql.connector
from dotenv import load_dotenv

# 1. Load the secrets from .env file
load_dotenv()

print("🔌 Attempting to connect to TiDB Cloud...")

try:
    # 2. Connect using the secrets
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "test"),
        # FIX: Just tell it to use SSL, but don't panic about the verify path
        ssl_disabled=False 
    )
    
    if conn.is_connected():
        print("✅ SUCCESS! Connected to Cloud Database.")
        print(f"Server Info: {conn.get_server_info()}")
        conn.close()

except mysql.connector.Error as err:
    print("❌ FAILED to connect.")
    print(f"Error Code: {err.errno}")
    print(f"Message: {err.msg}")
    
except Exception as e:
    print(f"General Error: {e}")