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
from app.models import ProjectDataMatrix, DataMatrix, Section, Message

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

    def _convert_to_langchain_message(self, message: Message) -> BaseMessage:
        """Convert SQLModel Message to LangChain BaseMessage."""
        if message.type == "human":
            return HumanMessage(content=message.content)
        elif message.type == "ai":
            return AIMessage(content=message.content)
        elif message.type == "system":
            return SystemMessage(content=message.content)
        else:
            # Default to HumanMessage for unknown types
            return HumanMessage(content=message.content)

    def _convert_to_sqlmodel_message(self,
                                   message: BaseMessage,
                                   project_data_matrix_id: str,
                                   user_id: Optional[str] = None) -> Message:
        """Convert LangChain BaseMessage to SQLModel Message."""
        from uuid import uuid4

        if isinstance(message, HumanMessage):
            message_type = "human"
        elif isinstance(message, AIMessage):
            message_type = "ai"
        elif isinstance(message, SystemMessage):
            message_type = "system"
        elif isinstance(message, ToolMessage):
            message_type = "tool"
        else:
            message_type = "unknown"

        return Message(
            id=str(uuid4()),
            project_data_matrix_id=project_data_matrix_id,
            user_id=user_id,
            type=message_type,
            content=message.content
        )

    def _get_langchain_messages(self, section: ProjectDataMatrix) -> List[BaseMessage]:
        """Convert SQLModel messages to LangChain messages for prompt template."""
        if not section.messages:
            return []

        return [self._convert_to_langchain_message(msg) for msg in section.messages]

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

    async def what_next(self, section: ProjectDataMatrix, db_session: AsyncSession, human_answer: str = None, user_id: Optional[str] = None) -> str:
        """Main function to interact with user - converted from ai.py."""
        try:
            # Validate message sequence
            if human_answer is None and section.messages and section.messages[-1].type == "ai":
                raise Exception("last message was from AI, a human message is needed next")

            # Convert human answer to SQLModel Message and add to section
            if human_answer is not None:
                human_message = self._convert_to_sqlmodel_message(
                    HumanMessage(content=human_answer),
                    project_data_matrix_id=section.id,
                    user_id=user_id
                )
                section.messages.append(human_message)
                # Persist the human message to database
                db_session.add(human_message)
                await db_session.commit()

            # Get LangChain messages for prompt template
            langchain_messages = self._get_langchain_messages(section)

            prompt = self.prompt_template.invoke({
                "title": section.data_matrix.title,
                "number": section.data_matrix.number,
                "question": section.data_matrix.question,
                "guide": section.data_matrix.guide,
                "knowledge_base": section.data_matrix.knowledge_bases,
                "history": langchain_messages,
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

            # Save AI message to database before tool call
            ai_sql_message = self._convert_to_sqlmodel_message(
                ai_msg,
                project_data_matrix_id=section.id,
                user_id=user_id
            )
            section.messages.append(ai_sql_message)
            db_session.add(ai_sql_message)
            await db_session.commit()

            # Execute tool call
            tool_msg = selected_tool.invoke(tool_call)

            # Save tool message to database
            tool_sql_message = self._convert_to_sqlmodel_message(
                tool_msg,
                project_data_matrix_id=section.id,
                user_id=user_id
            )
            section.messages.append(tool_sql_message)
            db_session.add(tool_sql_message)
            await db_session.commit()

            return json.loads(tool_msg.content)

        except Exception as e:
            logging.error(f"Error in what_to_pass_to_user: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

