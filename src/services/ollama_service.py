"""Ollama service for local Llama model analysis."""

import time
import re
import requests
from typing import Optional
from ..models.analysis import AnalysisResult, SessionSummary
from ..utils.exceptions import APIError, RateLimitError, AnalysisError
from ..utils.validators import sanitize_input
from ..utils.logging_config import get_logger
from .model_provider import ModelProvider

logger = get_logger(__name__)


class OllamaService(ModelProvider):
    """Service for interacting with local Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.2", max_requests_per_minute: int = 10):
        """
        Initialize Ollama service.
        
        Args:
            base_url: Ollama API base URL
            model_name: Name of the Ollama model to use
            max_requests_per_minute: Rate limit for requests
        """
        import os
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.max_requests_per_minute = max_requests_per_minute
        
        # Only check connection if not in cloud environment
        is_cloud_env = os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING_MODE')
        if not is_cloud_env:
            self._check_ollama_connection()
        else:
            logger.warning("OllamaService initialized in cloud environment - connection check skipped")
    
    def _check_ollama_connection(self) -> None:
        """Check if Ollama is running and the model is available."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise APIError(f"Ollama API not accessible at {self.base_url}")
            
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.model_name not in model_names:
                logger.warning(f"Model '{self.model_name}' not found. Available models: {model_names}")
                # Try to find a suitable language model (not embedding model)
                language_models = [name for name in model_names if not any(embed in name.lower() for embed in ['embed', 'embedding'])]
                
                if language_models:
                    # Prefer llama models if available
                    llama_models = [name for name in language_models if 'llama' in name.lower()]
                    if llama_models:
                        self.model_name = llama_models[0]
                        logger.info(f"Using available llama model: {self.model_name}")
                    else:
                        self.model_name = language_models[0]
                        logger.info(f"Using available language model: {self.model_name}")
                elif model_names:
                    # Fallback to any available model
                    self.model_name = model_names[0]
                    logger.warning(f"Using available model (may not be suitable for text generation): {self.model_name}")
                else:
                    raise APIError(f"No models available in Ollama. Please pull a model first.")
            
            logger.info(f"Ollama service initialized successfully with model: {self.model_name}")
            
        except requests.exceptions.ConnectionError:
            raise APIError(f"Cannot connect to Ollama at {self.base_url}. Please ensure Ollama is running.")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama service: {str(e)}")
            raise APIError(f"Failed to initialize Ollama service: {str(e)}")
    
    def analyze_logs(self, log_content: str, max_content_size_kb: int = 4000) -> AnalysisResult:
        """
        Analyze OCPP logs using Ollama local model.
        
        Args:
            log_content: Log content to analyze
            max_content_size_kb: Maximum content size in KB
            
        Returns:
            Analysis result
            
        Raises:
            AnalysisError: If analysis fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            # Sanitize input
            sanitize_input(log_content)
            
            # Limit content size
            max_content_size_bytes = max_content_size_kb * 1024
            if len(log_content) > max_content_size_bytes:
                log_content = log_content[:max_content_size_bytes] + "\n\n... (Content truncated for processing)"
                logger.info("Log content truncated for processing")
            
            logger.info(f"Starting analysis for content of size: {len(log_content)} characters")
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(log_content)

                        # write to file
            # with open('prompt.txt', 'w') as f:
            #     f.write(prompt)
            
            
            # Generate analysis
            start_time = time.time()
            response = self._generate_response(prompt)
            end_time = time.time()
            
            logger.info(f"Analysis completed in {end_time - start_time:.2f} seconds")
            
            # Process response
            analysis_text = self._highlight_key_elements(response)
            summary = self._extract_summary_from_analysis(analysis_text)
            
            return AnalysisResult(
                summary=summary,
                detailed_analysis=analysis_text,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            raise AnalysisError(f"Analysis failed: {str(e)}")
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response from Ollama model."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9,
                    "max_tokens": 4000  # Limit response length
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Longer timeout for local processing
            )
            
            if response.status_code != 200:
                raise APIError(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.Timeout:
            raise AnalysisError("Ollama request timed out. The model might be processing a large request.")
        except requests.exceptions.ConnectionError:
            raise APIError("Lost connection to Ollama. Please ensure Ollama is running.")
        except Exception as e:
            raise AnalysisError(f"Failed to generate response from Ollama: {str(e)}")
    
    def _create_analysis_prompt(self, log_content: str) -> str:
        """Create the analysis prompt for Ollama."""
        return f"""You are an expert in analyzing OCPP 1.6 logs.

Task:
Analyze the provided OCPP logs and generate both a structured summary table and detailed analysis.

REQUIRED OUTPUT FORMAT:

**PART 1: SUMMARY TABLE**
Provide the following metrics in this exact format:

| Metric | Value |
|--------|-------|
| Total Sessions | [number] |
| Successful Sessions | [number] |
| Failed Sessions | [number] |
| Total Energy Delivered (kWh) | [number] |
| Pre-charging Failures | [number] |

**PART 2: DETAILED ANALYSIS**
Then provide:
1. Summary of what happened
2. Identified issues and their severity 
3. Root cause analysis
4. Recommended troubleshooting steps 
5. Prevention measures for the future

DEFINITIONS:
- Successful Sessions: Sessions that ended normally (including user-requested stop)
- Failed Sessions: Sessions that ended due to error, abnormal stop, or EV disconnection
- Total Energy Delivered: Sum of energy reported across all successful sessions
- Pre-charging Failures: Sessions that failed before energy delivery started (authorization failed, connector not available, EV disconnected before charging)

ANALYSIS GUIDELINES:
- The log data is organized by transaction sessions for better analysis
- Each transaction session contains StartTransaction, StopTransaction, and related messages
- Look for complete session flows: Authorize → StartTransaction → Charging → StopTransaction (or) RemoteStartTransaction → RemoteStopTransaction
- Pay attention to error codes, status changes, and meter readings
- Calculate energy delivered by comparing meterStart and meterStop values
- Identify session failures by looking for error responses or abnormal stops

Log Content:
{log_content}

Important:
- Report only based on the log content.
- Focus on charging sessions and analyze each transaction session completely
- Use clear formatting with proper line breaks and bullet points.
- Structure your response with clear headings and sections.
- When mentioning Transaction IDs, timestamps, or errors, be specific and clear.
- Analyze the complete session flow for each transaction ID.

"""
    
    def _highlight_key_elements(self, text: str) -> str:
        """Highlight key elements in the analysis text."""
        # Highlight Transaction IDs
        text = re.sub(
            r'\b(transactionId|TransactionId|transaction_id|Transaction ID)\s*:?\s*(\d+)\b', 
            r'**`\1: \2`**', 
            text, flags=re.IGNORECASE
        )
        
        # Highlight timestamps
        text = re.sub(
            r'\b(\d{1,2}:\d{2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*(?:IST|UTC|GMT)?)\b', 
            r'**`\1`**', 
            text
        )
        
        # Highlight dates
        text = re.sub(
            r'\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b', 
            r'**`\1`**', 
            text
        )
        
        # Highlight errors
        error_patterns = [
            r'\b(ERROR|Error|error|FAILED|Failed|failed|REJECTED|Rejected|rejected|TIMEOUT|Timeout|timeout)\b',
            r'\b(NotImplemented|NOT_IMPLEMENTED|not_implemented)\b',
            r'\b(AuthorizationFailed|AUTHORIZATION_FAILED|authorization_failed)\b',
            r'\b(ConnectorUnavailable|CONNECTOR_UNAVAILABLE|connector_unavailable)\b',
            r'\b(InternalError|INTERNAL_ERROR|internal_error)\b'
        ]
        
        for pattern in error_patterns:
            text = re.sub(pattern, r'**`\1`**', text)
        
        return text
    
    def _extract_summary_from_analysis(self, analysis_text: str) -> SessionSummary:
        """Extract summary metrics from analysis text."""
        summary = SessionSummary()
        
        try:
            lines = analysis_text.split('\n')
            
            for line in lines:
                if '|' in line:
                    if 'Total Sessions' in line:
                        summary.total_sessions = self._extract_number_from_line(line)
                    elif 'Successful Sessions' in line:
                        summary.successful_sessions = self._extract_number_from_line(line)
                    elif 'Failed Sessions' in line:
                        summary.failed_sessions = self._extract_number_from_line(line)
                    elif 'Total Energy Delivered' in line:
                        summary.total_energy_delivered_kwh = self._extract_float_from_line(line)
                    elif 'Pre-charging Failures' in line:
                        summary.pre_charging_failures = self._extract_number_from_line(line)
        
        except Exception as e:
            logger.warning(f"Error extracting summary from analysis: {str(e)}")
        
        return summary
    
    def _extract_number_from_line(self, line: str) -> int:
        """Extract integer number from a table line."""
        parts = line.split('|')
        if len(parts) >= 3:
            try:
                return int(parts[2].strip())
            except (ValueError, IndexError):
                pass
        return 0
    
    def _extract_float_from_line(self, line: str) -> float:
        """Extract float number from a table line."""
        parts = line.split('|')
        if len(parts) >= 3:
            try:
                return float(parts[2].strip())
            except (ValueError, IndexError):
                pass
        return 0.0
    
    def get_available_models(self) -> list:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return []
    
    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        return f"Ollama ({self.model_name})"
    
    def is_available(self) -> bool:
        """Check if the provider is available."""
        import os
        # In cloud environment, Ollama is never available
        is_cloud_env = os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING_MODE')
        if is_cloud_env:
            return False
            
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
