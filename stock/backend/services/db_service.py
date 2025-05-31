from sqlmodel import Session, select
from stock.backend.database import get_db_session, engine
from stock.backend.models import StockQuote, StockPrice, StockCache, StockSymbol
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class StockDatabaseService:
    """주식 데이터베이스 서비스 클래스"""
    
    def __init__(self):
        self.session_factory = get_db_session
    
    def save_stock_quote(self, quote_data: Dict[str, Any], symbol: str) -> bool:
        """주식 시세 데이터를 데이터베이스에 저장"""
        try:
            with Session(engine) as session:
                # StockQuote 객체 생성
                stock_quote = StockQuote(
                    symbol=symbol,
                    current_price=float(quote_data.get('c', 0)),
                    change=float(quote_data.get('d', 0)),
                    change_percent=float(quote_data.get('dp', 0)),
                    high_price=float(quote_data.get('h', 0)),
                    low_price=float(quote_data.get('l', 0)),
                    open_price=float(quote_data.get('o', 0)),
                    previous_close=float(quote_data.get('pc', 0)),
                    volume=float(quote_data.get('v', 0)),
                    market_timestamp=quote_data.get('t'),
                    data_source=quote_data.get('data_source', 'api'),
                    cache_age=float(quote_data.get('cache_age', 0))
                )
                
                session.add(stock_quote)
                session.commit()
                session.refresh(stock_quote)
                
                logger.info(f"💾 주식 시세 저장 완료: {symbol} (ID: {stock_quote.id})")
                return True
                
        except Exception as e:
            logger.error(f"❌ 주식 시세 저장 실패: {symbol}, 오류: {e}")
            return False
    
    def save_stock_price(self, price_data: Dict[str, Any]) -> bool:
        """실시간 주식 가격 데이터 저장 (웹소켓용)"""
        try:
            with Session(engine) as session:
                stock_price = StockPrice(
                    symbol=price_data.get('s', ''),
                    price=float(price_data.get('p', 0)),
                    volume=float(price_data.get('v', 0)),
                    market_timestamp=int(price_data.get('t', 0))
                )
                
                session.add(stock_price)
                session.commit()
                
                logger.debug(f"📊 실시간 가격 저장: {stock_price.symbol} = ${stock_price.price}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 실시간 가격 저장 실패: {e}")
            return False
    
    def update_cache_info(self, symbol: str, is_api_call: bool = True, response_time: float = 0.0) -> None:
        """캐시 정보 업데이트"""
        try:
            with Session(engine) as session:
                # 기존 캐시 정보 조회
                cache_info = session.exec(
                    select(StockCache).where(StockCache.symbol == symbol)
                ).first()
                
                current_time = datetime.utcnow()
                
                if cache_info:
                    # 기존 정보 업데이트
                    cache_info.last_update = current_time
                    cache_info.total_requests += 1
                    
                    if is_api_call:
                        cache_info.last_api_call = current_time
                        cache_info.api_call_count += 1
                    else:
                        cache_info.cache_hit_count += 1
                    
                    # 평균 응답 시간 계산
                    if response_time > 0:
                        total_time = cache_info.avg_response_time * (cache_info.total_requests - 1)
                        cache_info.avg_response_time = (total_time + response_time) / cache_info.total_requests
                    
                else:
                    # 새 캐시 정보 생성
                    cache_info = StockCache(
                        symbol=symbol,
                        last_api_call=current_time if is_api_call else current_time,
                        last_update=current_time,
                        api_call_count=1 if is_api_call else 0,
                        cache_hit_count=0 if is_api_call else 1,
                        total_requests=1,
                        avg_response_time=response_time
                    )
                    session.add(cache_info)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"❌ 캐시 정보 업데이트 실패: {symbol}, 오류: {e}")

# 전역 데이터베이스 서비스 인스턴스
db_service = StockDatabaseService()
