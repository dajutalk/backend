from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from backend.api import stock  # WebSocket 라우터
from contextlib import asynccontextmanager
import threading
from backend.services.stock_service import run_ws  # 아래에서 만들 서비스
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ 앱 시작 시
    thread = threading.Thread(target=run_ws, daemon=True)
    thread.start()

    yield  # 앱이 실행되는 동안 유지됨

    # ⛔ 앱 종료 시 정리 작업 필요하면 여기에 추가
    # thread.join() 같은 건 일반적으로 안 넣어도 됩니다

app = FastAPI(lifespan=lifespan)
app.include_router(stock.router)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

TEMPLATE_PATH = "backend/templates/index.html"

@app.get("/")
async def get():
    return FileResponse(TEMPLATE_PATH)


@app.websocket("/ws")
async def test_ws(websocket: WebSocket):
    print("🟢 WebSocket 연결 시도됨")
    await websocket.accept()
    try:
        while True:
            await websocket.send_text("pong") 
            await asyncio.sleep(3)
    except Exception as e:
        print("❌ WebSocket 에러:", e)


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



        