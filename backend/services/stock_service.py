import websocket
import json
from backend.api.stock import broadcast_stock_data

def on_message(ws, message):
    data = json.loads(message)
    asyncio.run(broadcast_stock_data(data))  # 클라이언트에게 전달

def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"AAPL"}')

def run_ws():
    ws = websocket.WebSocketApp(
        "wss://ws.finnhub.io?token=YOUR_API_KEY",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

