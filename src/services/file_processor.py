"""File processing service for OCPP logs."""

import pandas as pd
import re
from io import StringIO
from typing import Optional, Dict, List, Tuple, Set

from ..models.analysis import LogFile, TransactionSession
from ..utils.exceptions import FileProcessingError, FileSizeError
from ..utils.validators import validate_file_size
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class FileProcessor:
    """Service for processing OCPP log files."""
    
    def __init__(self, max_file_size_mb: int = 5, max_dataframe_rows: int = 50000):
        """
        Initialize file processor.
        
        Args:
            max_file_size_mb: Maximum file size in MB
            max_dataframe_rows: Maximum number of rows to process
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_dataframe_rows = max_dataframe_rows
    
    def parse_file_to_text(self, log_file: LogFile, use_iris_cms_filtering: bool = False) -> str:
        """
        Parse CSV/XLSX content and convert to readable text format.
        
        Args:
            log_file: Log file to process
            use_iris_cms_filtering: Whether to use Iris CMS specific filtering
            
        Returns:
            Parsed text content
            
        Raises:
            FileProcessingError: If file processing fails
        """
        try:
            # Validate file size
            validate_file_size(log_file.content.encode(), self.max_file_size_mb)
            
            logger.info(f"Processing {log_file.file_type} file of size: {log_file.size_bytes} bytes")
            
            # Parse file based on type
            if log_file.file_type == 'csv':
                df = pd.read_csv(StringIO(log_file.content))
            elif log_file.file_type == 'xlsx':
                df = pd.read_excel(log_file.content)
            else:
                raise FileProcessingError(f"Unsupported file type: {log_file.file_type}")
            
            # Limit rows for performance
            if len(df) > self.max_dataframe_rows:
                df = df.head(self.max_dataframe_rows)
                logger.info(f"DataFrame truncated to {self.max_dataframe_rows} rows for performance")
            
            filtered_df = None
            if use_iris_cms_filtering:
                filtered_df = self._filter_iris_cms_logs(df)
            else:
                filtered_df = self._filter_heartbeat_and_boot_notification_messages(df)
            
            print(f"🚀 {use_iris_cms_filtering}")
            # write to csv
            filtered_df.to_csv('filtered_df.csv', index=False)
            return
            
            # Convert to structured text format
            text_content = self._convert_to_text_format(filtered_df)
            
            logger.info(f"Successfully parsed file with {len(filtered_df)} rows")
            return text_content
            
        except Exception as e:
            logger.error(f"Error parsing file: {str(e)}")
            raise FileProcessingError(f"Error processing file: {str(e)}")
    
    def _filter_heartbeat_and_boot_notification_messages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out heartbeat and boot notification messages from the dataframe."""
        heartbeat_mask = df.astype(str).apply(
            lambda x: x.str.contains('Heart', case=False, na=False)
        ).any(axis=1)

        boot_notification_mask = df.astype(str).apply(
            lambda x: x.str.contains('BootNotification', case=False, na=False)
        ).any(axis=1)

        # Combine boolean operations properly
        combined_mask = (heartbeat_mask == False) & (boot_notification_mask == False)
        return df[combined_mask]

    def _filter_iris_cms_logs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out iris cms logs from the dataframe."""
        messagesToRemove = ['HeartBeat',  'BootNotification' ,'StatusNotificationResponse' , 'MeterValuesResponse']
        mask = df.astype(str).apply(
            lambda x: x.str.contains('|'.join(messagesToRemove), case=False, na=False)
        ).any(axis=1)
        return df[mask == False]


    def _convert_to_text_format(self, df: pd.DataFrame) -> str:
        """Convert dataframe to structured text format."""
        text_content = "OCPP Log Data:\n\n"
        
        # Add column headers
        text_content += "Columns: " + ", ".join(df.columns.tolist()) + "\n\n"
        
        # Extract transaction sessions
        transaction_sessions = self._extract_transaction_sessions(df)
        
        # Add session analysis
        text_content += "=== SESSION ANALYSIS ===\n\n"
        
        for session in transaction_sessions:
            text_content += f"--- TRANSACTION SESSION {session.transaction_id} ---\n"
            
            for msg_index, (_, row) in enumerate(session.messages):
                text_content += f"  Message {msg_index + 1}:\n"
                for col in df.columns:
                    text_content += f"    {col}: {row[col]}\n"
                text_content += "\n"
            
            text_content += "\n"
        
        # Add remaining messages
        remaining_messages = self._get_remaining_messages(df, transaction_sessions)
        text_content += "=== OTHER MESSAGES ===\n\n"
        
        for msg_index, (_, row) in enumerate(remaining_messages):
            text_content += f"Message {msg_index + 1}:\n"
            for col in df.columns:
                text_content += f"  {col}: {row[col]}\n"
            text_content += "\n"
        
        return text_content
    
    def _extract_transaction_sessions(self, df: pd.DataFrame) -> List[TransactionSession]:
        """Extract transaction sessions from the dataframe."""
        transaction_ids = self._extract_transaction_ids(df)
        sessions = []
        
        for tx_id in sorted(transaction_ids):
            messages = self._get_messages_for_transaction(df, tx_id)
            if messages:
                session = TransactionSession(
                    transaction_id=tx_id,
                    messages=messages
                )
                sessions.append(session)
        
        logger.info(f"Found {len(sessions)} unique transaction sessions")
        return sessions
    
    def _extract_transaction_ids(self, df: pd.DataFrame) -> Set[int]:
        """Extract unique transaction IDs from the dataframe."""
        transaction_ids = set()
        
        for _, row in df.iterrows():
            payload = str(row.get('payLoadData', ''))
            if 'transactionId' in payload.lower():
                tx_id = self._extract_transaction_id_from_payload(payload)
                if tx_id is not None:
                    transaction_ids.add(tx_id)
        
        return transaction_ids
    
    def _extract_transaction_id_from_payload(self, payload: str) -> Optional[int]:
        """Extract transaction ID from JSON payload."""
        patterns = [
            r'"transactionId":\s*(\d+)',
            r'"transactionId":\s*"(\d+)"',
            r'"transactionId":\s*(\d+\.\d+)',
            r'"transactionId":\s*"(\d+\.\d+)"',
            r'"transactionid":\s*(\d+)',
            r'"transactionid":\s*"(\d+)"',
            r'"TransactionId":\s*(\d+)',
            r'"TransactionId":\s*"(\d+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, payload)
            if match:
                try:
                    return int(float(match.group(1)))
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _get_messages_for_transaction(self, df: pd.DataFrame, tx_id: int) -> List[Tuple[int, pd.Series]]:
        """Get all messages related to a specific transaction."""
        messages = []
        
        for index, row in df.iterrows():
            payload = str(row.get('payLoadData', ''))
            tx_patterns = [
                f'"transactionId":{tx_id}',
                f'"transactionId":"{tx_id}"',
                f'"transactionId": {tx_id}',
                f'"transactionId": "{tx_id}"',
                f'"transactionId":{tx_id}.0',
                f'"transactionId":"{tx_id}.0"',
                f'"transactionid":{tx_id}',
                f'"transactionid":"{tx_id}"',
                f'"TransactionId":{tx_id}',
                f'"TransactionId":"{tx_id}"',
            ]
            
            if any(pattern in payload for pattern in tx_patterns):
                messages.append((index, row))
        
        # Sort by timestamp
        messages.sort(key=lambda x: x[1].get('real_time', ''))
        return messages
    
    def _get_remaining_messages(self, df: pd.DataFrame, sessions: List[TransactionSession]) -> List[Tuple[int, pd.Series]]:
        """Get messages that don't belong to any transaction session."""
        transaction_ids = {session.transaction_id for session in sessions}
        remaining_messages = []
        
        for index, row in df.iterrows():
            payload = str(row.get('payLoadData', ''))
            has_transaction = False
            
            for tx_id in transaction_ids:
                tx_patterns = [
                    f'"transactionId":{tx_id}',
                    f'"transactionId":"{tx_id}"',
                    f'"transactionId": {tx_id}',
                    f'"transactionId": "{tx_id}"',
                    f'"transactionId":{tx_id}.0',
                    f'"transactionId":"{tx_id}.0"',
                    f'"transactionid":{tx_id}',
                    f'"transactionid":"{tx_id}"',
                    f'"TransactionId":{tx_id}',
                    f'"TransactionId":"{tx_id}"',
                ]
                if any(pattern in payload for pattern in tx_patterns):
                    has_transaction = True
                    break
            
            if not has_transaction:
                remaining_messages.append((index, row))
        
        # Sort by timestamp
        remaining_messages.sort(key=lambda x: x[1].get('real_time', ''))
        return remaining_messages
