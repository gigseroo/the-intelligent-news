import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. DATABASE ---
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

# --- 2. CONFIG ---
st.set_page_config(page_title="Intelligence News", layout="wide")
NEWS_KEY = "434fc8e864e04c43a7e07cdbce6d8fdb"
HF_KEY = "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"

# --- 3. UI & FORCE NO-REFRESH ---
st.markdown("""
    <style>
    /* Aggressive fix for mobile pull-to-refresh */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        overscroll-behavior: none !important;
    }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .news-card { 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #30363d; 
        margin-bottom: 15px; 
        background: #161b22;
        display: flex;
        flex-direction: column;
    }
    .source-tag {
        background: #238636;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        text-transform: uppercase;
        margin-bottom: 5px;
        width: fit-content;
    }
    img { border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE ---
def get_news(q=None, s=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 10}
    if s: p["sources"] = s
    if q: p["q"] = q
    try:
        return requests.get(url, params=p).json().get('articles', [])
    except: return []

def ask_ai(txt, task):
    # Using a different stable model for debate
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {"inputs": f"{task}: {txt[:600]}", "options": {"wait_for_model": True}}
    
    # Retry loop for cold starts
    for _ in range(5):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            res = response.json()
            if isinstance(res, list):
                return res[0]['summary_text']
            elif "estimated_time" in str(res):
                time.sleep(5) # Explicit wait for wake-up
                continue
        except:
            time.sleep(2)
            continue
    return "The AI is still waking up. Please press 'Fight' again in 10 seconds."

# --- 5. APP ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Debate", "History"])

# --- TAB 1: FEED ---
with t1:
    src = st.selectbox("Agency", ["All", "bbc-news", "reuters", "the-verge", "bloomberg"])
    news = get_news(s=None if src == "All" else src)
    
    if news:
        for n in news[:8]:
            with st.container():
                st.markdown(f"<div class='news-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='source-tag'>From: {n['source']['name']}</div>", unsafe_allow_html=True)
                if n.get('urlToImage'):
                    st.image(n['urlToImage'], use_column_width=True)
                st.subheader(n['title'])
                st.write(n['description'])
                st.markdown(f"[Read Full Intel]({n['url']})")
                st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SEARCH ---
with t2:
    query = st.text_input("Enter Subject")
    if query:
        res = get_news(q=query)
        for r in res[:5]:
            st.markdown(f"**Source: {r['source']['name']}**")
            st.write(r['title'])
            st.divider()

# --- TAB 3: DEBATE ---
with t3:
    st.subheader("Debate Mode")
    topic = st.text_input("Topic")
    arg = st.text_area("Your Argument")
    if st.button("Fight"):
        with st.status("Waking up Intelligence Unit...", expanded=True) as status:
            ctx = " ".join([n['title'] for n in get_news(q=topic)[:2]])
            reply = ask_ai(f"User: {arg}. News: {ctx}", "Counter-argue")
            st.session_state['rebuttal'] = reply
            save_mem(arg, reply, topic)
            status.update(label="Response generated!", state="complete")
            
    if 'rebuttal' in st.session_state:
        st.error(f"AI Response: {st.session_state['rebuttal']}")

# --- TAB 4: HISTORY ---
with t4:
    try:
        conn = sqlite3.connect('intel.db')
        st.dataframe(pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn), use_container_width=True)
        conn.close()
    except: st.write("No logs yet.")