"""Iris.agent - OCPP Log Analysis Platform."""

__version__ = "1.0.0"
__author__ = "Iris.agent Team"
__description__ = "AI-powered OCPP log analysis and troubleshooting platform"

from .config import config
from .models import SessionSummary, AnalysisResult, TransactionSession, LogFile
from .services import FileProcessor, GeminiService, RateLimiter
from .utils import (
    IrisAgentError,
    ConfigurationError,
    APIError,
    RateLimitError,
    FileProcessingError,
    FileSizeError,
    FileFormatError,
    SecurityError,
    AnalysisError,
    validate_file_size,
    sanitize_input,
    validate_file_type,
    setup_logging,
    get_logger
)
from .di import container

__all__ = [
    '__version__',
    '__author__',
    '__description__',
    'config',
    'SessionSummary',
    'AnalysisResult',
    'TransactionSession',
    'LogFile',
    'FileProcessor',
    'GeminiService',
    'RateLimiter',
    'IrisAgentError',
    'ConfigurationError',
    'APIError',
    'RateLimitError',
    'FileProcessingError',
    'FileSizeError',
    'FileFormatError',
    'SecurityError',
    'AnalysisError',
    'validate_file_size',
    'sanitize_input',
    'validate_file_type',
    'setup_logging',
    'get_logger',
    'container'
]
