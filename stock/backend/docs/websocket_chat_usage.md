# 실시간 채팅 웹소켓 연결 가이드

## 개요
이 문서는 웹소켓을 통한 실시간 채팅 기능을 프론트엔드에서 사용하는 방법을 설명합니다. 이 기능을 사용하면 주식 심볼별 채팅방에서 사용자들이 실시간으로 대화할 수 있습니다.

## 웹소켓 연결 방법

### 기본 URL
```
ws://[서버주소]/ws/chat
```

로컬 개발 환경에서는 다음과 같이 연결합니다:
```
ws://localhost:8000/ws/chat
```

### 연결 파라미터
웹소켓 연결 시 다음 쿼리 파라미터를 사용할 수 있습니다:

- `symbol`: 참여할 채팅방의 주식 심볼 (필수)
  - 예: BINANCE:BTCUSDT, NASDAQ:AAPL, KRX:005930
  - 각 심볼은 독립적인 채팅방으로 작동합니다

예시:
```
ws://localhost:8000/ws/chat?symbol=BINANCE:BTCUSDT
```

## 메시지 송수신 형식

### 메시지 전송 형식
채팅 메시지를 전송할 때는 JSON 형식을 사용하는 것이 권장됩니다:

```json
{
  "type": "chat_message",
  "message": "안녕하세요!",
  "username": "사용자이름"
}
```

- `type`: 메시지 유형 (일반적으로 'chat_message')
- `message`: 전송할 메시지 내용
- `username`: 발신자 이름 (선택 사항)

JSON 형식 외에도 단순 텍스트 메시지도 지원됩니다.

### 메시지 수신 형식
수신되는 메시지는 다른 사용자가 전송한 것과 동일한 형식입니다.

## 프론트엔드 사용 예시

### JavaScript 예시 코드

```javascript
// 웹소켓 연결 생성
const symbol = "BINANCE:BTCUSDT";
const username = "사용자123";
const socket = new WebSocket(`ws://localhost:8000/ws/chat?symbol=${symbol}`);

// 연결 이벤트
socket.onopen = (event) => {
  console.log("채팅 서버에 연결되었습니다!");
  
  // 입장 메시지 전송
  socket.send(JSON.stringify({
    type: "chat_message",
    message: "채팅방에 입장했습니다.",
    username: username
  }));
};

// 메시지 수신 이벤트
socket.onmessage = (event) => {
  try {
    // JSON 형식인 경우 파싱
    const data = JSON.parse(event.data);
    console.log(`${data.username || '익명'}: ${data.message}`);
    // 여기에 채팅 UI 업데이트 로직 추가
  } catch (error) {
    // 일반 텍스트인 경우
    console.log(`메시지 수신: ${event.data}`);
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

// 메시지 전송 함수
function sendMessage(message) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: "chat_message",
      message: message,
      username: username
    }));
  } else {
    console.error("웹소켓이 연결되어 있지 않습니다.");
  }
}
```

### React Hooks 사용 예시

```jsx
import { useState, useEffect, useRef } from 'react';

function ChatComponent({ symbol, username }) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const wsRef = useRef(null);

  useEffect(() => {
    // 웹소켓 연결 생성
    const socket = new WebSocket(`ws://localhost:8000/ws/chat?symbol=${symbol}`);
    wsRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      console.log("채팅 서버에 연결되었습니다!");
      
      // 입장 메시지 전송
      socket.send(JSON.stringify({
        type: "chat_message",
        message: "채팅방에 입장했습니다.",
        username: username
      }));
    };

    socket.onmessage = (event) => {
      try {
        // 메시지 파싱 시도
        const data = JSON.parse(event.data);
        // 새 메시지를 메시지 목록에 추가
        setMessages(prevMessages => [...prevMessages, {
          id: Date.now(),
          username: data.username || '익명',
          message: data.message,
          timestamp: new Date().toLocaleTimeString()
        }]);
      } catch (error) {
        // JSON이 아닌 일반 텍스트 메시지 처리
        setMessages(prevMessages => [...prevMessages, {
          id: Date.now(),
          username: '시스템',
          message: event.data,
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      console.log("채팅 서버 연결이 종료되었습니다.");
    };

    socket.onerror = (error) => {
      console.error("웹소켓 오류:", error);
    };

    // 컴포넌트 언마운트 시 연결 종료
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [symbol, username]);

  // 메시지 전송 함수
  const sendMessage = (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim()) return;
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "chat_message",
        message: inputMessage,
        username: username
      }));
      setInputMessage('');
    } else {
      console.error("웹소켓이 연결되어 있지 않습니다.");
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>{symbol} 채팅방</h2>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '연결됨' : '연결 끊김'}
        </div>
      </div>
      
      <div className="messages-container">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.username === username ? 'my-message' : ''}`}>
            <span className="message-username">{msg.username}</span>
            <span className="message-time">{msg.timestamp}</span>
            <div className="message-content">{msg.message}</div>
          </div>
        ))}
      </div>
      
      <form onSubmit={sendMessage} className="message-input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="메시지를 입력하세요..."
          disabled={!isConnected}
        />
        <button type="submit" disabled={!isConnected}>전송</button>
      </form>
    </div>
  );
}

export default ChatComponent;
```

## 채팅방 관리

### 채팅방 입장
특정 심볼에 해당하는 채팅방에 입장하려면 해당 심볼을 쿼리 파라미터로 지정하세요:

```javascript
// AAPL 주식 채팅방 입장
const socket = new WebSocket("ws://localhost:8000/ws/chat?symbol=NASDAQ:AAPL");
```

### 채팅방 퇴장
연결을 종료하면 자동으로 채팅방에서 퇴장합니다:

```javascript
socket.close();
```

## 자주 발생하는 문제와 해결 방법

### 연결이 자주 끊기는 경우
자동 재연결 로직을 구현하는 것이 좋습니다:

```javascript
function createChatWebSocket(symbol, username) {
  const socket = new WebSocket(`ws://localhost:8000/ws/chat?symbol=${symbol}`);
  
  socket.onopen = () => {
    console.log("채팅 서버에 연결되었습니다!");
    // 입장 메시지 전송
    socket.send(JSON.stringify({
      type: "chat_message",
      message: "채팅방에 다시 입장했습니다.",
      username: username
    }));
  };
  
  socket.onclose = (event) => {
    // 1000은 정상 종료를 의미합니다
    if (event.code !== 1000) {
      console.log("연결이 끊어졌습니다. 3초 후 재연결을 시도합니다.");
      setTimeout(() => createChatWebSocket(symbol, username), 3000);
    }
  };
  
  // 다른 이벤트 핸들러 설정...
  
  return socket;
}

const ws = createChatWebSocket("BINANCE:BTCUSDT", "사용자123");
```

### 메시지가 전송되지 않는 경우

1. 웹소켓 연결 상태를 확인하세요:
```javascript
if (socket.readyState !== WebSocket.OPEN) {
  console.error("웹소켓이 열려있지 않습니다. 현재 상태:", socket.readyState);
  // 0: CONNECTING, 1: OPEN, 2: CLOSING, 3: CLOSED
}
```

2. 메시지 형식을 확인하세요:
   - 메시지는 JSON 형식이어야 합니다.
   - `JSON.stringify()`를 사용해 객체를 문자열로 변환했는지 확인하세요.

3. 서버가 실행 중인지 확인하세요.

## 보안 및 최적화 고려사항

### 보안
- 사용자 인증: 실제 운영 환경에서는 토큰 또는 세션 기반 인증을 구현하는 것이 좋습니다.
- XSS 방지: 채팅 메시지를 표시하기 전에 항상 적절한 이스케이프 처리를 수행하세요.

### 최적화
- 메시지가 많은 경우 가상 스크롤(Virtual Scrolling)을 적용하여 성능을 향상시킬 수 있습니다.
- 대량의 메시지를 처리할 때는 메시지 큐를 구현하여 DOM 업데이트를 최적화하세요.

## 참고 사항
- 채팅 기록은 현재 세션에만 저장됩니다. 페이지를 새로고침하면 기존 메시지는 모두 사라집니다.
- 채팅방은 심볼별로 구분되며, 각 심볼에 대한 채팅방은 독립적으로 작동합니다.
- 모든 사용자는 동일한 채팅방 내에서 모든 메시지를 볼 수 있습니다.
