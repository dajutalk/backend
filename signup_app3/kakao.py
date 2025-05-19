# kakao.py
# 카카오 API 호출 함수를 작성하는 파일 (인가코드 -> access_token -> 사용자 정보 가져오기)

import os
import requests
from dotenv import load_dotenv

# .env 파일에서 카카오 API 관련 환경변수를 불러오기 위해 dotenv 로드
load_dotenv()

# .env에서 카카오 클라이언트 ID(앱키)와 리다이렉트 URI 읽기
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")          # 카카오 앱 REST API 키
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")     # 로그인 완료 후 돌아올 주소

# 인가코드를 받아서 카카오 access token을 요청하는 함수
def get_kakao_access_token(code: str):
    """
    클라이언트가 카카오 로그인을 완료하고 돌려받은 인가코드(code)를
    이용해서 access token을 발급받는 함수
    """

    url = "https://kauth.kakao.com/oauth/token"  # 카카오 토큰 요청 엔드포인트

    data = {
        "grant_type": "authorization_code",  # 고정값
        "client_id": KAKAO_CLIENT_ID,         # 카카오 앱 REST API 키
        "redirect_uri": KAKAO_REDIRECT_URI,    # 리다이렉트 URI (카카오 디벨로퍼 설정한 것)
        "code": code                           # 프론트에서 받은 인가코드
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"  # 카카오 API는 form형식 요청
    }

    # POST 방식으로 access token 요청
    response = requests.post(url, data=data, headers=headers)

    if response.status_code != 200:
        return None  # 실패 시 None 반환

    # 성공하면 access_token 값만 추출해서 반환
    return response.json().get("access_token")


# access token을 이용해서 카카오 사용자 정보를 요청하는 함수
def get_kakao_user_info(access_token: str):
    """
    발급받은 access token을 사용해서 카카오 사용자 정보(profile, id 등)를 가져오는 함수
    """

    url = "https://kapi.kakao.com/v2/user/me"  # 카카오 사용자 정보 조회 API 엔드포인트

    headers = {
        "Authorization": f"Bearer {access_token}"  # Authorization 헤더에 Bearer 토큰 붙이기
    }

    # GET 방식으로 사용자 정보 요청
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None  # 실패 시 None 반환

    # 성공하면 사용자 정보(json)를 반환
    return response.json()
