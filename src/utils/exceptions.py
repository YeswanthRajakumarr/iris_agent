"""Custom exceptions for Iris.agent application."""


class IrisAgentError(Exception):
    """Base exception for Iris.agent application."""
    pass


class ConfigurationError(IrisAgentError):
    """Raised when there's a configuration issue."""
    pass


class APIError(IrisAgentError):
    """Raised when there's an API-related error."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class FileProcessingError(IrisAgentError):
    """Raised when there's an error processing files."""
    pass


class FileSizeError(FileProcessingError):
    """Raised when file size exceeds limits."""
    pass


class FileFormatError(FileProcessingError):
    """Raised when file format is not supported."""
    pass


class SecurityError(IrisAgentError):
    """Raised when security validation fails."""
    pass


class AnalysisError(IrisAgentError):
    """Raised when analysis fails."""
    pass
