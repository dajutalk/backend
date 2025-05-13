from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from stock.backend.utils.ws_manager import safe_add_client,safe_remove_client
import threading
import asyncio
import json
from stock.backend.services.stock_service import run_ws  
router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)


running_threads = {}

@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket, symbol= Query(...)):
    await websocket.accept()
    await safe_add_client(websocket, symbol)

    if symbol not in running_threads:
        loop = asyncio.get_event_loop()
        thread = threading.Thread(target=run_ws, args=(loop, symbol), daemon=True)
        thread.start()
        running_threads[symbol] = thread

    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_text(json.dumps({'type':'ping'}))
    except WebSocketDisconnect:
        await safe_remove_client(websocket)
 



