````markdown
# 🚀 프론트엔드 개발자를 위한 API 가이드

## 🔗 Base URL
```
http://localhost:8000
```

## Authentication (인증)
사용 가능한 기능
회원가입: 별도 회원가입 API로 신규 사용자 등록
로그인: 기존 사용자 로그인
카카오 로그인: 소셜 로그인 지원
세션 유지: 쿠키 기반 인증으로 새로고침해도 로그인 상태 유지
사용자 정보 조회: 현재 로그인된 사용자 정보 확인
중복 확인: 이메일/닉네임 중복 체크

API 엔드포인트
회원가입
POST /auth/signup - 신규 사용자 등록 (Form 데이터)
```
const formData = new FormData();
formData.append('email', 'new@example.com');
formData.append('password', 'password123');
formData.append('nickname', '새사용자');

fetch('http://localhost:8000/auth/signup', {
    method: 'POST',
    body: formData,
    credentials: 'include'
});
```

로그인
POST /auth/login - 기존 사용자 로그인 (Form 데이터)
```
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('password', 'password123');

fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    body: formData,
    credentials: 'include'
});
```

중복 확인
POST /auth/check-email - 이메일 중복 체크
```
const formData = new FormData();
formData.append('email', 'check@example.com');

fetch('http://localhost:8000/auth/check-email', {
    method: 'POST',
    body: formData
});
// 응답: {"email": "check@example.com", "available": true, "message": "사용 가능한 이메일입니다"}
```
POST /auth/check-nickname - 닉네임 중복 체크

```
const formData = new FormData();
formData.append('nickname', '확인할닉네임');

fetch('http://localhost:8000/auth/check-nickname', {
    method: 'POST',
    body: formData
});
// 응답: {"nickname": "확인할닉네임", "available": false, "message": "이미 사용 중인 닉네임입니다"}
```

카카오 로그인
GET /auth/kakao/redirect - 카카오 로그인 시작

```
window.location.href = 'http://localhost:8000/auth/kakao/redirect';
```

기타 인증 API
GET /auth/me - 현재 사용자 정보 조회
POST /auth/logout - 로그아웃
GET /auth/status - 인증 시스템 상태
회원가입/로그인 플로우
회원가입 플로우
```
1. 이메일 중복 확인 (/auth/check-email)
   ↓
2. 닉네임 중복 확인 (/auth/check-nickname)
   ↓
3. 회원가입 요청 (/auth/signup)
   ↓
4. 성공 시 자동 로그인 (쿠키 설정)
```
로그인 플로우
```
1. 로그인 요청 (/auth/login)
   ↓
2. 이메일/비밀번호 검증
   ↓
3. 성공 시 JWT 토큰 발급 및 쿠키 설정
```
효성 검증 규칙
이메일: 유효한 이메일 형식, 중복 불가
비밀번호: 최소 6자리 이상
닉네임: 2~20자리, 중복 불가
중요 사항
⚠️ 모든 인증 요청에 credentials: 'include' 필수 (쿠키 포함)

📊 Stock Data (주식 데이터)
사용 가능한 기능
실시간 시세: 주요 50개 주식의 실시간 데이터
히스토리 조회: 과거 24시간 데이터 조회
암호화폐 데이터: 상위 10개 암호화폐 시세
통계 정보: 각 종목별 상세 통계
API 엔드포인트
GET /api/stocks/quote?symbol=AAPL - 개별 주식 시세
GET /api/stocks/history/AAPL?hours=24 - 주식 히스토리
GET /api/stocks/crypto/BTC - 암호화폐 시세
GET /api/stocks/symbols - 지원하는 주식 목록
GET /api/stocks/crypto/symbols - 지원하는 암호화폐 목록
지원 종목
주식: AAPL, MSFT, NVDA, TSLA 등 50개
암호화폐: BTC, ETH, BNB, ADA 등 10개
🔌 WebSocket 실시간 데이터
사용 가능한 기능
전체 시장 데이터: 모든 주식과 암호화폐 실시간 업데이트
개별 종목 데이터: 특정 종목만 실시간 모니터링
자동 재연결: 연결 끊어지면 자동으로 재연결 시도
WebSocket 엔드포인트
ws://localhost:8000/ws/main - 전체 시장 데이터
ws://localhost:8000/ws/stocks?symbol=AAPL - 개별 주식
ws://localhost:8000/ws/crypto?symbol=BTC - 개별 암호화폐
데이터 형식
```
{
  "type": "market_update",
  "data": {
    "stocks": [{"symbol": "AAPL", "price": 150.25, "change": 2.15}],
    "cryptos": [{"symbol": "BTC", "price": "45000.50"}]
  }
}
```

💬 Chat (채팅)
사용 가능한 기능
종목별 채팅방: 각 주식/암호화폐마다 독립된 채팅방
실시간 메시지: WebSocket으로 즉시 메시지 전송
사용자 관리: 입장/퇴장 알림, 현재 접속자 수 표시
인증 연동: 로그인 사용자는 닉네임 자동 연결
WebSocket 엔드포인트
ws://localhost:8000/ws/chat/AAPL?nickname=홍길동&user_id=123 - AAPL 채팅방
REST API
GET /api/chat/rooms - 활성 채팅방 목록
GET /api/chat/rooms/AAPL - 특정 채팅방 정보
메시지 형식
```
{
  "type": "chat_message",
  "message": "안녕하세요!"
}
```

프론트엔드 구현 가이드
회원가입 구현
이메일/닉네임 중복 확인 API 호출
유효성 검증 통과 시 회원가입 API 호출
성공 시 자동 로그인 상태
로그인 구현
로그인 폼에서 Form데이터로 POST 요청
성공 시 쿠키 자동 설정됨
이후 모든 요청에 credentials: 'include' 포함
실시간 데이터 구현
WebSocket 연결: ws://localhost:8000/ws/main
market_update 이벤트 수신하여 UI 업데이트
연결 끊어지면 자동 재연결 로직 구현
채팅 구현
종목별 WebSocket 연결
메시지 송수신 처리
입장/퇴장 알림 표시
🔧 개발 환경 설정
CORS 설정
프론트엔드 포트 3000, 3001 허용
credentials: true 설정됨
프록시 설정 (React)
```
{
  "proxy": "http://localhost:8000"
}
```
환경변수
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```
요 페이지 구성 예시
1. 회원가입 페이지
이메일/비밀번호/닉네임 입력
실시간 중복 확인
유효성 검증 메시지
2. 로그인 페이지
이메일/비밀번호 입력
카카오 로그인 버튼
회원가입 페이지 링크
3. 대시보드
전체 시장 데이터 실시간 표시
주식/암호화폐 구분하여 그리드 형태
가격 변동 색상으로 표시
4. 종목 상세 페이지
개별 종목 실시간 데이터
24시간 히스토리 차트
해당 종목 채팅방 포함
5. 채팅 페이지
종목별 채팅방 리스트
실시간 메시지 송수신
접속자 수 표시
⚠️ 중요 주의사항
인증
모든 API 요청에 credentials: 'include' 필수
401 에러 시 로그인 페이지로 리다이렉트
회원가입과 로그인은 별도 API 사용
WebSocket
연결 끊어짐 대비 재연결 로직 필수
모바일에서 백그라운드 처리 주의
에러 처리
API 호출 실패 시 사용자 친화적 메시지 표시
네트워크 오류 시 재시도 로직
성능
WebSocket 메시지 너무 자주 오면 throttling 적용
대량 데이터 렌더링 시 가상화 고려
🎨 UI/UX 권장사항
회원가입/로그인
실시간 유효성 검증
명확한 에러 메시지
로딩 상태 표시
실시간 데이터 표시
가격 상승: 녹색/빨간색 구분
실시간 업데이트 애니메이션
연결 상태 표시기
채팅 기능
메시지 구분 (본인/타인/시스템)
자동 스크롤
입력 중 표시
모바일 대응
반응형 디자인
터치 친화적 UI
스와이프 제스처 지원
````