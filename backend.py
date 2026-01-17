from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "test"),
    "ssl_disabled": False
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

class LoginRequest(BaseModel):
    username: str
    password: str

class SensorData(BaseModel):
    temperature: float
    flow_rate: float
    turbidity: float
    ph: float                
    conductivity: float      
    blood_leak: bool        
    total_volume: float      

@app.get("/")
def home():
    return {"message": "Dialysis Backend is Running!"}

@app.post("/login")
def login(request: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    
    query = "SELECT * FROM doctors WHERE username = %s AND password = %s"
    cursor.execute(query, (request.username, request.password))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        return {"status": "success", "user": user['username']}
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
@app.get("/machines")
def get_machines():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM machines")
    machines = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return machines

@app.post("/update-machine/{machine_id}")
def update_machine(machine_id: str, data: SensorData):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        log_query = """
        INSERT INTO sensor_logs 
        (machine_id, temperature, flow_rate, turbidity, ph, conductivity, blood_leak, total_volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(log_query, (
            machine_id, 
            data.temperature, 
            data.flow_rate, 
            data.turbidity,
            data.ph,
            data.conductivity,
            data.blood_leak,
            data.total_volume
        ))
        
        status_query = "UPDATE machines SET is_active = 1 WHERE machine_id = %s"
        cursor.execute(status_query, (machine_id,))
        
        conn.commit()
        return {"message": "Data logged successfully"}

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail=str(err))
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
@app.get("/machine-status/{machine_id}")
def get_status(machine_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT * FROM sensor_logs 
    WHERE machine_id = %s 
    ORDER BY timestamp DESC 
    LIMIT 1
    """
    cursor.execute(query, (machine_id,))
    data = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if data:
        return data
    else:
        return {"temperature": 0, "flow_rate": 0, "turbidity": 0}