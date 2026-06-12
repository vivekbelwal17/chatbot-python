import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun

# Load local environment variables from a .env file
load_dotenv()

# Fetch credentials securely from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

class Buddy:
    def __init__(self):
        # Pass keys directly to avoid routing confusion in LangChain
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini", 
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE
        )
        # Initialize the search tool instance 
        self.search = DuckDuckGoSearchRun()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a helpful AI assistant. current time: {current_time} | "
             "Weather: {weather} | Live Web Search Context: {search_results}"                
            ),
            MessagesPlaceholder(variable_name="messages"),
            ("human","{input}")
        ])
        
    def get_response(self, user_input, past_messages):
        current_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        
        # Trying to get the realtime weather reports 
        try:
            weather = self.search.run("current weather in Haldwani")
        except Exception:
            weather = "Weather data temporarily unavailable."            
            
        # Fetch search results 
        with st.spinner("Whatever... Looking it up..."):
            try:
                search_results = self.search.run(user_input)
            except Exception:
                search_results = "No relevant live search results found." 

        # FIXED: Everything below is now properly indented!
        langchain_messages = []
        
        # Format memory
        for msg in past_messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
                
        chain = self.prompt | self.llm
        
        # FIXED: Changed to .invoke() and fixed the brackets
        response = chain.invoke({
            "current_time": current_time,
            "weather": weather,
            "search_results": search_results,
            "messages": langchain_messages,
            "input": user_input
        })
        
        return response.content

# Streamlit UI Setup
def main():
    st.set_page_config(page_title="Nonchalant Buddy", page_icon="😎")
    st.title("Nonchalant Buddy 😎")
    
    st.info("Ask Something but I Don't care")
    
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = Buddy()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask anything But I dont care 😎"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            history_for_bot = st.session_state.messages[:-1]
            reply = st.session_state.chatbot.get_response(prompt, history_for_bot)
            
            # FIXED: Indented inside the 'with' block
            st.markdown(reply)
        
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

if __name__ == "__main__":
    main()