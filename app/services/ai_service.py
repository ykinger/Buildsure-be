"""
AI Service Module
Handles LangChain integration with Google Gemini for question generation.
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from app.config.settings import Settings, settings
from app.utils.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered question generation using Google Gemini."""
    
    def __init__(self):
        self.settings: Settings = settings
        self.llm = None
        self.prompt_builder = PromptBuilder("assets/prompt-parts")
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Google Gemini LLM client."""
        try:
            # Initialize Google Gemini LLM
            self.llm = ChatGoogleGenerativeAI(
                model=self.settings.gemini_model,
                google_api_key=self.settings.gemini_api_key,
                temperature=self.settings.gemini_temperature,
                max_tokens=self.settings.gemini_max_tokens,
                timeout=self.settings.ai_timeout_seconds
            )
            logger.info("Google Gemini LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini LLM: {str(e)}")
            raise
    
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
