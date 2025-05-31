from sqlalchemy.orm import Session
from stock.backend.database import SessionLocal
from stock.backend.models import CryptoQuote
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CryptoQuoteService:
    """암호화폐 시세 데이터베이스 서비스 클래스"""
    
    def __init__(self):
        pass
    
    def save_crypto_quote(self, crypto_data: Dict[str, Any]) -> bool:
        """암호화폐 시세 데이터를 데이터베이스에 저장"""
        try:
            # 🔍 입력 데이터 검증 및 로깅
            logger.info(f"💾 암호화폐 저장 시도: {crypto_data}")
            
            # 필수 필드 검증
            symbol = crypto_data.get('symbol', '')
            s = crypto_data.get('s', '')
            p = crypto_data.get('p', '0')
            v = crypto_data.get('v', '0')
            t = crypto_data.get('t', 0)
            
            if not symbol:
                logger.error(f"❌ 필수 필드 누락: symbol이 비어있음")
                return False
            
            if not s:
                logger.error(f"❌ 필수 필드 누락: s(전체 심볼)이 비어있음")
                return False
            
            if not p or p == '0':
                logger.error(f"❌ 유효하지 않은 가격: p={p}")
                return False
            
            if not t or t == 0:
                logger.error(f"❌ 유효하지 않은 타임스탬프: t={t}")
                return False
            
            logger.info(f"✅ 데이터 검증 통과: {symbol} - 가격: {p}, 타임스탬프: {t}")
            
            with SessionLocal() as db:
                # CryptoQuote 객체 생성
                crypto_quote = CryptoQuote(
                    symbol=symbol,                            # BTC, ETH 등
                    s=s,                                      # BINANCE:BTCUSDT
                    p=str(p),                                 # 현재가 (문자열)
                    v=str(v),                                 # 거래량 (문자열)
                    t=int(t)                                  # 타임스탬프 (밀리초)
                )
                
                logger.info(f"🔄 CryptoQuote 객체 생성 완료: {symbol}")
                
                db.add(crypto_quote)
                logger.info(f"🔄 세션에 추가 완료: {symbol}")
                
                db.commit()
                logger.info(f"🔄 커밋 완료: {symbol}")
                
                db.refresh(crypto_quote)
                logger.info(f"🔄 새로고침 완료: {symbol}, ID: {crypto_quote.id}")
                
                logger.info(f"💾 암호화폐 시세 저장 완료: {symbol} (ID: {crypto_quote.id})")
                return True
                
        except Exception as e:
            logger.error(f"❌ 암호화폐 시세 저장 실패: {crypto_data.get('symbol', 'UNKNOWN')}")
            logger.error(f"❌ 상세 오류: {str(e)}")
            logger.error(f"❌ 오류 타입: {type(e).__name__}")
            
            # 스택 트레이스 출력
            import traceback
            logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
            
            return False
    
    def get_latest_crypto_quote(self, symbol: str) -> Optional[CryptoQuote]:
        """최신 암호화폐 시세 조회"""
        try:
            with SessionLocal() as db:
                quote = db.query(CryptoQuote)\
                    .filter(CryptoQuote.symbol == symbol)\
                    .order_by(CryptoQuote.created_at.desc())\
                    .first()
                return quote
                
        except Exception as e:
            logger.error(f"❌ 최신 암호화폐 시세 조회 실패: {symbol}, 오류: {e}")
            return None
    
    def get_crypto_quote_history(self, symbol: str, hours: int = 24) -> List[CryptoQuote]:
        """암호화폐 시세 이력 조회"""
        try:
            with SessionLocal() as db:
                since = datetime.utcnow() - timedelta(hours=hours)
                quotes = db.query(CryptoQuote)\
                    .filter(CryptoQuote.symbol == symbol)\
                    .filter(CryptoQuote.created_at >= since)\
                    .order_by(CryptoQuote.created_at.desc())\
                    .all()
                return quotes
                
        except Exception as e:
            logger.error(f"❌ 암호화폐 시세 이력 조회 실패: {symbol}, 오류: {e}")
            return []
    
    def get_all_crypto_symbols(self) -> List[str]:
        """데이터베이스에 저장된 모든 암호화폐 심볼 조회"""
        try:
            with SessionLocal() as db:
                symbols = db.query(CryptoQuote.symbol)\
                    .distinct()\
                    .all()
                return [symbol[0] for symbol in symbols]
                
        except Exception as e:
            logger.error(f"❌ 암호화폐 심볼 목록 조회 실패: {e}")
            return []
    
    def get_crypto_quote_statistics(self, symbol: str) -> Dict[str, Any]:
        """특정 암호화폐 심볼의 통계 정보 조회"""
        try:
            with SessionLocal() as db:
                quotes = db.query(CryptoQuote)\
                    .filter(CryptoQuote.symbol == symbol)\
                    .order_by(CryptoQuote.created_at.desc())\
                    .limit(100)\
                    .all()
                
                if not quotes:
                    return {}
                
                # 통계 계산 (문자열 가격을 float로 변환)
                prices = [float(q.p) for q in quotes if q.p]
                volumes = [float(q.v) for q in quotes if q.v and q.v != '0']
                
                return {
                    "symbol": symbol,
                    "total_records": len(quotes),
                    "latest_price": float(quotes[0].p) if quotes[0].p else 0,
                    "highest_price": max(prices) if prices else 0,
                    "lowest_price": min(prices) if prices else 0,
                    "average_price": sum(prices) / len(prices) if prices else 0,
                    "total_volume": sum(volumes) if volumes else 0,
                    "first_record": quotes[-1].created_at.isoformat(),
                    "latest_record": quotes[0].created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ 암호화폐 통계 조회 실패: {symbol}, 오류: {e}")
            return {}
    
    def cleanup_old_crypto_data(self, days: int = 7) -> int:
        """오래된 암호화폐 데이터 정리"""
        try:
            with SessionLocal() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # 오래된 데이터 조회
                old_quotes = db.query(CryptoQuote)\
                    .filter(CryptoQuote.created_at < cutoff_date)\
                    .all()
                
                count = len(old_quotes)
                
                # 데이터 삭제
                db.query(CryptoQuote)\
                    .filter(CryptoQuote.created_at < cutoff_date)\
                    .delete()
                
                db.commit()
                logger.info(f"🧹 {count}개의 오래된 암호화폐 시세 데이터 정리 완료")
                return count
                
        except Exception as e:
            logger.error(f"❌ 암호화폐 데이터 정리 실패: {e}")
            return 0

# 전역 서비스 인스턴스
crypto_service = CryptoQuoteService()
