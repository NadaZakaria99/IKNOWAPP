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
    .stApp {
        background-color: lightblue;
    }
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
    .css-1d391kg h1 {
        font-size: 20px;
        font-weight: bold;
        color: #2c3e50;
    }
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
    .stTextInput>div>div>input::placeholder {
        color: #95a5a6;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
NUM_CHUNKS = 3
SLIDE_WINDOW = 7
CORTEX_SEARCH_DATABASE = st.secrets["snowflake"]["database"]
CORTEX_SEARCH_SCHEMA = st.secrets["snowflake"]["schema"]
CORTEX_SEARCH_SERVICE = "IKNOW_SEARCH_SERVICE_CS"
TAVILY_API_KEY = st.secrets["tavily"]["api_key"]
COLUMNS = ["chunk", "relative_path", "category"]

# Initialize Tavily client
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

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

session = Session.builder.configs(connection_params).create()
root = Root(session)
svc = root.databases[CORTEX_SEARCH_DATABASE].schemas[CORTEX_SEARCH_SCHEMA].cortex_search_services[CORTEX_SEARCH_SERVICE]

def get_web_search_results(query):
    """Perform web search using Tavily API."""
    try:
        search_result = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        return search_result
    except Exception as e:
        st.error(f"Web search error: {str(e)}")
        return None

def has_relevant_context(prompt_context):
    """Check if the Snowflake search returned relevant results."""
    try:
        json_data = json.loads(prompt_context)
        results = json_data.get('results', [])
        
        for result in results:
            chunk = result.get('chunk', '').strip()
            if len(chunk) > 100 and not chunk.startswith(('Source:', 'http', 'www')):
                return True
        return False
    except Exception as e:
        st.error(f"Error checking context: {str(e)}")
        return False

def config_options():
    """Configure sidebar options."""
    Course_Content = [
        'weekone', 'weektwo', 'weekthree', 'weekfour', 'weekfive',
        'weeksix', 'weekseven', 'weekeight', 'weeknine', 'weekten',
        'weekeleven', 'weektwelve', 'weekthirteen', 'weekfourteen', 'weekfifteen'
    ]
    st.sidebar.selectbox('Select the lecture', Course_Content, key="lec_category")
    st.sidebar.checkbox('Remember chat history?', key="use_chat_history", value=True)
    st.sidebar.button("Start Over", key="clear_conversation", on_click=init_messages)

def init_messages():
    """Initialize chat history."""
    if st.session_state.get("clear_conversation") or "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_message = "Hello! I'm IKNOW, your study partner! 👋 Share your course topics with me, and I'll help you organize, understand, and excel in your learning journey! 📚"
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})

def get_chat_history():
    """Retrieve recent chat history."""
    chat_history = []
    start_index = max(0, len(st.session_state.messages) - SLIDE_WINDOW)
    for i in range(start_index, len(st.session_state.messages) - 1):
        chat_history.append(st.session_state.messages[i])
    return chat_history

def summarize_question_with_history(chat_history, question):
    """Generate a summary query based on chat history and current question."""
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
    return df_response[0].RESPONSE.replace("'", "")

def get_similar_chunks_search_service(query, Course_Content):
    """Search for relevant content chunks."""
    if Course_Content == "ALL":
        response = svc.search(query, COLUMNS, limit=NUM_CHUNKS)
    else:
        filter_obj = {"@eq": {"category": Course_Content}}
        response = svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS)
    return response.json()

def create_prompt(query, Course_Content):
    """Create prompt with context from course materials or web search."""
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

    # Check for relevant context and use web search if needed
    if not has_relevant_context(prompt_context):
        web_results = get_web_search_results(query)
        if web_results:
            web_context = "Information from web search:\n" + "\n".join([
                f"Source: {result['url']}\n{result['content']}"
                for result in web_results['results'][:3]
            ])
            prompt_context = {
                "results": [{
                    "chunk": web_context,
                    "relative_path": "web_search_results",
                    "category": "external"
                }]
            }
            prompt_context = json.dumps(prompt_context)
            st.info("No relevant information found in course materials. Using web search results.")

    prompt = f"""
    I am IKNOW, a friendly and helpful lecture assistant specializing in {Course_Content} topics! 
    When using web search results, I'll clearly indicate that the information comes from external sources.

    Instructions for response:
    - If using course materials, focus on the provided lecture content
    - If using web search results, start the response with "Based on web search results:"
    - Always maintain an educational and informative tone
    - Provide specific examples when possible

    <chat_history>
    {chat_history}
    </chat_history>

    <context>
    {prompt_context}
    </context>

    User Query: {query}
    Current Course_Content: {Course_Content}

    Response (as IKNOW, study partner):
    """

    json_data = json.loads(prompt_context)
    relative_paths = set(item.get('relative_path', '') for item in json_data['results'])
    return prompt, relative_paths

def complete_query(query, Course_Content):
    """Generate response using Snowflake Cortex."""
    prompt, relative_paths = create_prompt(query, Course_Content)
    cmd = "select snowflake.cortex.complete(?, ?) as response"
    df_response = session.sql(cmd, params=['mistral-large2', prompt]).collect()
    
    response_text = df_response[0].RESPONSE
    if "web_search_results" in relative_paths:
        if not response_text.startswith("Based on web search results:"):
            response_text = "Based on web search results:\n" + response_text
    
    return [(response_text, df_response[0].keys()[0])], relative_paths

def main():
    """Main application function."""
    st.title(":books: :mortar_board: Lecture Assistant with History")

    if "previous_category" not in st.session_state:
        st.session_state.previous_category = None

    config_options()
    init_messages()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle category changes
    current_category = st.session_state.lec_category
    if (st.session_state.previous_category is not None and 
        current_category != st.session_state.previous_category):
        category_message = f"I see you've switched to {current_category}! Let me help you find {current_category} Lecture! 📚"
        st.session_state.messages.append({"role": "assistant", "content": category_message})
        with st.chat_message("assistant"):
            st.markdown(category_message)

    st.session_state.previous_category = current_category

    # Handle user input
    if query := st.chat_input("What topics do you have?"):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        response, relative_paths = complete_query(query, current_category)
        res_text = response[0][0]

        with st.chat_message("assistant"):
            st.markdown(res_text)
        st.session_state.messages.append({"role": "assistant", "content": res_text})

        # Display related documents for course content
        if relative_paths and "web_search_results" not in relative_paths:
            with st.sidebar.expander("Related Documents"):
                for path in relative_paths:
                    cmd2 = f"select GET_PRESIGNED_URL(@DOCS, '{path}', 360) as URL_LINK from directory(@DOCS)"
                    df_url_link = session.sql(cmd2).to_pandas()
                    url_link = df_url_link._get_value(0, 'URL_LINK')
                    display_url = f"Document: [{path}]({url_link})"
                    st.sidebar.markdown(display_url)

if __name__ == "__main__":
    main()
