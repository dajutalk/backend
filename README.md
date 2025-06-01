# 🚀 Stock Trading Platform

실시간 주식 데이터와 사용자 인증이 통합된 웹 플랫폼입니다.

## ✨ 주요 기능

- 📊 **실시간 주식 데이터**: 50개 주요 주식의 실시간 시세
- 💰 **암호화폐 데이터**: 상위 10개 암호화폐 실시간 시세
- 🔐 **사용자 인증**: 일반 로그인/회원가입 + 카카오 소셜 로그인
- 💬 **실시간 채팅**: 종목별 채팅방
- 🔌 **WebSocket 지원**: 실시간 데이터 스트리밍

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python
- **Database**: MySQL
- **Authentication**: JWT + OAuth (Kakao)
- **Real-time**: WebSocket
- **API**: Finnhub Stock API

## 📋 사전 요구사항

- Python 3.8+
- MySQL 8.0+
- Node.js 16+ (프론트엔드용)

## ⚙️ 설정

### 1. 환경변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 실제 값 입력
```

**필수 설정값:**
- `DB_PASSWORD`: MySQL 데이터베이스 비밀번호
- `FINNHUB_API_KEY`: [Finnhub](https://finnhub.io/)에서 발급받은 API 키
- `JWT_SECRET_KEY`: JWT 토큰 서명용 시크릿 키 (최소 32자)
- `KAKAO_CLIENT_ID`: 카카오 개발자 콘솔에서 발급받은 클라이언트 ID

### 2. 데이터베이스 설정

```sql
-- MySQL에 데이터베이스 생성
CREATE DATABASE stock_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 패키지 설치

```bash
# Python 의존성 설치
pip install -r requirements.txt

# 또는 uv 사용
uv sync
```

## 🚀 실행

### 백엔드 서버 실행

```bash
cd /path/to/project
uv run uvicorn stock.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### API 문서 확인

서버 실행 후 브라우저에서 접속:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API 엔드포인트

### 인증 API
- `POST /auth/signup` - 회원가입
- `POST /auth/login` - 로그인
- `GET /auth/kakao/redirect` - 카카오 로그인
- `GET /auth/me` - 사용자 정보 조회
- `POST /auth/logout` - 로그아웃

### 주식 데이터 API
- `GET /api/stocks/quote?symbol=AAPL` - 개별 주식 시세
- `GET /api/stocks/history/AAPL?hours=24` - 주식 히스토리
- `GET /api/stocks/crypto/BTC` - 암호화폐 시세

### WebSocket 엔드포인트
- `ws://localhost:8000/ws/main` - 전체 시장 데이터
- `ws://localhost:8000/ws/stocks?symbol=AAPL` - 개별 주식
- `ws://localhost:8000/ws/chat/AAPL?nickname=홍길동` - 채팅

## 🧪 테스트

```bash
# API 테스트
python -m stock.backend.test.test_scheduler

# WebSocket 테스트
python -m stock.backend.test.test_stock_websocket AAPL

# 채팅 테스트
python -m stock.backend.test.test_chat_room --symbol AAPL
```

## 📁 프로젝트 구조
````markdown
project-root/
├── backend/
│   ├── api/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── stock.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   ├── models/
│   │   │   └── user.py
│   │   ├── crud.py
│   │   └── session.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   └── stock_service.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── stock.py
│   │   └── chat.py
│   │
│   ├── static/              # (JS, CSS, 이미지) ← 템플릿 방식이면 사용
│   ├── templates/           # (Jinja2 템플릿용)
│   ├── main.py              # FastAPI 앱 진입점
│   └── config.py
│
├── frontend/
│   ├── public/              # 정적 자산
│   ├── src/
│   │   ├── components/      # 공통 컴포넌트 (ChatBox, StockPanel 등)
│   │   ├── pages/           # 페이지 (Home, Login, Chat 등)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── .env
│   ├── index.html
│   └── package.json
│
├── .gitignore
├── README.md
└── pyproject.toml
````
