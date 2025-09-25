"""Data models for log analysis."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class SessionSummary:
    """Summary metrics for charging sessions."""
    
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    total_energy_delivered_kwh: float = 0.0
    pre_charging_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            'Total Sessions': str(self.total_sessions),
            'Successful Sessions': str(self.successful_sessions),
            'Failed Sessions': str(self.failed_sessions),
            'Total Energy Delivered (kWh)': str(self.total_energy_delivered_kwh),
            'Pre-charging Failures': str(self.pre_charging_failures)
        }


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    
    summary: SessionSummary
    detailed_analysis: str
    timestamp: datetime
    source_file: Optional[str] = None
    original_content: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TransactionSession:
    """Represents a single charging transaction session."""
    
    transaction_id: int
    messages: List[Dict[str, Any]]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    energy_delivered: Optional[float] = None
    status: str = "unknown"
    
    @property
    def is_successful(self) -> bool:
        """Check if the session was successful."""
        return self.status.lower() in ['completed', 'successful', 'normal']


@dataclass
class LogFile:
    """Represents an uploaded log file."""
    
    filename: str
    content: str
    file_type: str
    size_bytes: int
    parsed_content: Optional[str] = None
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def is_valid_size(self, max_size_mb: int = 5) -> bool:
        """Check if file size is within limits."""
        return self.size_mb <= max_size_mb
