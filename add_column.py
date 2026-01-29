import mysql.connector
import os
from dotenv import load_dotenv

# Load your password from the .env file
load_dotenv()

def fix_database():
    print("🔌 Connecting to TiDB Cloud...")
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )
        cursor = connection.cursor()

        # 1. Add Heart Rate Column
        print("🛠  Adding 'heart_rate' column...")
        try:
            cursor.execute("ALTER TABLE sensor_logs ADD COLUMN heart_rate FLOAT DEFAULT 0;")
            print("✅ 'heart_rate' column added.")
        except mysql.connector.Error as err:
            print(f"⚠️  Note: {err}")

        # 2. Add Flow Rate Column (Just in case it's missing too)
        print("🛠  Adding 'flow_rate' column...")
        try:
            cursor.execute("ALTER TABLE sensor_logs ADD COLUMN flow_rate FLOAT DEFAULT 0;")
            print("✅ 'flow_rate' column added.")
        except mysql.connector.Error as err:
            print(f"⚠️  Note: {err}")

        connection.commit()
        cursor.close()
        connection.close()
        print("\n🎉 Database Schema Updated Successfully!")

    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")
        print("Check your .env file and internet connection.")

if __name__ == "__main__":
    fix_database()