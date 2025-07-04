"""Session-based logging configuration for debugging"""
import logging
import os
from datetime import datetime
from pathlib import Path
import sys

def setup_session_logging(service_name: str, session_id: str = None) -> logging.Logger:
    """
    Set up logging that outputs to both stdout and a session-specific file
    
    Args:
        service_name: Name of the service (e.g., 'voice_processor', 'realtime_client')
        session_id: Optional session ID for the log file
    
    Returns:
        Configured logger instance
    """
    # Create logs directory structure
    logs_dir = Path("logs") / service_name
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_suffix = f"_{session_id}" if session_id else ""
    log_filename = logs_dir / f"{timestamp}_{service_name}{session_suffix}.log"
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler (detailed logging)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (simpler format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Log the session start
    logger.info(f"=== Session started: {service_name} ===")
    logger.info(f"Log file: {log_filename}")
    if session_id:
        logger.info(f"Session ID: {session_id}")
    
    return logger

def get_session_logger(service_name: str) -> logging.Logger:
    """Get or create a logger for a service"""
    return logging.getLogger(service_name)