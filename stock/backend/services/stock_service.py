import asyncio
import websocket
import json
from stock.backend.utils.ws_manager import broadcast_stock_data
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
loop = asyncio.get_event_loop()



def run_ws(loop, symbol):
    def on_message(ws, message):
        try:
            data = json.loads(message)
            asyncio.run_coroutine_threadsafe(broadcast_stock_data(data), loop)
        except Exception as e:
            print("수신 처리 중 에러:", e)

    def on_open(ws):
        ws.send(json.dumps({
            "type": "subscribe",
            "symbol": symbol
        }))
        print(f" {symbol} 구독 시작")

    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={API_KEY}",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

 