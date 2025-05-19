from asyncio import Lock
from fastapi import WebSocket
import json

clients=[]
clients_lock =Lock()

async def safe_add_client(ws: WebSocket, symbol: str):
    async with clients_lock:
        clients.append({"websocket": ws, "symbol": symbol})

async def safe_remove_client(ws: WebSocket):
    async with clients_lock:
        clients[:] = [
            client for client in clients if client["websocket"] != ws
        ]

async def broadcast_stock_data(data: dict):
    print("브로드캐스트 시작:", data) 
    symbol = data["data"][0]["s"]
    async with clients_lock:
        for client in clients:
            if client["symbol"] == symbol:
                try:
                    await client["websocket"].send_text(json.dumps(data))
                except Exception as e:
                    print("전송 실패:", e)