from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    prefix="/ws",
    tags=["Chat"],
)

chat_clients: list[WebSocket] = []

@router.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_clients.append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            for client in chat_clients:
                await client.send_text(msg)
    except WebSocketDisconnect:
        chat_clients.remove(websocket)
