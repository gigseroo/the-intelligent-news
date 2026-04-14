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

# --- 3. UI STYLE & SCROLL PROTECTION ---
st.markdown("""
    <style>
    /* Blocks mobile pull-to-refresh */
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
        margin-bottom: 25px; background: #161b22; 
    }
    .source-tag {
        background: #238636; color: white; padding: 4px 12px;
        border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 12px;
        width: fit-content;
    }
    img { border-radius: 8px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE FUNCTIONS ---
def get_news(q=None, s=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 12}
    if s: p["sources"] = s
    if q: p["q"] = q
    try:
        r = requests.get(url, params=p).json()
        return r.get('articles', [])
    except: return []

def ask_ai_groq(user_arg, news_context):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Role: Expert Intelligence Debater.
    User Argument: {user_arg}
    Context: {news_context}
    Task: Argue against the user with logic and facts in 3-4 sentences.
    """
    
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.json()['choices'][0]['message']['content']
    except:
        return "Intelligence system link broken. Check if GROQ_API_KEY is in Streamlit Secrets."

# --- 5. APPLICATION INTERFACE ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Debate", "History"])

# --- TAB 1: NEWS FEED ---
with t1:
    src = st.selectbox("Select Agency", ["All", "bbc-news", "reuters", "the-verge", "bloomberg"])
    news = get_news(s=None if src == "All" else src)
    if news:
        for n in news[:10]:
            st.markdown(f"<div class='news-card'><div class='source-tag'>{n['source']['name']}</div>", unsafe_allow_html=True)
            if n.get('urlToImage'): st.image(n['urlToImage'])
            st.subheader(n['title'])
            st.write(n['description'])
            st.markdown(f"[View Full Document]({n['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SEARCH ---
with t2:
    query = st.text_input("Enter Topic to Investigate")
    if query:
        res = get_news(q=query)
        for r in res[:6]:
            st.markdown(f"<div class='news-card'><div class='source-tag'>{r['source']['name']}</div>", unsafe_allow_html=True)
            st.subheader(r['title'])
            summary = (r.get('content') or r.get('description') or "")
            st.write(summary[:500] + "...")
            st.markdown(f"[Read Full Intel]({r['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: DEBATE UNIT ---
with t3:
    st.subheader("Counter-Intel Debate")
    topic = st.text_input("Topic for Debate")
    arg = st.text_area("State Your Position")
    if st.button("Initiate Fight"):
        with st.spinner("Analyzing logical fallacies..."):
            ctx_news = get_news(q=topic)
            ctx_str = ctx_news[0]['title'] if ctx_news else "Global Current Affairs"
            reply = ask_ai_groq(arg, ctx_str)
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
    except: 
        st.write("No intelligence logs recorded yet.")