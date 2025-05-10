from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse


app =FastAPI()


TEMPLATE_PATH = "backend/templates/index.html"

@app.get("/")
async def get():
    return FileResponse(TEMPLATE_PATH)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"{data}")

        