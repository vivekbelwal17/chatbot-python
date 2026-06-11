import streamlit as st
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun

# ✅ Load local environment variables from a .env file
load_dotenv()

# Fetch credentials securely from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_BASE_URL = "https://api.weatherstack.com/current?"

def get_user_location():
    """Get approximate location from IP"""
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        return data.get("city", "Unknown"), data.get("country", "Unknown")
    except:
        return "Delhi", "India"  # Default fallback

def get_weather(city="Delhi"):
    """Get current weather"""
    if not WEATHER_API_KEY:
        return "🌤️ Weather configuration missing"
        
    try:
        city, country = get_user_location() if city == "auto" else (city, "IN")
        url = f"{WEATHER_BASE_URL}?q={city},{country}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if "current" in data:
            weather = data["current"]["weather_descriptions"][0]
            temp = data["current"]["temperature"]
            return f"🌤️ **{city}**: {temp}°C, {weather}"
        elif data.get("cod") == 200:
            weather = data["weather"][0]["main"]
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"🌤️ **{city}**: {temp}°C, {desc.title()} ({weather})"
        return "❌ Weather data unavailable"
    except Exception:
        return "🌤️ Weather service temporarily unavailable"

def get_current_time():
    """Get formatted current time"""
    now = datetime.now()
    return now.strftime("%I:%M %p - %B %d, %Y")

class NewChatbot:
    def __init__(self):
        # Pass keys directly to avoid routing confusion in LangChain
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini", 
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE
        )
        self.search = DuckDuckGoSearchRun()
        
        self.custom_responses = {
            "hi": "Hello! 👋 How can I help you today?",
            "hello": "Hey there! 😊 What would you like to chat about?",
            "hey": "Hi! 🚀 Ready to chat?",
            "how are you": "I'm doing great! 😄 How about you?",
            "bye": "Goodbye! 👋 Have a great day!",
            "thank you": "You're welcome! 😊 Happy to help anytime.",
            "thanks": "No problem! 😊 What else?",
            "help": "I can: 💬 Chat, ⏰ Time, 🌤️ Weather, 🔍 Search web! Try 'weather' or 'time'!",
            "who are you": "I'm your AI assistant! 🤖",
            "what can you do": "💬 Chat, ⏰ Current time, 🌤️ Weather, 🔍 Web search, 💻 Code help!",
            "time": f"Current time: {get_current_time()} 🕐",
            "what time": f"Right now it's {get_current_time()} 📅",
            "weather": get_weather(),  
            "current weather": get_weather(),
            "what's the weather": get_weather(),
            "temperature": get_weather()
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Current time: {current_time} | Weather: {weather}"),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])
    
    def get_response(self, user_input):
        user_input_lower = user_input.lower().strip()
        current_time = get_current_time()
        current_weather = get_weather()
        
        # ✅ Check custom triggers first
        for trigger, response in self.custom_responses.items():
            if trigger in user_input_lower:
                return str(response).replace("{current_time}", current_time).replace("{weather}", current_weather)
        
        # Build message context
        lc_messages = []
        for msg in st.session_state.messages + [{"role": "user", "content": user_input}]:
            lc_messages.append(HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]))
        
        search_keywords = ['what is', 'current', 'latest', 'price', 'news']
        if any(kw in user_input_lower for kw in search_keywords):
            try:
                search_result = self.search.run(user_input)
                response = self.llm.invoke(f"Search: {search_result}\nUser: {user_input}\nAnswer:")
            except:
                response = self.llm.invoke(user_input)
        else:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "messages": lc_messages, 
                "input": user_input,
                "current_time": current_time,
                "weather": current_weather
            })
        
        return response.content

# Streamlit UI Setup
def main():
    st.set_page_config(page_title="Smart AI Chatbot", page_icon="🚀")
    st.title("🚀 Smart AI Chatbot")
    
    # ✅ LIVE DISPLAYS
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🕐 Time", get_current_time())
    with col2:
        st.metric("🌤️ Weather", get_weather())
    
    st.info("💬 Try: 'hi', 'weather', 'time', 'help'")
    
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = NewChatbot()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Responding..."):
                response = st.session_state.chatbot.get_response(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    main()