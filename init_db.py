import mysql.connector
import os
from dotenv import load_dotenv

# 1. Load secrets from .env
load_dotenv()

def create_tables():
    conn = None
    cursor = None
    try:
        print("☁️ Connecting to TiDB Cloud...")
        # 2. Connect using .env variables
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "test"),
            ssl_disabled=False
        )
        cursor = conn.cursor()
        print("✅ Connected! Creating tables...")

        # 3. Create Doctors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(50) NOT NULL
        )
        """)

        # 4. Create Machines Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            machine_id VARCHAR(20) PRIMARY KEY,
            location VARCHAR(100),
            is_active BOOLEAN DEFAULT FALSE
        )
        """)

        # 5. Create Logs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            machine_id VARCHAR(20),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature FLOAT,
            flow_rate FLOAT,
            turbidity FLOAT,
            ph FLOAT,
            conductivity FLOAT,
            blood_leak BOOLEAN,
            total_volume FLOAT,
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        )
        """)

        # 6. Insert Dummy Data (Only if they don't exist)
        # Note: We use IGNORE to avoid errors if you run this twice
        cursor.execute("INSERT IGNORE INTO doctors (username, password) VALUES ('abhishek', '123456')")
        cursor.execute("INSERT IGNORE INTO machines (machine_id, location, is_active) VALUES ('M1', 'ICU Bed 1', 1)")
        cursor.execute("INSERT IGNORE INTO machines (machine_id, location, is_active) VALUES ('M2', 'Gen Ward 4', 0)")

        conn.commit()
        print("🎉 Success! Cloud Tables created and Data initialized.")
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    create_tables()