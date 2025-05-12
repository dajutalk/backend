from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.utils.ws_manager import safe_add_client,safe_remove_client
import threading
import asyncio
import json
from backend.services.stock_service import run_ws  
router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)


@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket, symbol= Query(...)):
    await websocket.accept()
    await safe_add_client(websocket)

    loop = asyncio.get_event_loop()
    threading.Thread(target=run_ws, args=(loop, symbol), daemon=True).start()

    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_text(json.dumps({'type':'ping'}))
    except WebSocketDisconnect:
        await safe_remove_client(websocket)
 



