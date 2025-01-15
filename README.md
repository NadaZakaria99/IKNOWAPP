# IKNOW - Your Study Partner
# Project Overview
# Key Features
- Interactive Study Assistant: IKNOW acts as a conversational AI study partner, allowing you to ask questions and get detailed, context-aware answers.
- Lecture Summarization: IKNOW can summarize your lecture materials, highlighting the most important points and key concepts.
- Exam Preparation: IKNOW can suggest the most important parts of your lectures that may appear in exams, helping you focus on high-priority topics.
- Context-Aware Responses: It provides answers based on your course content, ensuring relevance and accuracy.
- Web Search Integration: If the answer isn't in your study materials, IKNOW will perform a web search and provide a concise, filtered response.
- Streaming Output: Responses are streamed in real-time, enhancing the user experience.
- User-Friendly Interface: A clean, intuitive interface makes it easy to interact with IKNOW.
- Chat History: IKNOW remembers your previous queries, allowing for more contextual and coherent conversations.
- Evaluation-Driven Design: Uses TruLens to fine-tune the system for optimal answer relevance and performance.

# Why IKNOW?
IKNOW is more than just a study tool it's your 24/7 study partner that’s always ready to help, no matter the time or place. Whether you're struggling to understand a complex concept, need a quick summary of a lecture, or want to explore topics beyond your course material, IKNOW is here for you.
- Ask Anything, Anytime: Have a question at 2 AM? Need clarification on a topic you’re too shy to ask in class? IKNOW is available around the clock, ready to provide clear, accurate answers without judgment.
- Personalized Learning: IKNOW adapts to your needs, helping you focus on what matters most, whether it’s exam preparation, understanding tricky concepts, or exploring additional resources.
- Beyond the Classroom: If your course materials don’t have the answers, IKNOW will search the web for you, filtering and summarizing the information so you get only the most relevant insights.
- Streaming Responses for Real-Time Learning: With its real-time streaming output, IKNOW makes learning interactive and engaging, helping you grasp concepts faster and more effectively.
IKNOW is designed to make studying less stressful and more productive. It’s like having a patient, knowledgeable tutor in your pocket, ready to help you succeed anytime, anywhere.

# Setup and Installation
## Prerequisites
Before you begin, ensure you have the following installed:
- Python 3.9 or higher
- Streamlit
- Snowflake Snowpark Python
- Snowflake Core
- LangChain
- Tavily Python
## Installation Steps
1. Clone the Repository: git clone https://github.com/yourusername/IKNOW.git
cd IKNOW
2. Install Dependencies: pip install -r requirements.txt
3. Set Up Snowflake Credentials:
   Create a secrets.toml file in the streamlit directory with your Snowflake credentials:

   [snowflake]

   account = "your_account"

   user = "your_user"

   password = "your_password"

   warehouse = "your_warehouse"

   database = "your_database"
   
   schema = "your_schema"
   
   role = "your_role"
    
   [secrets]
   
   TAVILY_API_KEY = "your_tavily_api_key"
   
5. Run the Application: streamlit run IKNOW.py
