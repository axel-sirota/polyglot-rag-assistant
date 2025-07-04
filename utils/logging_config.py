"""Centralized logging configuration for all components"""
import logging
import os
from datetime import datetime

def setup_logging(component_name: str, log_level=logging.INFO):
    """
    Set up logging for a component to log to both stdout and file
    
    Args:
        component_name: Name of the component (used for log filename)
        log_level: Logging level (default: INFO)
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(component_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'{component_name}.log'),
        mode='a'  # Append mode
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler - simpler format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log startup
    logger.info(f"{'='*50}")
    logger.info(f"Starting {component_name} - {datetime.now()}")
    logger.info(f"{'='*50}")
    
    return logger

# Configure root logger to prevent duplicate logs
def configure_root_logger():
    """Configure root logger to prevent propagation issues"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only show warnings and above from libraries
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

# Suppress noisy libraries
def suppress_noisy_loggers():
    """Suppress verbose logging from certain libraries"""
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('gradio').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)