import vertexai
import streamlit as st
import datetime
import os

from vertexai.language_models import ChatModel, InputOutputTextPair

def create_chat_session():
    """Creates a new chat session with the Vertex AI Chat Model.

    Returns:
        A Vertex AI Chat Session object.
    """
    project = os.environ.get('PROJECT')
    location = os.environ.get('LOCATION')
    vertexai.init(project=project, location=location)
    chat_model = ChatModel.from_pretrained("chat-bison")
    context = ""
    examples = []
    chat_session = chat_model.start_chat(
        context=context,
        examples=examples
    )
    return chat_session


# Creates a new chat session if one does not already exist in the session state.
# We are using Streamlit's state management system to store the chat object
# The chat object is useful because it maintains a history of the entire chat
# And will automatically send the chat history along with new prompts
if "chat_session" not in st.session_state:
    st.session_state.chat_session = create_chat_session()
chat = st.session_state.chat_session

# Display the page title
st.title("Chat enabled app using PaLM APIs")

# The welcome message that is displayed to the user when they first open the app
# The chat_message component formats the display with background colors
# and Avatars appropriate for the entity that provided the text
with st.chat_message("assistant"):
    welcome = "Welcome to the chat app. Type something to get started."
    st.markdown(f"{welcome}")

# Iterates through the chat history and displays each message to the user.
for message in chat.message_history:
    if message.author == "bot":
        role = "assistant"
    elif message.author == "user":
        role = "user"
    else:
        role = "unknown"
    with st.chat_message(role):
        st.markdown(f"{message.content}")

# The parameters that are used to generate the response
parameters = {
    "candidate_count": 1,
    "max_output_tokens": 1024,
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40
}

# Gets the user's prompt and displays it in the chat area
if prompt := st.chat_input("What's up?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Makes the call to the API and streams the results into chat area
    with st.chat_message("assistant"):
        responses = chat.send_message_streaming(prompt)
        message_placeholder = st.empty()
        full_response = ""
        for response in responses:
            full_response += response.text
            message_placeholder.markdown(full_response  + "▌")
        message_placeholder.markdown(full_response)