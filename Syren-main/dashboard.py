import streamlit as st
import requests

st.set_page_config(page_title="Syren Dashboard", layout="wide")
st.title("🛡️ Syren: Active Deception Command Center")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Metrics
with st.sidebar:
    st.header("Security Metrics")
    if st.button("Refresh SIEM"):
        m = requests.get("http://localhost:8000/metrics").json()
        st.metric("Total Attacks Intercepted", m['canary_count'])

# Chat bubbles
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Test a prompt..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call FastAPI
    res = requests.post("http://localhost:8000/api/chat", json={"prompt": prompt, "model": "llama3"}).json()
    
    with st.chat_message("assistant"):
        if res['route_taken'] == 'canary':
            st.error(f"High Risk Detected: {res['risk_score']}")
        st.markdown(res['response'])
    
    st.session_state.messages.append({"role": "assistant", "content": res['response']})