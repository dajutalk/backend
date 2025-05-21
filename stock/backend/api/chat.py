from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

router = APIRouter(
    prefix="/ws",
    tags=["Chat"],
)

chat_rooms: dict[str, list[WebSocket]] = {}

@router.websocket("/chat")
async def chat_endpoint(websocket: WebSocket, symbol: str = Query(...)):
    await websocket.accept()
    if symbol not in chat_rooms:
        chat_rooms[symbol] = []

    chat_rooms[symbol].append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            for client in chat_rooms[symbol]:
                await client.send_text(msg)
    except WebSocketDisconnect:
        chat_rooms[symbol].remove(websocket)
