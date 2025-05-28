import asyncio
import json
import os
import requests
from datetime import datetime, timedelta
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

def get_stock_quote(symbol):
    """
    실시간 주식 가격 정보 조회
    """
    endpoint = f"{BASE_URL}/quote"
    params = {
        'symbol': symbol,
        'token': API_KEY
    }
    
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.status_code}")
        return None

def get_company_profile(symbol):
    """
    회사 정보 조회
    """
    endpoint = f"{BASE_URL}/stock/profile2"
    params = {
        'symbol': symbol,
        'token': API_KEY
    }
    
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.status_code}")
        return None

def get_historical_data(symbol, from_date=None, to_date=None, resolution="D"):
    """
    과거 주식 가격 데이터 조회
    resolution: 1, 5, 15, 30, 60, D, W, M (분 단위 또는 일/주/월)
    """
    if from_date is None:
        from_date = int((datetime.now() - timedelta(days=30)).timestamp())
    if to_date is None:
        to_date = int(datetime.now().timestamp())
    
    endpoint = f"{BASE_URL}/stock/candle"
    params = {
        'symbol': symbol,
        'resolution': resolution,
        'from': from_date,
        'to': to_date,
        'token': API_KEY
    }
    
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.status_code}")
        return None

async def get_stock_data_async(symbol):
    """
    비동기적으로 주식 데이터 조회
    """
    async with aiohttp.ClientSession() as session:
        # 실시간 주가 조회
        quote_url = f"{BASE_URL}/quote?symbol={symbol}&token={API_KEY}"
        async with session.get(quote_url) as response:
            if response.status == 200:
                quote_data = await response.json()
            else:
                quote_data = None
        
        # 회사 정보 조회
        profile_url = f"{BASE_URL}/stock/profile2?symbol={symbol}&token={API_KEY}"
        async with session.get(profile_url) as response:
            if response.status == 200:
                profile_data = await response.json()
            else:
                profile_data = None
                
        return {
            "quote": quote_data,
            "profile": profile_data
        }

