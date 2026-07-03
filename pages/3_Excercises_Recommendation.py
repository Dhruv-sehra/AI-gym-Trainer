import ast
import json
import os
import re
import sys
import streamlit as st
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import datetime
from dotenv import load_dotenv 
BASE_DIR = os.path.abspath(os.path.join(__file__, '../../'))
sys.path.append(BASE_DIR)

load_dotenv()
st.title("Weekly Excercises Recommendation")
# Create a placeholder for the chat messages
chat_container = st.empty()
from langchain_groq import ChatGroq

# Define your chatbot model
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("Grok_Api"),
    temperature=0
)

output_parser = StrOutputParser()
# Text input for entering messages

user_height = st.text_input("Enter your height:", "", key = "height")
user_weight = st.text_input("Enter your weight:", "", key = "weight")
push_up = st.text_input("How many push ups can you do in a row:", "", key = "push_up")
user_days = st.text_input("How many days a week do you want to go to the gym: (from 1 to 7)", "", key = "days")
goal = st.radio("Select your fitness goal:", ["Lose weight", "Bulk up", "Cut"], key = "goal")
experience = st.radio("Select your fitness experience:", ["Beginner", "Intermediate", "Advanced"], key = "experience")
current_date = datetime.datetime.now().date()

def change_format(response):
    prompt = ChatPromptTemplate.from_template("""Currently, I am having this weekly plan for my workout: {plan}. I want you to transform it into 
                                            this format: a list of dictionaries where each dictionaries includes: 
                                                \"title\": \"Excercise name - Set x Reps x Weight\",
                                                    \"color\": \"Color hexa code\" # Different pastel color for different focus of the excercise, same color for same focus
                                                    \"start\": \"\" #which is which day excercise start,
                                                    \"end\": \"\" # same day as start,
                                                    \"resourceId\": \"a\" # a to f, randomize it for each excercise
                                                    """)
    chain = prompt | llm | output_parser
    return chain.invoke({"plan":response})


def extract_json_text(text: str):
    if not isinstance(text, str):
        return None
    text = text.strip()
    if text.startswith("```"):
        if "```" in text[3:]:
            _, _, text = text.partition("```")
        text = text.rstrip("`").strip()
    text = re.sub(r"^.*?(\[|\{)", lambda m: m.group(1), text, count=1, flags=re.S)
    if text and text[0] not in "[{":
        return None
    if text.count("[") and text.count("]") and text.rfind("]") > text.find("["):
        square = text[text.find("["):text.rfind("]") + 1]
    else:
        square = None
    if text.count("{") and text.count("}") and text.rfind("}") > text.find("{"):
        curly = text[text.find("{"):text.rfind("}") + 1]
    else:
        curly = None
    candidates = []
    if square:
        candidates.append(square)
    if curly:
        candidates.append(curly)
    candidates.append(text)
    for candidate in candidates:
        candidate = candidate.strip()
        candidate = candidate.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
        if "'" in candidate and '"' not in candidate:
            candidate = candidate.replace("'", '"')
        if not candidate:
            continue
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
        try:
            ast.literal_eval(candidate)
            return candidate
        except Exception:
            pass
    return None


def parse_calendar_response(response):
    if isinstance(response, (list, dict)):
        return response
    if not isinstance(response, str):
        return None
    candidate = extract_json_text(response)
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except Exception:
        pass
    try:
        return ast.literal_eval(candidate)
    except Exception:
        return None


# Function to interact with the chatbot
def chat_with_bot(user_height,user_weight,user_days,goal):
    prompt = ChatPromptTemplate.from_template("""My weight is {kg} kg, my height is {cm} cm, I want to go to the gym {days} days a week,
                                                and I want my gym days to spread through out the week, and my goal is to {goal}. My experience with the gym is {experience}, 
                                                and currently I can only do {pushup} in a row. Can you plan me a weekly workout routine, with detailed excercises (How many rep and set)
                                                and recommended weight, and I want it to be in calendar view?. Starting from today, which is {date}, and I want to have format like this:
                                              Monday - (main focus of excercises) - year/month/date: 
                                              -list of excercises in the day """)
    chain = prompt | llm | output_parser
    return chain.invoke({ "kg": user_weight, "cm": user_height, "days": user_days, "goal": goal, "experience": experience, "pushup": push_up, "date": current_date})
input_placeholder = st.empty()
# Button to send the message
if st.button("Submit"):
    bot_respond = chat_with_bot(user_height,user_weight,user_days,goal)
    saved_response = change_format(bot_respond)
    parsed_response = parse_calendar_response(saved_response)

    st.write(bot_respond)
    #st.write("Calendar events:", parsed_response if parsed_response is not None else saved_response)

    if parsed_response is not None:
        st.session_state['transferred_variable'] = parsed_response
    else:
        st.session_state['transferred_variable'] = saved_response
        st.error("Could not parse the plan into calendar event data. Please check the response format.")
    
    

        



