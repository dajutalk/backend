import asyncio
import websocket
import json
from backend.api.stock import broadcast_stock_data

loop = asyncio.get_event_loop()





def run_ws(loop):
    def on_message(ws, message):
        try:
            data = json.loads(message)
            asyncio.run_coroutine_threadsafe(broadcast_stock_data(data), loop)
        except Exception as e:
            print("❌ 수신 처리 중 에러:", e)

    def on_open(ws):
        ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')

    ws = websocket.WebSocketApp(
        "wss://ws.finnhub.io?token=d0fgaf9r01qsv9ehav00d0fgaf9r01qsv9ehav0g",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()


