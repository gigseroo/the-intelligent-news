import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('intel.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS logs (time TEXT, user TEXT, ai TEXT, topic TEXT)')
    conn.commit()
    conn.close()

def save_mem(u, a, t):
    conn = sqlite3.connect('intel.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (?,?,?,?)", (datetime.now().strftime("%H:%M"), u, a, t))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="Intel News", layout="wide")
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 3. CRYSTAL VIBE + GESTURE KILLER ---
st.markdown("""
    <style>
    /* Prevent the bounce/refresh at the top */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        background-color: #050505;
    }
    
    .stApp { background-color: #050505; color: #e0e0e0; }
    header, footer, #MainMenu {visibility: hidden;}

    /* Chat Bubbles (Logo Colors) */
    .user-bubble {
        align-self: flex-end;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 12px 16px;
        border-radius: 18px 18px 2px 18px;
        margin: 8px 0 8px auto;
        max-width: 80%;
        backdrop-filter: blur(10px);
    }
    
    .ai-bubble {
        align-self: flex-start;
        background: linear-gradient(135deg, #007aff, #7000ff);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 2px;
        margin: 8px auto 8px 0;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(112, 0, 255, 0.3);
    }

    /* News Card Styling */
    .intel-card {
        padding: 15px; border-radius: 12px; border: 1px solid #30363d; 
        margin-bottom: 15px; background: rgba(22, 27, 34, 0.6);
        border-left: 4px solid #007aff;
    }
    
    .source-tag {
        background: #7000ff; color: white; padding: 2px 8px;
        border-radius: 4px; font-size: 10px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE FUNCTIONS ---
def get_news(q=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 10}
    if q: p["q"] = q
    try:
        r = requests.get(url, params=p).json()
        return r.get('articles', [])
    except: return []

def ask_ai_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.7}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.json()['choices'][0]['message']['content']
    except: return "Link unstable."

# --- 5. INTERFACE ---
t1, t2, t3 = st.tabs(["FEED", "DEBATE", "LOGS"])

with t1:
    st.markdown("### 📡 NEURAL FEED")
    news = get_news()
    if news:
        for n in news:
            st.markdown(f"""
            <div class='intel-card'>
                <span class='source-tag'>{n['source']['name']}</span><br>
                <div style='margin-top:8px; font-weight:bold;'>{n['title']}</div>
                <div style='font-size:13px; color:#aaa; margin-top:5px;'>{n.get('description') or ''}</div>
            </div>
            """, unsafe_allow_html=True)

with t2:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Render the chat
    for msg in st.session_state.messages:
        div_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)

    # Input Box
    user_input = st.chat_input("Input Position...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner(""):
            reply = ask_ai_groq([{"role": "user", "content": user_input}])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_mem(user_input, reply, "Debate")
        st.rerun()

with t3:
    try:
        conn = sqlite3.connect('intel.db')
        df = pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()
    except: st.write("No logs recorded.")