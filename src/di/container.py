"""Dependency injection container for Iris.agent."""

from typing import Optional
from ..config import config
from ..services import FileProcessor, GeminiService, RateLimiter
from ..utils.exceptions import ConfigurationError
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class DIContainer:
    """Dependency injection container."""
    
    def __init__(self):
        """Initialize the container."""
        self._services = {}
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initialize all services."""
        try:
            # Initialize rate limiter
            self._services['rate_limiter'] = RateLimiter(
                max_requests_per_minute=config.max_requests_per_minute
            )
            
            # Initialize file processor
            self._services['file_processor'] = FileProcessor(
                max_file_size_mb=config.max_file_size_mb,
                max_dataframe_rows=config.max_dataframe_rows
            )
            
            # Initialize Gemini service
            if not config.gemini_api_key:
                raise ConfigurationError("GEMINI_API_KEY not found in environment variables")
            
            self._services['gemini_service'] = GeminiService(
                api_key=config.gemini_api_key,
                max_requests_per_minute=config.max_requests_per_minute
            )
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            raise ConfigurationError(f"Service initialization failed: {str(e)}")
    
    def get_rate_limiter(self) -> RateLimiter:
        """Get rate limiter service."""
        return self._services['rate_limiter']
    
    def get_file_processor(self) -> FileProcessor:
        """Get file processor service."""
        return self._services['file_processor']
    
    def get_gemini_service(self) -> GeminiService:
        """Get Gemini service."""
        return self._services['gemini_service']


# Global container instance
container = DIContainer()
