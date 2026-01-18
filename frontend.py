import streamlit as st
import requests
import pandas as pd
import time

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
# Replace this with your actual Render Backend URL
API_URL = "https://dialysis-backend.onrender.com"

st.set_page_config(
    page_title="Dialysis Remote Monitor",
    page_icon="🏥",
    layout="wide"
)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def get_machines():
    """Fetch the list of active machines from the backend."""
    try:
        response = requests.get(f"{API_URL}/machines")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_latest_data(machine_id):
    """Fetch the single most recent data point for the live cards."""
    try:
        response = requests.get(f"{API_URL}/data/{machine_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_history_data(machine_id):
    """Fetch the last 100 data points for the trend graphs."""
    try:
        response = requests.get(f"{API_URL}/history/{machine_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# -----------------------------------------------------------------------------
# MAIN DASHBOARD UI
# -----------------------------------------------------------------------------

st.title("🏥 Renal Care - Remote Dialysis Monitor")
st.markdown("Real-time telemetry and trend monitoring for ICU Units.")
st.divider()

# --- SIDEBAR: Machine Selection ---
st.sidebar.header("Control Panel")
machines = get_machines()

if not machines:
    st.warning("⚠️ No machines detected. Please run the simulator.")
    st.stop() # Stop execution if no machines

# Create a dropdown to select a machine
machine_ids = [m['machine_id'] for m in machines]
selected_machine = st.sidebar.selectbox("Select Patient Monitor:", machine_ids)

# Add a manual refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# --- MAIN DISPLAY ---

# 1. Fetch Data
current_data = get_latest_data(selected_machine)
history_data = get_history_data(selected_machine)

# 2. Display Live Metrics (The "Now" View)
st.subheader(f"📍 Live Status: {selected_machine}")

if current_data:
    # Create 3 columns for big numbers
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🌡️ Temperature",
            value=f"{current_data.get('temperature', 0)} °F",
            delta="Normal" if 97 < current_data.get('temperature', 0) < 99 else "Warning",
            delta_color="normal" if 97 < current_data.get('temperature', 0) < 99 else "inverse"
        )
    
    with col2:
        st.metric(
            label="❤️ Heart Rate",
            value=f"{current_data.get('heart_rate', 0)} BPM",
            delta="-2 bpm" # You can make this dynamic later
        )
        
    with col3:
        st.metric(
            label="💧 Flow Rate",
            value=f"{current_data.get('flow_rate', 0)} ml/min"
        )
else:
    st.info("Waiting for data stream...")

# 3. Display History Graphs (The "Trend" View)
st.divider()
st.subheader("📈 Patient Trends (Last 100 Readings)")

if history_data:
    # Convert the JSON list to a Pandas DataFrame (Excel sheet format)
    df = pd.DataFrame(history_data)
    
    # Convert timestamp string to datetime objects for better graphing
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Create Tabs for different graphs to keep UI clean
    tab1, tab2, tab3 = st.tabs(["Temperature History", "Heart Rate History", "Raw Data Log"])

    with tab1:
        st.write("Temperature vs Time")
        # Line chart using 'timestamp' as X-axis and 'temperature' as Y-axis
        st.line_chart(df, x="timestamp", y="temperature", color="#FF4B4B") # Red color

    with tab2:
        st.write("Heart Rate vs Time")
        st.line_chart(df, x="timestamp", y="heart_rate", color="#0068C9") # Blue color

    with tab3:
        st.write("Detailed Data Logs")
        st.dataframe(df)

else:
    st.write("No history data available yet.")

# -----------------------------------------------------------------------------
# AUTO-REFRESH LOGIC
# -----------------------------------------------------------------------------
# This keeps the dashboard updating every 2 seconds automatically
time.sleep(2)
st.rerun()