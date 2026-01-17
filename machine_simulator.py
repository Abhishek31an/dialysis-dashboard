import requests
import time
import random

API_URL = "https://dialysis-backend.onrender.com"
machine_state = {
    "M1": {"total_vol": 0.0},
    "M2": {"total_vol": 0.0}
}

def generate_data(machine_id):
    flow_rate = round(random.uniform(250, 400), 0)  
    volume_added = (flow_rate / 60) * 2 
    machine_state[machine_id]["total_vol"] += volume_added
    is_leaking = True if random.random() < 0.01 else False
    
    return {
        "temperature": round(random.uniform(36, 38), 1),     
        "flow_rate": flow_rate,
        "turbidity": round(random.uniform(0.1, 0.4), 2),         
        "ph": round(random.uniform(7, 7.45), 2),              
        "conductivity": round(random.uniform(13, 15), 1),    
        "blood_leak": is_leaking,
        "total_volume": round(machine_state[machine_id]["total_vol"], 1)
    }

print("🚑 Dialysis Machine Simulator Started...")
print(f"Targeting Backend at: {API_URL}")
print("Press Ctrl+C to stop.\n")

while True:
    try:
        data_m1 = generate_data("M1")
        response = requests.post(f"{API_URL}/update-machine/M1", json=data_m1)
        
        if response.status_code == 200:
            print(f"✅ [M1] Sent: Flow={data_m1['flow_rate']} | Vol={data_m1['total_volume']}mL")
        else:
            print(f"❌ [M1] Failed: {response.text}")
        data_m2 = generate_data("M2")
        data_m2['temperature'] = round(random.uniform(37.0, 38.0), 1) 
        
        requests.post(f"{API_URL}/update-machine/M2", json=data_m2)
        print(f"✅ [M2] Sent: Flow={data_m2['flow_rate']} | Vol={data_m2['total_volume']}mL")

        print("-" * 30) 

    except Exception as e:
        print(f"⚠️ Error: Backend seems offline. Is it running? ({e})")
        
    time.sleep(2) 