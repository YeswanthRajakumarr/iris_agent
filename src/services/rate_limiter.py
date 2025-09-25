"""Rate limiting service for API requests."""

import time
from typing import Dict, Optional
from ..utils.exceptions import RateLimitError
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Service for managing API rate limits."""
    
    def __init__(self, max_requests_per_minute: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per minute
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.request_counts: Dict[str, Dict[str, int]] = {}
    
    def check_rate_limit(self, session_id: str = "default") -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if request is allowed
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Initialize session data if not exists
        if session_id not in self.request_counts:
            self.request_counts[session_id] = {
                'count': 0,
                'last_reset': current_time
            }
        
        session_data = self.request_counts[session_id]
        
        # Reset counter if minute has passed
        if current_time - session_data['last_reset'] > 60:
            session_data['count'] = 0
            session_data['last_reset'] = current_time
        
        # Check if limit exceeded
        if session_data['count'] >= self.max_requests_per_minute:
            logger.warning(f"Rate limit exceeded for session {session_id}")
            raise RateLimitError("Rate limit exceeded. Please wait a moment before trying again.")
        
        # Increment counter
        session_data['count'] += 1
        return True
    
    def get_remaining_requests(self, session_id: str = "default") -> int:
        """
        Get remaining requests for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Number of remaining requests
        """
        if session_id not in self.request_counts:
            return self.max_requests_per_minute
        
        session_data = self.request_counts[session_id]
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - session_data['last_reset'] > 60:
            return self.max_requests_per_minute
        
        return max(0, self.max_requests_per_minute - session_data['count'])
    
    def reset_session(self, session_id: str = "default") -> None:
        """
        Reset rate limit for a session.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self.request_counts:
            self.request_counts[session_id]['count'] = 0
            self.request_counts[session_id]['last_reset'] = time.time()
