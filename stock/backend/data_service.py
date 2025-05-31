from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from stock.backend.models import StockQuote, CryptoQuote

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def get_latest_stock_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최신 주식 데이터 조회"""
        try:
            # 각 심볼별로 최신 데이터 1개씩 조회
            subquery = self.db.query(
                StockQuote.symbol,
                desc(StockQuote.created_at).label('max_created_at')
            ).group_by(StockQuote.symbol).subquery()
            
            stocks = self.db.query(StockQuote).join(
                subquery,
                (StockQuote.symbol == subquery.c.symbol) &
                (StockQuote.created_at == subquery.c.max_created_at)
            ).limit(limit).all()
            
            return [
                {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "currentPrice": stock.c,
                    "change": stock.d,
                    "changePercent": stock.dp,
                    "high": stock.h,
                    "low": stock.l,
                    "open": stock.o,
                    "previousClose": stock.pc,
                    "timestamp": stock.created_at.isoformat(),
                    "type": "stock"
                }
                for stock in stocks
            ]
        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            return []
            
    def get_latest_crypto_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최신 암호화폐 데이터 조회"""
        try:
            # 각 심볼별로 최신 데이터 1개씩 조회
            subquery = self.db.query(
                CryptoQuote.symbol,
                desc(CryptoQuote.created_at).label('max_created_at')
            ).group_by(CryptoQuote.symbol).subquery()
            
            cryptos = self.db.query(CryptoQuote).join(
                subquery,
                (CryptoQuote.symbol == subquery.c.symbol) &
                (CryptoQuote.created_at == subquery.c.max_created_at)
            ).limit(limit).all()
            
            return [
                {
                    "id": crypto.id,
                    "symbol": crypto.symbol,
                    "fullSymbol": crypto.s,
                    "price": crypto.p,
                    "volume": crypto.v,
                    "timestamp": crypto.created_at.isoformat(),
                    "socketTimestamp": crypto.t,
                    "type": "crypto"
                }
                for crypto in cryptos
            ]
        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            return []
            
    def get_combined_market_data(self) -> Dict[str, Any]:
        """주식과 암호화폐 데이터를 합쳐서 반환"""
        stocks = self.get_latest_stock_data()
        cryptos = self.get_latest_crypto_data()
        
        return {
            "type": "market_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "stocks": stocks,
                "cryptos": cryptos,
                "summary": {
                    "stockCount": len(stocks),
                    "cryptoCount": len(cryptos),
                    "totalAssets": len(stocks) + len(cryptos)
                }
            }
        }
