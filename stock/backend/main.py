from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from stock.backend.api import stock, chat




app = FastAPI()
app.include_router(stock.router)
app.include_router(chat.router)




        