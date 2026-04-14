import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('user_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memory 
                 (timestamp TEXT, user_input TEXT, ai_response TEXT, topic TEXT)''')
    conn.commit()
    conn.close()

def save_interaction(user_text, ai_text, topic):
    conn = sqlite3.connect('user_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO memory VALUES (?,?,?,?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_text, ai_text, topic))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIG & KEYS ---
st.set_page_config(page_title="Nexus Intelligence News", layout="wide")

# Get keys from secrets
NEWS_API_KEY ="434fc8e864e04c43a7e07cdbce6d8fdb" if "NEWS_API_KEY" in st.secrets else "YOUR_NEWS_API_KEY"
HF_TOKEN ="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" if "HF_TOKEN" in st.secrets else "YOUR_HF_TOKEN"

# --- 3. FIX SCROLLING & STYLE ---
st.markdown("""
    <style>
    /* Prevents the 'pull-to-refresh' on mobile devices */
    body {
        overscroll-behavior-y: contain;
    }
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .nav-card {
        background: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    .arg-box {
        background: #1e1b4b;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #818cf8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE ENGINES ---
def fetch_news(query=None, source=None):
    base_url = "https://newsapi.org/v2/"
    params = {"apiKey": NEWS_API_KEY, "language": "en"}
    if source:
        endpoint = "top-headlines"
        params["sources"] = source
    elif query:
        endpoint = "everything"
        params["qInTitle"] = query
        params["sortBy"] = "relevancy"
    else:
        endpoint = "top-headlines"
        params["category"] = "general"
    try:
        r = requests.get(base_url + endpoint, params=params)
        return r.json().get('articles', [])
    except:
        return []

def ai_engine(prompt, task="summarize"):
    API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": f"Task: {task}. Content: {prompt[:600]}", "options": {"wait_for_model": True}}
    
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
            res = response.json()
            if isinstance(res, list) and len(res) > 0:
                return res[0]['summary_text']
            elif "estimated_time" in str(res):
                st.info("System warming up...")
                time.sleep(6)
                continue
        except:
            continue
    return "Intelligence currently unavailable. Please try again in a few moments."

# --- 5. UI INTERFACE ---
st.title("Nexus Intelligence News")
tabs = st.tabs(["Live Feed", "Deep Search", "Debate Unit", "Memory"])

# --- TAB 1: LIVE FEED ---
with tabs[0]:
    col1, col2 = st.columns([1, 3])
    with col1:
        company = st.selectbox("Select Agency", ["All Sources", "bbc-news", "reuters", "the-verge", "bloomberg"])
        source_id = None if company == "All Sources" else company
        
    with col2:
        articles = fetch_news(source=source_id)
        if articles:
            # We cache the summary so it doesn't disappear
            if f"summary_{company}" not in st.session_state:
                blob = " ".join([a['title'] for a in articles[:5]])
                st.session_state[f"summary_{company}"] = ai_engine(blob, "General Analysis")
            
            st.markdown(f"<div class='nav-card'><b>Executive Summary:</b><br>{st.session_state[f'summary_{company}']}</div>", unsafe_allow_html=True)
            
            for a in articles[:5]:
                st.write(f"### {a['title']}")
                st.write(a['description'])
                st.markdown(f"[View Document]({a['url']})")
                st.divider()

# --- TAB 2: DEEP SEARCH ---
with tabs[1]:
    query = st.text_input("Search Subject")
    if query:
        results = fetch_news(query=query)
        for r in results[:5]:
            st.write(f"**{r['title']}**")
            st.write(r['description'])

# --- TAB 3: DEBATE UNIT ---
with tabs[2]:
    st.subheader("Counter-Intelligence Debate")
    topic = st.text_input("Debate Topic")
    user_arg = st.text_area("Your Position")
    
    if st.button("Initiate Debate"):
        with st.spinner("Analyzing arguments..."):
            news = fetch_news(query=topic)
            context = " ".join([n['title'] for n in news[:3]])
            rebuttal = ai_engine(f"User says: {user_arg}. News: {context}", "Debate")
            st.session_state['last_rebuttal'] = rebuttal
            save_interaction(user_arg, rebuttal, topic)
            
    if 'last_rebuttal' in st.session_state:
        st.markdown(f"<div class='arg-box'><b>AI Rebuttal:</b><br>{st.session_state['last_rebuttal']}</div>", unsafe_allow_html=True)

# --- TAB 4: MEMORY ---
with tabs[3]:
    st.subheader("Stored Intelligence Patterns")
    try:
        conn = sqlite3.connect('user_memory.db')
        df = pd.read_sql_query("SELECT * FROM memory", conn)
        st.dataframe(df)
        conn.close()
    except:
        st.write("Memory logs empty.")