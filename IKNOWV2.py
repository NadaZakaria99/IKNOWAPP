import streamlit as st
from snowflake.snowpark.session import Session
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import snowflake.connector
import pandas as pd
import json
from tavily import TavilyClient

# Custom CSS for styling
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: lightblue;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .css-1d391kg h1 {
        color: #2c3e50;
        font-size: 24px;
    }
    .css-1d391kg .stSelectbox, .css-1d391kg .stCheckbox, .css-1d391kg .stButton {
        margin-bottom: 15px;
    }

    /* Chat input box styling */
    .stTextInput>div>div>input {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 10px 15px;
        font-size: 16px;
        border: 2px solid #2c3e50;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3498db;
        box-shadow: 0 0 8px rgba(52, 152, 219, 0.5);
    }

    /* Chat message styling */
    .stChatMessage {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stChatMessage.user {
        background-color: #3498db;
        color: white;
    }
    .stChatMessage.assistant {
        background-color: #ecf0f1;
        color: #2c3e50;
    }

    /* Sidebar header styling */
    .css-1d391kg h1 {
        font-size: 20px;
        font-weight: bold;
        color: #2c3e50;
    }

    /* Sidebar button styling */
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }

    /* Input box placeholder text */
    .stTextInput>div>div>input::placeholder {
        color: #95a5a6;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
NUM_CHUNKS = 3  # Number of chunks to retrieve
SLIDE_WINDOW = 7  # Number of last conversations to remember
CORTEX_SEARCH_DATABASE = st.secrets["snowflake"]["database"]
CORTEX_SEARCH_SCHEMA = st.secrets["snowflake"]["schema"]
CORTEX_SEARCH_SERVICE = "IKNOW_SEARCH_SERVICE_CS"
COLUMNS = [
    "chunk",
    "relative_path",
    "category"
]

# Snowflake Connection and Session
connection_params = {
    "account": st.secrets["snowflake"]["account"],
    "user": st.secrets["snowflake"]["user"],
    "password": st.secrets["snowflake"]["password"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": st.secrets["snowflake"]["database"],
    "schema": st.secrets["snowflake"]["schema"],
    "role": st.secrets["snowflake"]["role"],
}

# Get active Snowflake session
session = Session.builder.configs(connection_params).create()
root = Root(session)
svc = root.databases[CORTEX_SEARCH_DATABASE].schemas[CORTEX_SEARCH_SCHEMA].cortex_search_services[CORTEX_SEARCH_SERVICE]

# Initialize Tavily client
tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])

def config_options():
    """Configure sidebar options for the application."""
    Course_Content = ['weekone', 'weektwo', 'weekthree', 'weekfour', 'weekfive', 'weeksix', 'weekseven', 'weekeight', 'weeknine', 'weekten', 'weekeleven', 'weektwelve', 'weekthirteen', 'weekfourteen','weekfifteen']
    st.sidebar.selectbox('Select the lecture', Course_Content, key="lec_category")
    st.sidebar.checkbox('Remember chat history?', key="use_chat_history", value=True)
    st.sidebar.button("Start Over", key="clear_conversation", on_click=init_messages)

def init_messages():
    """Initialize chat history."""
    if st.session_state.get("clear_conversation") or "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_message = "Hello! I'm IKNOW, your study partner! 👋 Share your course topics with me, and I'll help you organize, understand, and excel in your learning journey! 📚 What can we explore together today? 🎓"
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})

def get_chat_history():
    """Retrieve recent messages from the chat history."""
    chat_history = []
    start_index = max(0, len(st.session_state.messages) - SLIDE_WINDOW)
    for i in range(start_index, len(st.session_state.messages) - 1):
        chat_history.append(st.session_state.messages[i])
    return chat_history

def summarize_question_with_history(chat_history, question):
    """Summarize the chat history and current question for better context."""
    prompt = f"""
        Based on the chat history below and the question, generate a query that extends the question
        with the chat history provided. The query should be in natural language. 
        Answer with only the query. Do not add any explanation.
        <chat_history>
        {chat_history}
        </chat_history>
        <question>
        {question}
        </question>
    """
    cmd = "select snowflake.cortex.complete(?, ?) as response"
    df_response = session.sql(cmd, params=['mistral-large2', prompt]).collect()
    summary = df_response[0].RESPONSE
    return summary.replace("'", "")

def get_similar_chunks_search_service(query, Course_Content):
    """Search for similar chunks based on query and category."""
    if Course_Content == "ALL":
        response = svc.search(query, COLUMNS, limit=NUM_CHUNKS)
    else:
        filter_obj = {"@eq": {"category": Course_Content}}  # Use "category" instead of "COURSE_CONTENT"
        response = svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS)
    st.sidebar.json(response.json())
    return response.json()

def create_prompt(query, Course_Content):
    """Create a prompt for the LLM with context from search results and chat history."""
    if st.session_state.use_chat_history:
        chat_history = get_chat_history()
        if chat_history:
            question_summary = summarize_question_with_history(chat_history, query)
            prompt_context = get_similar_chunks_search_service(question_summary, Course_Content)
        else:
            prompt_context = get_similar_chunks_search_service(query, Course_Content)
    else:
        prompt_context = get_similar_chunks_search_service(query, Course_Content)
        chat_history = ""

    prompt = f"""
    I am IKNOW, a friendly and witty lecture assistant specializing in helping with {Course_Content} topics! I love assisting students by explaining concepts and finding the best study resources from our collection.

    Conversation Flow:
    1. When suggesting lecture content or topics:
        - Prioritize topics that align with the syllabus or current lecture needs.
        - List all matching topics or resources as numbered options.
        - Ask which topic they'd like to explore in more detail.
    2. When the user selects a topic, provide full details in this format:
        Topic Name:
        Key Concepts Covered (for better understanding):
        Estimated Study Time:
        Explanation/Steps:
        Relevant Examples:
        Additional Resources (if any):

    <chat_history>
    {chat_history}
    </chat_history>

    <context>
    {prompt_context}
    </context>

    User Query: {query}
    Current Course_Content: {Course_Content}

    Response (as IKNOW,study partner):
    """

    json_data = json.loads(prompt_context)
    relative_paths = set(item.get('relative_path', '') for item in json_data['results'])
    return prompt, relative_paths

def complete_query(query, Course_Content):
    """Complete the query using Snowflake Cortex with Mistral Large 2 model."""
    prompt, relative_paths = create_prompt(query, Course_Content)
    
    # Check if the local search returned any results
    if not relative_paths:
        # Fallback to Tavily web search
        web_search_results = tavily_client.search(query)
        if web_search_results:
            # Format the web search results into a response
            web_response = "Here are some web search results that might help:\n\n"
            for result in web_search_results[:3]:  # Limit to top 3 results
                web_response += f"- [{result['title']}]({result['url']})\n"
            return web_response, []
    
    # If local search returned results, proceed as usual
    cmd = """
        select snowflake.cortex.complete(?, ?) as response
    """
    df_response = session.sql(cmd, params=['mistral-large2', prompt]).collect()
    return df_response, relative_paths

def main():
    """Main Streamlit application function."""
    st.title(":books: :mortar_board: Lecture Assistant with History")

    # Track previous category
    if "previous_category" not in st.session_state:
        st.session_state.previous_category = None

    config_options()
    init_messages()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check for category change
    current_category = st.session_state.lec_category
    if (st.session_state.previous_category is not None and 
        current_category != st.session_state.previous_category):
        category_message = f"I see you've switched to {current_category}! Let me help you find {current_category} Lecture! 👨‍🍳"
        st.session_state.messages.append({"role": "assistant", "content": category_message})
        with st.chat_message("assistant"):
            st.markdown(category_message)

    st.session_state.previous_category = current_category

    # Accept user input
    if query := st.chat_input("What topics do you have?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Generate response
        current_category = st.session_state.lec_category
        response, relative_paths = complete_query(query, current_category)
        
        # Handle the response differently based on whether it's from local search or web search
        if isinstance(response, str):  # Web search response
            res_text = response
        else:  # Local search response
            res_text = response[0].RESPONSE

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(res_text)
        st.session_state.messages.append({"role": "assistant", "content": res_text})

        # Display related documents (only for local search)
        if relative_paths:
            with st.sidebar.expander("Related Documents"):
                for path in relative_paths:
                    cmd2 = f"select GET_PRESIGNED_URL(@DOCS, '{path}', 360) as URL_LINK from directory(@DOCS)"
                    df_url_link = session.sql(cmd2).to_pandas()
                    url_link = df_url_link._get_value(0, 'URL_LINK')
                    display_url = f"Document: [{path}]({url_link})"
                    st.sidebar.markdown(display_url)

if __name__ == "__main__":
    main()
