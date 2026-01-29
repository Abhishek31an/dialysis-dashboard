import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIG ---
API_URL = "https://dialysis-backend.onrender.com"

st.set_page_config(page_title="Dialysis Monitor", layout="wide", page_icon="🩸")

# --- CSS STYLING ---
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    div[data-testid="metric-container"] label {
        color: #aaaaaa;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE SETUP ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "latest_data" not in st.session_state:
    st.session_state.latest_data = {} # Start empty
if "logs_df" not in st.session_state:
    st.session_state.logs_df = pd.DataFrame()
if "last_log_update" not in st.session_state:
    st.session_state.last_log_update = 0
if "session" not in st.session_state:
    st.session_state.session = requests.Session()

# --- 1. LOGIN SCREEN (RESTORED) ---
if not st.session_state.authenticated:
    st.title("🔒 Login Portal")
    col1, col2 = st.columns([1, 2])
    with col1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                # Optional: You can check against backend API here
                resp = requests.post(f"{API_URL}/login", json={"username": u, "password": p})
                if resp.status_code == 200:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
            except:
                st.error("Backend Offline. Check uvicorn.")
    st.stop() # Stop here if not logged in

# --- 2. SIDEBAR ---
st.sidebar.title("⚙️ Controls")
st.sidebar.write(f"Logged in as: **abhishek**")
machine_id = st.sidebar.selectbox("Select Monitor", ["M1", "M2"])
st.sidebar.markdown("---")

st.sidebar.subheader("Motor Speed")
motor_val = st.sidebar.slider("Pump Speed (%)", 0, 100, 0)

if st.sidebar.button("Update Speed"):
    try:
        requests.post(f"{API_URL}/set-motor/{machine_id}", json={"speed": motor_val}, timeout=0.5)
        st.sidebar.success(f"Set to {motor_val}%")
    except:
        pass

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

# --- 3. MAIN DASHBOARD ---
st.title("🩸 Kidney Dialysis Monitor")
dashboard_placeholder = st.empty()

def render_ui():
    """Draws the UI using data from Memory"""
    data = st.session_state.latest_data
    df = st.session_state.logs_df
    
    with dashboard_placeholder.container():
        # Timestamp formatting
        ts = data.get("timestamp", "Waiting for Data...")
        if "T" in str(ts): ts = ts.replace("T", " ")[:19]

        # 2x4 Matrix
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1: st.metric("🕒 Last Update", ts)
        with r1c2: st.metric("⚡ Current", f"{data.get('current_mA', 0)} mA")
        with r1c3: st.metric("🌡 Temperature", f"{data.get('temperature', 0)} °C")
        with r1c4: st.metric("🧪 pH Level", f"{data.get('ph', 7.0)}")

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        with r2c1: st.metric("💧 Flow Rate", f"{data.get('flow_rate', 0)} ml/min")
        with r2c2: st.metric("🌫 Turbidity", f"{data.get('turbidity', 0)} NTU")
        with r2c3: st.metric("🔽 Pressure", f"{data.get('pressure_Pa', 0)} Pa")
        with r2c4: st.metric("☁️ Humidity", f"{data.get('humidity', 0)} %")

        st.markdown("---")
        
        # Logs Table
        st.subheader("📜 Recent Logs (Updates every 5s)")
        if not df.empty:
            cols = ["timestamp", "current_mA", "ph", "turbidity", 
                    "pressure_Pa", "flow_rate", "temperature", "humidity"]
            # Only show columns that actually exist
            valid_cols = [c for c in cols if c in df.columns]
            st.dataframe(df[valid_cols], use_container_width=True, hide_index=True)
        else:
            st.info("Loading logs from database...")

# Initial Draw
render_ui()

# --- 4. DATA FETCH LOOP ---
while True:
    try:
        # A. FAST LOOP: Get Status from RAM (Every 0.5s)
        try:
            resp = st.session_state.session.get(f"{API_URL}/machine-status/{machine_id}", timeout=0.2)
            if resp.status_code == 200:
                new_data = resp.json()
                # Only update if we actually got data, otherwise keep old data
                if "timestamp" in new_data or "temperature" in new_data:
                    st.session_state.latest_data = new_data
        except:
            pass # Keep showing old data if request fails

        # B. SLOW LOOP: Get History from DB (Every 5s)
        current_time = time.time()
        if current_time - st.session_state.last_log_update > 5.0:
            try:
                hist_resp = st.session_state.session.get(f"{API_URL}/history/{machine_id}", timeout=1.0)
                if hist_resp.status_code == 200:
                    st.session_state.logs_df = pd.DataFrame(hist_resp.json())
                    st.session_state.last_log_update = current_time
            except:
                pass

        # C. Redraw
        render_ui()
        time.sleep(0.5)

    except Exception as e:
        time.sleep(1)