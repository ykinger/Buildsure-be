
from langchain_core.tools import tool
import logging
import json
import sys
import os
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, ToolMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.data_matrix import DataMatrix

history = None
def set_history(h):
    global history
    history = h

# Add the project root to Python path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Pydantic models for return types
class MCQData(BaseModel):
    """Data structure for a multiple-choice question."""
    type: Literal["mcq"] = "mcq"
    question: str
    answer_options: list[str]

class MultipleChoiceQuestionResponse(BaseModel):
    """
    Represents a structured response for asking a multiple-choice question to the user.
    Use this when the AI needs to ask a question and provide predefined options for the user to choose from.
    """
    type: Literal["question"] = "question"
    data: MCQData

class NumericQuestionData(BaseModel):
    """Data structure for a numeric question."""
    type: Literal["numeric"] = "numeric"
    question: str

class NumericQuestionResponse(BaseModel):
    """
    Represents a structured response for presenting a numeric question to the user.
    The AI can ask for validation of user input based on defined criteria,
    including minimum and maximum allowed values, and units.
    """
    type: Literal["question"] = "question"
    data: NumericQuestionData

class FreeTextQuestionData(BaseModel):
    """Data structure for a free-form text question."""
    type: Literal["free_form_text"] = "free_form_text"
    question: str

class FreeTextQuestionResponse(BaseModel):
    """
    Represents a structured response for presenting a free-form text question to the user.
    Use this when the AI needs to ask a question that requires a free-form text answer.
    """
    type: Literal["question"] = "question"
    data: FreeTextQuestionData

class FinalAnswerData(BaseModel):
    """Data structure for providing a final answer to a form question."""
    answer: str

class FinalAnswerResponse(BaseModel):
    """
    Represents a structured response to let the user know this is the final answer
    to a form question and there will be no more questions regarding this specific form question.
    """
    type: Literal["answer"] = "answer"
    data: FinalAnswerData


@tool
def ask_multiple_choice_question(question_text: str, options: list[str]) -> MultipleChoiceQuestionResponse:
    """
    Ask a multiple-choice question to the user and receives their answer.
    Use this when you have a question to the user and you are able to define
    the options for the user to choose from.

    Args:
        question_text (str): The text of the multiple-choice question.
        options (list[str]): A list of possible answer choices.

    Returns:
        MultipleChoiceQuestionResponse: The user's selected answer (one of the options).
    """
    logging.info("[MCQ] %s %s", question_text, options)
    mcq_data = MCQData(question=question_text, answer_options=options)
    history.append(AIMessage(question_text))
    return MultipleChoiceQuestionResponse(data=mcq_data).model_dump()

@tool
def ask_numeric_question(question_text: str) -> NumericQuestionResponse:
    """
    Presents a numeric question to the user and receives their answer.

    The LLM can ask for validation of user input based on defined criteria,
    including minimum and maximum allowed values, and units.

    Args:
        question_text (str): The text of the numeric question.

    Returns:
        NumericQuestionResponse: The user's numeric answer.
    """
    numeric_data = NumericQuestionData(question=question_text)
    history.append(AIMessage(question_text))
    return NumericQuestionResponse(data=numeric_data).model_dump()

@tool
def ask_free_text_question(question_text: str) -> FreeTextQuestionResponse:
    """
    Presents a free form text question to the user.

    This question is

    Args:
        question_text (str): The text of the free-form question.

    Returns:
        FreeTextQuestionResponse: The user's answer to the question.
    """
    free_text_data = FreeTextQuestionData(question=question_text)
    history.append(AIMessage(question_text))
    return FreeTextQuestionResponse(data=free_text_data).model_dump()

@tool
def retrieve_obc_section(section: str) -> str:
    """
    Retrieves a section from the Ontario Building Code based on a section number.

    Args:
        section (str): Section number in the format of part.section.sub-section.article

    Returns:
        str: The content of the OBC section.
    """
    logging.info("Asked to retreive section %s", section)
    return "NOT IMPLEMENTED YET - I cannot return OBC section as of now"

@tool
def provide_final_answer(answer: str) -> FinalAnswerResponse:
    """
    Let user know this is the final answer to form question and there will be no more
    questions regarding this specific form question.

    Args:
        answer (str): The final answer to be used by user to fill the form question
    """
    logging.info("[Final] Answer: %s", answer)
    final_answer_data = FinalAnswerData(answer=answer)
    history.append(AIMessage(answer))
    return FinalAnswerResponse(data=final_answer_data).model_dump()

async def get_form_section_info(number: str, db: AsyncSession) -> dict:
    """
    Provides basic form section information, including:
    - Of the section in the form
    - The question AI should seek the answer to
    - A guide on where in OBC to look for relevant information
    """
    # Query the data_matrix table for the section
    stmt = select(DataMatrix).where(DataMatrix.number == number)
    result = await db.execute(stmt)
    data_matrix = result.scalar_one_or_none()

    if not data_matrix:
        return None

    # Return the section information in the expected format
    return {
        "number": data_matrix.number,
        "title": data_matrix.title,
        "question": data_matrix.question,
        "guide": data_matrix.guide
    }

DEFINED_TOOLS = {
    "ask_free_text_question": ask_free_text_question,
    "ask_multiple_choice_question": ask_multiple_choice_question,
    "ask_numeric_question": ask_numeric_question,
    "provide_final_answer": provide_final_answer,
    "retrieve_obc_section": retrieve_obc_section,
}

ACCEPTABLE_RESPONSE_TYPES = [
    FreeTextQuestionResponse,
    MultipleChoiceQuestionResponse,
    NumericQuestionResponse,
    FinalAnswerResponse
]
