import asyncio
import aiohttp
import threading
import time
import logging
from typing import List, Dict, Any
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

class StockAutoCollector:
    """주식 데이터 자동 수집기 - 자체 API 호출"""
    
    def __init__(self, host="localhost", port="8000"):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api/stocks/quote"
        self.is_running = False
        self.collector_thread = None
        self.processed_count = 0
        self.error_count = 0
        self.success_count = 0
        
    def start_collector(self):
        """자동 수집기 시작"""
        if self.is_running:
            logger.warning("자동 수집기가 이미 실행 중입니다")
            return
        
        self.is_running = True
        self.collector_thread = threading.Thread(target=self._run_collector, daemon=True)
        self.collector_thread.start()
    
        logger.info(f" 주식 데이터 자동 수집기 시작")
        logger.info(f" API 엔드포인트: {self.base_url}")
        logger.info(f" 모니터링 심볼: {len(MOST_ACTIVE_STOCKS)}개")
    
    def stop_collector(self):
        """자동 수집기 중지"""
        self.is_running = False
        if self.collector_thread and self.collector_thread.is_alive():
            self.collector_thread.join(timeout=5)
        
        logger.info(f" 자동 수집기 중지됨 (성공: {self.success_count}, 오류: {self.error_count})")
    
    def _run_collector(self):
        """수집기 메인 루프"""
        logger.info(" 자동 수집기 루프 시작 - 1분마다 데이터 수집")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # asyncio 이벤트 루프 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 비동기 수집 실행
                loop.run_until_complete(self._collect_all_stocks())
                loop.close()
                
                # 처리 완료 통계
                elapsed_time = time.time() - start_time
                
                logger.info(
                    f" 수집 라운드 완료: 성공 {self.success_count}, 오류 {self.error_count} "
                    f"(소요시간: {elapsed_time:.1f}초)"
                )
                
                # 다음 실행까지 대기 (1분 - 처리 시간)
                remaining_time = 60
                if remaining_time > 0:
                    logger.info(f" 다음 수집까지 {remaining_time:.1f}초 대기...")
                    time.sleep(remaining_time)
                else:
                    logger.warning(f"⚠️ 처리 시간이 1분을 초과했습니다 ({elapsed_time:.1f}초)")
                
            except Exception as e:
                logger.error(f" 수집기 루프 오류: {e}")
                time.sleep(10)  # 오류 시 10초 대기 후 재시도
        
        logger.info(" 자동 수집기 루프 종료")
    
    async def _collect_all_stocks(self):
        """모든 주식 데이터 비동기 수집"""
        logger.info(f" 데이터 수집 시작 - {len(MOST_ACTIVE_STOCKS)}개 심볼 처리")
        
        # 🔍 중복 저장 원인 분석:
        # 1. API 엔드포인트 중복 호출 - /api/stocks/quote에서 이미 DB 저장
        # 2. 자동 수집기에서 다시 한 번 더 저장
        # 3. 결과: 같은 데이터가 두 번 저장됨
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            tasks = []
            for symbol in MOST_ACTIVE_STOCKS:
                if not self.is_running:
                    break
                task = self._collect_single_stock(session, symbol)
                tasks.append(task)
            
            # 모든 요청을 병렬로 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            round_success = 0
            round_errors = 0
            
            for i, result in enumerate(results):
                symbol = MOST_ACTIVE_STOCKS[i] if i < len(MOST_ACTIVE_STOCKS) else "UNKNOWN"
                
                if isinstance(result, Exception):
                    round_errors += 1
                    logger.error(f" {symbol} 수집 실패: {result}")
                elif result:
                    round_success += 1
                    logger.debug(f" {symbol} 수집 성공")
                else:
                    round_errors += 1
                    logger.error(f" {symbol} 수집 실패: 알 수 없는 오류")
            
            self.success_count += round_success
            self.error_count += round_errors
            
            logger.info(f" 이번 라운드: {round_success}/{len(MOST_ACTIVE_STOCKS)} 성공")
    
    async def _collect_single_stock(self, session: aiohttp.ClientSession, symbol: str) -> bool:
        """단일 주식 데이터 수집 - save_to_db=false로 중복 방지"""
        try:
            #  save_to_db=false 파라미터 추가로 중복 저장 방지
            url = f"{self.base_url}?symbol={symbol}&save_to_db=false"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    #  여기서 직접 DB 저장 (한 번만)
                    quote_data = {
                        "symbol": symbol,
                        "c": float(data.get('c', 0)),
                        "d": float(data.get('d', 0)),
                        "dp": float(data.get('dp', 0)),
                        "h": float(data.get('h', 0)),
                        "l": float(data.get('l', 0)),
                        "o": float(data.get('o', 0)),
                        "pc": float(data.get('pc', 0))
                    }
                    
                    if quote_service.save_stock_quote(quote_data):
                        logger.debug(f" {symbol} 자동수집 저장 완료")
                        return True
                    else:
                        logger.error(f" {symbol} 자동수집 저장 실패")
                        return False
                else:
                    logger.error(f" {symbol} API 호출 실패: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f" {symbol} 수집 중 오류: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """수집기 상태 반환"""
        total_processed = self.success_count + self.error_count
        success_rate = (self.success_count / total_processed * 100) if total_processed > 0 else 0
        
        return {
            "is_running": self.is_running,
            "api_endpoint": self.base_url,
            "monitored_symbols": len(MOST_ACTIVE_STOCKS),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "total_processed": total_processed,
            "success_rate": round(success_rate, 2)
        }

# 전역 수집기 인스턴스
auto_collector = StockAutoCollector()
