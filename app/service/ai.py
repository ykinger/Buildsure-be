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
    # (
    #     "system",
    #     """
    #     You are an expert AI assistant specializing in the Ontario Building Code (OBC).
    #     Your purpose is to help architects accurately and efficiently complete a standardized building compliance form, known as code data matrix.
    #     The user interacting with you is not familiar with technical terms. You need to ask questions in simplified form to get closer to the answer for
    #     the question from code data matrix that you are tasked to find the answer to.
    #     The user will provide answers to you to the best they can until you get to a definitive answer for the form question you are tasked with.
    #     You have tools at your disposal to retreive relevant sections of the OBC in case you need a reference.
    #     Your interactions with the user is limited to tools you have, do not ask questions that require anything outside those tools.
    #     For example, if you nee to ask a question turn it into form of multiple choice questions only.

    #     You are currently finding the answer to <question-number>3.02</question-number> <question-title>Major Occupancy Classification</question-title>.
    #     If you do have the answer to the question, present it for verification.
    #     If you need additional information, use the tools available to you to get the information you need.
    #     """
    # ),
    # (
    #     "human",
    #     """
    #     Identify each of the major occupancy group in the building and describe their use. (e.g. D - Business and
    #     Personal Services / Medical Clinic). Refer to OBC 3.1.2. and to Appendix A to the building code for multiple
    #     major occupancies. Refer also to Hazard Index tables 11.2.1.1.B – 11.2.1.1.N in Part 11 of the building code
    #     and A-3.1.2.1 (1) of Appendix A to the building code for assistance in determining or classifying major
    #     occupancies.
    #     """
    # ),
    (
        "system",
        "exclusively use tool_call for getting information"
    ),
    (
        "system",
        """
        You are an AI assistant expert at reading the Ontario Building Code (OBC) and understaidng it, helping the user to fill a form with
        questions that could be answered by referring to specific sections of OBC, known as "Code Data Matrix".
        The user filling this form is a non-technical user not familiar with technical terminology require required to fully understand the OBC.
        You are provided with a list of clarifying questions related to current main form question from code data matrix that will help figure out
        the answer to form question.
        The user is not able to type their answer. They are interacting with you through a restricted user interface that is only capable of interactions using
        the tools provided to you (tool_call).
        If you find the information sufficient to answer the form question, provide the answer. If not, use the tools available to you to ask questions.
        You can retreive sections of OBC to refer to, and ask questions to the user to get more clarification.
        - Exclusively use tool_call for your interactions.
        - Always make sure you have relevant sections of OBC before starting the analysis
        """
    ),
    (
        "human",
        """
        Help me answer form question <number>3.02</number> <title>Major Occupancy Group</title>
        
        In order to do so, dentify each of the major occupancy group in the building and describe their use. (e.g. D - Business and
        Personal Services / Medical Clinic). Refer to OBC 3.1.2. and to Appendix A to the building code for multiple
        major occupancies. Refer also to Hazard Index tables 11.2.1.1.B - 11.2.1.1.N in Part 11 of the building code
        and A-3.1.2.1 (1) of Appendix A to the building code for assistance in determining or classifying major
        occupancies.

        Limit your questions to the tools availabel to use.
        """
    ),
    # (
    #     "human",
    #     "ask me a multiple choice question to test your access to tools"
    # ),

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
