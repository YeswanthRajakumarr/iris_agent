"""Configuration settings for Iris.agent application."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Model Provider Configuration
    model_provider: str = "gemini"  # "gemini" or "ollama"
    
    # API Configuration
    gemini_api_key: Optional[str] = None
    max_requests_per_minute: int = 10
    request_timeout: int = 60
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "llama3.2"
    
    # File Processing Configuration
    max_file_size_mb: int = 5
    max_log_content_size_kb: int = 500
    max_dataframe_rows: int = 50000
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "agent.log"
    
    # Application Configuration
    app_title: str = "Iris.agent"
    app_icon: str = "Iris_agent_logo.png"
    page_layout: str = "centered"
    sidebar_state: str = "expanded"
    
    
    def __post_init__(self) -> None:
        """Initialize configuration from environment variables."""
        # Model provider configuration - default to gemini for cloud deployment
        self.model_provider = os.getenv('MODEL_PROVIDER', self.model_provider)
        
        # For cloud deployment, ensure we use gemini if ollama is not available
        if self.model_provider.lower() == "ollama":
            # Check if we're in a cloud environment (Streamlit Cloud)
            is_cloud_env = (
                os.getenv('STREAMLIT_CLOUD') or 
                os.getenv('STREAMLIT_SHARING_MODE') or
                os.getenv('STREAMLIT_SERVER_PORT') == '8501' or  # Default Streamlit Cloud port
                'streamlit' in os.getenv('PATH', '').lower() or  # Streamlit in PATH
                os.path.exists('/app')  # Streamlit Cloud app directory
            )
            if is_cloud_env:
                logger.warning("Ollama not available in cloud environment, switching to Gemini")
                self.model_provider = "gemini"
        
        # API configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Ollama configuration
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', self.ollama_base_url)
        self.ollama_model_name = os.getenv('OLLAMA_MODEL_NAME', self.ollama_model_name)
        
        # Override with environment variables if present
        self.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', self.max_requests_per_minute))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', self.request_timeout))
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', self.max_file_size_mb))
        self.max_log_content_size_kb = int(os.getenv('MAX_LOG_CONTENT_SIZE_KB', self.max_log_content_size_kb))
        self.max_dataframe_rows = int(os.getenv('MAX_DATAFRAME_ROWS', self.max_dataframe_rows))
        self.log_level = os.getenv('LOG_LEVEL', self.log_level)
        self.log_file = os.getenv('LOG_FILE', self.log_file)


# Global configuration instance
config = AppConfig()
