#! ./env/bin/python
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from dotenv import load_dotenv
from .tools import DEFINED_TOOLS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the AI script")

# OpenRouter model configuration
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize Gemini LLM
model_name = os.getenv("GEMINI_MODEL")
llm = ChatGoogleGenerativeAI(
    model=model_name,
    temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4096")),
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
llm = llm.bind_tools(list(DEFINED_TOOLS.values()))

def lm(msg):
    try:
        lm.invocation = lm.invocation + 1
    except Exception:
        lm.invocation = 1
    logging.info("[msg %d] %s", lm.invocation, msg.content)

###############################################################################

messages = [

    (
        "system",
        """
        You are an AI agent designed to help a non-expert user fill out the 'Ontario Building Code Data Matrix'.
        Your task is to break down complex questions from the form into simpler, more user-friendly questions.

        Your knowledge base is limited to the content provided in this prompt.
        Using these information, ask questions to gather the information needed to complete a specific section of the form.

        your questions must meet the following criteria:

        - The question must be in simple, non-technical language.
        - You are limited to asking multiple choice questions or questions with a numeric value as answer.
        """
    ),
    (
        "system",
        """
        Currently you are interacting with the user to gather required information to answer the following part of the form:

        Question number: {number}
        Original title in the Code Data Matrix Form: {original_title}
        Equivalent of the title in a more comrehensive, question like tone: {question}
        """
    ),
    (
        "system",
        """
        Here is a guide specifically about how to answer the form question you are working on:

        <question_guide>
        {guide}
        </question_guide>
        """
    ),
    (
        "system",
        """
        Here are the relevant parts of Ontario Building Code for your reference:

        <obc_sections>
        {sections}
        </obc_sections>
        """
    ),
    (
        "system",
        """
        If you need any other section of OBC, ask for it and I will provide.
        """
    ),
    (
        "human",
        """
        If you have enough information to answer the form question, provide me the answer. Otherwise, ask your next question and I will provide the answer.
        """
    ),
]

# Initial invocation of AI
ai_msg = llm.invoke(messages)
lm(ai_msg)
messages.append(ai_msg)

# Do what AI wanted us
if len(ai_msg.tool_calls) > 0 :
    logging.info(f"I received %d tool call"%len(ai_msg.tool_calls))
else:
    logging.info("There were no tool calls")

for tool_call in ai_msg.tool_calls:
    logging.info("Running %s",tool_call["name"].lower())
    selected_tool = DEFINED_TOOLS[tool_call["name"].lower()]
    tool_msg = selected_tool.invoke(tool_call)
    messages.append(tool_msg)

# Give it back its requested information
ai_msg = llm.invoke(messages)
lm(ai_msg)
messages.append(ai_msg)

logging.debug(messages)
logging.info("Finished the AI script")
