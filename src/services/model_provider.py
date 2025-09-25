"""Model provider abstraction for different AI services."""

from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from ..models.analysis import AnalysisResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ModelProviderType(Enum):
    """Enumeration of supported model providers."""
    GEMINI = "gemini"
    OLLAMA = "ollama"

class ModelProvider(ABC):
    """Abstract base class for model providers."""
    
    @abstractmethod
    def analyze_logs(self, log_content: str, max_content_size_kb: int = 4000) -> AnalysisResult:
        """
        Analyze OCPP logs using the model provider.
        
        Args:
            log_content: Log content to analyze
            max_content_size_kb: Maximum content size in KB
            
        Returns:
            Analysis result
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class ModelProviderFactory:
    """Factory for creating model providers."""
    
    @staticmethod
    def create_provider(
        provider_type: ModelProviderType,
        **kwargs
    ) -> ModelProvider:
        """
        Create a model provider instance.
        
        Args:
            provider_type: Type of provider to create
            **kwargs: Provider-specific configuration
            
        Returns:
            Model provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type == ModelProviderType.GEMINI:
            from .gemini_service import GeminiService
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Gemini API key is required")
            return GeminiService(
                api_key=api_key,
                max_requests_per_minute=kwargs.get('max_requests_per_minute', 10)
            )
        
        elif provider_type == ModelProviderType.OLLAMA:
            import os
            # Check if we're in a cloud environment
            is_cloud_env = os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING_MODE')
            if is_cloud_env:
                raise ValueError("Ollama is not available in cloud environment. Please use Gemini instead.")
            
            from .ollama_service import OllamaService
            return OllamaService(
                base_url=kwargs.get('base_url', 'http://localhost:11434'),
                model_name=kwargs.get('model_name', 'llama3.2'),
                max_requests_per_minute=kwargs.get('max_requests_per_minute', 10)
            )
        
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    @staticmethod
    def get_available_providers() -> list[ModelProviderType]:
        """Get list of available providers."""
        import os
        available = []
        
        # Check Gemini availability
        try:
            from .gemini_service import GeminiService
            # Just check if we can import, actual availability depends on API key
            available.append(ModelProviderType.GEMINI)
        except ImportError:
            pass
        
        # Check Ollama availability - only if not in cloud environment
        is_cloud_env = os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING_MODE')
        if not is_cloud_env:
            try:
                from .ollama_service import OllamaService
                # Try to create a service to check availability
                service = OllamaService()
                if service.is_available():
                    available.append(ModelProviderType.OLLAMA)
            except Exception:
                pass
        
        return available
