import streamlit as st
import requests
import urllib.parse

# --- 1. JARVIS STEALTH UI ---
st.set_page_config(page_title="JARVIS", layout="wide")

st.markdown("""
    <style>
    /* Kill Streamlit UI */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #000; color: #00d2ff; }
    
    /* Holographic Glow */
    .jarvis-orb {
        width: 120px; height: 120px;
        border: 3px solid #00d2ff;
        border-radius: 50%;
        margin: 20px auto;
        box-shadow: 0 0 30px #00d2ff, inset 0 0 20px #00d2ff;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-family: monospace;
        animation: rotate 4s linear infinite;
    }
    @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

    .system-card {
        background: rgba(0, 210, 255, 0.05);
        border: 1px solid #00d2ff;
        padding: 15px; border-radius: 12px;
        margin-bottom: 20px;
    }
    
    /* Action Button */
    .stButton>button {
        background: linear-gradient(135deg, #00d2ff, #007aff) !important;
        color: black !important; font-weight: bold !important;
        border: none !important; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BRAIN (Groq) ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def jarvis_brain(prompt, sys_msg="You are JARVIS, a helpful AI assistant."):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "Neural link unstable, sir."

# --- 3. THE INTERFACE ---
st.markdown('<div class="jarvis-orb">J.A.R.V.I.S</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["COMMAND", "INTEL", "DEBATE"])

with tab1:
    st.subheader("Neural Command Center")
    cmd = st.text_input("Awaiting Input...", placeholder="Message [Name] on Instagram / Search Marketplace for [Item]")
    
    if cmd:
        cmd_lower = cmd.lower()
        
        # Action: Facebook Marketplace
        if "marketplace" in cmd_lower:
            item = cmd_lower.replace("search marketplace for", "").replace("search", "").strip()
            encoded_item = urllib.parse.quote(item)
            url = f"https://www.facebook.com/marketplace/search/?query={encoded_item}"
            st.markdown(f"<div class='system-card'>Scanning Global Markets for: {item.upper()}</div>", unsafe_allow_html=True)
            st.link_button("OPEN MARKETPLACE", url)

        # Action: Instagram
        elif "instagram" in cmd_lower or "message" in cmd_lower:
            st.markdown("<div class='system-card'>Establishing Secure Instagram Uplink...</div>", unsafe_allow_html=True)
            # This opens the IG app directly to the inbox
            st.link_button("OPEN INSTAGRAM", "https://www.instagram.com/direct/inbox/")

        # General Assistant
        else:
            response = jarvis_brain(cmd, "You are Jarvis. Be polite, concise, and refer to the user as Sir.")
            st.markdown(f"<div class='system-card'>{response}</div>", unsafe_allow_html=True)

with tab2:
    # This is your old 'Search' code integrated
    s_query = st.text_input("Global Search Protocols")
    if s_query:
        with st.spinner("Analyzing News Cycles..."):
            report = jarvis_brain(f"Search context for {s_query}. Summarize deeply.", "You are Jarvis. Provide a deep-dive intelligence report.")
            st.write(report)

with tab3:
    # This is your 'Debate Time' code integrated
    subject = st.text_input("Set Logic Parameters (Subject)")
    if subject:
        arg = st.chat_input("State your argument...")
        if arg:
            rebuttal = jarvis_brain(arg, f"Subject: {subject}. Argue against the user concisely as Jarvis.")
            st.info(rebuttal)