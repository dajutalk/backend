from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()
clients = []

@router.websocket("/ws/stocks")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # heartbeat 또는 ping 유지용
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        clients.remove(websocket)

# 외부 WebSocket(Finnhub) → 이 clients 리스트에 broadcast
async def broadcast_stock_data(data: dict):
    living = []
    for ws in clients:
        try:
            await ws.send_text(json.dumps(data))
            living.append(ws)
        except:
            pass
    clients[:] = living
