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

from app.services.tools import DEFINED_TOOLS, get_form_section_info, set_history
from app.services.obc_query_service import OBCQueryService
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import Settings, settings
from app.utils.prompt_builder import PromptBuilder


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Enable debug mode
set_debug(True)

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered question generation using Google Gemini."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings: Settings = settings
        self.llm = None
        self.prompt_builder = PromptBuilder("assets/prompt-parts")

        # Constants from ai.py
        self.tool_calling_quota = 10
        self.HISTORY_DIR = Path("storage/history")

        # Message types mapping
        self.MESSAGE_TYPES = {
            "human": HumanMessage,
            "ai": AIMessage,
            "system": SystemMessage,
            "tool": ToolMessage
        }

        # Hardcoded form question for testing
        self.form_question = {
            "number": "3.02",
            "title": "Major Occupancy Classification",
            "question": "What are the major occupancy groups in the building? What is their use?",
            "guide": "Identify each of the major occupancy group in the building and describe their use. (e.g. D - Business and Personal Services / Medical Clinic). Refer to OBC 3.1.2. and to Appendix A to the building code for multiple major occupancies. Refer also to Hazard Index tables 11.2.1.1.B – 11.2.1.1.N in Part 11 of the building code and A-3.1.2.1 (1) of Appendix A to the building code for assistance in determining or classifying major occupancies."
        }

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

    async def get_obc_content(self, section):
        """Get OBC content using injected database session."""
        obc = OBCQueryService(self.db)
        section["sections"] = []
        for x in section["obc_reference"]:
            x["content"] = await obc.find_by_reference(x["section"])
            section["sections"].append(x["content"])
        return section

    def save_chat_history(self, num: str, history: list[BaseMessage]):
        """Save chat history to a json file."""
        file_path = self.HISTORY_DIR / f"{num}.json"
        serializable_history = []
        for msg in history:
            serializable_history.append({"type": msg.type, "content": msg.content})

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(serializable_history, f, indent=4)
        logging.info(f"Chat history for section {num} saved to {file_path}")

    def clear_chat_history(self, num: str):
        """Clear chat history for a section."""
        logging.info(f"Clearing history for section {num}")
        self.save_chat_history(num, [])

    def load_chat_history(self, id: str) -> list[BaseMessage]:
        """Reconstruct Langchain message objects from saved history."""
        file_path = self.HISTORY_DIR / f"{id}.json"
        if not file_path.exists():
            logging.error(f"No chat history found for section {id} at {file_path}")
            return []

        try:
            with open(file_path, "r") as f:
                loaded_history = json.load(f)

            return [
                self.MESSAGE_TYPES[msg["type"]](**msg)
                for msg in loaded_history
            ]
        except Exception as e:
            logging.error(f"Error loading chat history for {id}: {str(e)}")
            return []

    async def what_to_pass_to_user(self, num: str, human_answer: str = None) -> str:
        """Main function to interact with user - converted from ai.py."""
        try:
            current_section = get_form_section_info(num)
            if not current_section:
                return {
                    "status": "error",
                    "message": f"Section {num} not found"
                }

            await self.get_obc_content(current_section)

            history = self.load_chat_history(num)
            if human_answer is None and history != [] and history[len(history)-1].type == "ai":
                raise Exception("last message was from AI, a human message is needed next")

            set_history(history)
            if human_answer is not None:
                history.append(HumanMessage(human_answer))

            prompt = self.prompt_template.invoke({**current_section, "history": history})
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
            tool_msg = selected_tool.invoke(tool_call)
            self.save_chat_history(num, history)  # Save history after tool call
            return json.loads(tool_msg.content)

        except Exception as e:
            logging.error(f"Error in what_to_pass_to_user: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def generate_question(
        self,
        section_number: int,
        ontario_chunks: List[Dict[str, Any]],
        form_questions_and_answers: List[str] = None,
        clarifying_questions_and_answers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a contextual question for the given section using Gemini.

        Args:
            section_number: The current section number
            ontario_chunks: Relevant Ontario Building Code chunks
            form_questions_and_answers: Previously answered form questions
            clarifying_questions_and_answers: Previous clarifying Q&As

        Returns:
            Dict containing the generated question and metadata
        """
        try:
            # Prepare context data
            form_qa = form_questions_and_answers or []
            clarifying_qa = clarifying_questions_and_answers or []

            # Build the prompt using the existing prompt builder
            prompt_text = self.prompt_builder.render(
                current_question_number=str(section_number),
                form_questions_and_answers=form_qa,
                clarifying_questions_and_answers=clarifying_qa
            )

            # Add ontario chunks context to the prompt
            ontario_context = self._format_ontario_chunks(ontario_chunks)
            enhanced_prompt = f"{prompt_text}\n\n### Relevant Ontario Building Code Sections:\n{ontario_context}"

            # Create the chat prompt template
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    "You are an expert Ontario Building Code consultant helping users complete "
                    "building permit applications. Generate clear, specific questions based on "
                    "the provided context and building code requirements."
                ),
                HumanMessagePromptTemplate.from_template("{prompt}")
            ])

            # Format the prompt
            formatted_prompt = chat_prompt.format_prompt(prompt=enhanced_prompt)

            # Generate response using Gemini
            response = await self._call_llm_async(formatted_prompt.to_messages())

            # Parse and format the response
            question_data = self._parse_llm_response(response, section_number)

            logger.info(f"Successfully generated question for section {section_number}")
            return question_data

        except Exception as e:
            logger.error(f"Error generating question for section {section_number}: {str(e)}")
            # Return a fallback question
            return self._get_fallback_question(section_number)

    async def process_answer_and_generate_next(
        self,
        section_number: int,
        current_question: str,
        current_answer: str,
        previous_answers: List[Dict[str, Any]],
        ontario_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process the current answer and determine next step: ask another question or generate draft.

        Args:
            section_number: The current section number
            current_question: The question that was just answered
            current_answer: The answer provided by the user
            previous_answers: List of previous Q&A pairs for this section
            ontario_chunks: Relevant Ontario Building Code chunks

        Returns:
            Dict containing either next_question or draft_output
        """
        try:
            # Format previous Q&A pairs for context
            qa_context = self._format_previous_answers(previous_answers)

            # Add current Q&A to context
            current_qa = f"Q: {current_question}\nA: {current_answer}"

            # Format ontario chunks context
            ontario_context = self._format_ontario_chunks(ontario_chunks)

            # Create decision prompt
            decision_prompt = f"""
Based on the following context, determine if we need to ask more clarifying questions or if we have enough information to generate a draft section.

Section Number: {section_number}

Previous Q&A pairs:
{qa_context}

Current Q&A:
{current_qa}

Relevant Building Code Sections:
{ontario_context}

Instructions:
1. If more information is needed, respond with: QUESTION: [your next question]
2. If enough information is gathered, respond with: DRAFT: [generate a draft section based on all the information]

Consider that we need sufficient detail to create a comprehensive building permit section.
"""

            # Create the chat prompt template
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    "You are an expert Ontario Building Code consultant. Analyze the conversation "
                    "and determine if more questions are needed or if you can generate a draft section. "
                    "Be thorough but efficient - don't ask unnecessary questions."
                ),
                HumanMessagePromptTemplate.from_template("{prompt}")
            ])

            # Format and call LLM
            formatted_prompt = chat_prompt.format_prompt(prompt=decision_prompt)
            response = await self._call_llm_async(formatted_prompt.to_messages())

            # Parse the response to determine next action
            return self._parse_decision_response(response, section_number)

        except Exception as e:
            logger.error(f"Error processing answer for section {section_number}: {str(e)}")
            # Return a fallback next question
            return {
                "action": "question",
                "next_question": f"Could you provide any additional details about section {section_number} requirements?",
                "metadata": {
                    "generated_by": "fallback",
                    "reason": "error_processing_answer"
                }
            }

    def _format_previous_answers(self, answers: List[Dict[str, Any]]) -> str:
        """Format previous answers for context."""
        if not answers:
            return "No previous questions asked."

        formatted_answers = []
        for i, answer in enumerate(answers, 1):
            q_text = answer.get('question_text', 'Unknown question')
            a_text = answer.get('answer_text', 'No answer')
            formatted_answers.append(f"{i}. Q: {q_text}\n   A: {a_text}")

        return "\n".join(formatted_answers)

    def _parse_decision_response(self, response: str, section_number: int) -> Dict[str, Any]:
        """Parse the LLM decision response."""
        try:
            cleaned_response = response.strip()

            if cleaned_response.startswith("QUESTION:"):
                # Extract the question
                question_text = cleaned_response[9:].strip()
                return {
                    "action": "question",
                    "next_question": question_text,
                    "metadata": {
                        "generated_by": "gemini-pro",
                        "section_number": section_number
                    }
                }
            elif cleaned_response.startswith("DRAFT:"):
                # Extract the draft content
                draft_content = cleaned_response[6:].strip()
                return {
                    "action": "draft",
                    "draft_output": {
                        "section_number": section_number,
                        "content": draft_content,
                        "generated_at": "now",
                        "status": "draft"
                    },
                    "metadata": {
                        "generated_by": "gemini-pro",
                        "section_number": section_number
                    }
                }
            else:
                # Default to asking another question if format is unclear
                return {
                    "action": "question",
                    "next_question": f"Could you provide more specific details about section {section_number}?",
                    "metadata": {
                        "generated_by": "gemini-pro",
                        "reason": "unclear_response_format"
                    }
                }

        except Exception as e:
            logger.error(f"Error parsing decision response: {str(e)}")
            return {
                "action": "question",
                "next_question": f"Could you provide additional information about section {section_number}?",
                "metadata": {
                    "generated_by": "fallback",
                    "reason": "parse_error"
                }
            }

    async def _call_llm_async(self, messages: List[Any]) -> str:
        """Make async call to the LLM."""
        try:
            # Run the LLM call in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    def _format_ontario_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Format ontario chunks for inclusion in the prompt."""
        if not chunks:
            return "No specific building code sections available."

        formatted_chunks = []
        for chunk in chunks:
            section_ref = chunk.get('section_reference', 'Unknown')
            section_title = chunk.get('section_title', 'No title')
            chunk_text = chunk.get('chunk_text', '')

            formatted_chunk = f"**{section_ref}: {section_title}**\n{chunk_text}\n"
            formatted_chunks.append(formatted_chunk)

        return "\n".join(formatted_chunks)

    def _parse_llm_response(self, response: str, section_number: int) -> Dict[str, Any]:
        """Parse the LLM response into a structured question format."""
        try:
            # Clean up the response
            cleaned_response = response.strip()

            # For now, return the response as a simple question
            # In the future, this could be enhanced to parse structured responses
            return {
                "question_id": f"section_{section_number}_q1",
                "section_number": section_number,
                "question_text": cleaned_response,
                "question_type": "text",  # Could be "multiple_choice", "numeric", etc.
                "options": None,  # For multiple choice questions
                "validation": None,  # For input validation
                "metadata": {
                    "generated_by": "gemini-pro",
                    "section_context": True
                }
            }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return self._get_fallback_question(section_number)

    def _get_fallback_question(self, section_number: int) -> Dict[str, Any]:
        """Return a fallback question when AI generation fails."""
        return {
            "question_id": f"section_{section_number}_fallback",
            "section_number": section_number,
            "question_text": f"Please provide details about the requirements for section {section_number} of your building project.",
            "question_type": "text",
            "options": None,
            "validation": None,
            "metadata": {
                "generated_by": "fallback",
                "section_context": False
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """Check if the AI service is healthy and operational."""
        try:
            if self.llm is None:
                return {"status": "unhealthy", "error": "LLM not initialized"}

            # Simple test call
            test_messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Say 'OK' if you can respond.")
            ]

            response = self.llm.invoke(test_messages)

            return {
                "status": "healthy",
                "model": "gemini-pro",
                "response_length": len(response.content)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
