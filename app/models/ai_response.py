"""
AI Response Models

This module defines the unified response structure for AI service responses.
Uses dataclasses for simple, typed response structures.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Literal, Union
from datetime import datetime
import json


@dataclass
class Metadata:
    """Metadata for AI responses"""
    timestamp: str
    confidence: float
    version: str = "1.0"
    model: str = "gemini-pro"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinalAnswerData:
    """Data structure for final_answer responses"""
    form_question_number: str
    form_question_title: str
    final_answer: str
    justification: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClarifyingQuestionData:
    """Base class for clarifying question data"""
    clarifying_question: str
    clarifying_question_context: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultipleChoiceMultipleOptionsData(ClarifyingQuestionData):
    """Data structure for multiple choice (multiple options) questions"""
    input_type: Literal["multiple_choice_multiple_options"] = "multiple_choice_multiple_options"
    choices: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultipleChoiceSingleOptionData(ClarifyingQuestionData):
    """Data structure for multiple choice (single option) questions"""
    input_type: Literal["multiple_choice_single_option"] = "multiple_choice_single_option"
    choices: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NumericInputData(ClarifyingQuestionData):
    """Data structure for numeric input questions"""
    input_type: Literal["numeric"] = "numeric"
    unit: str = ""
    validation: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TextInputData(ClarifyingQuestionData):
    """Data structure for text input questions"""
    input_type: Literal["text"] = "text"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorData:
    """Data structure for error responses"""
    error_type: Literal["service_unavailable", "validation_error", "processing_error"]
    message: str
    suggestion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Union type for all possible data types
ResponseData = Union[
    FinalAnswerData,
    MultipleChoiceMultipleOptionsData,
    MultipleChoiceSingleOptionData,
    NumericInputData,
    TextInputData,
    ErrorData
]


class AIResponse:
    """Unified AI response structure"""
    
    def __init__(
        self,
        response_type: Literal["final_answer", "clarifying_question", "error"],
        data: ResponseData,
        metadata: Optional[Metadata] = None
    ):
        self.response_type = response_type
        self.data = data
        self.metadata = metadata or Metadata(
            timestamp=datetime.utcnow().isoformat() + "Z",
            confidence=1.0  # Default confidence
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for JSON serialization"""
        return {
            "response_type": self.response_type,
            "data": self.data.to_dict(),
            "metadata": self.metadata.to_dict()
        }
    
    def to_json(self) -> str:
        """Convert response to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


def create_error_response(
    error_type: str,
    message: str,
    suggestion: str = "",
    confidence: float = 0.0
) -> AIResponse:
    """Helper function to create error responses"""
    error_data = ErrorData(
        error_type=error_type,
        message=message,
        suggestion=suggestion
    )
    metadata = Metadata(
        timestamp=datetime.utcnow().isoformat() + "Z",
        confidence=confidence,
        model="error"
    )
    return AIResponse(
        response_type="error",
        data=error_data,
        metadata=metadata
    )
