"""Validation utilities for Iris.agent."""

import logging
from typing import Optional
from .exceptions import FileSizeError, SecurityError

logger = logging.getLogger(__name__)


def validate_file_size(file_content: bytes, max_size_mb: int = 5) -> bool:
    """
    Validate file size for security.
    
    Args:
        file_content: The file content to validate
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        True if file size is valid
        
    Raises:
        FileSizeError: If file size exceeds limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if len(file_content) > max_size_bytes:
        logger.warning(f"File size exceeded limit: {len(file_content)} bytes")
        raise FileSizeError(f"File too large. Maximum size allowed: {max_size_mb}MB")
    
    return True


def sanitize_input(text: str) -> bool:
    """
    Sanitize input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        True if input is safe
        
    Raises:
        SecurityError: If potentially dangerous content is detected
    """
    dangerous_patterns = ['<script>', 'javascript:', 'vbscript:']
    
    for pattern in dangerous_patterns:
        if pattern.lower() in text.lower():
            logger.warning(f"Potentially dangerous content detected: {pattern}")
            raise SecurityError(f"Potentially dangerous content detected: {pattern}")
    
    return True


def validate_file_type(filename: str, allowed_types: list[str]) -> bool:
    """
    Validate file type.
    
    Args:
        filename: Name of the file
        allowed_types: List of allowed file extensions
        
    Returns:
        True if file type is allowed
        
    Raises:
        FileFormatError: If file type is not supported
    """
    from .exceptions import FileFormatError
    
    file_extension = filename.split('.')[-1].lower()
    
    if file_extension not in allowed_types:
        raise FileFormatError(f"File type '{file_extension}' not supported. Allowed types: {allowed_types}")
    
    return True
