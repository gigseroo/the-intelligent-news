import streamlit as st
import requests
import urllib.parse

# --- 1. MINIMALIST HUD UI ---
st.set_page_config(page_title="G.R.E.G.", layout="wide")

st.markdown("""
    <style>
    /* Clean Monochrome Theme */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Result List Styling */
    .link-card {
        background: #111111;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #333;
    }
    
    .direct-link {
        color: #ffffff !important;
        text-decoration: none;
        font-weight: bold;
        display: block;
        padding: 10px;
        background: #222;
        border-radius: 5px;
        text-align: center;
        border: 1px solid #444;
    }
    .direct-link:hover { background: #333; border-color: #fff; }

    .greg-msg { color: #888; margin: 15px 0; border-left: 2px solid #444; padding-left: 15px; }
    .user-msg { color: #fff; font-weight: 600; margin-top: 20px; text-transform: uppercase; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BRAIN ENGINE ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def ask_greg(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.2}
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "Connection lost."

# --- 3. SESSION STATE ---
if "history" not in st.session_state: st.session_state.history = []
if "item" not in st.session_state: st.session_state.item = None
if "results" not in st.session_state: st.session_state.results = []

# --- 4. THE INTERFACE ---
st.title("G.R.E.G.")

# DISPLAY SEARCH RESULTS AREA
if st.session_state.item:
    st.markdown(f"### Results for {st.session_state.item.upper()}")
    
    # We generate a variety of marketplace viewpoints for the user
    search_queries = [
        f"{st.session_state.item}",
        f"cheap {st.session_state.item}",
        f"used {st.session_state.item}"
    ]
    
    for q in search_queries:
        encoded = urllib.parse.quote(q)
        link = f"https://www.facebook.com/marketplace/search/?query={encoded}"
        st.markdown(f"""
            <div class="link-card">
                <small style="color:#666">SOURCE: FACEBOOK MARKETPLACE</small>
                <p style="margin: 5px 0;">Broad search for: <b>{q}</b></p>
                <a href="{link}" target="_blank" class="direct-link">VIEW ALL PRODUCTS</a>
            </div>
        """, unsafe_allow_html=True)
    
    if st.button("Clear Results"):
        st.session_state.item = None
        st.rerun()

st.divider()

# CHAT LOG
for m in st.session_state.history:
    if m["role"] == "assistant":
        st.markdown(f'<div class="greg-msg">{m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="user-msg">YOU // {m["content"]}</div>', unsafe_allow_html=True)

# INPUT
cmd = st.chat_input("What are we finding today?")

if cmd:
    st.session_state.history.append({"role": "user", "content": cmd})
    
    # Identify the product
    item_id = ask_greg([
        {"role": "system", "content": "Extract the specific item name. If the user mentions price/color for the previous item, keep the original name. Return only 1-2 words."},
        {"role": "user", "content": f"Previous: {st.session_state.item}. New: {cmd}"}
    ])
    
    if len(item_id.split()) < 4:
        st.session_state.item = item_id.strip()

    # Bot Personality Response
    low_cmd = cmd.lower()
    if any(x in low_cmd for x in ["find", "buy", "search", "look", "price"]):
        reply = f"I've generated a few specialized links for {st.session_state.item} below. These will take you directly to the best deals."
    else:
        reply = ask_greg([
            {"role": "system", "content": f"You are GREG, a helpful shopping bot for finding {st.session_state.item}. Be concise and friendly. No military talk."},
            {"role": "user", "content": cmd}
        ])

    st.session_state.history.append({"role": "assistant", "content": reply})
    st.rerun()
