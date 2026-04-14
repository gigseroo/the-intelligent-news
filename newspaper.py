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

# --- 3. UI STYLE & JAVASCRIPT SCROLL SHIELD ---
st.markdown("""
    <script>
    // Hard-stop for mobile pull-to-refresh
    document.body.style.overscrollBehaviorY = 'none';
    </script>
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        position: fixed;
        width: 100%;
        height: 100%;
        overflow-y: scroll !important;
    }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .news-card { 
        padding: 20px; border-radius: 12px; border: 1px solid #30363d; 
        margin-bottom: 20px; background: #161b22; 
    }
    .source-tag {
        background: #238636; color: white; padding: 3px 10px;
        border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 10px;
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
    # SWITCHED TO GEMMA-2B: Faster, lighter, and more reliable for free tier
    API_URL = "https://api-inference.huggingface.co/models/google/gemma-1.1-2b-it"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {"inputs": f"Instruction: {task}. Context: {txt[:600]}", "options": {"wait_for_model": True}}
    
    for _ in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
            res = response.json()
            if isinstance(res, list) and 'generated_text' in res[0]:
                return res[0]['generated_text'].split("Response:")[-1] # Clean up output
            elif "estimated_time" in str(res):
                time.sleep(6)
                continue
        except:
            time.sleep(2)
    return "Intelligence Unit busy. Please try one last time."

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
            # Showing longer summary
            summary_txt = r.get('content') or r.get('description') or "No data."
            st.write(summary_txt[:500] + "...")
            st.markdown(f"[Read Full Intel]({r['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: DEBATE ---
with t3:
    st.subheader("Counter-Intel Debate")
    topic = st.text_input("Topic")
    arg = st.text_area("Your Argument")
    if st.button("Initiate Fight"):
        with st.spinner("AI is thinking..."):
            ctx_news = get_news(q=topic)
            ctx_str = " ".join([n['title'] for n in ctx_news[:2]])
            prompt = f"Topic: {topic}. User Argument: {arg}. Real News: {ctx_str}. Argue against the user."
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
    except: st.write("No history found.")