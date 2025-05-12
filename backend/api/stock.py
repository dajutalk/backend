from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.utils.ws_manager import safe_add_client,safe_remove_client
import asyncio
import json

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)


@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await websocket.accept()
    await safe_add_client(websocket, symbol)
    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_text(json.dumps({'type':'ping'}))
    except WebSocketDisconnect:
        await safe_remove_client(websocket)
 



