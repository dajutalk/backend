from sqlalchemy.orm import Session
from stock.backend.database import SessionLocal
from stock.backend.models import StockQuote
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class StockQuoteService:
    """주식 시세 데이터베이스 서비스 클래스"""
    
    def __init__(self):
        pass
    
    def save_stock_quote(self, quote_data: Dict[str, Any]) -> bool:
        """주식 시세 데이터를 데이터베이스에 저장"""
        try:
            with SessionLocal() as db:
                # StockQuote 객체 생성
                stock_quote = StockQuote(
                    symbol=quote_data.get('symbol', ''),
                    c=float(quote_data.get('c', 0)),
                    d=float(quote_data.get('d', 0)),
                    dp=float(quote_data.get('dp', 0)),
                    h=float(quote_data.get('h', 0)),
                    l=float(quote_data.get('l', 0)),
                    o=float(quote_data.get('o', 0)),
                    pc=float(quote_data.get('pc', 0))
                )
                
                db.add(stock_quote)
                db.commit()
                db.refresh(stock_quote)
                
                logger.info(f"💾 주식 시세 저장 완료: {quote_data.get('symbol')} (ID: {stock_quote.id})")
                return True
                
        except Exception as e:
            logger.error(f"❌ 주식 시세 저장 실패: {quote_data.get('symbol')}, 오류: {e}")
            return False
    
    def get_latest_quote(self, symbol: str) -> Optional[StockQuote]:
        """최신 주식 시세 조회"""
        try:
            with SessionLocal() as db:
                quote = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .order_by(StockQuote.created_at.desc())\
                    .first()
                return quote
                
        except Exception as e:
            logger.error(f"❌ 최신 시세 조회 실패: {symbol}, 오류: {e}")
            return None
    
    def get_quote_history(self, symbol: str, hours: int = 24) -> List[StockQuote]:
        """주식 시세 이력 조회"""
        try:
            with SessionLocal() as db:
                since = datetime.utcnow() - timedelta(hours=hours)
                quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .filter(StockQuote.created_at >= since)\
                    .order_by(StockQuote.created_at.desc())\
                    .all()
                return quotes
                
        except Exception as e:
            logger.error(f"❌ 시세 이력 조회 실패: {symbol}, 오류: {e}")
            return []
    
    def get_all_symbols(self) -> List[str]:
        """데이터베이스에 저장된 모든 심볼 조회"""
        try:
            with SessionLocal() as db:
                symbols = db.query(StockQuote.symbol)\
                    .distinct()\
                    .all()
                return [symbol[0] for symbol in symbols]
                
        except Exception as e:
            logger.error(f"❌ 심볼 목록 조회 실패: {e}")
            return []
    
    def get_quote_statistics(self, symbol: str) -> Dict[str, Any]:
        """특정 심볼의 통계 정보 조회"""
        try:
            with SessionLocal() as db:
                quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .order_by(StockQuote.created_at.desc())\
                    .limit(100)\
                    .all()
                
                if not quotes:
                    return {}
                
                # 통계 계산
                prices = [q.c for q in quotes]
                return {
                    "symbol": symbol,
                    "total_records": len(quotes),
                    "latest_price": quotes[0].c,
                    "highest_price": max(prices),
                    "lowest_price": min(prices),
                    "average_price": sum(prices) / len(prices),
                    "first_record": quotes[-1].created_at.isoformat(),
                    "latest_record": quotes[0].created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ 통계 조회 실패: {symbol}, 오류: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 7) -> int:
        """오래된 데이터 정리"""
        try:
            with SessionLocal() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # 오래된 데이터 조회
                old_quotes = db.query(StockQuote)\
                    .filter(StockQuote.created_at < cutoff_date)\
                    .all()
                
                count = len(old_quotes)
                
                # 데이터 삭제
                db.query(StockQuote)\
                    .filter(StockQuote.created_at < cutoff_date)\
                    .delete()
                
                db.commit()
                logger.info(f"🧹 {count}개의 오래된 시세 데이터 정리 완료")
                return count
                
        except Exception as e:
            logger.error(f"❌ 데이터 정리 실패: {e}")
            return 0

# 전역 서비스 인스턴스
quote_service = StockQuoteService()
