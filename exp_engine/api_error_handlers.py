"""
Simplified API Error Handling
Provides consistent error response formatting
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorDetail(BaseModel):
    """Standardized error detail structure"""
    code: str
    message: str
    exp_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response wrapper"""
    error: ErrorDetail


def create_error_response(code: str, message: str, exp_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> dict:
    """
    Create a standardized error response

    Args:
        code: Error code (e.g., "NOT_FOUND", "INTERNAL_ERROR")
        message: Human-readable error message
        exp_name: Optional experiment name for context
        details: Optional additional error details

    Returns:
        Dictionary formatted as standardized error response
    """
    response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            exp_name=exp_name,
            details=details
        )
    )
    return response.model_dump(exclude_none=True)
