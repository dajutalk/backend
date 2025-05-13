# 웹 소켓을 이용한 실시간 채팅 

이 프로젝트는 Django와 MySQL을 기반으로 실시간 채팅 기능을 구현하며,  
협업을 위한 **uv 가상환경 기반 개발환경**을 구축합니다.

---

## 프로젝트 개요

- **백엔드 프레임워크**: Django 4.2.20 (LTS)
- **DB**: MySQL 8.0.11 이상
- **패키지 관리**: uv
- **Python 버전**: 3.12.9

---
# 세팅 가이드
1. uv 설치
- `curl -LsSf https://astral.sh/uv/install.sh | sh`

2. 레포지토리 클론
- `git clone 

3. 프로젝트 디렉토리 진입 후
cd Chat_Project
4. 가상환경 설정 및 패키지 설치
- `uv venv`
- `source .venv/bin/activate`
- `uv sync`

# 주의사항
**.env** 절대 커밋 금지
**.env.example을 참고하여 .env를 직접 생성하세요**


# 파일 구조

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
