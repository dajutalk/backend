# 실시간 주식 데이터 웹소켓 연결 가이드

## 개요
이 문서는 실시간 주식 데이터를 웹소켓을 통해 받아오는 방법을 설명합니다. 프론트엔드에서 웹소켓 연결을 통해 실시간으로 주식 가격과 거래량 정보를 받을 수 있습니다.

## 웹소켓 연결 방법

### 기본 URL

**주식용:**
```
ws://[서버주소]/ws/stocks?symbol={symbol}
```

**암호화폐용:**
```
ws://[서버주소]/ws/crypto?symbol={symbol}
```

**통합 시장 데이터용:**
```
ws://[서버주소]/ws/main
```

로컬 개발 환경에서는 다음과 같이 연결합니다:
```
ws://localhost:8000/ws/stocks?symbol=AAPL
ws://localhost:8000/ws/crypto?symbol=BTC
ws://localhost:8000/ws/main
```

### 연결 파라미터
웹소켓 연결 시 다음 쿼리 파라미터를 사용할 수 있습니다:

**주식 (`/ws/stocks`)**:
- `symbol`: 조회할 주식 심볼 (필수)
  - 예: AAPL, MSFT, GOOGL
  - 기본값: 없음 (필수 파라미터)

**암호화폐 (`/ws/crypto`)**:
- `symbol`: 조회할 암호화폐 심볼 (필수)
  - 예: BTC, ETH, DOGE
  - 기본값: 없음 (필수 파라미터)

예시:
```
ws://localhost:8000/ws/stocks?symbol=AAPL
ws://localhost:8000/ws/crypto?symbol=BTC
```

## 수신 데이터 형식

웹소켓으로 수신되는 데이터는 다음과 같은 JSON 형식입니다:

**주식 데이터:**
```json
{
  "type": "stock_update",
  "data": [
    {
      "s": "AAPL",           // 심볼
      "p": "150.25",         // 가격
      "v": "1000000",        // 거래량
      "t": 1632145789000     // 타임스탬프
    }
  ]
}
```

**암호화폐 데이터:**
```json
{
  "type": "crypto_update",
  "data": [
    {
      "s": "BINANCE:BTCUSDT", // 전체 심볼
      "p": "50000.25",        // 가격
      "v": "0.1234",          // 거래량
      "t": 1632145789000      // 타임스탬프
    }
  ]
}
```

### 데이터 필드 설명
- `s`: 주식/암호화폐 심볼
- `p`: 현재 가격 (문자열)
- `v`: 거래량 (문자열)
- `t`: 타임스탬프 (밀리초 단위)

## 프론트엔드 사용 예시

### JavaScript 예시 코드

```javascript
// 주식용 웹소켓 연결
function connectToStock(symbol) {
  const socket = new WebSocket(`ws://localhost:8000/ws/stocks?symbol=${symbol}`);
  
  socket.onopen = (event) => {
    console.log(`주식 웹소켓 연결 성공: ${symbol}`);
  };
  
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'stock_update' && data.data.length > 0) {
        const stockData = data.data[0];
        console.log(`${stockData.s}: $${stockData.p}`);
        // UI 업데이트 로직
      }
    } catch (error) {
      console.error("메시지 처리 중 오류:", error);
    }
  };
  
  return socket;
}

// 암호화폐용 웹소켓 연결
function connectToCrypto(symbol) {
  const socket = new WebSocket(`ws://localhost:8000/ws/crypto?symbol=${symbol}`);
  
  socket.onopen = (event) => {
    console.log(`암호화폐 웹소켓 연결 성공: ${symbol}`);
  };
  
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'crypto_update' && data.data.length > 0) {
        const cryptoData = data.data[0];
        console.log(`${cryptoData.s}: $${cryptoData.p}`);
        // UI 업데이트 로직
      }
    } catch (error) {
      console.error("메시지 처리 중 오류:", error);
    }
  };
  
  return socket;
}

// 사용 예시
const appleSocket = connectToStock('AAPL');
const bitcoinSocket = connectToCrypto('BTC');
```

### React Hooks 사용 예시

```jsx
import { useState, useEffect } from 'react';

function MarketDataComponent({ symbol, type = 'stock' }) {
  const [marketData, setMarketData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // 타입에 따라 적절한 웹소켓 URL 생성
    const wsUrl = type === 'crypto' 
      ? `ws://localhost:8000/ws/crypto?symbol=${symbol}`
      : `ws://localhost:8000/ws/stocks?symbol=${symbol}`;
      
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setIsConnected(true);
      console.log(`${type} 웹소켓 연결됨: ${symbol}`);
    };

    socket.onmessage = (event) => {
      try {
        const response = JSON.parse(event.data);
        const expectedType = type === 'crypto' ? 'crypto_update' : 'stock_update';
        
        if (response.type === expectedType && response.data.length > 0) {
          setMarketData(response.data[0]);
        }
      } catch (error) {
        console.error("데이터 파싱 오류:", error);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      console.log(`${type} 웹소켓 연결 종료: ${symbol}`);
    };

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [symbol, type]);

  return (
    <div>
      <h2>{type === 'crypto' ? '암호화폐' : '주식'} 실시간 가격</h2>
      <p>연결 상태: {isConnected ? '연결됨' : '연결되지 않음'}</p>
      <p>심볼: {symbol}</p>
      {marketData && (
        <div>
          <p>가격: ${marketData.p}</p>
          <p>거래량: {marketData.v}</p>
          <p>업데이트 시간: {new Date(marketData.t).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
}

export default MarketDataComponent;
```

## 엔드포인트별 특징

### `/ws/stocks` - 주식 전용
- 업데이트 주기: 10초
- 지원 심볼: AAPL, MSFT, GOOGL 등 미국 주식
- 데이터 소스: Finnhub API (캐시 사용)

### `/ws/crypto` - 암호화폐 전용  
- 업데이트 주기: 5초
- 지원 심볼: BTC, ETH, DOGE 등 상위 10개 암호화폐
- 데이터 소스: Binance (Finnhub API 경유)

### `/ws/main` - 통합 시장 데이터
- 업데이트 주기: 10초 
- 모든 시장 데이터 통합 제공
- 클라이언트별 개별 요청 가능

## 자주 발생하는 문제와 해결 방법

### 1. 연결은 되지만 데이터가 오지 않는 경우

**원인**: 백그라운드 데이터 수집기가 아직 시작되지 않았을 수 있습니다.

**해결방법**: 
```javascript
// 연결 후 약간의 지연을 두고 확인
socket.onopen = () => {
  setTimeout(() => {
    if (!receivedData) {
      console.log("데이터 수신 대기 중...");
    }
  }, 15000); // 15초 후 확인
};
```

### 2. 특정 심볼의 데이터만 오지 않는 경우

**원인**: 해당 심볼이 지원 목록에 없거나 API 제한에 걸렸을 수 있습니다.

**해결방법**: 서버 로그 확인 및 지원 심볼 목록 조회
```bash
curl http://localhost:8000/api/stocks/symbols
curl http://localhost:8000/api/stocks/crypto/symbols
```

## 참고 사항
- 모든 가격 데이터는 문자열로 전송되므로 필요시 숫자로 변환하세요
- 암호화폐 데이터는 실시간성이 높아 업데이트가 더 빈번합니다
- 서버 재시작 시 모든 WebSocket 연결이 끊어지므로 자동 재연결 로직을 구현하세요
