# Stock Trading Platform API

## 프로젝트 개요

실시간 주식 데이터와 사용자 인증이 통합된 종합 주식 거래 플랫폼입니다. WebSocket을 통한 실시간 데이터 스트리밍, 채팅 시스템, 모의투자 기능을 제공합니다.

### 주요 기능

- **사용자 인증**: JWT + 카카오 소셜 로그인
- **실시간 주식 데이터**: 50개 주요 주식 + 10개 암호화폐
- **WebSocket 실시간 스트리밍**: 시세 데이터 + 채팅
- **실시간 채팅**: 종목별 채팅방
- **모의투자**: 가상 거래 시스템
- **AI 챗봇**: OpenAI 기반 투자 상담

## 기술 스택

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: MySQL 8.0 + SQLAlchemy ORM
- **Authentication**: JWT + OAuth2 (카카오)
- **Real-time**: WebSocket
- **External APIs**: Finnhub (주식), OpenAI (챗봇)
- **Environment**: Python 3.9+

### Frontend 권장사항
- **Framework**: React 18+ / Next.js 13+
- **Real-time**: WebSocket Client
- **State Management**: Redux Toolkit / Zustand
- **UI**: Material-UI / Tailwind CSS
- **Charts**: Chart.js / Recharts

## 프로젝트 구조

```
juda/
├── stock/backend/                 # 백엔드 루트
│   ├── main.py                   # FastAPI 앱 진입점
│   ├── core/
│   │   └── config.py            # 환경 설정
│   ├── auth/                    # 인증 시스템
│   │   ├── auth_routes.py       # 인증 API 라우터
│   │   ├── auth_service.py      # JWT 토큰 관리
│   │   ├── kakao_service.py     # 카카오 OAuth
│   │   ├── models.py            # 사용자 모델
│   │   └── schemas.py           # Pydantic 스키마
│   ├── api/                     # REST API
│   │   ├── stock.py             # 주식 데이터 API
│   │   └── chat.py              # 채팅 API
│   ├── services/                # 비즈니스 로직
│   │   ├── stock_service.py     # 주식 데이터 처리
│   │   ├── auto_collector.py    # 자동 데이터 수집
│   │   └── cache_service.py     # 캐싱 관리
│   ├── websocket_routes.py      # WebSocket 엔드포인트
│   ├── websocket_manager.py     # WebSocket 연결 관리
│   ├── stockDeal/               # 모의투자
│   │   └── mock_investment.py   # 가상 거래
│   ├── chatbot/                 # AI 챗봇
│   │   └── chat_router.py       # 챗봇 API
│   ├── database.py              # DB 설정 및 모델
│   ├── utils/
│   │   └── logger.py            # 로깅 설정
│   ├── test/                    # 테스트 도구
│   │   ├── test_stock_quote_api.py
│   │   └── fix_crypto_table.py
│   └── docs/                    # API 문서
│       ├── websocket_usage.md
│       ├── websocket_chat_usage.md
│       ├── stock_quote_api_usage.md
│       └── frontend_integration_guide.md
├── .env                         # 환경변수 설정
└── README.md                    # 이 파일
```

## 설치 및 설정

### 1. 환경 요구사항

```bash
# Python 3.9+ 필수
python --version

# MySQL 8.0+ 필수
mysql --version
```

### 2. 프로젝트 클론 및 의존성 설치

```bash
git clone <repository-url>
cd juda

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install fastapi[all] sqlalchemy pymysql python-multipart
pip install requests python-jose[cryptography] passlib[bcrypt]
pip install python-dotenv websockets openai
```

### 3. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 설정하세요:

```bash
# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=stock_db

# API 키
FINNHUB_API_KEY=your_finnhub_api_key
OPENAI_API_KEY=your_openai_api_key

# JWT 인증
JWT_SECRET_KEY=your_very_secure_random_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 카카오 로그인 (선택사항)
KAKAO_CLIENT_ID=your_kakao_app_key
KAKAO_REDIRECT_URI=https://dajutalk.com/auth/kakao/callback

# 프론트엔드 URL
FRONTEND_URL=https://dajutalk.com

# 개발 환경에서는 다음과 같이 설정
# KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
# FRONTEND_URL=http://localhost:3000
```

### 4. 데이터베이스 설정

```bash
# MySQL에 데이터베이스 생성
mysql -u root -p
CREATE DATABASE stock_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit

# 테이블 자동 생성 (서버 시작 시 자동으로 생성됨)
```

### 5. API 키 발급

#### Finnhub API 키 (필수)
1. https://finnhub.io 회원가입
2. API 키 발급
3. `.env` 파일에 `FINNHUB_API_KEY` 설정

#### OpenAI API 키 (챗봇 기능용)
1. https://openai.com 계정 생성
2. API 키 발급
3. `.env` 파일에 `OPENAI_API_KEY` 설정

#### 카카오 로그인 (선택사항)
1. https://developers.kakao.com 앱 생성
2. JavaScript 키 복사
3. `.env` 파일에 `KAKAO_CLIENT_ID` 설정

## 서버 실행

```bash
cd stock/backend
python main.py

# 또는 uvicorn으로 실행
uvicorn stock.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

서버 실행 후 다음 URL에서 확인:
- 메인 API: https://dajutalk.com
- API 문서: https://dajutalk.com/docs
- 헬스 체크: https://dajutalk.com/health



## API 엔드포인트

### 인증 API (`/auth`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 |
| POST | `/auth/logout` | 로그아웃 |
| GET | `/auth/me` | 현재 사용자 정보 |
| POST | `/auth/check-email` | 이메일 중복 확인 |
| POST | `/auth/check-nickname` | 닉네임 중복 확인 |
| GET | `/auth/kakao/redirect` | 카카오 로그인 시작 |

### 주식 데이터 API (`/api/stocks`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/stocks/quote?symbol=AAPL` | 개별 주식 시세 |
| GET | `/api/stocks/history/{symbol}?hours=24` | 주식 히스토리 |
| GET | `/api/stocks/symbols` | 지원 주식 목록 |
| GET | `/api/stocks/crypto/{symbol}` | 암호화폐 시세 |
| GET | `/api/stocks/crypto/symbols` | 지원 암호화폐 목록 |

### 채팅 API (`/api/chat`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/chat/rooms` | 활성 채팅방 목록 |
| GET | `/api/chat/rooms/{symbol}` | 특정 채팅방 정보 |

### 모의투자 API (`/mock`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/mock/buy` | 가상 매수 |
| POST | `/mock/sell` | 가상 매도 |
| GET | `/mock/portfolio` | 포트폴리오 조회 |
| GET | `/mock/balance` | 가상 잔고 조회 |

### AI 챗봇 API (`/chatbot`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/chatbot/chat` | AI 투자 상담 |

## 🔌 WebSocket 엔드포인트

### 실시간 데이터

```bash
# 전체 시장 데이터
wss://dajutalk.com/ws/main

# 개별 주식 데이터
wss://dajutalk.com/ws/stocks?symbol=AAPL

# 개별 암호화폐 데이터  
wss://dajutalk.com/ws/crypto?symbol=BTC
```

### 실시간 채팅

```bash
# 종목별 채팅방
wss://dajutalk.com/ws/chat?symbol=AAPL&nickname=사용자명&user_id=123
```

## 프론트엔드 통합 가이드

### 인증 구현 예시

```javascript
// 회원가입
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('password', 'password123');
formData.append('nickname', '사용자');

fetch('https://dajutalk.com/auth/signup', {
    method: 'POST',
    body: formData,
    credentials: 'include'  // 중요: 쿠키 포함
});

// 로그인
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('password', 'password123');

fetch('https://dajutalk.com/auth/login', {
    method: 'POST',
    body: formData,
    credentials: 'include'
});
```

### WebSocket 실시간 데이터

```javascript
// 전체 시장 데이터 구독
const socket = new WebSocket('wss://dajutalk.com/ws/main');

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'market_update') {
        // UI 업데이트
        updateStockData(data.data.stocks);
        updateCryptoData(data.data.cryptos);
    }
};

// 개별 종목 구독
const appleSocket = new WebSocket('wss://dajutalk.com/ws/stocks?symbol=AAPL');
```

### 채팅 구현

```javascript
// 채팅방 연결
const chatSocket = new WebSocket('wss://dajutalk.com/ws/chat?symbol=AAPL&nickname=사용자&user_id=123');

// 메시지 전송
chatSocket.send(JSON.stringify({
    type: 'chat_message',
    message: '안녕하세요!'
}));

// 메시지 수신
chatSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    displayMessage(data.username, data.message);
};
```

## 테스트 도구

### 주식 시세 API 테스트

```bash
cd stock/backend/test

# 단일 조회
python test_stock_quote_api.py AAPL

# 실시간 모니터링 (5초 간격)
python test_stock_quote_api.py AAPL --monitor --interval 5

# 특정 시간 동안 모니터링
python test_stock_quote_api.py AAPL --monitor --duration 60
```

### 데이터베이스 테이블 수정

```bash
# 암호화폐 테이블 재생성
python test/fix_crypto_table.py
```

## 상세 문서

프로젝트의 각 기능에 대한 상세한 문서는 `docs/` 폴더에서 확인할 수 있습니다:

- [WebSocket 사용법](stock/backend/docs/websocket_usage.md)
- [채팅 WebSocket 가이드](stock/backend/docs/websocket_chat_usage.md)
- [REST API 사용법](stock/backend/docs/stock_quote_api_usage.md)
- [프론트엔드 통합 가이드](stock/backend/docs/frontend_integration_guide.md)

## 개발 환경 설정

### 환경 구분

**프로덕션 환경 (기본값)**
```bash
# API URL
API_URL=https://dajutalk.com
# WebSocket URL  
WS_URL=wss://dajutalk.com
```

**개발 환경**
```bash
# API URL
API_URL=http://localhost:8000
# WebSocket URL
WS_URL=ws://localhost:8000
```

### CORS 설정

기본적으로 다음 도메인이 허용됩니다:
- `https://dajutalk.com`
- `https://www.dajutalk.com`
- `http://localhost:3000` (개발용)
- `http://localhost:3001` (개발용)

### 로깅

모든 로그는 콘솔에 출력되며, 다음 레벨로 구분됩니다:
- INFO: 일반 정보
- WARNING: 경고사항
- ERROR: 오류 발생

##  문제해결

### 자주 발생하는 문제

1. **데이터베이스 연결 실패**
   - MySQL 서버 실행 확인
   - `.env` 파일의 DB 설정 확인

2. **API 키 오류**
   - Finnhub API 키 유효성 확인
   - API 사용량 제한 확인

3. **WebSocket 연결 끊김**
   - 방화벽 설정 확인
   - 프록시 설정 확인

4. **카카오 로그인 실패**
   - 카카오 앱 설정의 도메인 등록 확인 (dajutalk.com)
   - redirect_uri 정확성 확인 (https://dajutalk.com/auth/kakao/callback)

### 로그 확인

```bash
# 서버 로그 실시간 확인
tail -f /var/log/stock-api.log

# 또는 콘솔에서 직접 확인
python main.py
```

##  배포

### 프로덕션 환경 설정

1. **환경변수 설정**
   ```bash
   # 프로덕션 환경 (기본값)
   KAKAO_REDIRECT_URI=https://dajutalk.com/auth/kakao/callback
   FRONTEND_URL=https://dajutalk.com
   
   # 개발 환경
   KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
   FRONTEND_URL=http://localhost:3000
   ```

2. **HTTPS 설정**
   - SSL 인증서 설정
   - 보안 쿠키 활성화

3. **데이터베이스 최적화**
   - 인덱스 설정
   - 커넥션 풀 조정

4. **모니터링 설정**
   - 로그 수집 시스템 구축
   - 성능 모니터링 도구 연동

## 라이선스

이 프로젝트는 MIT 라이선스로 제공됩니다.

##  기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.

---

**최종 업데이트**: 2025년 06월
