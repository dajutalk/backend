import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 경로 명시적 설정 - 프로젝트 루트에서 찾기
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # stock/backend/core/ -> juda/
env_path = project_root / "stock" / "backend" / ".env"

if not env_path.exists():
    # 대안 경로들 시도
    alt_paths = [
        project_root / ".env",
        current_file.parent.parent / ".env",
        Path.cwd() / ".env"
    ]
    for alt_path in alt_paths:
        if alt_path.exists():
            env_path = alt_path
            break

print(f"🔍 .env 파일 경로: {env_path}")
print(f"📁 .env 파일 존재: {env_path.exists()}")

load_dotenv(dotenv_path=env_path, override=True)

# 환경변수 디버깅
print(f"🔍 환경변수 확인:")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT_SET')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT_SET')}")
print(f"DB_HOST: {os.getenv('DB_HOST', 'NOT_SET')}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'NOT_SET')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT_SET')}")

class DatabaseSettings:
    """데이터베이스 설정"""
    
    def __init__(self):
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "36367")
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "3306")
        self.name = os.getenv("DB_NAME", "stock_db")
        
        print(f"🔧 데이터베이스 설정:")
        print(f"   사용자: {self.user}")
        print(f"   호스트: {self.host}:{self.port}")
        print(f"   데이터베이스: {self.name}")
    
    @property
    def url(self) -> str:
        url = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?charset=utf8mb4"
        print(f"🔗 DB URL: mysql+pymysql://{self.user}:***@{self.host}:{self.port}/{self.name}?charset=utf8mb4")
        return url
    
    @property
    def base_url(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}?charset=utf8mb4"

class APISettings:
    """API 설정"""
    
    def __init__(self):
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")

class AppSettings:
    """애플리케이션 설정"""
    
    def __init__(self):
        self.title = "Stock Backend API"
        self.version = "1.0.0"
        self.debug = True
        
        # CORS 설정
        self.allowed_origins = ["*"]
        self.allowed_methods = ["*"]
        self.allowed_headers = ["*"]

# 전역 설정 인스턴스
db_settings = DatabaseSettings()
api_settings = APISettings()
app_settings = AppSettings()
