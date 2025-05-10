# import yfinance as yf

# dat = yf.Ticker("MSFT")

# print(dat.info)



import requests

url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/MSFT?modules=price"
r = requests.get(url)
print(r.status_code)
print(r.text)