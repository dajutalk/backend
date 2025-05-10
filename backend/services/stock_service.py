import websocket
import threading
import json
from backend.api.stock import broadcast_stock_data

def on_message(ws, message):
    data = json.loads(message)
    # 수신된 데이터를 프론트에 중계
    asyncio.run(broadcast_stock_data(data))

def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"AAPL"}')

def run_ws():
    ws = websocket.WebSocketApp(
        "wss://ws.finnhub.io?token=YOUR_API_KEY",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

# FastAPI 시작 시 자동 실행
threading.Thread(target=run_ws).start()
