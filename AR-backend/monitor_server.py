#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR-backend 监控服务
提供健康检查、状态查询、性能指标等HTTP API
"""

import sys
import os
import time
import psutil
import yaml
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)

# 加载配置
config_path = project_root / "monitor_config.yaml"
if config_path.exists():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
else:
    config = {
        "host": "0.0.0.0",
        "port": 5501,
        "debug": False,
        "log_level": "INFO",
        "cors": {"enabled": True, "origins": ["*"]},
        "security": {"api_key_enabled": False, "api_key": ""}
    }

# 配置CORS - 从配置文件读取允许的域名
cors_config = config.get('cors', {})
cors_origins = cors_config.get('origins', ["*"]) if cors_config.get('enabled', True) else ["*"]
CORS(app, resources={r"/*": {"origins": cors_origins}})

# API认证配置
security_config = config.get('security', {})
API_KEY_ENABLED = security_config.get('api_key_enabled', False)
API_KEY = security_config.get('api_key', '').replace('${MONITOR_API_KEY}', os.environ.get('MONITOR_API_KEY', ''))

# 服务状态
service_status = {
    "start_time": datetime.utcnow().isoformat(),
    "last_health_check": None,
    "camera_status": "unknown",
    "audio_status": "unknown",
    "face_modules": {}
}


def get_system_metrics():
    """获取系统性能指标"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


def check_camera_status():
    """检查摄像头状态"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                return {
                    "status": "available",
                    "resolution": f"{width}x{height}"
                }
        return {"status": "unavailable", "error": "无法打开摄像头"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_audio_status():
    """检查音频状态"""
    try:
        # 这里可以集成实际的音频检查
        return {"status": "available", "devices": []}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_face_modules():
    """检查人脸合成模块状态"""
    modules = {}
    module_paths = {
        "deep_live_cam": project_root / "integrations" / "Deep-Live-Cam",
        "deepface_lab": project_root / "integrations" / "DeepFaceLab",
        "faceswap": project_root / "integrations" / "faceswap"
    }
    
    for name, path in module_paths.items():
        modules[name] = {
            "available": path.exists(),
            "path": str(path)
        }
    
    return modules


def require_api_key(f):
    """API密钥验证装饰器"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_KEY_ENABLED:
            return f(*args, **kwargs)
        
        # 从请求头获取API密钥
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key or api_key != API_KEY:
            abort(401, description="无效的API密钥")
        
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    返回服务基本健康状态
    """
    service_status['last_health_check'] = datetime.utcnow().isoformat()
    
    start_time = datetime.fromisoformat(
        service_status['start_time'].replace('Z', '+00:00')
    )
    uptime = time.time() - start_time.timestamp()
    
    return jsonify({
        "status": "healthy",
        "service": "ar-backend",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": uptime,
        "api_auth_enabled": API_KEY_ENABLED
    })


@app.route('/status', methods=['GET'])
@require_api_key
def status():
    """
    详细状态查询端点
    返回各组件详细状态
    """
    service_status['camera_status'] = check_camera_status()
    service_status['audio_status'] = check_audio_status()
    service_status['face_modules'] = check_face_modules()
    
    return jsonify({
        "service": "ar-backend",
        "version": "2.0.0",
        "status": "running",
        "start_time": service_status['start_time'],
        "camera": service_status['camera_status'],
        "audio": service_status['audio_status'],
        "face_modules": service_status['face_modules'],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route('/metrics', methods=['GET'])
@require_api_key
def metrics():
    """
    性能指标端点
    返回系统性能指标
    """
    return jsonify({
        "service": "ar-backend",
        "system": get_system_metrics(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    """启动摄像头（预留接口）"""
    return jsonify({
        "status": "success",
        "message": "摄像头启动命令已接收",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """停止摄像头（预留接口）"""
    return jsonify({
        "status": "success",
        "message": "摄像头停止命令已接收",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "error": "Not Found",
        "message": "请求的接口不存在",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 500


if __name__ == '__main__':
    print("[*] AR-backend 监控服务启动中...")
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 5501)
    print(f"[*] 监听地址: {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=config.get('debug', False),
        threaded=True
    )
