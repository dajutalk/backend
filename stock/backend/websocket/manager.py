from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, metadata: Dict[str, Any] = None):
        """WebSocket 연결"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.connection_data[websocket] = metadata or {}
            logger.info(f"✅ WebSocket 연결 추가. 총 연결: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_data.pop(websocket, None)
            logger.info(f"❌ WebSocket 연결 제거. 총 연결: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """개별 메시지 전송"""
        try:
            message_str = json.dumps(message, ensure_ascii=False)
            await websocket.send_text(message_str)
        except WebSocketDisconnect:
            logger.info("WebSocket 연결이 클라이언트에 의해 종료됨")
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"❌ 개별 메시지 전송 실패: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결에 브로드캐스트"""
        if not self.active_connections:
            logger.debug("브로드캐스트할 활성 연결이 없음")
            return
            
        disconnected = []
        message_str = json.dumps(message, ensure_ascii=False)
        
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(message_str)
            except WebSocketDisconnect:
                logger.info("WebSocket 연결이 클라이언트에 의해 종료됨")
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"❌ 브로드캐스트 실패: {e}")
                disconnected.append(websocket)
        
        # 실패한 연결 정리
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_type(self, message: Dict[str, Any], connection_type: str):
        """특정 타입의 연결들에만 브로드캐스트"""
        target_connections = self.get_connections_by_type(connection_type)
        
        if not target_connections:
            logger.debug(f"타입 '{connection_type}'의 활성 연결이 없음")
            return
            
        disconnected = []
        message_str = json.dumps(message, ensure_ascii=False)
        
        for websocket in target_connections:
            try:
                await websocket.send_text(message_str)
            except WebSocketDisconnect:
                logger.info("WebSocket 연결이 클라이언트에 의해 종료됨")
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"❌ 타입별 브로드캐스트 실패: {e}")
                disconnected.append(websocket)
        
        # 실패한 연결 정리
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_connection_count(self) -> int:
        """활성 연결 수 반환"""
        return len(self.active_connections)
    
    def get_connections_by_type(self, connection_type: str) -> List[WebSocket]:
        """타입별 연결 조회"""
        return [
            ws for ws, data in self.connection_data.items() 
            if data.get("type") == connection_type and ws in self.active_connections
        ]
    
    def get_connection_info(self, websocket: WebSocket) -> Dict[str, Any]:
        """특정 연결의 메타데이터 조회"""
        return self.connection_data.get(websocket, {})
    
    def update_connection_data(self, websocket: WebSocket, data: Dict[str, Any]):
        """연결 메타데이터 업데이트"""
        if websocket in self.connection_data:
            self.connection_data[websocket].update(data)
    
    async def ping_all_connections(self):
        """모든 연결에 ping 전송 (연결 상태 확인)"""
        ping_message = {"type": "ping", "timestamp": asyncio.get_event_loop().time()}
        await self.broadcast(ping_message)
    
    def cleanup_stale_connections(self):
        """비활성 연결 정리"""
        stale_connections = []
        
        for websocket in self.active_connections.copy():
            try:
                # WebSocket 상태 확인
                if websocket.client_state.name in ['DISCONNECTED', 'CLOSED']:
                    stale_connections.append(websocket)
            except Exception:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            self.disconnect(websocket)
        
        if stale_connections:
            logger.info(f"정리된 비활성 연결: {len(stale_connections)}개")
