import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables (e.g., API_KEY)
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
# Instantiate the language model
llm = ChatGroq(
    model="llama3-8b-8192",
    api_key=api_key,
    temperature=0.1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


# File I/O functions for persistent conversation history
def load_history(username):
    if username is None:
        return []
    file_path = f"history_{username}.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        return []


def save_history(username, history):
    if username is None:
        return
    file_path = f"history_{username}.json"
    with open(file_path, "w") as f:
        json.dump(history, f)


def remove_history(username):
    file_path = f"history_{username}.json"
    if os.path.exists(file_path):
        os.remove(file_path)



# Sidebar: User identification and AI character selection
st.sidebar.title("Chat Settings")
username = st.sidebar.text_input("Enter your username", value=None)

# Option to choose character type: Generate New or Custom
character_type = st.sidebar.radio(
    "Select AI Character Source", options=["Generate New", "Custom"]
)

# For storing the generated character in session state
if "generated_character" not in st.session_state:
    st.session_state.generated_character = None

# UI for Generated Character option
if character_type == "Generate New":
    if st.sidebar.button("Generate AI Character"):
        # Prompt the LLM to generate a creative AI character prompt
        generation_prompt = (
            "Generate a creative and engaging personality for an AI chat assistant. "
            "Describe the character in a brief system prompt format (e.g., 'You are a witty and insightful assistant...')."
        )
        generated = llm.invoke([("human", generation_prompt)]).content.strip()
        st.session_state.generated_character = generated

    if st.session_state.generated_character:
        st.sidebar.markdown("**Generated AI Character:**")
        st.sidebar.info(st.session_state.generated_character)
    else:
        st.sidebar.warning(
            "No AI character generated yet. Click the button above to generate one."
        )

# UI for Custom Character option
if character_type == "Custom":
    custom_character = st.sidebar.text_area(
        "Enter your custom AI character prompt", value="You are a knowledgeable expert."
    )

# Button to set/reset the AI character (which resets the conversation)
if st.sidebar.button("Set AI Character", help='This would set the selected AI character and reset the conversation history'):
    system_prompt = None
    if character_type == "Generate New" and st.session_state.generated_character:
        system_prompt = st.session_state.generated_character
    elif character_type == "Custom":
        system_prompt = custom_character
    # else:
    #     system_prompt = "You are a helpful assistant."  # Fallback

    if system_prompt is not None:
        # Reset the conversation history with the chosen system prompt.
        st.session_state.conversation = [("system", system_prompt)]
        remove_history(username)
        st.rerun()

# Load persistent conversation history (if it exists)
if "conversation" not in st.session_state:
    history = load_history(username)
    if history:
        st.session_state.conversation = history

st.title("Chat with Select AI Character")

if username is not None and "conversation" in st.session_state:

    # Display the conversation history
    for role, message in st.session_state.conversation:
        if role == "human":
            st.markdown(f"**{username}:** {message}")
        elif role == "assistant":
            st.markdown(f"**Chatbot:** {message}")
        elif role == "system":
            st.markdown(f"*Chabot Character:* {message}")

    st.markdown("---")
    st.write("Enter your message below:")

    # Form for sending new messages
    with st.form(key="chat_form", clear_on_submit=True):
        user_message = st.text_input("Your message")
        submit_button = st.form_submit_button(label="Send")

    if submit_button and user_message:
        # Append the user's message
        st.session_state.conversation.append(("human", user_message))

        # Call the model with the full conversation history
        response = llm.invoke(st.session_state.conversation)
        assistant_reply = response.content.strip()

        # Append the assistant's reply
        st.session_state.conversation.append(("assistant", assistant_reply))

        # Save the updated conversation history
        save_history(username, st.session_state.conversation)

        # Rerun to update the display
        st.rerun()
else:
    st.write(
        "Kindly enter a username and select an AI character from the sidebar to start a chat with, OR, to continue from an existing conversation"
    )
    st.write(
        "***NOTE:*** Ensure **username** is unique and known to you only, to avoid others gaining access to your conversation history"
    )
