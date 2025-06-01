import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 상위 10개 암호화폐
TOP_10_CRYPTOS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
    "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "SHIBUSDT"
]

class CryptoService:
    """암호화폐 서비스"""
    
    def __init__(self):
        self.cache = {}
    
    def get_cached_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """캐시된 암호화폐 데이터 조회"""
        return self.cache.get(symbol, {})
    
    def update_cache(self, symbol: str, data: Dict[str, Any]):
        """캐시 업데이트"""
        self.cache[symbol] = data
    
    def get_supported_symbols(self) -> List[str]:
        """지원되는 암호화폐 심볼 목록"""
        return TOP_10_CRYPTOS
    
    def get_statistics(self) -> Dict[str, Any]:
        """암호화폐 통계 정보"""
        return {
            "crypto_symbols": TOP_10_CRYPTOS,
            "cached_count": len(self.cache),
            "thread_running": False  # WebSocket 서비스에서 관리
        }
