import streamlit as st
import requests

API_URL = "https://footy-intel-app.blackplant-0a9e640c.eastus.azurecontainerapps.io/ask"

st.set_page_config(page_title="footy_intel", page_icon="⚽")

st.title("⚽ footy_intel")
st.caption("Ask anything about football — tactics, players, live scores, results.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a football question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(API_URL, json={"question": prompt})
                data = response.json()
                answer = data["answer"]
                tool = data["tool_used"]
                latency = data["latency_seconds"]
                tokens = data["tokens_used"]

                st.markdown(answer)
                st.caption(f"🔧 tool: `{tool}` · ⏱ {latency}s · 🪙 {tokens} tokens")
            except Exception as e:
                answer = f"Error: {str(e)}"
                st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})