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
st.set_page_config(page_title="Intelligence News", layout="wide")
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 3. THE "PULL-TO-REFRESH" KILLER CSS ---
st.markdown("""
    <style>
    /* 1. This stops the whole browser from bouncing/refreshing */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        position: fixed;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }

    /* 2. This creates a specific zone that IS allowed to scroll */
    .chat-scroll-area {
        height: 70vh; /* Takes up most of the screen */
        overflow-y: auto !important;
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 15px;
        background-color: #0d1117;
        /* Custom scrollbar for a cleaner look */
        scrollbar-width: thin;
        scrollbar-color: #30363d #0d1117;
    }

    /* 3. WhatsApp/Insta Style Bubbles */
    .user-bubble {
        align-self: flex-end;
        background-color: #30363d;
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 2px 18px;
        max-width: 85%;
        margin-left: auto;
        font-family: sans-serif;
    }
    
    .ai-bubble {
        align-self: flex-start;
        background: linear-gradient(45deg, #007aff, #00c6ff);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 2px;
        max-width: 85%;
        margin-right: auto;
        font-family: sans-serif;
    }

    .stApp { background-color: #0d1117; }
    .news-card { padding: 15px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; background: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE FUNCTIONS ---
def get_news(q=None, s=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 10}
    if s: p["sources"] = s
    if q: p["q"] = q
    try:
        r = requests.get(url, params=p).json()
        return r.get('articles', [])
    except: return []

def ask_ai_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    api_token = str(GROQ_KEY).strip().replace('"', '').replace("'", "")
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    data = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.7}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except: return "Connection lost. Try again."

# --- 5. INTERFACE ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Fight", "History"])

with t1:
    src = st.selectbox("Agency", ["All", "bbc-news", "reuters", "the-verge"])
    news = get_news(s=None if src == "All" else src)
    if news:
        for n in news[:8]:
            st.markdown(f"<div class='news-card'><b>{n['source']['name']}</b><br>{n['title']}<br><a href='{n['url']}'>Link</a></div>", unsafe_allow_html=True)

with t2:
    query = st.text_input("Investigate Topic")
    if query:
        res = get_news(q=query)
        for r in res[:5]:
            st.markdown(f"<div class='news-card'><b>{r['source']['name']}</b><br>{r['title']}</div>", unsafe_allow_html=True)

# --- TAB 3: FIGHT (THE CHAT) ---
with t3:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    topic = st.text_input("Debate Topic", placeholder="Enter topic...")

    # THE SCROLLABLE CHAT CONTAINER
    # This <div> is the only thing allowed to scroll up and down
    st.markdown("<div class='chat-scroll-area'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        div_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # THE INPUT BOX (STAYS AT BOTTOM)
    user_input = st.chat_input("Type your argument...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Analyzing..."):
            ctx_news = get_news(q=topic) if topic else []
            ctx_str = ctx_news[0]['title'] if ctx_news else "global events"
            system_prompt = {"role": "system", "content": f"You are a sharp debater. Topic: {ctx_str}. Be brief."}
            full_history = [system_prompt] + st.session_state.messages
            ai_reply = ask_ai_groq(full_history)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            save_mem(user_input, ai_reply, topic)
        st.rerun()

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

with t4:
    try:
        conn = sqlite3.connect('intel.db')
        df = pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()
    except: st.write("History empty.")