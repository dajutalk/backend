from fastapi import WebSocket
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)

class MarketDataHandler:
    """시장 데이터 핸들러"""
    
    def __init__(self, manager):
        self.manager = manager
    
    async def send_initial_data(self, websocket: WebSocket):
        """연결 시 초기 데이터 전송"""
        try:
            from ...database import SessionLocal
            db = SessionLocal()
            try:
                await self.send_market_data_from_db(websocket, db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ 초기 데이터 전송 실패: {e}")
            await self.send_cached_market_data(websocket)
    
    async def send_latest_data(self, websocket: WebSocket):
        """최신 데이터 전송"""
        await self.send_initial_data(websocket)
    
    async def broadcast_market_data(self):
        """모든 메인 연결에 시장 데이터 브로드캐스트"""
        try:
            from ...database import SessionLocal
            db = SessionLocal()
            try:
                main_connections = self.manager.get_connections_by_type("main")
                for websocket in main_connections.copy():
                    try:
                        await self.send_market_data_from_db(websocket, db)
                    except Exception as e:
                        logger.error(f"❌ 클라이언트 전송 오류: {e}")
                        self.manager.disconnect(websocket)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ 브로드캐스트 오류: {e}")
    
    async def send_market_data_from_db(self, websocket: WebSocket, db: Session):
        """DB에서 최근 30개 데이터를 가져와서 전송"""
        try:
            from ...database.models import StockQuote, CryptoQuote
            from ...services.stock_service import TOP_10_CRYPTOS
            from sqlalchemy import desc
            
            # 주요 주식 데이터 수집
            stock_symbols = [
                "NVDA", "TSLA", "PLTR", "INTC", "AAPL", "BAC", "AMZN", "AMD", "GOOG", "MSFT",
                "META", "AVGO", "NFLX", "COST", "UNH", "MSTR", "LLY", "CRM", "V", "REGN",
                "APP", "WMT", "XOM", "MRVL", "ORCL", "JPM", "TXN", "ZS", "NOW", "MA",
                "IBM", "UBER", "JNJ", "AMAT", "HOOD", "ADI", "GE", "MU", "PANW",
                "INTU", "ABBV", "PG", "DELL", "CRWD", "SPOT", "LIN", "KO", "TMUS", "QCOM", "F"
            ]
            stocks_data = []
            
            for symbol in stock_symbols:
                try:
                    recent_quotes = db.query(StockQuote)\
                        .filter(StockQuote.symbol == symbol)\
                        .order_by(desc(StockQuote.created_at))\
                        .limit(30)\
                        .all()
                    
                    if recent_quotes:
                        recent_quotes.reverse()
                        
                        history_data = []
                        for i, quote in enumerate(recent_quotes):
                            history_data.append({
                                "time": i + 1,
                                "price": float(quote.c)
                            })
                        
                        current_price = float(recent_quotes[-1].c)
                        change = float(recent_quotes[-1].d) if recent_quotes[-1].d else 0
                        change_percent = float(recent_quotes[-1].dp) if recent_quotes[-1].dp else 0
                        
                        stocks_data.append({
                            "symbol": symbol,
                            "price": current_price,
                            "change": change,
                            "changePercent": change_percent,
                            "history": history_data,
                            "timestamp": int(recent_quotes[-1].created_at.timestamp() * 1000),
                            "data_source": "database"
                        })
                except Exception as e:
                    logger.error(f"❌ 주식 {symbol} 조회 오류: {e}")
                    continue
            
            # 암호화폐 데이터 수집
            cryptos_data = []
            for symbol in TOP_10_CRYPTOS:
                try:
                    recent_crypto_quotes = db.query(CryptoQuote)\
                        .filter(CryptoQuote.symbol == symbol)\
                        .order_by(desc(CryptoQuote.created_at))\
                        .limit(30)\
                        .all()
                    
                    if recent_crypto_quotes:
                        recent_crypto_quotes.reverse()
                        
                        history_data = []
                        for i, quote in enumerate(recent_crypto_quotes):
                            history_data.append({
                                "time": i + 1,
                                "price": float(quote.p)
                            })
                        
                        cryptos_data.append({
                            "symbol": symbol,
                            "price": float(recent_crypto_quotes[-1].p),
                            "change": 0,
                            "changePercent": 0,
                            "history": history_data,
                            "timestamp": int(recent_crypto_quotes[-1].created_at.timestamp() * 1000),
                            "data_source": "database"
                        })
                except Exception as e:
                    logger.error(f"❌ 암호화폐 {symbol} 조회 오류: {e}")
                    continue
            
            market_data = {
                "type": "market_update",
                "data": {
                    "stocks": stocks_data,
                    "cryptos": cryptos_data
                },
                "timestamp": int(time.time() * 1000),
                "data_source": "database",
                "message": f"DB에서 {len(stocks_data)}개 주식, {len(cryptos_data)}개 암호화폐 데이터 전송"
            }
            
            await self.manager.send_personal_message(market_data, websocket)
            logger.info(f"✅ DB market data sent - {len(stocks_data)} stocks, {len(cryptos_data)} cryptos")
            
        except Exception as e:
            logger.error(f"❌ DB에서 데이터 조회 오류: {e}")
            await self.send_cached_market_data(websocket)
    
    async def send_cached_market_data(self, websocket: WebSocket):
        """캐시된 데이터를 전송 (DB 연결 실패 시 fallback)"""
        try:
            # 간단한 더미 데이터
            market_data = {
                "type": "market_update",
                "data": {
                    "stocks": [],
                    "cryptos": []
                },
                "timestamp": int(time.time() * 1000),
                "data_source": "cache",
                "message": "캐시 모드 - 데이터베이스 연결 실패"
            }
            
            await self.manager.send_personal_message(market_data, websocket)
            logger.info("Cache market data sent (fallback)")
            
        except Exception as e:
            logger.error(f"❌ 캐시 데이터 전송 오류: {e}")
