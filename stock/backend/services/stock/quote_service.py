from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from ...database.models import StockQuote
from ...database.connection import SessionLocal
from ...core.exceptions import ServiceException
import logging

logger = logging.getLogger(__name__)

class QuoteService:
    """주식 시세 서비스"""
    
    def save_stock_quote(self, quote_data: Dict[str, Any]) -> bool:
        """주식 시세를 DB에 저장"""
        try:
            db = SessionLocal()
            try:
                stock_quote = StockQuote(
                    symbol=quote_data["symbol"],
                    c=quote_data["c"],
                    d=quote_data.get("d"),
                    dp=quote_data.get("dp"),
                    h=quote_data.get("h"),
                    l=quote_data.get("l"),
                    o=quote_data.get("o"),
                    pc=quote_data.get("pc")
                )
                
                db.add(stock_quote)
                db.commit()
                db.refresh(stock_quote)
                
                logger.info(f"✅ 주식 시세 저장 성공: {quote_data['symbol']}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 주식 시세 저장 실패: {e}")
            raise ServiceException(f"주식 시세 저장 실패: {e}", "QuoteService")
    
    def get_quote_history(self, symbol: str, hours: int = 24) -> List[StockQuote]:
        """주식 시세 이력 조회"""
        try:
            db = SessionLocal()
            try:
                since = datetime.utcnow() - timedelta(hours=hours)
                
                quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .filter(StockQuote.created_at >= since)\
                    .order_by(desc(StockQuote.created_at))\
                    .all()
                
                return quotes
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 주식 이력 조회 실패: {e}")
            raise ServiceException(f"주식 이력 조회 실패: {e}", "QuoteService")
    
    def get_latest_quotes(self, symbol: str, limit: int = 30) -> List[StockQuote]:
        """최근 주식 시세 조회"""
        try:
            db = SessionLocal()
            try:
                quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .order_by(desc(StockQuote.created_at))\
                    .limit(limit)\
                    .all()
                
                return list(reversed(quotes))  # 오래된 순으로 정렬
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 최근 주식 시세 조회 실패: {e}")
            raise ServiceException(f"최근 주식 시세 조회 실패: {e}", "QuoteService")
    
    def get_quote_statistics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """주식 통계 정보 조회"""
        try:
            db = SessionLocal()
            try:
                stats = db.query(
                    func.count(StockQuote.id).label('total_records'),
                    func.max(StockQuote.created_at).label('latest_update'),
                    func.avg(StockQuote.c).label('avg_price'),
                    func.min(StockQuote.c).label('min_price'),
                    func.max(StockQuote.c).label('max_price')
                ).filter(StockQuote.symbol == symbol).first()
                
                if stats and stats.total_records > 0:
                    return {
                        "symbol": symbol,
                        "total_records": stats.total_records,
                        "latest_update": stats.latest_update.isoformat() if stats.latest_update else None,
                        "avg_price": float(stats.avg_price) if stats.avg_price else 0,
                        "min_price": float(stats.min_price) if stats.min_price else 0,
                        "max_price": float(stats.max_price) if stats.max_price else 0
                    }
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 주식 통계 조회 실패: {e}")
            raise ServiceException(f"주식 통계 조회 실패: {e}", "QuoteService")
    
    def get_all_symbols(self) -> List[str]:
        """저장된 모든 주식 심볼 조회"""
        try:
            db = SessionLocal()
            try:
                symbols = db.query(StockQuote.symbol)\
                    .distinct()\
                    .order_by(StockQuote.symbol)\
                    .all()
                
                return [symbol[0] for symbol in symbols]
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 주식 심볼 목록 조회 실패: {e}")
            raise ServiceException(f"주식 심볼 목록 조회 실패: {e}", "QuoteService")
