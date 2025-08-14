"""
Google Gemini AI Client

This module provides a client for interacting with Google's Gemini AI API.
It includes proper error handling, type hints, and configuration management.
"""
import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class GeminiConfig:
    """Configuration class for Gemini AI client."""
    api_key: str
    model_name: str = "gemini-pro"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.8
    top_k: int = 40


@dataclass
class GeminiResponse:
    """Response object from Gemini AI."""
    content: str
    success: bool
    error_message: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None


class GeminiClient:
    """
    Google Gemini AI client with comprehensive functionality.
    
    This client provides methods for text generation, conversation handling,
    and proper error management when interacting with Gemini AI.
    """
    
    def __init__(self, config: GeminiConfig):
        """
        Initialize the Gemini client.
        
        Args:
            config: GeminiConfig object with API settings
            
        Raises:
            ValueError: If API key is not provided
        """
        if not config.api_key:
            raise ValueError("Gemini API key is required")
        
        self.config = config
        self._model = None
        self._configure_client()
    
    def _configure_client(self) -> None:
        """Configure the Gemini client with API key and settings."""
        try:
            genai.configure(api_key=self.config.api_key)
            
            # Configure generation settings
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_output_tokens": self.config.max_output_tokens,
            }
            
            # Configure safety settings to be less restrictive for business use
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
            ]
            
            self._model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info(f"Gemini client configured with model: {self.config.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to configure Gemini client: {e}")
            raise
    
    def generate_text(self, prompt: str, context: Optional[str] = None) -> GeminiResponse:
        """
        Generate text using Gemini AI.
        
        Args:
            prompt: The input prompt for text generation
            context: Optional context to provide additional information
            
        Returns:
            GeminiResponse object with generated content and metadata
        """
        try:
            if not self._model:
                return GeminiResponse(
                    content="",
                    success=False,
                    error_message="Gemini model not initialized"
                )
            
            # Prepare the full prompt with context if provided
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nPrompt: {prompt}"
            
            logger.info(f"Generating text with Gemini for prompt: {prompt[:100]}...")
            
            # Generate response
            response = self._model.generate_content(full_prompt)
            
            if response.text:
                logger.info("Successfully generated text with Gemini")
                return GeminiResponse(
                    content=response.text,
                    success=True,
                    usage_metadata=self._extract_usage_metadata(response)
                )
            else:
                logger.warning("Gemini returned empty response")
                return GeminiResponse(
                    content="",
                    success=False,
                    error_message="Empty response from Gemini"
                )
                
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return GeminiResponse(
                content="",
                success=False,
                error_message=str(e)
            )
    
    def start_chat(self, history: Optional[List[Dict[str, str]]] = None) -> 'GeminiChat':
        """
        Start a chat session with Gemini.
        
        Args:
            history: Optional chat history to continue conversation
            
        Returns:
            GeminiChat object for conversation management
        """
        return GeminiChat(self, history)
    
    def analyze_sentiment(self, text: str) -> GeminiResponse:
        """
        Analyze sentiment of given text using Gemini.
        
        Args:
            text: Text to analyze for sentiment
            
        Returns:
            GeminiResponse with sentiment analysis
        """
        prompt = f"""
        Analyze the sentiment of the following text and provide:
        1. Overall sentiment (positive, negative, neutral)
        2. Confidence score (0-1)
        3. Key emotional indicators
        4. Brief explanation
        
        Text: "{text}"
        
        Please respond in JSON format.
        """
        
        return self.generate_text(prompt)
    
    def summarize_text(self, text: str, max_length: int = 200) -> GeminiResponse:
        """
        Summarize the given text using Gemini.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            GeminiResponse with text summary
        """
        prompt = f"""
        Please provide a concise summary of the following text in maximum {max_length} words.
        Focus on the key points and main ideas.
        
        Text: "{text}"
        """
        
        return self.generate_text(prompt)
    
    def extract_keywords(self, text: str, count: int = 10) -> GeminiResponse:
        """
        Extract keywords from the given text using Gemini.
        
        Args:
            text: Text to extract keywords from
            count: Number of keywords to extract
            
        Returns:
            GeminiResponse with extracted keywords
        """
        prompt = f"""
        Extract the top {count} most important keywords or phrases from the following text.
        Provide them as a comma-separated list, ordered by importance.
        
        Text: "{text}"
        """
        
        return self.generate_text(prompt)
    
    def _extract_usage_metadata(self, response) -> Dict[str, Any]:
        """
        Extract usage metadata from Gemini response.
        
        Args:
            response: Gemini API response object
            
        Returns:
            Dictionary with usage metadata
        """
        try:
            metadata = {}
            if hasattr(response, 'usage_metadata'):
                metadata['usage_metadata'] = response.usage_metadata
            if hasattr(response, 'prompt_feedback'):
                metadata['prompt_feedback'] = response.prompt_feedback
            return metadata
        except Exception as e:
            logger.warning(f"Failed to extract usage metadata: {e}")
            return {}
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Gemini client.
        
        Returns:
            True if client is healthy, False otherwise
        """
        try:
            if not self._model:
                return False
            
            # Test with a simple prompt
            test_response = self.generate_text("Hello, this is a health check. Please respond with 'OK'.")
            return test_response.success
            
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False


class GeminiChat:
    """
    Chat session manager for Gemini AI conversations.
    
    This class manages conversation history and provides methods for
    interactive chat sessions with Gemini AI.
    """
    
    def __init__(self, client: GeminiClient, history: Optional[List[Dict[str, str]]] = None):
        """
        Initialize chat session.
        
        Args:
            client: GeminiClient instance
            history: Optional conversation history
        """
        self.client = client
        self.history = history or []
        self._chat_session = None
        self._initialize_chat()
    
    def _initialize_chat(self) -> None:
        """Initialize the chat session with Gemini."""
        try:
            if self.client._model:
                # Convert history to Gemini format if provided
                gemini_history = []
                for message in self.history:
                    gemini_history.append({
                        "role": message.get("role", "user"),
                        "parts": [message.get("content", "")]
                    })
                
                self._chat_session = self.client._model.start_chat(history=gemini_history)
                logger.info("Chat session initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chat session: {e}")
    
    def send_message(self, message: str) -> GeminiResponse:
        """
        Send a message in the chat session.
        
        Args:
            message: Message to send
            
        Returns:
            GeminiResponse with the AI's reply
        """
        try:
            if not self._chat_session:
                return GeminiResponse(
                    content="",
                    success=False,
                    error_message="Chat session not initialized"
                )
            
            logger.info(f"Sending message to Gemini chat: {message[:100]}...")
            
            response = self._chat_session.send_message(message)
            
            if response.text:
                # Update local history
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": response.text})
                
                logger.info("Successfully received chat response from Gemini")
                return GeminiResponse(
                    content=response.text,
                    success=True,
                    usage_metadata=self.client._extract_usage_metadata(response)
                )
            else:
                logger.warning("Gemini chat returned empty response")
                return GeminiResponse(
                    content="",
                    success=False,
                    error_message="Empty response from Gemini chat"
                )
                
        except Exception as e:
            logger.error(f"Error in Gemini chat: {e}")
            return GeminiResponse(
                content="",
                success=False,
                error_message=str(e)
            )
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear the conversation history and restart the chat session."""
        self.history = []
        self._initialize_chat()


def create_gemini_client(config: Optional[GeminiConfig] = None) -> GeminiClient:
    """
    Factory function to create a Gemini client with configuration.
    
    Args:
        config: Optional GeminiConfig, will use environment variables if not provided
        
    Returns:
        Configured GeminiClient instance
        
    Raises:
        ValueError: If required configuration is missing
    """
    if config is None:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        config = GeminiConfig(
            api_key=api_key,
            model_name=os.environ.get('GEMINI_MODEL', 'gemini-pro'),
            temperature=float(os.environ.get('GEMINI_TEMPERATURE', '0.7')),
            max_output_tokens=int(os.environ.get('GEMINI_MAX_OUTPUT_TOKENS', '2048')),
            top_p=float(os.environ.get('GEMINI_TOP_P', '0.8')),
            top_k=int(os.environ.get('GEMINI_TOP_K', '40'))
        )
    
    return GeminiClient(config)
