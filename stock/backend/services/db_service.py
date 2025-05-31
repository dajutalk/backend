from sqlmodel import Session, select
from stock.backend.database import get_db_session, engine
from stock.backend.models import StockQuote, StockPrice, StockCache, StockSymbol, User
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import time
import bcrypt

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
    
    def create_user(self, email: Optional[str], password: Optional[str], nickname: str, provider: str) -> Optional[User]:
        """새 사용자 생성"""
        try:
            with Session(engine) as session:
                # 비밀번호 해싱 (일반 로그인인 경우)
                hashed_password = None
                if password and provider == "local":
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                # 사용자 객체 생성
                user = User(
                    email=email,
                    password=hashed_password,
                    nickname=nickname,
                    provider=provider,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(user)
                session.commit()
                session.refresh(user)
                
                logger.info(f"✅ 새 사용자 생성: {email} ({provider})")
                return user
                
        except Exception as e:
            logger.error(f"❌ 사용자 생성 실패: {email}, 오류: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        try:
            with Session(engine) as session:
                user = session.exec(
                    select(User).where(User.email == email).where(User.is_active == True)
                ).first()
                return user
                
        except Exception as e:
            logger.error(f"❌ 사용자 조회 실패: {email}, 오류: {e}")
            return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"❌ 비밀번호 검증 실패: {e}")
            return False
    
    def get_latest_quote(self, symbol: str) -> Optional[StockQuote]:
        """최신 주식 시세 조회"""
        try:
            with Session(engine) as session:
                quote = session.exec(
                    select(StockQuote)
                    .where(StockQuote.symbol == symbol)
                    .order_by(StockQuote.timestamp.desc())
                ).first()
                return quote
                
        except Exception as e:
            logger.error(f"❌ 최신 시세 조회 실패: {symbol}, 오류: {e}")
            return None
    
    def get_price_history(self, symbol: str, hours: int = 24) -> List[StockQuote]:
        """주식 시세 이력 조회"""
        try:
            with Session(engine) as session:
                since = datetime.utcnow() - timedelta(hours=hours)
                quotes = session.exec(
                    select(StockQuote)
                    .where(StockQuote.symbol == symbol)
                    .where(StockQuote.timestamp >= since)
                    .order_by(StockQuote.timestamp.desc())
                ).all()
                return list(quotes)
                
        except Exception as e:
            logger.error(f"❌ 시세 이력 조회 실패: {symbol}, 오류: {e}")
            return []
    
    def get_cache_statistics(self) -> List[StockCache]:
        """캐시 통계 조회"""
        try:
            with Session(engine) as session:
                cache_stats = session.exec(
                    select(StockCache).order_by(StockCache.last_update.desc())
                ).all()
                return list(cache_stats)
                
        except Exception as e:
            logger.error(f"❌ 캐시 통계 조회 실패: {e}")
            return []

# 전역 데이터베이스 서비스 인스턴스
db_service = StockDatabaseService()
