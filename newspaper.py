import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & API SETUP ---
st.set_page_config(page_title="Neural Intel", layout="wide", initial_sidebar_state="collapsed")

NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 2. DEVICE-LOCAL MEMORY ENGINE ---
def init_local_brain():
    conn = sqlite3.connect('neural_memory.db')
    c = conn.cursor()
    # Stores user's argumentative style and past positions to 'learn'
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

# --- 3. COOL GRAPHICS & UI CUSTOMIZATION ---
st.markdown(f"""
    <style>
    /* Global Styles */
    .stApp {{ background-color: #050505; color: #e0e0e0; font-family: 'Inter', sans-serif; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    
    /* Glassmorphism News Cards */
    .news-card {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }}
    .news-card:hover {{ transform: translateY(-5px); border-color: #007aff; }}
    
    /* AI Chat Bubbles */
    .user-bubble {{
        background: #222;
        padding: 15px;
        border-radius: 15px 15px 2px 15px;
        margin: 10px 0 10px auto;
        width: fit-content;
        max-width: 80%;
        border: 1px solid #333;
    }}
    .ai-bubble {{
        background: linear-gradient(135deg, #007aff, #7000ff);
        padding: 15px;
        border-radius: 15px 15px 15px 2px;
        margin: 10px auto 10px 0;
        width: fit-content;
        max-width: 80%;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3);
    }}
    
    /* Neon Accents */
    .source-tag {{ color: #007aff; font-weight: bold; font-size: 12px; text-transform: uppercase; }}
    .summary-box {{ 
        background: linear-gradient(90deg, rgba(0,122,255,0.1), rgba(112,0,255,0.1));
        border-left: 4px solid #007aff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }}
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
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    learned_style = get_learned_context()
    
    system_msg = "You are a high-level intelligence analyst."
    if mode == "debate":
        system_msg = f"Argue AGAINST the user. Be sharp. Learn from their style: {learned_style}"
    elif mode == "summary":
        system_msg = "Analyze these news headlines and provide a 3-sentence 'Executive Summary' of the global situation."

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Context: {context_data}\n\nInput: {prompt}"}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data).json()
        return response['choices'][0]['message']['content']
    except: return "Connection to Neural Net lost."

# --- 5. APP INTERFACE ---
st.title("NEURAL INTEL")

tab1, tab2 = st.tabs(["SIGNAL FEED", "NEURAL DEBATE"])

with tab1:
    # Feature: Pick Company or Search
    c1, c2 = st.columns([1, 2])
    with c1:
        agency = st.selectbox("Signal Source", ["All