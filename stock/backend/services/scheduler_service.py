import asyncio
import threading
import time
import logging
from typing import List
from stock.backend.services.stock_service import get_cached_stock_data, register_symbol
from stock.backend.services.quote_service import quote_service

logger = logging.getLogger(__name__)

# 가장 활발한 주식 목록
MOST_ACTIVE_STOCKS = [
    "NVDA", "TSLA", "PLTR", "INTC", "AAPL", "BAC", "AMZN", "AMD", "GOOG", "MSFT",
    "META", "AVGO", "NFLX", "COST", "UNH", "MSTR", "LLY", "CRM", "V", "REGN",
    "APP", "WMT", "XOM", "MRVL", "ORCL", "JPM", "TXN", "ZS", "NOW", "MA",
    "IBM", "UBER", "JNJ", "AMAT", "HOOD", "ADI", "GE", "MU", "PANW", "INTU",
    "ABBV", "PG", "DELL", "CRWD", "SPOT", "LIN", "KO", "TMUS", "QCOM", "F"
]

class StockDataScheduler:
    """주식 데이터 자동 수집 스케줄러"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.processed_count = 0
        self.error_count = 0
        
    def start_scheduler(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"🚀 주식 데이터 스케줄러 시작 - {len(MOST_ACTIVE_STOCKS)}개 심볼 모니터링")
        logger.info(f"📋 모니터링 심볼: {', '.join(MOST_ACTIVE_STOCKS[:10])}... (총 {len(MOST_ACTIVE_STOCKS)}개)")
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info(f"⏹️ 주식 데이터 스케줄러 중지됨 (처리: {self.processed_count}, 오류: {self.error_count})")
    
    def _run_scheduler(self):
        """스케줄러 메인 루프"""
        logger.info("⏰ 스케줄러 루프 시작 - 1분마다 데이터 수집")
        
        while self.is_running:
            try:
                start_time = time.time()
                success_count = 0
                
                logger.info(f"📊 데이터 수집 시작 - {len(MOST_ACTIVE_STOCKS)}개 심볼 처리")
                
                for i, symbol in enumerate(MOST_ACTIVE_STOCKS):
                    if not self.is_running:  # 중지 신호 확인
                        break
                    
                    try:
                        # 심볼 등록 및 데이터 가져오기
                        register_symbol(symbol)
                        data = get_cached_stock_data(symbol)
                        
                        if data:
                            # 데이터베이스에 저장
                            response_data = {
                                "symbol": symbol,
                                "c": data.get('c', 0),
                                "d": data.get('d', 0),
                                "dp": data.get('dp', 0),
                                "h": data.get('h', 0),
                                "l": data.get('l', 0),
                                "o": data.get('o', 0),
                                "pc": data.get('pc', 0)
                            }
                            
                            if quote_service.save_stock_quote(response_data):
                                success_count += 1
                                logger.debug(f"✅ {symbol} 데이터 저장 완료 ({i+1}/{len(MOST_ACTIVE_STOCKS)})")
                            else:
                                self.error_count += 1
                                logger.error(f"❌ {symbol} 데이터 저장 실패")
                        else:
                            self.error_count += 1
                            logger.error(f"❌ {symbol} 데이터 가져오기 실패")
                        
                        # API 요청 제한을 위한 지연 (1.2초 간격)
                        time.sleep(1.2)
                        
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"❌ {symbol} 처리 중 오류: {e}")
                
                # 처리 완료 통계
                elapsed_time = time.time() - start_time
                self.processed_count += success_count
                
                logger.info(
                    f"📈 수집 완료: {success_count}/{len(MOST_ACTIVE_STOCKS)} 성공 "
                    f"(소요시간: {elapsed_time:.1f}초, 누적: {self.processed_count}개)"
                )
                
                # 다음 실행까지 대기 (1분 - 처리 시간)
                remaining_time = 60 - elapsed_time
                if remaining_time > 0:
                    logger.info(f"⏱️ 다음 수집까지 {remaining_time:.1f}초 대기...")
                    time.sleep(remaining_time)
                else:
                    logger.warning(f"⚠️ 처리 시간이 1분을 초과했습니다 ({elapsed_time:.1f}초)")
                
            except Exception as e:
                logger.error(f"❌ 스케줄러 루프 오류: {e}")
                time.sleep(10)  # 오류 시 10초 대기 후 재시도
        
        logger.info("🛑 스케줄러 루프 종료")
    
    def get_status(self):
        """스케줄러 상태 반환"""
        return {
            "is_running": self.is_running,
            "monitored_symbols": len(MOST_ACTIVE_STOCKS),
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "success_rate": (self.processed_count / (self.processed_count + self.error_count) * 100) if (self.processed_count + self.error_count) > 0 else 0
        }

# 전역 스케줄러 인스턴스
stock_scheduler = StockDataScheduler()
