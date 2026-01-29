import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def fix_schema():
    print("🔌 Connecting to TiDB...")
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor()

        # We need these specific columns for your 8-point data
        columns = [
            "current_mA FLOAT DEFAULT 0",
            "ph FLOAT DEFAULT 7.0",
            "turbidity FLOAT DEFAULT 0",
            "pressure_Pa FLOAT DEFAULT 0",
            "flow_rate FLOAT DEFAULT 0",
            "temperature FLOAT DEFAULT 0",
            "humidity FLOAT DEFAULT 0"
            # Timestamp already exists by default in SQL
        ]

        print("🛠  Adding missing columns...")
        for col in columns:
            try:
                cursor.execute(f"ALTER TABLE sensor_logs ADD COLUMN {col};")
                print(f"   ✅ Added: {col.split()[0]}")
            except mysql.connector.Error as err:
                # If column exists, just ignore
                pass

        # Add motor control support
        try:
            cursor.execute("ALTER TABLE machines ADD COLUMN motor_speed INT DEFAULT 0;")
        except:
            pass

        conn.commit()
        conn.close()
        print("\n🎉 Database Ready for 2x4 Matrix Data!")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    fix_schema()