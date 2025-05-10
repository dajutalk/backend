import websocket
import json
from backend.api.stock import broadcast_stock_data

def on_message(ws, message):
    data = json.loads(message)
    asyncio.run(broadcast_stock_data(data))  # 클라이언트에게 전달

def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')

def run_ws():
    ws = websocket.WebSocketApp(
        "wss://ws.finnhub.io?token=d0fgaf9r01qsv9ehav00d0fgaf9r01qsv9ehav0g",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

