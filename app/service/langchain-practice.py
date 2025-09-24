#! ./env/bin/python
import os
import sys
import logging
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

from dotenv import load_dotenv
from langchain.globals import set_debug

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncToolExecutionError(Exception):
    """Raised when async tool execution fails"""
    pass

@tool
def interact_with_other_llm(riddle: str) -> str:
    """
    Send a riddle to an external (slow) LLM and return its response.
    This is a placeholder that will trigger async execution.
    """
    logger.info(f"Tool called with riddle: {riddle}")

    # In a real implementation, this would:
    # 1. Trigger an async job/webhook
    # 2. Save the current state
    # 3. Exit the script
    # 4. External system processes and calls back

    # For now, we'll raise a special exception to indicate async execution needed
    raise AsyncToolExecutionError(f"ASYNC_TOOL_CALL:{riddle}")

DEFINED_TOOLS = [interact_with_other_llm]

# Load environment variables
load_dotenv()
set_debug(True)

# Initialize Gemini LLM
model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite-preview")
llm = ChatGoogleGenerativeAI(
    model=model_name,
    temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4096")),
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Directory for storage
STORAGE_DIR = Path("storage/conversations")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# --- Persistence Helpers ---
def _hash_id(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

def store_conversation_state(memory: ConversationBufferMemory,
                           pending_tool_call: Optional[Dict[str, Any]] = None) -> str:
    """Persist conversation memory and optional pending tool call state"""
    state = {
        "memory": memory.chat_memory.dict(),
        "pending_tool_call": pending_tool_call,
        "timestamp": datetime.now().isoformat()
    }

    state_text = json.dumps(state, indent=2)
    conv_id = _hash_id(state_text)
    file_path = STORAGE_DIR / f"{conv_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(state_text)

    logger.info(f"Stored conversation state to {file_path}")
    return conv_id

def retrieve_conversation_state(conv_id: str) -> tuple[ConversationBufferMemory, Optional[Dict[str, Any]]]:
    """Load conversation memory and pending tool call state from file"""
    file_path = STORAGE_DIR / f"{conv_id}.json"
    if not file_path.exists():
        raise ValueError(f"No conversation found for id {conv_id}")

    with open(file_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Reconstruct memory
    memory = ConversationBufferMemory(return_messages=True)
    memory.chat_memory = memory.chat_memory.__class__.from_dict(state["memory"])

    pending_tool_call = state.get("pending_tool_call")
    logger.info(f"Retrieved conversation state from {file_path}")

    return memory, pending_tool_call

# --- Agent Setup ---
def create_agent(memory: ConversationBufferMemory) -> AgentExecutor:
    """Create an agent executor with tools and memory"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a riddle designer and facilitator. Your job is to:
1. Create interesting riddles for users
2. When asked to give a riddle to another LLM, use the interact_with_other_llm tool
3. Present the riddle clearly and wait for the external LLM's response
4. Help analyze and discuss the solutions

You have access to a tool that can send riddles to an external slow LLM for solving.
Use this tool when the user asks you to give a riddle to another LLM."""),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(llm, DEFINED_TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=DEFINED_TOOLS,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True
    )

# --- Conversation Flow ---
def start_conversation(user_input: str) -> str:
    """Start a new conversation"""
    logger.info(f"Starting conversation with input: {user_input}")

    memory = ConversationBufferMemory(return_messages=True)
    agent_executor = create_agent(memory)

    try:
        response = agent_executor.invoke({"input": user_input})
        logger.info(f"Agent response: {response['output']}")

        # Normal completion - store and return
        conv_id = store_conversation_state(memory)
        logger.info(f"Conversation completed and stored with id: {conv_id}")
        print(f"[Assistant]: {response['output']}")
        return conv_id

    except AsyncToolExecutionError as e:
        # Tool requested async execution
        error_msg = str(e)
        if error_msg.startswith("ASYNC_TOOL_CALL:"):
            riddle = error_msg.replace("ASYNC_TOOL_CALL:", "")

            # Store the pending tool call state
            pending_tool_call = {
                "tool_name": "interact_with_other_llm",
                "tool_input": {"riddle": riddle},
                "riddle": riddle
            }

            conv_id = store_conversation_state(memory, pending_tool_call)
            logger.info(f"Async tool execution requested. Conversation paused with id: {conv_id}")
            logger.info(f"Riddle sent to external LLM: {riddle}")

            print(f"[System]: Riddle sent to external LLM for processing: '{riddle}'")
            print(f"[System]: Conversation paused. Use conversation ID '{conv_id}' to resume when tool completes.")

            # In a real implementation, you would:
            # 1. Trigger your external LLM job here
            # 2. Pass the conv_id and riddle to the external system
            # 3. The external system will call resume_with_tool_result when done

            return conv_id

    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        raise

def resume_conversation(conv_id: str, user_input: str) -> str:
    """Resume a conversation with new user input"""
    logger.info(f"Resuming conversation {conv_id} with input: {user_input}")

    memory, pending_tool_call = retrieve_conversation_state(conv_id)

    if pending_tool_call:
        logger.warning(f"Conversation has pending tool call: {pending_tool_call}")
        print("[System]: This conversation has a pending tool call. Use resume_with_tool_result instead.")
        return conv_id

    agent_executor = create_agent(memory)

    try:
        response = agent_executor.invoke({"input": user_input})
        logger.info(f"Agent response: {response['output']}")

        conv_id = store_conversation_state(memory)
        logger.info(f"Conversation updated and stored with id: {conv_id}")
        print(f"[Assistant]: {response['output']}")
        return conv_id

    except AsyncToolExecutionError as e:
        # Handle another async tool call
        error_msg = str(e)
        if error_msg.startswith("ASYNC_TOOL_CALL:"):
            riddle = error_msg.replace("ASYNC_TOOL_CALL:", "")

            pending_tool_call = {
                "tool_name": "interact_with_other_llm",
                "tool_input": {"riddle": riddle},
                "riddle": riddle
            }

            conv_id = store_conversation_state(memory, pending_tool_call)
            logger.info(f"Another async tool execution requested. Conversation paused with id: {conv_id}")
            print(f"[System]: Another riddle sent to external LLM: '{riddle}'")
            return conv_id

def resume_with_tool_result(conv_id: str, tool_result: str) -> str:
    """Resume a conversation after async tool execution completes"""
    logger.info(f"Resuming conversation {conv_id} with tool result: {tool_result}")

    memory, pending_tool_call = retrieve_conversation_state(conv_id)

    if not pending_tool_call:
        raise ValueError(f"No pending tool call found for conversation {conv_id}")

    # Reconstruct the tool call and inject the result
    tool_call_id = f"call_{hashlib.md5(pending_tool_call['riddle'].encode()).hexdigest()[:8]}"

    # Add the tool call message to memory
    tool_call_message = AIMessage(
        content="",
        tool_calls=[{
            "name": pending_tool_call["tool_name"],
            "args": pending_tool_call["tool_input"],
            "id": tool_call_id
        }]
    )
    memory.chat_memory.add_message(tool_call_message)

    # Add the tool result message
    tool_result_message = ToolMessage(
        content=tool_result,
        tool_call_id=tool_call_id
    )
    memory.chat_memory.add_message(tool_result_message)

    # Create agent and let it process the tool result
    agent_executor = create_agent(memory)

    try:
        # Agent will see the tool result and generate final response
        response = agent_executor.invoke({"input": "Please continue based on the tool result."})
        logger.info(f"Final agent response: {response['output']}")

        # Clear pending tool call and store final state
        conv_id = store_conversation_state(memory, pending_tool_call=None)
        logger.info(f"Conversation completed after tool result. Final id: {conv_id}")
        print(f"[Assistant]: {response['output']}")
        return conv_id

    except Exception as e:
        logger.error(f"Error processing tool result: {e}")
        raise

# --- CLI Interface ---
def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python script.py start 'your message'")
        print("  python script.py resume <conv_id> 'your message'")
        print("  python script.py tool_result <conv_id> 'tool result'")
        return

    command = sys.argv[1]

    try:
        if command == "start":
            if len(sys.argv) < 3:
                print("Error: Please provide a message to start the conversation")
                return
            user_input = sys.argv[2]
            conv_id = start_conversation(user_input)
            print(f"\n[System]: Conversation ID: {conv_id}")

        elif command == "resume":
            if len(sys.argv) < 4:
                print("Error: Please provide conversation ID and message")
                return
            conv_id = sys.argv[2]
            user_input = sys.argv[3]
            new_conv_id = resume_conversation(conv_id, user_input)
            print(f"\n[System]: Updated conversation ID: {new_conv_id}")

        elif command == "tool_result":
            if len(sys.argv) < 4:
                print("Error: Please provide conversation ID and tool result")
                return
            conv_id = sys.argv[2]
            tool_result = sys.argv[3]
            final_conv_id = resume_with_tool_result(conv_id, tool_result)
            print(f"\n[System]: Final conversation ID: {final_conv_id}")

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        logger.error(f"Error executing command {command}: {e}")
        print(f"Error: {e}")

# --- Example Usage ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # Interactive example
        print("=== Interactive Example ===")
        print("Starting conversation...")
        conv_id = start_conversation("Give the other LLM a fun riddle to solve.")

        if conv_id:
            print(f"\nSimulating external LLM processing...")
            print("External LLM would process the riddle and return a result...")

            # Simulate tool result
            tool_result = "I think the answer might be 'an echo' - it repeats what you say but gets quieter each time!"

            print(f"\nResuming with tool result...")
            final_conv_id = resume_with_tool_result(conv_id, tool_result)
            print(f"Conversation completed with ID: {final_conv_id}")