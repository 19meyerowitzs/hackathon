import logging
import sys

# Global variable to hold the user's logger
_user_logger = None

def set_logger(user_logger):
    """
    Set a custom logger to be used throughout the application.
    
    Args:
        user_logger: A logging.Logger instance to use instead of the default logger
    """
    global _user_logger
    _user_logger = user_logger

def get_logger():
    """
    Get the current logger (user's custom logger or default logger).
    
    Returns:
        logging.Logger: The active logger instance
    """
    global _user_logger
    if _user_logger is not None:
        return _user_logger
    return _default_logger

# Create the default logger (existing logic)
_default_logger = logging.getLogger('utils.logging_config')
_default_logger.setLevel(logging.INFO)

# Prevent adding handlers multiple times (more robust check)
if not _default_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    ))
    _default_logger.addHandler(handler)
    
# Prevent log propagation to avoid duplicate messages from parent loggers
_default_logger.propagate = False

# For backward compatibility, expose the default logger
# But users should migrate to using get_logger()
logger = _default_logger
