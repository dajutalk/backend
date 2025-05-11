from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)
clients = []

@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    if  WebSocketDisconnect:
        clients.remove(websocket)

# 외부 WebSocket(Finnhub) → 이 clients 리스트에 broadcast
async def broadcast_stock_data(data: dict):
    print("📡 브로드캐스트 시작:", data)  # 로그 추가
    living = []
    for ws in clients:
        try:
            await ws.send_text(json.dumps(data))
            living.append(ws)
        except Exception as e:
            print("전송 실패:", e)
    clients[:] = living
