import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from .database.connection import engine, Base
from .routes import stock

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    lifespan=lifespan,
)


connections = []
app.include_router(stock.router, prefix="/api")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index.html")

@app.get("/")
async def get():
    return FileResponse(TEMPLATE_PATH)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for conn in connections:
                await conn.send_text(f"{data}")
    except WebSocketDisconnect:
        connections.remove(websocket)
        