#! ./env/bin/python
import os
import logging
import json
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.prompts import PromptTemplate

from app.service.tools import DEFINED_TOOLS, get_form_section_info, set_history
from app.database import get_db, get_async_db
from app.services.obc_query_service import OBCQueryService

async def _get_async_obc_content(section):
    async for db in get_async_db():
        obc = OBCQueryService(db)
        section["sections"] = []
        for x in section["obc_reference"]:
            x["content"] = await obc.find_by_reference(x["section"])
            section["sections"].append(x["content"])
        return section

def get_obc_content(section):
    return asyncio.run(_get_async_obc_content(section))
from langchain.globals import set_debug

set_debug(True)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the AI script")

# Initialize Gemini LLM
model_name = os.getenv("GEMINI_MODEL")
llm = ChatGoogleGenerativeAI(
    model=model_name,
    temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4096")),
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Bind tools and force LLM to use tools only
llm = llm.bind_tools(list(DEFINED_TOOLS.values()), tool_choice="any")

#########################################################################
#                Use these hardcode values for testing                  #
#########################################################################

form_question = {
    "number": "3.02",
    "title": "Major Occupancy Classification",
    "question": "What are the major occupancy groups in the building? What is their use?",
    "guide": "Identify each of the major occupancy group in the building and describe their use. (e.g. D - Business and Personal Services / Medical Clinic). Refer to OBC 3.1.2. and to Appendix A to the building code for multiple major occupancies. Refer also to Hazard Index tables 11.2.1.1.B – 11.2.1.1.N in Part 11 of the building code and A-3.1.2.1 (1) of Appendix A to the building code for assistance in determining or classifying major occupancies."
}

#########################################################################
#                    Do not modify these templates                      #
#########################################################################

prompt_template = ChatPromptTemplate([
    (
        "system",
        """
        <your_role_and_purpose>
        You are an AI agent designed to help a non-expert user fill out the 'Ontario Building Code Data Matrix'.
        Your task is to break down complex questions from the form into simpler, more user-friendly questions.

        Your knowledge base is limited to the content provided in this prompt.
        Using these information, ask questions to gather the information needed to complete a specific section of the form.

        your questions must meet the following criteria:

        - The question must be in simple, non-technical language.
        - Aim to simplify questions for the user, for example instead of directly asking about a technical term "major occupancy", ask the user what kind of building this is, and provide sensible non-technical options that will help you map the answer to the technical term.
        - When possible, provide examples to help the user understand your question or suggested options better.
        - You are limited to asking multiple choice questions or questions with a numeric value as answer.
        </your_role_and_purpose>
        ---
        <current_task>
        Currently you are interacting with the user to gather required information to answer the following part of the form:

        Section number: {number}
        Original title in the Code Data Matrix Form: {title}
        The question you are trying to answer: {question}
        </current_task>
        ---
        <additional_helpful_information>
        Here is a guide specifically about how to answer the form question you are working on:

            <question_guide>
            {guide}
            </question_guide>

        Here are the relevant parts of Ontario Building Code for your reference:

            <obc_sections>
            {sections}
            </obc_sections>

        </additional_helpful_information>
        ---
        If you need any other section of OBC, ask for it and I will provide.
        """
    ),
    (
        "human",
        """
        If you have enough information to answer the form question, provide me the answer. Otherwise, ask your next question and I will respond to you.
        """
    ),
    MessagesPlaceholder("history")
])

# How many times we invoke LLM after fulfilling its tool calling request
tool_calling_quota = 10

# Define history storage directory
HISTORY_DIR = Path("storage/history")


MESSAGE_TYPES = {
    "human": HumanMessage,
    "ai": AIMessage,
    "system": SystemMessage,
    "tool": ToolMessage
}

# Let exceptions bubble for now
# Save chat history to a json file
def save_chat_history(num: str, history: list[BaseMessage]):
    file_path = HISTORY_DIR / f"{num}.json"
    serializable_history = []
    for msg in history:
        serializable_history.append({"type": msg.type, "content": msg.content})
    with open(file_path, "w") as f:
        json.dump(serializable_history, f, indent=4)
    logging.info(f"Chat history for section {num} saved to {file_path}")

def clear_chat_history(num: str):
    logging.info(f"Clearing history for section {num}")
    save_chat_history(num, [])

# Let exceptions bubble for now
# Reconstruct Langchain message objects
def load_chat_history(id: str) -> list[BaseMessage]:
    file_path = HISTORY_DIR / f"{id}.json"
    if not file_path.exists():
        logging.error(f"No chat history found for section {id} at {file_path}")
        return []
    with open(file_path, "r") as f:
        loaded_history = json.load(f)

    return [
        MESSAGE_TYPES[msg["type"]](**msg)
        for msg in loaded_history
    ]

def what_to_pass_to_user(num: str, human_answer:str = None) -> str:
    current_section = get_form_section_info(num)
    get_obc_content(current_section)

    history = load_chat_history(num)
    if human_answer is None and history != [] and history[len(history)-1].type == "ai":
        raise Exception("last message was from AI, a human message is needed next")
    set_history(history)
    if human_answer is not None:
        history.append(HumanMessage(human_answer))
    prompt = prompt_template.invoke({**current_section, "history": history})
    ai_msg = llm.invoke(prompt)

    if len(ai_msg.tool_calls) == 0 :
        return {
            "status": "error",
            "message": "no request for calling tools"
        }
    if len(ai_msg.tool_calls) > 1 :
        return {
            "status": "error",
            "message": "too many tools requested"
        }

    tool_call = ai_msg.tool_calls[0]
    logging.info("Running %s",tool_call["name"].lower())
    selected_tool = DEFINED_TOOLS[tool_call["name"].lower()]
    tool_msg = selected_tool.invoke(tool_call)
    save_chat_history(num, history) # Save history after tool call
    return json.loads(tool_msg.content)

# what_to_pass_to_user("3.02")
# what_to_pass_to_user("3.02", "Industrial (e.g., factories, warehouses)")
# what_to_pass_to_user("3.02", "No")
# what_to_pass_to_user("3.02", "Yes")
# logging.info("Done")
