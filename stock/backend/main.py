from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from stock.backend.api import stock, chat
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영환경에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 라우터 등록
app.include_router(stock.router)
app.include_router(chat.router)

# REST API 라우터 추가
app.include_router(stock.rest_router)




