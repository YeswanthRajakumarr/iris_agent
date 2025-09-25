"""Gemini AI service for log analysis."""

import time
import re
from typing import Optional
import google.generativeai as genai
from ..models.analysis import AnalysisResult, SessionSummary
from ..utils.exceptions import APIError, RateLimitError, AnalysisError
from ..utils.validators import sanitize_input
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class GeminiService:
    """Service for interacting with Gemini AI API."""
    
    def __init__(self, api_key: str, max_requests_per_minute: int = 10):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key
            max_requests_per_minute: Rate limit for requests
        """
        self.api_key = api_key
        self.max_requests_per_minute = max_requests_per_minute
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the Gemini model."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            raise APIError(f"Failed to initialize Gemini API: {str(e)}")
    
    def analyze_logs(self, log_content: str, max_content_size_kb: int = 4000) -> AnalysisResult:
        """
        Analyze OCPP logs using Gemini AI.
        
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
            

            # write to file
            # with open('before_analysis_log_content.txt', 'w') as f:
            #     f.write(log_content)

            # Limit content size
            max_content_size_bytes = max_content_size_kb * 1024
            if len(log_content) > max_content_size_bytes:
                log_content = log_content[:max_content_size_bytes] + "\n\n... (Content truncated for processing)"
                logger.info("Log content truncated for processing")
            
            logger.info(f"Starting analysis for content of size: {len(log_content)} characters")
            
                    # write to file
            # with open('after_analysis_log_content.txt', 'w') as f:
            #     f.write(log_content)

            # Create analysis prompt
            prompt = self._create_analysis_prompt(log_content)

            # write to file
            # with open('prompt.txt', 'w') as f:
            #     f.write(prompt)
            
            # Generate analysis
            start_time = time.time()
            response = self.model.generate_content(prompt)
            end_time = time.time()
            
            logger.info(f"Analysis completed in {end_time - start_time:.2f} seconds")
            
            # Process response
            analysis_text = self._highlight_key_elements(response.text)
            summary = self._extract_summary_from_analysis(analysis_text)
            
            return AnalysisResult(
                summary=summary,
                detailed_analysis=analysis_text,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            raise AnalysisError(f"Analysis failed: {str(e)}")
    
    def _create_analysis_prompt(self, log_content: str) -> str:
        """Create the analysis prompt for Gemini."""
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
