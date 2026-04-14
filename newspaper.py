import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & API SETUP ---
st.set_page_config(page_title="Neural Intel", layout="wide", initial_sidebar_state="collapsed")

# Safely get keys from secrets
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 2. DEVICE-LOCAL MEMORY ENGINE ---
def init_local_brain():
    conn = sqlite3.connect('neural_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS personality 
                 (timestamp TEXT, user_input TEXT, ai_rebuttal TEXT, topic TEXT)''')
    conn.commit()
    conn.close()

def save_to_brain(u, a, t):
    conn = sqlite3.connect('neural_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO personality VALUES (?,?,?,?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M"), u, a, t))
    conn.commit()
    conn.close()

def get_learned_context():
    try:
        conn = sqlite3.connect('neural_memory.db')
        df = pd.read_sql_query("SELECT user_input FROM personality ORDER BY timestamp DESC LIMIT 5", conn)
        conn.close()
        return " ".join(df['user_input'].tolist())
    except:
        return ""

init_local_brain()

# --- 3. UI CUSTOMIZATION (FIXED CSS ESCAPING) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    .news-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
    }
    
    .user-bubble {
        background: #222;
        padding: 15px;
        border-radius: 15px 15px 2px 15px;
        margin: 10px 0 10px auto;
        max-width: 80%;
        border: 1px solid #333;
    }
    .ai-bubble {
        background: linear-gradient(135deg, #05ffa1, #007aff);
        padding: 15px;
        border-radius: 15px 15px 15px 2px;
        margin: 10px auto 10px 0;
        max-width: 80%;
        color: black;
        font-weight: 500;
    }
    
    .source-tag { color: #05ffa1; font-weight: bold; font-size: 12px; text-transform: uppercase; }
    .summary-box { 
        background: rgba(5, 255, 161, 0.1);
        border-left: 4px solid #05ffa1;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE LOGIC FUNCTIONS ---
def fetch_news(query=None, source=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    if source and source != "All":
        url = f"https://newsapi.org/v2/top-headlines?sources={source}&apiKey={NEWS_KEY}"
    elif query:
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_KEY}&pageSize=10"
    else:
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_KEY}&pageSize=10"
    
    try:
        r = requests.get(url, headers=headers).json()
        return r.get('articles', [])
    except: return []

def ai_engine(prompt, context_data="", mode="debate"):