import streamlit as st
import requests
import urllib.parse

# --- 1. MODERN MINIMALIST UI ---
st.set_page_config(page_title="G.R.E.G.", layout="wide")

st.markdown("""
    <style>
    /* Clean Black & White Theme */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Shopping Card */
    .shop-card {
        background: #111111;
        border: 1px solid #333333;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 12px;
    }
    
    .greg-text { color: #bbbbbb; margin-bottom: 20px; font-size: 16px; }
    .user-text { color: #ffffff; font-weight: 600; margin-bottom: 5px; font-size: 14px; }
    
    /* Clean White Button */
    .stButton>button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100%;
        height: 45px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BRAIN ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def ask_greg(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.3}
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "I'm having trouble connecting right now."

# --- 3. SMART MEMORY ---
if "history" not in st.session_state: st.session_state.history = []
if "item" not in st.session_state: st.session_state.item = None
if "link" not in st.session_state: st.session_state.link = None

# --- 4. THE APP ---
st.title("G.R.E.G.")
if st.session_state.item:
    st.caption(f"Currently looking for: {st.session_state.item}")

# THE SEARCH BOX (Stays at the top when active)
if st.session_state.link:
    with st.container():
        st.markdown(f"""<div class="shop-card">
            <h4 style="margin:0;">Found some options for your {st.session_state.item}</h4>
            <p style="color:#888; font-size:13px;">Click below to see the latest prices on Marketplace</p>
        </div>""", unsafe_allow_html=True)
        col1, col2 = st.columns([4,1])
        with col1:
            st.link_button(f"View {st.session_state.item} listings", st.session_state.link)
        with col2:
            if st.button("Clear"):
                st.session_state.link = None
                st.rerun()

st.divider()

# Conversation
for m in st.session_state.history:
    if m["role"] == "assistant":
        st.markdown(f'<div class="greg-text">{m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="user-text">{m["content"]}</div>', unsafe_allow_html=True)

# Input
chat_input = st.chat_input("What can I find for you?")

if chat_input:
    st.session_state.history.append({"role": "user", "content": chat_input})
    
    # 1. Update the item name (Memory)
    mem_check = ask_greg([
        {"role": "system", "content": "The user is shopping. Identify the main object they are looking for. If they are just adding details like 'cheap' or 'blue' to a previous item, keep the original item name. Return just the 1-2 word name of the object."},
        {"role": "user", "content": f"Context: {st.session_state.item}. Input: {chat_input}"}
    ])
    if len(mem_check.split()) < 4:
        st.session_state.item = mem_check.strip()

    # 2. Respond & Link
    low_input = chat_input.lower()
    if any(x in low_input for x in ["find", "buy", "search", "marketplace", "looking for", "price"]):
        query = urllib.parse.quote(st.session_state.item)
        st.session_state.link = f"https://www.facebook.com/marketplace/search/?query={query}"
        reply = f"I've pulled up some listings for that {st.session_state.item}. Check the link at the top!"
    else:
        reply = ask_greg([
            {"role": "system", "content": f"You are GREG, a helpful shopping bot. You're assisting with finding a {st.session_state.item}. Be friendly, helpful, and concise. No military talk."},
            {"role": "user", "content": chat_input}
        ])

    st.session_state.history.append({"role": "assistant", "content": reply})
    st.rerun()