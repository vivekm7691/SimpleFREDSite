"""
Google Gemini API service for generating AI-powered summaries.
"""
import os
from typing import Optional, Dict, Any
import google.generativeai as genai


class GeminiService:
    """Service for interacting with the Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro"):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Google Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
            model_name: Name of the Gemini model to use (default: "gemini-pro")
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.model_name = model_name
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
    
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
        # Format the prompt for summarization
        prompt = self._create_summarization_prompt(data)
        
        try:
            # Generate content using Gemini API
            response = await self._generate_content_async(prompt)
            return response
        except Exception as e:
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
            response = self.model.generate_content(prompt)
            if response.text:
                return response.text
            else:
                raise Exception("Empty response from Gemini API")
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


# Singleton instance (will be initialized with API key from env)
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

