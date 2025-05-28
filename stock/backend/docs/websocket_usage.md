# 실시간 주식 데이터 웹소켓 연결 가이드

## 개요
이 문서는 실시간 주식 데이터를 웹소켓을 통해 받아오는 방법을 설명합니다. 프론트엔드에서 웹소켓 연결을 통해 실시간으로 주식 가격과 거래량 정보를 받을 수 있습니다.

## 웹소켓 연결 방법

### 기본 URL
```
ws://[서버주소]/ws/stocks
```

로컬 개발 환경에서는 다음과 같이 연결합니다:
```
ws://localhost:8000/ws/stocks
```

### 연결 파라미터
웹소켓 연결 시 다음 쿼리 파라미터를 사용할 수 있습니다:

- `symbol`: 조회할 주식 심볼 (필수)
  - 예: BINANCE:BTCUSDT, NASDAQ:AAPL, KRX:005930(삼성전자)
  - 기본값: BINANCE:BTCUSDT

예시:
```
ws://localhost:8000/ws/stocks?symbol=BINANCE:BTCUSDT
```

## 수신 데이터 형식

웹소켓으로 수신되는 데이터는 다음과 같은 JSON 형식입니다:

```json
{
  "type": "stock_update",
  "data": [
    {
      "s": "BINANCE:BTCUSDT",  // 심볼
      "p": "50000.25",         // 가격
      "v": "0.1234",           // 거래량
      "t": 1632145789000       // 타임스탬프
    }
  ]
}
```

### 데이터 필드 설명
- `s`: 주식/암호화폐 심볼
- `p`: 현재 가격
- `v`: 거래량
- `t`: 타임스탬프 (밀리초 단위)

## 프론트엔드 사용 예시

### JavaScript 예시 코드

```javascript
// 웹소켓 연결 생성
const symbol = "BINANCE:BTCUSDT";
const socket = new WebSocket(`ws://localhost:8000/ws/stocks?symbol=${symbol}`);

// 연결 이벤트
socket.onopen = (event) => {
  console.log("웹소켓 연결 성공!");
};

// 메시지 수신 이벤트
socket.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    if (data.data && data.data.length > 0) {
      data.data.forEach(item => {
        console.log(`심볼: ${item.s}, 가격: ${item.p}, 거래량: ${item.v}`);
        // 여기에 UI 업데이트 로직 추가
      });
    }
  } catch (error) {
    console.error("메시지 처리 중 오류:", error);
  }
};

// 오류 이벤트
socket.onerror = (error) => {
  console.error("웹소켓 오류:", error);
};

// 연결 종료 이벤트
socket.onclose = (event) => {
  console.log(`연결 종료: ${event.code} - ${event.reason}`);
};

// 연결 종료
// 필요할 때 실행: socket.close();
```

### React Hooks 사용 예시

```jsx
import { useState, useEffect } from 'react';

function StockPriceComponent({ symbol = "BINANCE:BTCUSDT" }) {
  const [stockData, setStockData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // 웹소켓 연결 생성
    const socket = new WebSocket(`ws://localhost:8000/ws/stocks?symbol=${symbol}`);

    socket.onopen = () => {
      setIsConnected(true);
      console.log("웹소켓 연결됨");
    };

    socket.onmessage = (event) => {
      try {
        const response = JSON.parse(event.data);
        if (response.data && response.data.length > 0) {
          setStockData(response.data[0]);
        }
      } catch (error) {
        console.error("데이터 파싱 오류:", error);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      console.log("웹소켓 연결 종료");
    };

    // 컴포넌트 언마운트 시 연결 종료
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [symbol]);

  return (
    <div>
      <h2>실시간 주식 가격</h2>
      <p>연결 상태: {isConnected ? '연결됨' : '연결되지 않음'}</p>
      <p>심볼: {symbol}</p>
      {stockData && (
        <div>
          <p>가격: {stockData.p}</p>
          <p>거래량: {stockData.v}</p>
          <p>업데이트 시간: {new Date(stockData.t).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
}

export default StockPriceComponent;
```

## 여러 심볼 구독하기

여러 심볼을 동시에 구독하려면 쉼표(,)로 구분하여 전달합니다:

```
ws://localhost:8000/ws/stocks?symbol=BINANCE:BTCUSDT,NASDAQ:AAPL,KRX:005930
```

## 자주 발생하는 문제와 해결 방법

### 연결이 자주 끊기는 경우
자동 재연결 로직을 구현하는 것이 좋습니다:

```javascript
function createWebSocket(symbol) {
  const socket = new WebSocket(`ws://localhost:8000/ws/stocks?symbol=${symbol}`);
  
  socket.onclose = () => {
    console.log("연결이 끊어졌습니다. 3초 후 재연결을 시도합니다.");
    setTimeout(() => createWebSocket(symbol), 3000);
  };
  
  // 다른 이벤트 핸들러 설정...
  
  return socket;
}

const ws = createWebSocket("BINANCE:BTCUSDT");
```

### 데이터가 수신되지 않는 경우
1. 심볼이 올바르게 지정되었는지 확인하세요.
2. 서버가 실행 중인지 확인하세요.
3. 네트워크 연결을 확인하세요.

## 참고 사항
- 웹소켓은 양방향 통신을 지원하지만, 현재 구현에서는 서버에서 클라이언트로의 단방향 데이터 스트리밍만 지원합니다.
- 데이터는 실시간으로 업데이트되며, 시장 상황에 따라 업데이트 빈도가 달라질 수 있습니다.
