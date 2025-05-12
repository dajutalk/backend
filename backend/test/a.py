
import finnhub

API_KEY = "d0fgaf9r01qsv9ehav00d0fgaf9r01qsv9ehav0g"  # 또는 os.getenv("FINNHUB_API_KEY")

finnhub_client = finnhub.Client(api_key="d0fgaf9r01qsv9ehav00d0fgaf9r01qsv9ehav0g")

print(finnhub_client.quote('AAPL'))
