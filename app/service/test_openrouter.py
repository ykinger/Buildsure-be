#! ./env/bin/python
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenRouter LLM
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1:free"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "4096")),
)

# Simple test without tool calling
messages = [
    ("human", "Hello! Can you introduce yourself?"),
]

response = llm.invoke(messages)
print("Response:", response.content)
print("Model:", response.response_metadata.get('model_name'))
print("Token usage:", response.response_metadata.get('token_usage'))
