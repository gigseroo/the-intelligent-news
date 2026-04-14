import streamlit as st
import requests
import sqlite3
import uuid
from datetime import datetime

# --- 1. SETTINGS & DEVICE-LOCAL DATABASE ---
st.set_page_config(page_title="Intel", layout="wide")
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

if "device_id" not in st.session_state:
    st.session_state.device_id = str(uuid.uuid4())

def save_private_mem(u, a):
    conn = sqlite3.connect('local_intel.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS logs (device TEXT, time TEXT, user TEXT, ai TEXT)')
    c.execute("INSERT INTO logs VALUES (?,?,?,?)", (st.session_state.device_id, datetime.now().strftime("%H:%M"), u, a))
    conn.commit()
    conn.close()

# --- 2. THE UI & SCROLL LOCK ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050505 !important;
        overscroll-behavior: none !important;
        position: fixed;
        width: 100%;
        height: 100%;
        overflow: hidden !important;
    }

    .scroll-area {
        height: 70vh;
        overflow-y: auto !important;
        padding: 10px;
        -webkit-overflow-scrolling: touch;
    }

    header, footer, [data-testid="stHeader"] {visibility: hidden !important;}

    /* User: Minimalist Slate | AI: Emerald Neon */
    .user-bubble {
        align-self: flex-end;
        background: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 14px;
        border-radius: 20px 20px 4px 20px;
        margin: 8px 0 8px auto;
        max-width: 85%;
        color: #fff;
        font-family: sans-serif;
    }
    .ai-bubble {
        align-self: flex-start;
        background: linear-gradient(135deg, #05ffa1, #007aff);
        color: #000;
        font-weight: 600;
        padding: 14px;
        border-radius: 20px 20px 20px 4px;
        margin: 8px auto 8px 0;
        max-width: 85%;
        box-shadow: 0 4px 20px rgba(5, 255, 161, 0.2);
    }

    .intel-card {
        background: #111;
        padding: 15px;
        border-radius: 12px;
        border-left: 2px solid #05ffa1;
        margin-bottom: 15px;
    }
    
    /* Search Bar Styling */
    .stTextInput>div>div>input {
        background-color: #111 !important;
        color: #05ffa1 !important;
        border: 1px solid #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ENGINE ---
def get_intel(query=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    if query:
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_KEY}&language=en&pageSize=12"
    else:
        url = f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_KEY}&language=en&pageSize=12"
    
    try:
        r = requests.get(url, headers=headers).json()
        return r.get('articles', [])
    except: return []

def ask_neural(msgs):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {"model": "llama-3.1-8b-instant", "messages": msgs, "temperature": 0.6}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.json()['choices'][0]['message']['content']
    except: return "Neural Link Timeout."

# --- 4. TABS ---
t1, t2 = st.tabs(["FEED", "DEBATE"])

with t1:
    col1, col2 = st.columns([4, 1])
    with col1:
        s_query = st.text_input("", placeholder="Search Intel...", label_visibility="collapsed")
    with col2:
        if st.button("🌐"): s_query = None # Reset button
        
    st.markdown("<div class='scroll-area'>", unsafe_allow_html=True)
    intel = get_intel(s_query)
    if intel:
        for i in intel:
            st.markdown(f"<div class='intel-card'><b>{i['title']}</b><br><small style='color:#666'>{i['source']['name']}</small></div>", unsafe_allow_html=True)
    else:
        st.write("No signals detected.")
    st.markdown("</div>", unsafe_allow_html=True)

with t2:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    st.markdown("<div class='scroll-area'>", unsafe_allow_html=True)
    for m in st.session_state.messages:
        cls = "user-bubble" if m["role"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{cls}'>{m['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("Input Position...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner(""):
            ans = ask_neural([{"role": "user", "content": prompt}])
            st.session_state.messages.append({"role": "assistant", "content": ans})
            save_private_mem(prompt, ans)
        st.rerun()