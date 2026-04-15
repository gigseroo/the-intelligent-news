import streamlit as st
import requests
import urllib.parse

# --- 1. THE STEALTH HUD UI ---
st.set_page_config(page_title="G.R.E.G. STEALTH", layout="wide")

st.markdown("""
    <style>
    /* Kill all Streamlit branding and headers */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Courier New', monospace; }
    
    /* Tactical Background */
    .stApp {
        background-image: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), 
                    linear-gradient(90deg, rgba(255, 255, 255, 0.01), rgba(255, 255, 255, 0.01));
        background-size: 100% 2px, 3px 100%;
    }

    /* Action Card */
    .dispatch-unit {
        background: #0a0a0a;
        border: 2px solid #ffffff;
        padding: 20px;
        margin-bottom: 30px;
        text-align: center;
    }
    
    .msg-greg { color: #888; border-left: 2px solid #fff; padding-left: 15px; margin-bottom: 20px; }
    .msg-user { color: #fff; font-weight: bold; margin-bottom: 5px; letter-spacing: 2px; text-transform: uppercase; }
    
    /* High-Contrast Action Buttons */
    .stButton>button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
        height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BRAIN ENGINE ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def greg_query(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.1}
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "CORE LINK TIMEOUT."

# --- 3. PERSISTENT STATE ---
if "history" not in st.session_state: st.session_state.history = []
if "target" not in st.session_state: st.session_state.target = "None"
if "link" not in st.session_state: st.session_state.link = None

# --- 4. HUD INTERFACE ---
st.markdown("<h1 style='letter-spacing:20px; text-align:center; margin-top:-20px;'>GREG</h1>", unsafe_allow_html=True)
st.caption(f"ACTIVE OBJECTIVE: {st.session_state.target.upper()}")

# THE DISPATCHER (Sticky Action Button)
if st.session_state.link:
    st.markdown('<div class="dispatch-unit"><b>UPLINK SIGNAL DETECTED</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.link_button(f"EXECUTE: SEARCH FOR {st.session_state.target.upper()}", st.session_state.link)
    with c2:
        if st.button("CLOSE"):
            st.session_state.link = None
            st.rerun()

st.divider()

# Display Chat History
for m in st.session_state.history:
    if m["role"] == "assistant":
        st.markdown(f'<div class="msg-greg">{m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-user">>> {m["content"]}</div>', unsafe_allow_html=True)

# Command Input
cmd_in = st.chat_input("Enter Protocol...")

if cmd_in:
    st.session_state.history.append({"role": "user", "content": cmd_in})
    
    # 1. Subject Persistence (Keep track of what we are talking about)
    mem_prompt = [
        {"role": "system", "content": "Extract the specific item name from the user's input. If the user is giving details about a previous item (like price/color), return the previous item name. Return ONLY the item name (1-2 words)."},
        {"role": "user", "content": f"History: {st.session_state.target}. New: {cmd_in}"}
    ]
    new_subject = greg_query(mem_prompt)
    if len(new_subject.split()) < 4:
        st.session_state.target = new_subject.strip()

    # 2. Command Processing
    cmd_lower = cmd_in.lower()
    if any(word in cmd_lower for word in ["find", "search", "buy", "marketplace", "look for"]):
        # Generate the Marketplace link
        q = urllib.parse.quote(st.session_state.target)
        st.session_state.link = f"https://www.facebook.com/marketplace/search/?query={q}"
        msg = f"Sir, I've locked the search perimeter for {st.session_state.target}. The execute link is active at the top of your HUD."
    elif "instagram" in cmd_lower or "message" in cmd_lower:
        st.session_state.link = "https://www.instagram.com/direct/inbox/"
        msg = "Instagram uplink established. Direct Inbox access ready above."
    else:
        # Standard Conversation
        msg = greg_query([
            {"role": "system", "content": f"You are GREG. A stealth military AI. You are helping find {st.session_state.target}. Be extremely brief and professional."},
            {"role": "user", "content": cmd_in}
        ])

    st.session_state.history.append({"role": "assistant", "content": msg})
    st.rerun()