import requests
import os
import logging

logger = logging.getLogger(__name__)

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/auth/kakao/callback")

def get_kakao_access_token(code: str) -> str:
    """카카오 인증 코드로 액세스 토큰 발급"""
    try:
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            logger.error(f"카카오 토큰 발급 실패: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"카카오 토큰 발급 오류: {e}")
        return None

def get_kakao_user_info(access_token: str) -> dict:
    """카카오 사용자 정보 조회"""
    try:
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"카카오 사용자 정보 조회 실패: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"카카오 사용자 정보 조회 오류: {e}")
        return None
