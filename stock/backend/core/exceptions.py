from fastapi import HTTPException
from typing import Optional

class StockAPIException(HTTPException):
    """주식 API 관련 예외"""
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class DatabaseException(Exception):
    """데이터베이스 관련 예외"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class WebSocketException(Exception):
    """WebSocket 관련 예외"""
    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ServiceException(Exception):
    """서비스 레이어 예외"""
    def __init__(self, message: str, service: str):
        self.message = message
        self.service = service
        super().__init__(f"[{service}] {message}")
