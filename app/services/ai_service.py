"""
AI Service Module
Handles LangChain integration with Google Gemini for question generation.
Merged functionality from app/service/ai.py
"""

import logging
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.globals import set_debug
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.tools import DEFINED_TOOLS
# from app.services.obc_query_service import OBCQueryService
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import Settings, settings
from app.models import ProjectDataMatrix, DataMatrix, Section

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Enable debug mode
set_debug(True)

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered question generation using Google Gemini."""

    def __init__(self):
        # self.db = db
        self.settings: Settings = settings
        self.llm = None

        # Constants from ai.py
        self.tool_calling_quota = 10

        # Prompt template from ai.py
        self.prompt_template = ChatPromptTemplate([
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
                    {knowledge_base}
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

        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the Google Gemini LLM client with tools binding."""
        try:
            # Use settings for all configuration
            model_name = self.settings.gemini_model
            temperature = self.settings.gemini_temperature
            max_tokens = self.settings.gemini_max_tokens
            api_key = self.settings.gemini_api_key

            # Initialize Google Gemini LLM
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                google_api_key=api_key,
                timeout=self.settings.ai_timeout_seconds
            )

            # Bind tools and force LLM to use tools only (from ai.py approach)
            self.llm = self.llm.bind_tools(list(DEFINED_TOOLS.values()), tool_choice="any")

            logging.info("Google Gemini LLM initialized successfully with tools")
        except Exception as e:
            logging.error(f"Failed to initialize Google Gemini LLM: {str(e)}")
            raise
        """Get OBC content using the pivot table relationship."""
    async def what_next(self, section: ProjectDataMatrix,  human_answer: str = None) -> str:
        """Main function to interact with user - converted from ai.py."""
        try:

            # history = await self.load_chat_history(section.id)
            if human_answer is None and section.messages != [] and section.messages[len(section.messages)-1].type == "ai":
                raise Exception("last message was from AI, a human message is needed next")

            if human_answer is not None:
                section.messages.append(HumanMessage(human_answer))

            prompt = self.prompt_template.invoke({
                "title": section.data_matrix.title,
                "number": section.data_matrix.number,
                "question": section.data_matrix.question,
                "guide": section.data_matrix.guide,
                "knowledge_base": section.data_matrix.knowledge_bases,
                "history": [message.content for message in section.messages],
            })

            ai_msg = self.llm.invoke(prompt)

            if len(ai_msg.tool_calls) == 0:
                return {
                    "status": "error",
                    "message": "no request for calling tools"
                }
            if len(ai_msg.tool_calls) > 1:
                return {
                    "status": "error",
                    "message": "too many tools requested"
                }

            tool_call = ai_msg.tool_calls[0]
            logging.info("Running %s", tool_call["name"].lower())
            selected_tool = DEFINED_TOOLS[tool_call["name"].lower()]
            #TODO: Grab ai message and add it to messages
            tool_msg = selected_tool.invoke(tool_call)
            # TODO: save history after tool call
            return json.loads(tool_msg.content)

        except Exception as e:
            logging.error(f"Error in what_to_pass_to_user: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

