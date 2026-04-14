import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. DATABASE & MEMORY ---
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

# --- 3. UI & MOBILE FIX ---
st.markdown("""
    <style>
    body { overscroll-behavior-y: contain; }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .news-card { padding: 15px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 10px; background: #161b22; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #21262d; border-radius: 4px; padding: 10px; }
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
    url = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    h = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {"inputs": f"{task}: {txt[:500]}", "options": {"wait_for_model": True}}
    try:
        res = requests.post(url, headers=h, json=payload, timeout=15).json()
        return res[0]['summary_text'] if isinstance(res, list) else "AI Warming up... try again in 5s."
    except: return "System busy."

# --- 5. APP INTERFACE ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Debate", "History"])

# --- TAB 1: FEED ---
with t1:
    src = st.selectbox("Source", ["All", "bbc-news", "reuters", "the-verge", "bloomberg"])
    sid = None if src == "All" else src
    news = get_news(s=sid)
    
    if news:
        if st.button("Summarize Top Stories"):
            with st.spinner("Processing..."):
                blob = " ".join([n['title'] for n in news[:5]])
                st.info(ask_ai(blob, "Summarize"))
        
        for n in news[:8]:
            st.markdown(f"<div class='news-card'><b>{n['title']}</b><br><small>{n['source']['name']}</small></div>", unsafe_allow_html=True)
            st.write(n['description'])
            st.markdown(f"[Read More]({n['url']})")

# --- TAB 2: SEARCH ---
with t2:
    query = st.text_input("Topic")
    if query:
        res = get_news(q=query)
        for r in res[:5]:
            st.write(f"**{r['title']}**")
            st.write(r['description'])

# --- TAB 3: DEBATE ---
with t3:
    topic = st.text_input("Debate Topic")
    arg = st.text_area("Your Argument")
    if st.button("Fight"):
        with st.spinner("Thinking..."):
            ctx = " ".join([n['title'] for n in get_news(q=topic)[:2]])
            reply = ask_ai(f"Arg: {arg}. Context: {ctx}", "Argue against")
            st.session_state['rebuttal'] = reply
            save_mem(arg, reply, topic)
    if 'rebuttal' in st.session_state:
        st.error(f"AI: {st.session_state['rebuttal']}")

# --- TAB 4: HISTORY ---
with t4:
    try:
        conn = sqlite3.connect('intel.db')
        st.table(pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn))
        conn.close()
    except: st.write("No history.")