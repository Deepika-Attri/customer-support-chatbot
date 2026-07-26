import streamlit as st
from chatbot import chatbot_response

st.set_page_config(page_title="Customer Support Bot", page_icon="🤖", layout="centered")

st.sidebar.title("Customer Support")

st.sidebar.write("Ask me about:")
st.sidebar.write("- Business Hours")
st.sidebar.write("- Refunds")
st.sidebar.write("- Shipping")
st.sidebar.write("- Contact")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []

    if "last_intent" in st.session_state:
        del st.session_state["last_intent"]

    st.rerun()

# Create chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show old messages
for message in st.session_state.messages:

    if message["role"] == "user":
        with st.chat_message("user", avatar="👩"):
            st.write(message["content"])

    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(message["content"])

# User input
question = st.chat_input("Ask me anything...")

if question:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})

    last_intent = st.session_state.get("last_intent")

    answer, intent = chatbot_response(question, last_intent)

    # Save the Intent
    st.session_state.last_intent = intent

    # Show bot message
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Refresh page
    st.rerun()
