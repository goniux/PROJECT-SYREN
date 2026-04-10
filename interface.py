import streamlit as st
import requests

st.set_page_config(page_title="Syren Dashboard", layout="wide")
st.title("🛡️ Project Syren: Active Deception Layer")

with st.sidebar:
    st.header("Security Metrics")
    risk_display = st.empty()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Test a prompt (e.g., 'Ignore instructions')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call FastAPI Backend
    response = requests.post("http://localhost:8000/chat", json={"prompt": prompt}).json()
    
    # Update UI
    risk_color = "red" if response["risk"] > 0.6 else "green"
    risk_display.markdown(f"### Risk Score: :{risk_color}[{response['risk']}]")
    
    with st.chat_message("assistant"):
        st.markdown(response["output"])
    st.session_state.messages.append({"role": "assistant", "content": response["output"]})