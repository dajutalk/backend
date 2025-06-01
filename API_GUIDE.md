# 통합 Stock & Auth API 사용 가이드

## 🔗 Base URL
```
authentication


POST
/auth/login
Login Or Signup


GET
/auth/kakao/callback
Kakao Login Callback


POST
/auth/kakao/callback
Kakao Login


GET
/auth/me
Read Me


POST
/auth/logout
Logout


GET
/auth/kakao/redirect
Redirect To Kakao


GET
/auth/status
Auth Status

websocket


GET
/ws/stocks/status
Stocks Websocket Status


GET
/ws/crypto/status
Crypto Websocket Status

Stocks


GET
/api/stocks/quote
Get Stock Quote Endpoint


GET
/api/stocks/history/{symbol}
Get Stock History


GET
/api/stocks/statistics/{symbol}
Get Stock Statistics


GET
/api/stocks/symbols
Get Stored Symbols


GET
/api/stocks/scheduler/status
Get Scheduler Status


POST
/api/stocks/scheduler/start
Start Scheduler


POST
/api/stocks/scheduler/stop
Stop Scheduler


GET
/api/stocks/scheduler/symbols
Get Monitored Symbols


GET
/api/stocks/collector/status
Get Collector Status


POST
/api/stocks/collector/start
Start Collector


POST
/api/stocks/collector/stop
Stop Collector


GET
/api/stocks/collector/symbols
Get Collector Symbols


GET
/api/stocks/crypto/{symbol}
Get Crypto Quote


GET
/api/stocks/crypto/history/{symbol}
Get Crypto History


GET
/api/stocks/crypto/statistics/{symbol}
Get Crypto Statistics


GET
/api/stocks/crypto/symbols
Get Stored Crypto Symbols

Chat API


GET
/api/chat/rooms
Get All Chat Rooms


GET
/api/chat/rooms/{symbol}
Get Chat Room Info


GET
/api/chat/history/{symbol}
Get Chat History

default


GET
/
Root


GET
/health
Health Check
```




