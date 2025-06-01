from fastapi import WebSocket
from sqlalchemy.orm import Session
import asyncio
import logging

logger = logging.getLogger(__name__)

class CryptoHandler:
    """암호화폐 데이터 핸들러"""
    
    def __init__(self, manager):
        self.manager = manager
    
    async def handle_crypto_updates(self, websocket: WebSocket, symbol: str, db: Session):
        """암호화폐 업데이트 처리"""
        try:
            from ...database.models import CryptoQuote
            from sqlalchemy import desc
            
            while True:
                # DB에서 해당 암호화폐의 최근 30개 레코드 조회
                recent_crypto_quotes = db.query(CryptoQuote)\
                    .filter(CryptoQuote.symbol == symbol.upper())\
                    .order_by(desc(CryptoQuote.created_at))\
                    .limit(30)\
                    .all()
                
                if recent_crypto_quotes:
                    recent_crypto_quotes.reverse()
                    
                    crypto_history = []
                    for quote in recent_crypto_quotes:
                        crypto_history.append({
                            "time": quote.created_at.strftime("%H:%M:%S"),
                            "price": float(quote.p),
                            "timestamp": int(quote.created_at.timestamp() * 1000)
                        })
                    
                    formatted_data = {
                        "type": "crypto_update",
                        "data": {
                            "symbol": symbol.upper(),
                            "history": crypto_history,
                            "current_price": float(recent_crypto_quotes[-1].p),
                            "last_update": recent_crypto_quotes[-1].created_at.isoformat(),
                            "data_source": "database"
                        }
                    }
                    await self.manager.send_personal_message(formatted_data, websocket)
                else:
                    # DB에 데이터가 없는 경우
                    formatted_data = {
                        "type": "crypto_update",
                        "data": {
                            "symbol": symbol.upper(),
                            "history": [],
                            "current_price": 0,
                            "last_update": None,
                            "data_source": "database",
                            "message": "DB에 데이터가 없습니다"
                        }
                    }
                    await self.manager.send_personal_message(formatted_data, websocket)
                
                await asyncio.sleep(1.0)
                
        except Exception as e:
            logger.error(f"❌ 암호화폐 핸들러 오류: {e}")
