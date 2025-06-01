from fastapi import WebSocket
from sqlalchemy.orm import Session
import asyncio
import logging

logger = logging.getLogger(__name__)

class StockHandler:
    """주식 데이터 핸들러"""
    
    def __init__(self, manager):
        self.manager = manager
    
    async def handle_stock_updates(self, websocket: WebSocket, symbol: str, db: Session):
        """주식 업데이트 처리"""
        try:
            from ...database.models import StockQuote
            from sqlalchemy import desc
            
            while True:
                # DB에서 해당 심볼의 최근 30개 레코드 조회
                recent_quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .order_by(desc(StockQuote.created_at))\
                    .limit(30)\
                    .all()
                
                if recent_quotes:
                    recent_quotes.reverse()
                    
                    stock_history = []
                    for quote in recent_quotes:
                        stock_history.append({
                            "time": quote.created_at.strftime("%H:%M:%S"),
                            "price": float(quote.c),
                            "timestamp": int(quote.created_at.timestamp() * 1000)
                        })
                    
                    formatted_data = {
                        "type": "stock_update",
                        "data": {
                            "symbol": symbol,
                            "history": stock_history,
                            "current_price": float(recent_quotes[-1].c),
                            "last_update": recent_quotes[-1].created_at.isoformat(),
                            "data_source": "database"
                        }
                    }
                    await self.manager.send_personal_message(formatted_data, websocket)
                else:
                    # DB에 데이터가 없는 경우
                    formatted_data = {
                        "type": "stock_update",
                        "data": {
                            "symbol": symbol,
                            "history": [],
                            "current_price": 0,
                            "last_update": None,
                            "data_source": "database",
                            "message": "DB에 데이터가 없습니다"
                        }
                    }
                    await self.manager.send_personal_message(formatted_data, websocket)
                
                await asyncio.sleep(2.0)
                
        except Exception as e:
            logger.error(f"❌ 주식 핸들러 오류: {e}")
