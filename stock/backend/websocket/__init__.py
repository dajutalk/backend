from .manager import WebSocketManager
from .routes import router

manager = WebSocketManager()

__all__ = ["manager", "router"]
