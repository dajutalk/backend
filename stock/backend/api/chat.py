from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from stock.backend.database import get_db, SessionLocal
from typing import Dict, List, Set
import asyncio
import json
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws/chat",
    tags=["Chat"],
)

rest_router = APIRouter(
    prefix="/api/chat",
    tags=["Chat API"],
)

# Symbol별 채팅방 관리
class ChatRoomManager:
    def __init__(self):
        # symbol -> set of websockets
        self.chat_rooms: Dict[str, Set[WebSocket]] = {}
        # websocket -> user info
        self.user_connections: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, symbol: str, user_info: Dict):
        """채팅방에 연결"""
        if symbol not in self.chat_rooms:
            self.chat_rooms[symbol] = set()
        
        self.chat_rooms[symbol].add(websocket)
        self.user_connections[websocket] = {
            "symbol": symbol,
            "nickname": user_info.get("nickname", "익명"),
            "user_id": user_info.get("user_id", "guest"),
            "joined_at": datetime.now()
        }
        
        logger.info(f" 사용자 '{user_info.get('nickname')}' {symbol} 채팅방 입장")
        
        # 입장 알림 브로드캐스트
        await self.broadcast_to_room(symbol, {
            "type": "user_joined",
            "data": {
                "message": f"{user_info.get('nickname', '익명')}님이 입장했습니다.",
                "symbol": symbol,
                "timestamp": int(time.time() * 1000),
                "user_count": len(self.chat_rooms[symbol])
            }
        }, exclude=websocket)
    
    def disconnect(self, websocket: WebSocket):
        """채팅방에서 연결 해제"""
        if websocket in self.user_connections:
            user_info = self.user_connections[websocket]
            symbol = user_info["symbol"]
            nickname = user_info["nickname"]
            
            # 채팅방에서 제거
            if symbol in self.chat_rooms:
                self.chat_rooms[symbol].discard(websocket)
                
                # 채팅방이 비어있으면 삭제
                if not self.chat_rooms[symbol]:
                    del self.chat_rooms[symbol]
            
            # 사용자 연결 정보 제거
            del self.user_connections[websocket]
            
            logger.info(f" 사용자 '{nickname}' {symbol} 채팅방 퇴장")
            
            # 퇴장 알림 브로드캐스트 (비동기로 실행)
            if symbol in self.chat_rooms:
                asyncio.create_task(self.broadcast_to_room(symbol, {
                    "type": "user_left",
                    "data": {
                        "message": f"{nickname}님이 퇴장했습니다.",
                        "symbol": symbol,
                        "timestamp": int(time.time() * 1000),
                        "user_count": len(self.chat_rooms[symbol])
                    }
                }))
    
    async def broadcast_to_room(self, symbol: str, message: Dict, exclude: WebSocket = None):
        """특정 symbol 채팅방에 메시지 브로드캐스트"""
        if symbol not in self.chat_rooms:
            return
        
        disconnected = []
        for websocket in self.chat_rooms[symbol].copy():
            if websocket != exclude:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(websocket)
        
        # 연결이 끊어진 WebSocket 정리
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_room_info(self, symbol: str) -> Dict:
        """채팅방 정보 조회"""
        if symbol not in self.chat_rooms:
            return {"user_count": 0, "users": []}
        
        users = []
        for websocket in self.chat_rooms[symbol]:
            if websocket in self.user_connections:
                user_info = self.user_connections[websocket]
                users.append({
                    "nickname": user_info["nickname"],
                    "user_id": user_info["user_id"],
                    "joined_at": user_info["joined_at"].isoformat()
                })
        
        return {
            "user_count": len(self.chat_rooms[symbol]),
            "users": users
        }

# 전역 채팅방 매니저
chat_manager = ChatRoomManager()

@router.websocket("/{symbol}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    symbol: str,
    nickname: str = Query(default="익명"),
    user_id: str = Query(default="guest")
):
    """Symbol별 채팅 WebSocket 엔드포인트"""
    await websocket.accept()
    
    user_info = {
        "nickname": nickname,
        "user_id": user_id
    }
    
    await chat_manager.connect(websocket, symbol.upper(), user_info)
    
    try:
        # 현재 채팅방 정보 전송
        room_info = chat_manager.get_room_info(symbol.upper())
        await websocket.send_text(json.dumps({
            "type": "room_info",
            "data": {
                "symbol": symbol.upper(),
                "user_count": room_info["user_count"],
                "users": room_info["users"],
                "message": f"{symbol.upper()} 채팅방에 입장했습니다."
            }
        }))
        
        # 메시지 수신 루프
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 채팅 메시지 처리
                if message_data.get("type") == "chat_message":
                    chat_message = {
                        "type": "chat_message",
                        "data": {
                            "symbol": symbol.upper(),
                            "nickname": user_info["nickname"],
                            "user_id": user_info["user_id"],
                            "message": message_data.get("message", ""),
                            "timestamp": int(time.time() * 1000)
                        }
                    }
                    
                    # 같은 symbol 채팅방의 모든 사용자에게 브로드캐스트
                    await chat_manager.broadcast_to_room(symbol.upper(), chat_message)
                    
                    # 메시지 DB 저장 (선택사항)
                    await save_chat_message(symbol.upper(), user_info, message_data.get("message", ""))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "잘못된 메시지 형식입니다."}
                }))
            except Exception as e:
                logger.error(f"채팅 메시지 처리 오류: {e}")
                
    except WebSocketDisconnect:
        pass
    finally:
        chat_manager.disconnect(websocket)

async def save_chat_message(symbol: str, user_info: Dict, message: str):
    """채팅 메시지를 DB에 저장 (선택사항)"""
    try:
        # 여기에 DB 저장 로직 추가
        # 예: ChatMessage 모델 생성 후 저장
        logger.info(f" 채팅 저장: {symbol} - {user_info['nickname']}: {message}")
    except Exception as e:
        logger.error(f"채팅 메시지 저장 실패: {e}")

# REST API 엔드포인트들
@rest_router.get("/rooms")
async def get_all_chat_rooms():
    """모든 활성 채팅방 목록 조회"""
    rooms = {}
    for symbol in chat_manager.chat_rooms:
        rooms[symbol] = chat_manager.get_room_info(symbol)
    
    return {
        "active_rooms": len(rooms),
        "rooms": rooms
    }

@rest_router.get("/rooms/{symbol}")
async def get_chat_room_info(symbol: str):
    """특정 symbol 채팅방 정보 조회"""
    room_info = chat_manager.get_room_info(symbol.upper())
    return {
        "symbol": symbol.upper(),
        **room_info
    }

@rest_router.get("/history/{symbol}")
async def get_chat_history(symbol: str, limit: int = 50):
    """채팅 히스토리 조회 (DB에서)"""
    # TODO: DB에서 채팅 히스토리 조회 로직 구현
    return {
        "symbol": symbol.upper(),
        "messages": [],
        "message": "채팅 히스토리 기능은 아직 구현되지 않았습니다."
    }
