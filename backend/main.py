from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from backend.api import stock  # WebSocket 라우터





app = FastAPI()
app.include_router(stock.router)

# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: list[WebSocket] = []

#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)

#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)


#     async def broadcast(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)


# manager = ConnectionManager()

# TEMPLATE_PATH = "backend/templates/index.html"

# @app.get("/")
# async def get():
#     return FileResponse(TEMPLATE_PATH)




# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.broadcast(f"Client  says: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client  left the chat")



        