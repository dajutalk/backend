from .quote_service import QuoteService
from .finnhub_service import FinnhubService
from .auto_collector import AutoCollector

quote_service = QuoteService()
finnhub_service = FinnhubService()
auto_collector = AutoCollector()

__all__ = ["quote_service", "finnhub_service", "auto_collector"]
