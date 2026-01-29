from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import mysql.connector
from mysql.connector import pooling # <--- NEW: Pooling Library
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "ssl_disabled": False,
    "connection_timeout": 10
}

# --- 1. CONNECTION POOL (The "Bank" of Connections) ---
# We create 5 permanent connections to reuse safely.
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="dialysis_pool",
        pool_size=5,  # Allow 5 parallel operations
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("✅ Database Connection Pool Created")
except Exception as e:
    print(f"❌ Failed to create Pool: {e}")
    connection_pool = None

# --- GLOBAL STATE ---
motor_controls = {"M1": 0, "M2": 0}
realtime_cache = {}       
last_db_save_time = {}    

def get_db_connection():
    """Borrows a connection from the pool"""
    if not connection_pool:
        return None
    try:
        return connection_pool.get_connection()
    except Exception as e:
        print(f"⚠️ Pool Exhausted: {e}")
        return None

# --- BACKGROUND DB SAVE (Thread-Safe) ---
def save_data_sync(machine_id, data):
    conn = None
    try:
        # Borrow connection
        conn = get_db_connection()
        if not conn: return

        cursor = conn.cursor()
        query = """
            INSERT INTO sensor_logs 
            (machine_id, current_mA, ph, turbidity, pressure_Pa, 
             flow_rate, temperature, humidity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            machine_id,
            data.get("current_mA", 0),
            data.get("ph", 7.0),
            data.get("turbidity", 0),
            data.get("pressure_Pa", 0),
            data.get("flow_rate", 0),
            data.get("temperature", 0),
            data.get("humidity", 0)
        ))
        conn.commit()
        cursor.close()
        # Connection is automatically returned to pool when closed
        conn.close() 
        print(f"💾 Saved {machine_id}") 

    except Exception as e:
        print(f"⚠️ Save Error: {e}")
        if conn:
            try: conn.close() # Ensure we return it even on error
            except: pass

# --- ENDPOINTS ---

@app.post("/login")
def login(data: dict):
    if data["username"] == "abhishek" and data["password"] == "123456":
        return {"status": "success", "user": "abhishek"}
    raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.post("/set-motor/{machine_id}")
def set_motor(machine_id: str, data: dict):
    motor_controls[machine_id] = data.get("speed", 0)
    return {"message": "Speed set"}

@app.get("/machine-status/{machine_id}")
def get_status(machine_id: str):
    # RAM ONLY - Fast
    if machine_id in realtime_cache:
        return realtime_cache[machine_id]
    return {"timestamp": "Waiting for Data..."}

@app.get("/history/{machine_id}")
def get_history(machine_id: str):
    conn = None
    try:
        conn = get_db_connection()
        if not conn: return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT timestamp, current_mA, ph, turbidity, pressure_Pa, 
                   flow_rate, temperature, humidity
            FROM sensor_logs 
            WHERE machine_id = %s 
            ORDER BY timestamp DESC LIMIT 50
        """, (machine_id,))
        data = cursor.fetchall()
        cursor.close()
        conn.close() # Return to pool
        return data
    except Exception as e:
        print(f"Read Error: {e}")
        if conn: conn.close()
        return []

# --- WEBSOCKET ---
@app.websocket("/ws/machine/{machine_id}")
async def websocket_endpoint(websocket: WebSocket, machine_id: str):
    await websocket.accept()
    print(f"✅ {machine_id} Connected")
    
    try:
        while True:
            # 1. Receive
            raw = await websocket.receive_text()
            data = json.loads(raw)
            
            # 2. Update RAM
            realtime_cache[machine_id] = data 
            
            # 3. Save to DB (Every 2s)
            current_time = time.time()
            last_save = last_db_save_time.get(machine_id, 0)
            
            if current_time - last_save > 2.0:
                await run_in_threadpool(save_data_sync, machine_id, data)
                last_db_save_time[machine_id] = current_time
            
            # 4. Motor
            target = motor_controls.get(machine_id, 0)
            await websocket.send_text(json.dumps({"motor_speed": target}))

    except WebSocketDisconnect:
        print(f"❌ {machine_id} Disconnected")