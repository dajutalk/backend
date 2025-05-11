from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.utils.ws_manager import safe_add_client,safe_remove_client
import asyncio


router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)


@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await safe_add_client(websocket)
    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        await safe_remove_client(websocket)
 



