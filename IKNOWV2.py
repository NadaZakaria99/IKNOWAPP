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
    .stApp {background-color: lightblue;}
    .css-1d391kg {background-color: #f0f2f6; padding: 20px; border-radius: 10px;}
    .stTextInput>div>div>input {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 10px 15px;
        font-size: 16px;
        border: 2px solid #2c3e50;
    }
    .stChatMessage {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
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

# Snowflake Connection
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

def handle_greeting(query):
    """Check if the message is a greeting."""
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if query.lower().strip() in greetings:
        return True, "Hi! 👋 What would you like to learn about today?"
    return False, None

def get_web_search_results(query):
    """Perform web search using Tavily API."""
    try:
        return tavily_client.search(query=query, search_depth="basic", max_results=3)
    except Exception as e:
        st.error(f"Web search error: {str(e)}")
        return None

def has_relevant_context(prompt_context):
    """Check if Snowflake search returned relevant results."""
    try:
        json_data = json.loads(prompt_context)
        results = json_data.get('results', [])
        for result in results:
            chunk = result.get('chunk', '').strip()
            if len(chunk) > 100 and not chunk.startswith(('Source:', 'http', 'www')):
                return True
        return False
    except Exception as e:
        return False

def config_options():
    """Configure sidebar options."""
    Course_Content = ['weekone', 'weektwo', 'weekthree', 'weekfour', 'weekfive',
                     'weeksix', 'weekseven', 'weekeight', 'weeknine', 'weekten',
                     'weekeleven', 'weektwelve', 'weekthirteen', 'weekfourteen', 'weekfifteen']
    st.sidebar.selectbox('Select the lecture', Course_Content, key="lec_category")
    st.sidebar.checkbox('Remember chat history?', key="use_chat_history", value=True)
    st.sidebar.button("Start Over", key="clear_conversation", on_click=init_messages)

def init_messages():
    """Initialize chat history."""
    if st.session_state.get("clear_conversation") or "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_message = "Hello! I'm IKNOW, your study partner! 👋 What would you like to learn about today?"
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})

def get_chat_history():
    """Get recent chat history."""
    if not st.session_state.get("messages"):
        return []
    start_idx = max(0, len(st.session_state.messages) - SLIDE_WINDOW)
    return st.session_state.messages[start_idx:-1]

def get_similar_chunks_search_service(query, Course_Content):
    """Search for similar chunks in Snowflake."""
    filter_obj = {"@eq": {"category": Course_Content}} if Course_Content != "ALL" else None
    response = svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS)
    return response.json()

def create_prompt(query, Course_Content):
    """Create streamlined prompt for response generation."""
    is_greeting, greeting_response = handle_greeting(query)
    if is_greeting:
        return greeting_response, set()

    chat_history = get_chat_history() if st.session_state.use_chat_history else ""
    prompt_context = get_similar_chunks_search_service(query, Course_Content)
    has_course_content = has_relevant_context(prompt_context)
    
    if has_course_content:
        prompt = f"""
        Based on the course materials, provide a direct and concise answer to: {query}
        
        <context>
        {prompt_context}
        </context>
        """
    else:
        try:
            web_results = get_web_search_results(query)
            if web_results:
                web_context = "\n".join([
                    f"{result['content']}"
                    for result in web_results['results'][:3]
                ])
                prompt_context = json.dumps({
                    "results": [{
                        "chunk": web_context,
                        "relative_path": "web_search_results",
                        "category": "external"
                    }]
                })
                st.info("Using web search for this answer.")
                prompt = f"Provide a direct and concise answer to: {query}\n\nContext:\n{web_context}"
        except Exception as e:
            return "I couldn't find information about that. Please try asking something else.", set()

    json_data = json.loads(prompt_context)
    relative_paths = set(item.get('relative_path', '') for item in json_data['results'])
    return prompt, relative_paths

def complete_query(query, Course_Content):
    """Generate concise response."""
    prompt, relative_paths = create_prompt(query, Course_Content)
    
    if isinstance(prompt, str):
        return [(prompt, "response")], relative_paths
        
    cmd = "select snowflake.cortex.complete(?, ?) as response"
    df_response = session.sql(cmd, params=['mistral-large2', prompt]).collect()
    
    response_text = df_response[0].RESPONSE
    if "web_search_results" in relative_paths:
        response_text = f"Based on web search: {response_text}"
    
    return [(response_text, df_response[0].keys()[0])], relative_paths

def main():
    """Main application function."""
    st.title("📚 Lecture Assistant")
    
    if "previous_category" not in st.session_state:
        st.session_state.previous_category = None

    config_options()
    init_messages()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    current_category = st.session_state.lec_category
    if (st.session_state.previous_category and 
        current_category != st.session_state.previous_category):
        with st.chat_message("assistant"):
            st.markdown(f"Switched to {current_category}. What would you like to know?")

    st.session_state.previous_category = current_category

    if query := st.chat_input("Ask your question"):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        response, relative_paths = complete_query(query, current_category)
        res_text = response[0][0]

        with st.chat_message("assistant"):
            st.markdown(res_text)
        st.session_state.messages.append({"role": "assistant", "content": res_text})

        if relative_paths and "web_search_results" not in relative_paths:
            with st.sidebar.expander("Related Materials"):
                for path in relative_paths:
                    cmd2 = f"select GET_PRESIGNED_URL(@DOCS, '{path}', 360) as URL_LINK from directory(@DOCS)"
                    df_url_link = session.sql(cmd2).to_pandas()
                    url_link = df_url_link._get_value(0, 'URL_LINK')
                    st.sidebar.markdown(f"Document: [{path}]({url_link})")

if __name__ == "__main__":
    main()
