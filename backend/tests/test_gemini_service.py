"""
Tests for Gemini service methods.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.gemini_service import GeminiService, get_gemini_service


class TestGeminiServiceInitialization:
    """Test cases for GeminiService initialization."""
    
    def test_init_with_api_key(self):
        """Test GeminiService initialization with provided API key."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key_123")
            assert service.api_key == "test_key_123"
            mock_genai.configure.assert_called_once_with(api_key="test_key_123")
    
    def test_init_with_env_var(self, monkeypatch):
        """Test GeminiService initialization with environment variable."""
        monkeypatch.setenv("GEMINI_API_KEY", "env_key_456")
        
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService()
            assert service.api_key == "env_key_456"
            mock_genai.configure.assert_called_once_with(api_key="env_key_456")
    
    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test that GeminiService raises error when no API key is provided."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiService()
    
    def test_init_with_custom_model(self):
        """Test GeminiService initialization with custom model name."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key", model_name="gemini-ultra")
            assert service.model_name == "gemini-ultra"
            mock_genai.GenerativeModel.assert_called_once_with("gemini-ultra")


class TestGeminiServiceSummarizeData:
    """Test cases for summarize_data method."""
    
    @pytest.mark.asyncio
    async def test_summarize_data_success_with_fred_data(self):
        """Test successful data summarization with FRED data structure."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "This is a test summary of economic data."
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            fred_data = {
                "series_info": {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "units": "Billions of Dollars",
                    "frequency": "Quarterly",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate"
                },
                "observations": [
                    {"date": "2024-01-01", "value": 25000.0},
                    {"date": "2023-10-01", "value": 24800.0},
                ]
            }
            
            result = await service.summarize_data(fred_data)
            
            assert result == "This is a test summary of economic data."
            assert mock_model.generate_content.called
            # Verify prompt contains FRED data
            call_args = mock_model.generate_content.call_args[0][0]
            assert "Gross Domestic Product" in call_args
            assert "GDP" in call_args
    
    @pytest.mark.asyncio
    async def test_summarize_data_success_with_generic_data(self):
        """Test successful data summarization with generic data."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Summary of generic data."
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            generic_data = {"key": "value", "number": 123}
            
            result = await service.summarize_data(generic_data)
            
            assert result == "Summary of generic data."
            assert mock_model.generate_content.called
    
    @pytest.mark.asyncio
    async def test_summarize_data_with_missing_values(self):
        """Test summarization with observations that have missing values."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Summary with missing data."
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            fred_data = {
                "series_info": {
                    "id": "GDP",
                    "title": "Gross Domestic Product"
                },
                "observations": [
                    {"date": "2024-01-01", "value": 25000.0},
                    {"date": "2023-12-01", "value": None},  # Missing value
                ]
            }
            
            result = await service.summarize_data(fred_data)
            
            assert result == "Summary with missing data."
            call_args = mock_model.generate_content.call_args[0][0]
            assert "No data available" in call_args
    
    @pytest.mark.asyncio
    async def test_summarize_data_api_error(self):
        """Test summarization when Gemini API raises an error."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API Error")
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            data = {"test": "data"}
            
            with pytest.raises(Exception, match="Error generating summary"):
                await service.summarize_data(data)
    
    @pytest.mark.asyncio
    async def test_summarize_data_empty_response(self):
        """Test summarization when Gemini API returns empty response."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = None  # Empty response
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            data = {"test": "data"}
            
            with pytest.raises(Exception, match="Empty response"):
                await service.summarize_data(data)
    
    @pytest.mark.asyncio
    async def test_summarize_data_limits_observations(self):
        """Test that summarization limits observations to 10 most recent."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Summary."
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            # Create data with more than 10 observations
            observations = [
                {"date": f"2024-{i:02d}-01", "value": 1000 + i}
                for i in range(1, 20)  # 19 observations
            ]
            
            fred_data = {
                "series_info": {"id": "GDP", "title": "GDP"},
                "observations": observations
            }
            
            await service.summarize_data(fred_data)
            
            call_args = mock_model.generate_content.call_args[0][0]
            # Should mention showing 10 most recent
            assert "showing 10 most recent" in call_args
            # Count occurrences of dates in the prompt (should be 10)
            date_count = call_args.count("2024-")
            assert date_count == 10


class TestGeminiServicePromptCreation:
    """Test cases for prompt creation."""
    
    def test_create_summarization_prompt_with_fred_data(self):
        """Test prompt creation with FRED data structure."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            fred_data = {
                "series_info": {
                    "id": "UNRATE",
                    "title": "Unemployment Rate",
                    "units": "Percent",
                    "frequency": "Monthly",
                    "seasonal_adjustment": "Seasonally Adjusted"
                },
                "observations": [
                    {"date": "2024-01-01", "value": 3.7},
                    {"date": "2023-12-01", "value": 3.8},
                ]
            }
            
            prompt = service._create_summarization_prompt(fred_data)
            
            assert "Unemployment Rate" in prompt
            assert "UNRATE" in prompt
            assert "Percent" in prompt
            assert "Monthly" in prompt
            assert "2024-01-01" in prompt
            assert "3.7" in prompt
    
    def test_create_summarization_prompt_with_generic_data(self):
        """Test prompt creation with generic data."""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service = GeminiService(api_key="test_key")
            
            generic_data = {"custom": "data", "value": 42}
            
            prompt = service._create_summarization_prompt(generic_data)
            
            assert "custom" in prompt or "data" in prompt
            assert "2-3 paragraphs" in prompt


class TestGetGeminiService:
    """Test cases for get_gemini_service singleton function."""
    
    def test_get_gemini_service_singleton(self, monkeypatch):
        """Test that get_gemini_service returns singleton instance."""
        # Clear any existing instance
        import app.services.gemini_service as gemini_service_module
        gemini_service_module._gemini_service = None
        
        # Set up environment
        monkeypatch.setenv("GEMINI_API_KEY", "test_key_123")
        
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            
            service1 = get_gemini_service()
            service2 = get_gemini_service()
            
            assert service1 is service2
            assert isinstance(service1, GeminiService)
            assert service1.api_key == "test_key_123"

