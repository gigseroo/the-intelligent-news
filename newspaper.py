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

# --- 3. UI STYLE & SCROLL REFRESH BLOCK ---
st.markdown("""
    <style>
    /* Prevents the browser from refreshing when pulling down */
    html, body {
        overscroll-behavior-y: contain !important;
        position: fixed;
        overflow: hidden;
        width: 100%;
        height: 100%;
    }
    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        height: 100%;
    }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .news-card { 
        padding: 20px; border-radius: 12px; border: 1px solid #30363d; 
        margin-bottom: 20px; background: #161b22; 
    }
    .source-tag {
        background: #238636; color: white; padding: 3px 10px;
        border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 10px;
        width: fit-content;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE ---
def get_news(q=None, s=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 12}
    if s: p["sources"] = s
    if q: p["q"] = q
    try:
        r = requests.get(url, params=p).json()
        return r.get('articles', [])
    except: return []

def ask_ai(txt, task):
    # Models to try in order (Fastest and least busy first)
    models = [
        "google/gemma-1.1-2b-it",
        "facebook/bart-large-cnn",
        "google/flan-t5-large"
    ]
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {"inputs": f"Argue against this: {txt[:500]}", "options": {"wait_for_model": True}}

    for model in models:
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        try:
            # We give each model a quick 10-second window to respond
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            res = response.json()
            
            if isinstance(res, list) and len(res) > 0:
                # Handle different response formats
                text = res[0].get('generated_text') or res[0].get('summary_text')
                if text: return text
            elif isinstance(res, dict) and 'generated_text' in res:
                return res['generated_text']
        except:
            continue # Try the next model if this one fails or times out
            
    return "All Intelligence units are currently deployed (Busy). Wait 15 seconds and tap Fight again."

# --- 5. APP ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Debate", "History"])

# --- TAB 1: FEED ---
with t1:
    src = st.selectbox("Agency", ["All", "bbc-news", "reuters", "the-verge", "bloomberg"])
    news = get_news(s=None if src == "All" else src)
    if news:
        for n in news[:8]:
            st.markdown(f"<div class='news-card'><div class='source-tag'>{n['source']['name']}</div>", unsafe_allow_html=True)
            if n.get('urlToImage'): st.image(n['urlToImage'])
            st.subheader(n['title'])
            st.write(n['description'])
            st.markdown(f"[View Full Document]({n['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SEARCH ---
with t2:
    query = st.text_input("Enter Search Term")
    if query:
        res = get_news(q=query)
        for r in res[:6]:
            st.markdown(f"<div class='news-card'><div class='source-tag'>{r['source']['name']}</div>", unsafe_allow_html=True)
            st.subheader(r['title'])
            summary_txt = r.get('content') or r.get('description') or "Data restricted."
            st.write(summary_txt[:500] + "...")
            st.markdown(f"[Read Full Intel]({r['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: DEBATE ---
with t3:
    st.subheader("Counter-Intel Debate")
    topic = st.text_input("Topic")
    arg = st.text_area("Your Argument")
    if st.button("Initiate Fight"):
        with st.spinner("Connecting to Intelligence Units..."):
            # Simplified context for speed
            ctx_news = get_news(q=topic)
            ctx_str = ctx_news[0]['title'] if ctx_news else "Global Trends"
            prompt = f"Argument: {arg}. Context: {ctx_str}."
            reply = ask_ai(prompt, "Debate")
            st.session_state['rebuttal'] = reply
            save_mem(arg, reply, topic)
    if 'rebuttal' in st.session_state:
        st.error(f"AI Response: {st.session_state['rebuttal']}")

# --- TAB 4: HISTORY ---
with t4:
    try:
        conn = sqlite3.connect('intel.db')
        st.dataframe(pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn), use_container_width=True)
        conn.close()
    except: st.write("History log is empty.")