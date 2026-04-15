import streamlit as st
import requests
import urllib.parse

# --- 1. TACTICAL HUD UI (NEW VIBE) ---
st.set_page_config(page_title="G.R.E.G. HUD", layout="wide")

st.markdown("""
    <style>
    /* Kill Streamlit UI */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    
    /* Background: Deep Slate with Scanlines */
    .stApp { 
        background-color: #020202; 
        background-image: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        background-size: 100% 2px, 3px 100%;
        color: #00ffcc; 
        font-family: 'Courier New', monospace;
    }

    /* Tactical Header */
    .hud-header {
        border-bottom: 2px solid #00ffcc;
        padding: 10px;
        text-align: left;
        font-weight: bold;
        letter-spacing: 5px;
        text-shadow: 0 0 10px #00ffcc;
    }

    /* Execution Box (The Fix for the missing button) */
    .execution-unit {
        background: rgba(0, 255, 204, 0.1);
        border: 2px solid #00ffcc;
        padding: 20px;
        margin: 20px 0;
        border-radius: 0px; /* Sharp edges for tactical vibe */
        clip-path: polygon(0% 0%, 100% 0%, 100% 80%, 95% 100%, 0% 100%);
    }

    .msg-greg { color: #00ffcc; margin-bottom: 10px; border-left: 2px solid #00ffcc; padding-left: 10px; }
    .msg-user { color: #ffffff; opacity: 0.7; text-align: right; margin-bottom: 10px; }
    
    /* Input Styling */
    .stChatInput { border-top: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BRAIN ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def greg_brain(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.4
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "CORE LINK OFFLINE."

# --- 3. PERSISTENT STATE ---
if "history" not in st.session_state:
    st.session_state.history = []
if "active_link" not in st.session_state:
    st.session_state.active_link = None
if "link_label" not in st.session_state:
    st.session_state.link_label = None

# --- 4. HUD INTERFACE ---
st.markdown('<div class="hud-header">SYSTEM: G.R.E.G. // VER 4.0</div>', unsafe_allow_html=True)

# Display active execution units (THE FIX)
if st.session_state.active_link:
    with st.container():
        st.markdown(f'<div class="execution-unit"><b>PRIORITY UPLINK:</b> {st.session_state.link_label}</div>', unsafe_allow_html=True)
        if st.link_button(f"EXECUTE: {st.session_state.link_label}", st.session_state.active_link):
            st.session_state.active_link = None # Clear after use
            st.rerun()

# Display Chat History
for m in st.session_state.history:
    cls = "msg-user" if m["role"] == "user" else "msg-greg"
    st.markdown(f'<div class="{cls}">{m["content"]}</div>', unsafe_allow_html=True)

# Tactical Input
prompt = st.chat_input("ENTER SYSTEM COMMAND...")

if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    cmd = prompt.lower()
    
    # Logic: Search/Actions
    if "marketplace" in cmd:
        item = cmd.replace("search marketplace for", "").replace("search", "").strip()
        st.session_state.active_link = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(item)}"
        st.session_state.link_label = f"MARKETPLACE SCAN [{item.upper()}]"
        st.session_state.history.append({"role": "assistant", "content": f"Sir, I have established a search perimeter for {item}. Execute the priority uplink above."})
        
    elif "instagram" in cmd or "message" in cmd:
        st.session_state.active_link = "https://www.instagram.com/direct/inbox/"
        st.session_state.link_label = "INSTAGRAM UPLINK"
        st.session_state.history.append({"role": "assistant", "content": "Instagram protocols engaged. Awaiting manual execution."})
        
    else:
        with st.spinner("COMMUNICATING..."):
            ctx = [{"role": "system", "content": "You are GREG, a tactical AI assistant. Sharp, concise, professional. Refer to user as Sir."}]
            ctx.extend(st.session_state.history[-6:])
            ans = greg_brain(ctx)
            st.session_state.history.append({"role": "assistant", "content": ans})
    
    st.rerun()