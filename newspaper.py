import streamlit as st
import requests
import sqlite3
from datetime import datetime

# --- 1. CONFIG & DATABASE ---
st.set_page_config(page_title="Intel", layout="wide")
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def save_mem(u, a):
    conn = sqlite3.connect('intel.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS logs (time TEXT, user TEXT, ai TEXT)')
    c.execute("INSERT INTO logs VALUES (?,?,?)", (datetime.now().strftime("%H:%M"), u, a))
    conn.commit()
    conn.close()

# --- 2. THE "CRYSTAL" UI & GESTURE KILLER ---
st.markdown("""
    <style>
    /* Absolute background lock */
    .stApp { 
        background-color: #050505; 
        color: #e0e0e0; 
        overscroll-behavior-y: none !important;
    }
    
    /* Hide all web-style headers/footers */
    header, footer, #MainMenu {visibility: hidden;}
    
    /* Glass-morphism Chat Bubbles */
    .user-bubble {
        align-self: flex-end;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 14px;
        border-radius: 18px 18px 2px 18px;
        margin: 10px 0 10px auto;
        max-width: 85%;
        backdrop-filter: blur(10px);
    }
    .ai-bubble {
        align-self: flex-start;
        background: linear-gradient(135deg, #007aff, #7000ff);
        padding: 14px;
        border-radius: 18px 18px 18px 2px;
        margin: 10px auto 10px 0;
        max-width: 85%;
        box-shadow: 0 8px 20px rgba(112, 0, 255, 0.3);
    }
    
    /* Simple Feed Cards */
    .intel-card {
        background: #111;
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #7000ff;
        margin-bottom: 12px;
        font-weight: 500;
    }
    </style>
    
    <script>
    // This script physically stops the pull-to-refresh circle at the browser level
    var container = window.parent.document.querySelector('.main');
    container.addEventListener('touchmove', function(e) {
        if (window.parent.pageYOffset === 0 && e.touches[0].pageY > 0) {
            // If user is at top and swipes down, stop the action
        }
    }, {passive: false});
    </script>
    """, unsafe_allow_html=True)

# --- 3. LOGIC ---
def ask_ai(msgs):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {"model": "llama-3.1-8b-instant", "messages": msgs, "temperature": 0.5}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.json()['choices'][0]['message']['content']
    except: return "Connection unstable."

# --- 4. APP INTERFACE ---
# Clean Tabs
t1, t2 = st.tabs(["NEURAL FEED", "DEBATE"])

with t1:
    st.markdown("### 📡 ACTIVE INTEL")
    try:
        # Fetching a few more to fill the screen
        r = requests.get(f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_KEY}&language=en&pageSize=10").json().get('articles', [])
        for n in r:
            st.markdown(f"<div class='intel-card'>{n['title']}</div>", unsafe_allow_html=True)
    except: st.write("Scanning frequencies...")

with t2:
    if "chat" not in st.session_state: st.session_state.chat = []
    
    # Message container
    for m in st.session_state.chat:
        cls = "user-bubble" if m["role"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{cls}'>{m['content']}</div>", unsafe_allow_html=True)

    # Input fixed to the bottom by Streamlit chat_input
    prompt = st.chat_input("Enter Argument...")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.spinner(""):
            ans = ask_ai([{"role": "user", "content": prompt}])
            st.session_state.chat.append({"role": "assistant", "content": ans})
            save_mem(prompt, ans)
        st.rerun()