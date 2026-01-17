import streamlit as st
import requests
import time

# --- CONFIG ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Dialysis Monitor", layout="wide")

# --- SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'selected_machine' not in st.session_state:
    st.session_state['selected_machine'] = None
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'live_mode' not in st.session_state: # New flag to control the loop
    st.session_state['live_mode'] = False

# --- HELPER FUNCTIONS ---
def login_user(username, password):
    try:
        res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            return True
        return False
    except:
        st.error("Cannot connect to Backend.")
        return False

# --- PAGE 1: LOGIN ---
def show_login():
    st.markdown("<h1 style='text-align: center;'>🏥 NephroCare Monitor</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.subheader("Doctor Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign In", use_container_width=True):
            if login_user(username, password):
                st.session_state['user'] = username
                st.session_state['page'] = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- PAGE 2: DASHBOARD ---
def show_dashboard():
    st.title(f"👨‍⚕️ Welcome, Dr. {st.session_state['user']}")
    
    # Auto-refresh button for the main dashboard (optional)
    if st.button("🔄 Refresh List"):
        st.rerun()
        
    st.markdown("---")
    
    # Fetch Machines from Backend
    try:
        machines = requests.get(f"{API_URL}/machines").json()
    except:
        st.error("Backend is offline.")
        machines = []

    if not machines:
        st.warning("No machines found.")
        return

    # Create a grid of cards
    cols = st.columns(3)
    for index, machine in enumerate(machines):
        with cols[index % 3]:
            status_emoji = "🟢 Active" if machine['is_active'] else "🔴 Offline"
            
            with st.container(border=True):
                st.markdown(f"### 🖥 {machine['machine_id']}")
                st.caption(f"📍 {machine['location']}")
                st.markdown(f"**Status:** {status_emoji}")
                
                # When clicked, we enter "Live Mode"
                if st.button(f"View Live Data", key=machine['machine_id']):
                    st.session_state['selected_machine'] = machine['machine_id']
                    st.session_state['live_mode'] = True 
                    st.session_state['page'] = 'details'
                    st.rerun()

# --- PAGE 3: DETAILS (LIVE) ---
def show_details():
    m_id = st.session_state['selected_machine']
    
    # Header area
    c1, c2 = st.columns([1, 8])
    with c1:
        # Button to STOP the loop and go back
        if st.button("⬅ Stop"):
            st.session_state['live_mode'] = False
            st.session_state['page'] = 'dashboard'
            st.rerun()
    with c2:
        st.title(f"Live Telemetry: {m_id}")

    # Create a placeholder. This container will be wiped and redrawn every second.
    live_container = st.empty()

    # THE LIVE LOOP
    while st.session_state['live_mode']:
        try:
            # 1. Fetch Data
            data = requests.get(f"{API_URL}/machine-status/{m_id}").json()
            
            # 2. Draw Inside the Placeholder
            with live_container.container():
                
                # --- ROW 1 (4 Columns) ---
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("🌡 Temp", f"{data.get('temperature', 0)} °C")
                k2.metric("💧 Flow Rate", f"{data.get('flow_rate', 0)} ml/min")
                k3.metric("🧪 pH Level", f"{data.get('ph', 0)}", "7.35-7.45")
                k4.metric("⚡ Conductivity", f"{data.get('conductivity', 0)} mS/cm")

                st.markdown("---") # Visual separator

                # --- ROW 2 (4 Columns for Alignment) ---
                # We use 4 columns again so 'Blood Leak' aligns perfectly under 'Temp'
                j1, j2, j3, j4 = st.columns(4)
                
                # Blood Leak Logic
                leak = data.get('blood_leak', False)
                status_text = "⚠️ LEAK DETECTED" if leak else "✅ SAFE"
                status_color = "inverse" if leak else "normal"
                j1.metric("🩸 Blood Leak", status_text, delta_color=status_color)

                j2.metric("🌫 Turbidity", f"{data.get('turbidity', 0)} NTU")
                
                # Volume Logic
                vol = data.get('total_volume', 0)
                vol_str = f"{vol/1000:.2f} L" if vol > 1000 else f"{vol:.0f} mL"
                j3.metric("📊 Total Vol", vol_str)
                
                j4.info(f"Last Update:\n{data.get('timestamp', '')[11:19]}") # Show Time Only

            # 3. Wait before next update (matches your simulator speed)
            time.sleep(2)
            
        except Exception as e:
            st.error(f"Connection lost: {e}")
            break

# --- MAIN CONTROLLER ---
if st.session_state['page'] == 'login':
    show_login()
elif st.session_state['page'] == 'dashboard':
    show_dashboard()
elif st.session_state['page'] == 'details':
    show_details()