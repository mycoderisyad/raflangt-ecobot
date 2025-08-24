"""
Error Handler Utilities
Centralized error handling and logging
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable
from functools import wraps
from core.utils import LoggerUtils


class ErrorHandler:
    """Centralized error handling utilities"""

    @staticmethod
    def handle_database_error(error: Exception, context: str = None) -> Dict[str, Any]:
        """Handle database-related errors"""
        error_msg = (
            f"Database error in {context}: {str(error)}" if context else str(error)
        )
        LoggerUtils.log_error(logging.getLogger(__name__), error, context)

        return {
            "success": False,
            "error": "database_error",
            "message": "Terjadi kesalahan database. Silakan coba lagi.",
            "details": error_msg
            if logging.getLogger().level <= logging.DEBUG
            else None,
        }

    @staticmethod
    def handle_api_error(error: Exception, context: str = None) -> Dict[str, Any]:
        """Handle API-related errors"""
        error_msg = f"API error in {context}: {str(error)}" if context else str(error)
        LoggerUtils.log_error(logging.getLogger(__name__), error, context)

        return {
            "success": False,
            "error": "api_error",
            "message": "Terjadi kesalahan API. Silakan coba lagi.",
            "details": error_msg
            if logging.getLogger().level <= logging.DEBUG
            else None,
        }

    @staticmethod
    def handle_validation_error(
        error: Exception, context: str = None
    ) -> Dict[str, Any]:
        """Handle validation errors"""
        error_msg = (
            f"Validation error in {context}: {str(error)}" if context else str(error)
        )
        LoggerUtils.log_error(logging.getLogger(__name__), error, context)

        return {
            "success": False,
            "error": "validation_error",
            "message": "Data tidak valid. Silakan periksa input Anda.",
            "details": error_msg
            if logging.getLogger().level <= logging.DEBUG
            else None,
        }

    @staticmethod
    def handle_permission_error(
        error: Exception, context: str = None
    ) -> Dict[str, Any]:
        """Handle permission-related errors"""
        error_msg = (
            f"Permission error in {context}: {str(error)}" if context else str(error)
        )
        LoggerUtils.log_error(logging.getLogger(__name__), error, context)

        return {
            "success": False,
            "error": "permission_error",
            "message": "Anda tidak memiliki izin untuk melakukan tindakan ini.",
            "details": error_msg
            if logging.getLogger().level <= logging.DEBUG
            else None,
        }

    @staticmethod
    def handle_general_error(error: Exception, context: str = None) -> Dict[str, Any]:
        """Handle general errors"""
        error_msg = (
            f"General error in {context}: {str(error)}" if context else str(error)
        )
        LoggerUtils.log_error(logging.getLogger(__name__), error, context)

        return {
            "success": False,
            "error": "general_error",
            "message": "Terjadi kesalahan sistem. Silakan coba lagi.",
            "details": error_msg
            if logging.getLogger().level <= logging.DEBUG
            else None,
        }


def safe_execute(error_type: str = "general", context: str = None):
    """Decorator for safe function execution with error handling"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_type == "database":
                    return ErrorHandler.handle_database_error(e, context)
                elif error_type == "api":
                    return ErrorHandler.handle_api_error(e, context)
                elif error_type == "validation":
                    return ErrorHandler.handle_validation_error(e, context)
                elif error_type == "permission":
                    return ErrorHandler.handle_permission_error(e, context)
                else:
                    return ErrorHandler.handle_general_error(e, context)

        return wrapper

    return decorator


def log_errors(logger: logging.Logger = None):
    """Decorator for logging errors without changing return value"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    LoggerUtils.log_error(logger, e, f"in {func.__name__}")
                else:
                    LoggerUtils.log_error(
                        logging.getLogger(__name__), e, f"in {func.__name__}"
                    )
                raise  # Re-raise the exception

        return wrapper

    return decorator


def handle_errors(error_handler: Callable = None):
    """Decorator for custom error handling"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    return error_handler(e, func.__name__)
                else:
                    return ErrorHandler.handle_general_error(e, func.__name__)

        return wrapper

    return decorator
