# 🎓IKNOW - Your Study Partner
# 💡Project Overview
IKNOW is an AI-powered study partner that leverages advanced technologies to revolutionize the way you learn. It integrates Snowpark Cortex Search for efficient retrieval of relevant study materials and uses the Mistral Large-2 model for generating accurate and context-aware responses. Whether you need lecture summaries, key exam topics, or intelligent web-based explanations, IKNOW provides real-time assistance through a user-friendly interface, making it your ultimate study partner.

# 🌟Key Features
- Interactive Study Assistant: IKNOW acts as a conversational AI study partner, allowing you to ask questions and get detailed, context-aware answers.
- Lecture Summarization: IKNOW can summarize your lecture materials, highlighting the most important points and key concepts.
- Exam Preparation: IKNOW can suggest the most important parts of your lectures that may appear in exams, helping you focus on high-priority topics.
- Context-Aware Responses: It provides answers based on your course content, ensuring relevance and accuracy.
- Web Search Integration: If the answer isn't in your study materials, IKNOW will perform a web search and provide a concise, filtered response.
- Streaming Output: Responses are streamed in real-time, enhancing the user experience.
- User-Friendly Interface: A clean, intuitive interface makes it easy to interact with IKNOW.
- Chat History: IKNOW remembers your previous queries, allowing for more contextual and coherent conversations.
- Evaluation-Driven Design: Uses TruLens to fine-tune the system for optimal answer relevance and performance.

# 🎯Why IKNOW?
IKNOW is more than just a study tool it's your 24/7 study partner that’s always ready to help, no matter the time or place. Whether you're struggling to understand a complex concept, need a quick summary of a lecture, or want to explore topics beyond your course material, IKNOW is here for you.
- Ask Anything, Anytime: Have a question at 2 AM? Need clarification on a topic you’re too shy to ask in class? IKNOW is available around the clock, ready to provide clear, accurate answers without judgment.
- Personalized Learning: IKNOW adapts to your needs, helping you focus on what matters most, whether it’s exam preparation, understanding tricky concepts, or exploring additional resources.
- Beyond the Classroom: If your course materials don’t have the answers, IKNOW will search the web for you, filtering and summarizing the information so you get only the most relevant insights.
- Streaming Responses for Real-Time Learning: With its real-time streaming output, IKNOW makes learning interactive and engaging, helping you grasp concepts faster and more effectively.
IKNOW is designed to make studying less stressful and more productive. It’s like having a patient, knowledgeable tutor in your pocket, ready to help you succeed anytime, anywhere.

# 🚀Setup and Installation
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
3. Configure database: Execute the SQL scripts to set up the schema, tables, and required functions.
4. Set Up Snowflake Credentials: Create a secrets.toml file in the streamlit directory with your Snowflake credentials:
```
[snowflake]
account = "<your-account>"
user = "<your-user>"
password = "<your-password>"
warehouse = "<your-warehouse>"
database = "<your-database>"
schema = "<your-schema>"
role = "<your-role>"   
[secrets]
TAVILY_API_KEY = "<your_tavily_api_key>"
```
5. Run the Application: streamlit run IKNOW.py

# 📂File Details
- IKNOW.py: The main Streamlit application file that contains the logic for the study assistant.
- requirements.txt: Lists all the Python dependencies required to run the application.
- sql_queries.txt: Contains the SQL queries used to set up the Snowflake database and schema and cortex search.
- upload_your_files.py: A script to upload study materials to Snowflake.
- TruLens_Eval.ipynb: A Jupyter notebook used to evaluate the RAG system's performance.

# 🔌Usage
- Launch the IKNOW App: Open the app and access the intuitive user interface.
- Upload Study Materials: Upload your lecture notes or study materials in supported formats (e.g., PDFs)
- Ask a Question: Enter a study-related query

# 💡How It Works
IKNOW leverages a combination of Snowflake Cortex, Mistral Large 2 model and Tavily Search to provide accurate, context-aware, and real-time responses to your study-related queries. Here's a detailed breakdown of how it works:
1. User Query:
   The user inputs a question or query related to their study material
2. Context Retrieval:
   IKNOW uses Snowflake Cortex Search to retrieve relevant chunks of text from the study materials stored in the Snowflake database. The search is filtered based on the selected lecture or week to ensure the context is relevant.
3. Prompt Generation:
   A prompt is dynamically generated using the retrieved context, the user's query, and the chat history (if enabled). The prompt is designed to guide the Mistral Large 2 model to provide a concise and accurate response.
4. Response Generation with Mistral Large 2:
The generated prompt is passed to Snowflake Cortex, which uses the Mistral Large 2 model to generate a response.
5. Web Search Integration (if needed):
   If the query cannot be answered using the study material, IKNOW performs a web search using Tavily Search. The search results are filtered and summarized, and the response is generated using the Mistral Large 2 model 
   to ensure accuracy and relevance. A note is added to indicate that the answer is based on a web search.
6.Streaming Output:
  The response is streamed to the user in real-time, providing a smooth and interactive experience. This feature enhances user engagement and makes the interaction feel more natural.

# 🕒What's Next for IKNOW?
- Multi-Language Support: Expanding support for multiple languages to serve a global audience.
- Voice Interaction: Add voice-based assistance for enhanced accessibility, benefiting visually impaired users with voice commands and audio responses.

# 📝License
This project is licensed under the MIT License. See the LICENSE file for details.

# ⚡Challenges I Ran Into
- Contextual Relevance: Ensuring that the responses were contextually relevant to the user's query and course material.
- Streaming Output: Implementing real-time streaming of responses to enhance user experience.
- Web Search Integration: Filtering and summarizing web search results to provide concise and accurate answers.

# 📚What I Learned
- Snowflake Cortex: Learned how to leverage Snowflake Cortex for advanced data processing and querying.
- Evaluation Metrics: Learned how to use TruLens to evaluate the performance of RAG systems based on relevance and groundedness.

### IKNOW is here to make your study sessions more productive and less stressful. Give it a try and experience the future of learning! 🚀




