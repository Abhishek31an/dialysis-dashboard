import asyncio
import websockets
import json
import random

# Localhost URL
WS_URL = "wss://dialysis-backend.onrender.com/ws/machine/M1"

def get_data():
    return {
        "current_mA": round(random.uniform(100, 300), 1),
        "ph": round(random.uniform(6.8, 7.4), 2),
        "turbidity": int(random.uniform(0, 20)),
        "pressure_Pa": round(random.uniform(900, 1050), 1),
        "flow_rate": int(random.uniform(450, 550)),
        "temperature": round(random.uniform(36.5, 37.5), 1),
        "humidity": int(random.uniform(40, 60))
    }

async def run_persistent():
    while True:
        try:
            print(f"🔌 Connecting to {WS_URL}...")
            # ping_interval=None prevents timeouts during slow operations
            async with websockets.connect(WS_URL, ping_interval=None) as ws:
                print("✅ Connected! Streaming data...")
                
                while True:
                    data = get_data()
                    await ws.send(json.dumps(data))
                    print(f"📤 Sent Fast: Temp={data['temperature']}C")
                    
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.1)
                        cmd = json.loads(msg)
                        if "motor_speed" in cmd:
                            print(f"   ⚙️ Motor Speed: {cmd['motor_speed']}%")
                    except asyncio.TimeoutError:
                        pass
                    
                    # FAST SPEED: 0.5s
                    await asyncio.sleep(0.5)

        except Exception as e:
            print("❌ Connection Lost. Retrying...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(run_persistent())
    except KeyboardInterrupt:
        print("\n🛑 Stopped")