from asyncio import Lock
from fastapi import WebSocket
import json

clients=[]
clients_lock =Lock()

async def safe_add_client(ws: WebSocket):
    async with clients_lock:
        clients.append(ws)

async def safe_remove_client(ws: WebSocket):
    async with clients_lock:
        clients.remove(ws)

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