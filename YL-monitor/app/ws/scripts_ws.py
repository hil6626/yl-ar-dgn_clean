"""
脚本执行 WebSocket 处理器
提供实时执行进度和日志推送
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.script_metadata import (
    get_script_metadata_manager,
    ScriptExecutionRecord
)
from app.services.scripts_scanner import get_scripts_scanner


router = APIRouter()


class ScriptsWebSocketManager:
    """
    脚本 WebSocket 管理器
    
    管理所有脚本相关的 WebSocket 连接
    """
    
    def __init__(self):
        # 按脚本ID组织的连接
        self.script_connections: Dict[str, Set[WebSocket]] = {}
        # 全局连接（接收所有脚本更新）
        self.global_connections: Set[WebSocket] = set()
        # 执行ID到连接的映射
        self.execution_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect_script(self, websocket: WebSocket, script_id: str):
        """
        连接到特定脚本的更新
        """
        await websocket.accept()
        
        if script_id not in self.script_connections:
            self.script_connections[script_id] = set()
        self.script_connections[script_id].add(websocket)
        
        # 发送当前状态
        await self._send_script_status(websocket, script_id)
    
    async def connect_global(self, websocket: WebSocket):
        """
        连接到全局更新
        """
        await websocket.accept()
        self.global_connections.add(websocket)
        
        # 发送所有脚本状态概览
        await self._send_all_scripts_status(websocket)
    
    async def connect_execution(self, websocket: WebSocket, execution_id: str):
        """
        连接到特定执行任务的实时日志
        """
        await websocket.accept()
        
        if execution_id not in self.execution_connections:
            self.execution_connections[execution_id] = set()
        self.execution_connections[execution_id].add(websocket)
        
        # 发送当前执行状态
        await self._send_execution_status(websocket, execution_id)
    
    def disconnect(self, websocket: WebSocket):
        """
        断开连接
        """
        # 从脚本连接中移除
        for connections in self.script_connections.values():
            connections.discard(websocket)
        
        # 从全局连接中移除
        self.global_connections.discard(websocket)
        
        # 从执行连接中移除
        for connections in self.execution_connections.values():
            connections.discard(websocket)
    
    async def broadcast_script_update(self, script_id: str, data: dict):
        """
        广播脚本状态更新
        """
        message = {
            "type": "script_update",
            "script_id": script_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 发送给关注该脚本的连接
        if script_id in self.script_connections:
            disconnected = []
            for ws in self.script_connections[script_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            
            # 清理断开的连接
            for ws in disconnected:
                self.script_connections[script_id].discard(ws)
        
        # 发送给全局连接
        await self._broadcast_to_global(message)
    
    async def broadcast_execution_update(
        self,
        execution_id: str,
        script_id: str,
        status: str,
        output: Optional[str] = None,
        progress: Optional[float] = None
    ):
        """
        广播执行进度更新
        """
        message = {
            "type": "execution_update",
            "execution_id": execution_id,
            "script_id": script_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if output is not None:
            message["output"] = output
        
        if progress is not None:
            message["progress"] = progress
        
        # 发送给关注该执行的连接
        if execution_id in self.execution_connections:
            disconnected = []
            for ws in self.execution_connections[execution_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            
            for ws in disconnected:
                self.execution_connections[execution_id].discard(ws)
        
        # 同时发送给关注该脚本的连接
        await self.broadcast_script_update(script_id, {
            "execution_id": execution_id,
            "status": status,
            "progress": progress
        })
    
    async def broadcast_log(self, execution_id: str, log_line: str):
        """
        广播实时日志
        """
        message = {
            "type": "log",
            "execution_id": execution_id,
            "message": log_line,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if execution_id in self.execution_connections:
            disconnected = []
            for ws in self.execution_connections[execution_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            
            for ws in disconnected:
                self.execution_connections[execution_id].discard(ws)
    
    async def _send_script_status(self, websocket: WebSocket, script_id: str):
        """
        发送脚本状态给客户端
        """
        manager = get_script_metadata_manager()
        scanner = get_scripts_scanner()
        
        # 获取脚本元数据
        script = scanner.get_script(script_id)
        status = await manager.get_script_status(script_id)
        
        message = {
            "type": "script_status",
            "script_id": script_id,
            "metadata": {
                "id": script.id if script else script_id,
                "name": script.name if script else script_id,
                "category": script.category if script else "unknown",
                "description": script.description if script else ""
            } if script else None,
            "status": {
                "current_status": status.status if status else "unknown",
                "is_running": status.is_running if status else False,
                "execution_count": status.execution_count if status else 0,
                "last_execution": status.last_execution if status else None
            } if status else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    async def _send_all_scripts_status(self, websocket: WebSocket):
        """
        发送所有脚本状态概览
        """
        manager = get_script_metadata_manager()
        scanner = get_scripts_scanner()
        
        # 扫描所有脚本
        scripts = scanner.scan_all()
        all_status = await manager.get_all_status()
        
        overview = []
        for script in scripts:
            status = all_status.get(script.id)
            overview.append({
                "id": script.id,
                "name": script.name,
                "category": script.category,
                "status": status.status if status else "idle",
                "is_running": status.is_running if status else False
            })
        
        message = {
            "type": "all_scripts_status",
            "scripts": overview,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    async def _send_execution_status(self, websocket: WebSocket, execution_id: str):
        """
        发送执行状态
        """
        manager = get_script_metadata_manager()
        record = await manager.get_execution(execution_id)
        
        if record:
            message = {
                "type": "execution_status",
                "execution_id": execution_id,
                "script_id": record.script_id,
                "status": record.status,
                "output": record.output,
                "error": record.error,
                "returncode": record.returncode,
                "duration": record.duration,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            try:
                await websocket.send_json(message)
            except Exception:
                pass
    
    async def _broadcast_to_global(self, message: dict):
        """
        广播给全局连接
        """
        disconnected = []
        for ws in self.global_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            self.global_connections.discard(ws)


# 全局 WebSocket 管理器
ws_manager = ScriptsWebSocketManager()


@router.websocket("/ws/scripts")
async def scripts_websocket(websocket: WebSocket):
    """
    脚本全局 WebSocket 连接
    接收所有脚本的更新
    """
    await ws_manager.connect_global(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            
            # 处理客户端请求
            if data.get("action") == "get_script_status":
                script_id = data.get("script_id")
                if script_id:
                    await ws_manager._send_script_status(websocket, script_id)
            
            elif data.get("action") == "subscribe_script":
                script_id = data.get("script_id")
                if script_id:
                    if script_id not in ws_manager.script_connections:
                        ws_manager.script_connections[script_id] = set()
                    ws_manager.script_connections[script_id].add(websocket)
            
            elif data.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/scripts/{script_id}")
async def script_detail_websocket(websocket: WebSocket, script_id: str):
    """
    特定脚本的 WebSocket 连接
    """
    await ws_manager.connect_script(websocket, script_id)
    
    try:
        while True:
            # 保持连接，接收心跳
            data = await websocket.receive_json()
            
            if data.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/execution/{execution_id}")
async def execution_websocket(websocket: WebSocket, execution_id: str):
    """
    执行任务的实时日志 WebSocket 连接
    """
    await ws_manager.connect_execution(websocket, execution_id)
    
    try:
        while True:
            # 保持连接
            data = await websocket.receive_json()
            
            if data.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# 辅助函数：广播执行更新
async def broadcast_execution_progress(
    execution_id: str,
    script_id: str,
    status: str,
    output: Optional[str] = None,
    progress: Optional[float] = None
):
    """
    广播执行进度（供其他模块调用）
    """
    await ws_manager.broadcast_execution_update(
        execution_id, script_id, status, output, progress
    )


async def broadcast_log_line(execution_id: str, log_line: str):
    """
    广播日志行（供其他模块调用）
    """
    await ws_manager.broadcast_log(execution_id, log_line)
