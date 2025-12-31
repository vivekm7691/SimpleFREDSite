"""
Google Gemini API service for generating AI-powered summaries.
"""
import os
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with the Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/gemini-2.5-flash"):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Google Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
            model_name: Name of the Gemini model to use (default: "models/gemini-2.5-flash")
        """
        # Always reload .env file to get the latest API key
        from pathlib import Path
        from dotenv import load_dotenv
        
        # Get API key from parameter first
        if api_key:
            self.api_key = api_key
        else:
            # Force reload .env file to ensure we get the latest key
            env_path = Path(__file__).parent.parent.parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=True)
                logger.info(f"Reloaded .env from: {env_path}")
            
            # Get from environment
            self.api_key = os.getenv("GEMINI_API_KEY")
            
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Strip any whitespace from the API key
        self.api_key = self.api_key.strip()
        
        # Validate API key format
        if not self.api_key.startswith("AIza"):
            raise ValueError(f"Invalid API key format. Gemini API keys should start with 'AIza'. Got: {self.api_key[:10]}...")
        
        # Logging (masked for security - only first 10 and last 5 characters)
        logger.info("=== GeminiService initializing ===")
        logger.info(f"API Key: {self.api_key[:10]}...{self.api_key[-5:]} (length: {len(self.api_key)})")
        logger.info(f"Model: {model_name}")
        
        self.model_name = model_name
        
        # IMPORTANT: Always reconfigure genai with the new API key
        # Clear any existing configuration first
        try:
            if hasattr(genai, '_client'):
                delattr(genai, '_client')
        except:
            pass
        
        # Configure with the API key
        genai.configure(api_key=self.api_key)
        logger.info(f"genai.configure() called with key: {self.api_key[:10]}...{self.api_key[-5:]}")
        
        # Create model instance
        # Note: GenerativeModel doesn't accept api_key parameter, it uses the configured one
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Model created: {model_name}")
        logger.info(f"GeminiService initialized successfully with model: {model_name}")
    
    async def summarize_data(self, data: Dict[str, Any]) -> str:
        """
        Generate an AI-powered summary of the provided data.
        
        Args:
            data: Dictionary containing data to summarize (typically FRED economic data)
            
        Returns:
            Generated summary text
            
        Raises:
            Exception: If API request fails or summary cannot be generated
        """
        logger.info("summarize_data called")
        # Format the prompt for summarization
        prompt = self._create_summarization_prompt(data)
        logger.info(f"Prompt created (length: {len(prompt)})")
        
        try:
            # Generate content using Gemini API
            logger.info("Calling _generate_content_async...")
            response = await self._generate_content_async(prompt)
            logger.info(f"Response received (length: {len(response)})")
            return response
        except Exception as e:
            logger.error(f"Error in summarize_data: {str(e)}", exc_info=True)
            raise Exception(f"Error generating summary: {str(e)}")
    
    def _create_summarization_prompt(self, data: Dict[str, Any]) -> str:
        """
        Create a prompt for summarizing economic data.
        
        Args:
            data: Dictionary containing data to summarize
            
        Returns:
            Formatted prompt string
        """
        # Check if data contains FRED-specific structure
        if "series_info" in data and "observations" in data:
            series_info = data.get("series_info", {})
            observations = data.get("observations", [])
            
            prompt = f"""Please provide a clear and concise summary of the following economic data:

Series Information:
- Title: {series_info.get('title', 'N/A')}
- Series ID: {series_info.get('id', 'N/A')}
- Units: {series_info.get('units', 'N/A')}
- Frequency: {series_info.get('frequency', 'N/A')}
- Seasonal Adjustment: {series_info.get('seasonal_adjustment', 'N/A')}

Recent Observations (showing {min(10, len(observations))} most recent):
"""
            # Include up to 10 most recent observations
            for obs in observations[:10]:
                date = obs.get("date", "N/A")
                value = obs.get("value")
                if value is not None:
                    prompt += f"- {date}: {value}\n"
                else:
                    prompt += f"- {date}: No data available\n"
            
            prompt += """
Please provide:
1. A brief overview of what this economic indicator represents
2. Key trends or patterns visible in the recent data
3. Any notable observations or insights
4. Keep the summary concise (2-3 paragraphs maximum)
"""
        else:
            # Generic data summarization
            prompt = f"""Please provide a clear and concise summary of the following data:

{str(data)}

Provide key insights and trends in 2-3 paragraphs.
"""
        
        return prompt
    
    async def _generate_content_async(self, prompt: str) -> str:
        """
        Generate content asynchronously using Gemini API.
        
        Note: The google-generativeai library is synchronous, but we wrap it
        in an async function for consistency with the rest of the async codebase.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Generated text response
        """
        # Since google-generativeai is synchronous, we'll use it directly
        # In a production environment, you might want to run this in a thread pool
        try:
            logger.info(f"Calling model.generate_content() with model: {self.model_name}")
            response = self.model.generate_content(prompt)
            logger.info("Model.generate_content() completed")
            if response.text:
                logger.info(f"Response text received (length: {len(response.text)})")
                return response.text
            else:
                logger.error("Empty response from Gemini API")
                raise Exception("Empty response from Gemini API")
        except Exception as e:
            # Provide more detailed error information
            error_msg = str(e)
            # Provide detailed error information
            logger.error(f"Exception in _generate_content_async: {error_msg}", exc_info=True)
            if "API_KEY" in error_msg.upper() or "API key" in error_msg or "invalid" in error_msg.lower():
                raise Exception(f"Invalid API key or API key error: {error_msg}")
            raise Exception(f"Gemini API error: {error_msg}")


# Singleton instance (will be initialized with API key from env)
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service
    # Force recreation to ensure latest model name is used
    if _gemini_service is None:
        logger.info("Creating new GeminiService instance")
        _gemini_service = GeminiService()
    else:
        logger.info(f"Using existing GeminiService instance with model: {_gemini_service.model_name}")
    return _gemini_service


def reset_gemini_service():
    """Reset the singleton instance (useful for testing or reinitialization)."""
    global _gemini_service
    _gemini_service = None


