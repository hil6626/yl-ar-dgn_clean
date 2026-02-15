#!/usr/bin/env python3
"""
AR 系统监控应用 - 后端路由调度器（重构版）
核心原则：不做业务逻辑 → 只做接口路由 + 调度
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class MonitorRouter:
    """监控路由调度器 - 只负责路由和调度，不做业务逻辑"""

    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        self.setup_routes()

    def setup_routes(self):
        """设置路由 - 只做调度"""

        @self.app.route('/api/v1/health')
        def health_check():
            """健康检查 - 调度到健康检查服务"""
            return self._dispatch_to_service('health_check', {})

        @self.app.route('/api/v1/system/metrics')
        def system_metrics():
            """系统指标 - 调度到系统监控服务"""
            return self._dispatch_to_service('system_metrics', {})

        @self.app.route('/api/v1/deployment/progress')
        def deployment_progress():
            """部署进度 - 调度到部署跟踪服务"""
            return self._dispatch_to_service('deployment_progress', {})

        @self.app.route('/api/v1/logs/recent')
        def recent_logs():
            """最近日志 - 调度到日志服务"""
            params = {
                'limit': request.args.get('limit', 30, type=int),
                'level': request.args.get('level')
            }
            return self._dispatch_to_service('recent_logs', params)

        @self.app.route('/api/v1/alerts/active')
        def active_alerts():
            """活跃告警 - 调度到告警服务"""
            return self._dispatch_to_service('active_alerts', {})

        @self.app.route('/api/v1/scripts/execute', methods=['POST'])
        def execute_script():
            """执行脚本 - 调度到脚本管理器"""
            data = request.get_json()
            return self._dispatch_to_service('execute_script', data)

        @self.app.route('/api/v1/cache/clear', methods=['POST'])
        def clear_cache():
            """清除缓存 - 调度到缓存管理服务"""
            return self._dispatch_to_service('clear_cache', {})

        # 新增的路由
        @self.app.route('/api/v1/modules/status')
        def modules_status():
            """模块状态 - 调度到模块状态服务"""
            return self._dispatch_to_service('modules_status', {})

        @self.app.route('/api/v1/config/system')
        def system_config():
            """系统配置 - 调度到配置服务"""
            return self._dispatch_to_service('system_config', {})

    def _dispatch_to_service(self, service_name, params):
        """调度到具体服务 - 核心调度逻辑"""
        try:
            # 记录调度请求
            self.logger.info(f"调度服务: {service_name}, 参数: {params}")

            # 根据服务名称调度到不同处理器
            result = self._route_to_processor(service_name, params)

            # 统一返回格式
            response = self._create_response('success', result, service_name)

            return jsonify(response)

        except Exception as e:
            self.logger.error(f"服务调度失败: {service_name}, 错误: {str(e)}")
            return jsonify(self._create_response('error', str(e), service_name)), 500

    def _route_to_processor(self, service_name, params):
        """路由到具体处理器 - 不包含业务逻辑"""
        processors = {
            'health_check': self._call_health_processor,
            'system_metrics': self._call_system_processor,
            'deployment_progress': self._call_deployment_processor,
            'recent_logs': self._call_log_processor,
            'active_alerts': self._call_alert_processor,
            'execute_script': self._call_script_processor,
            'clear_cache': self._call_cache_processor,
            'modules_status': self._call_modules_processor,
            'system_config': self._call_config_processor
        }

        processor = processors.get(service_name)
        if not processor:
            raise ValueError(f"未知服务: {service_name}")

        return processor(params)

    def _call_health_processor(self, params):
        """调用健康检查处理器"""
        from services.health_check_service import HealthCheckService
        service = HealthCheckService()
        return service.perform_check()

    def _call_system_processor(self, params):
        """调用系统监控处理器"""
        from services.system_monitor_service import SystemMonitorService
        service = SystemMonitorService()
        return service.get_system_metrics()

    def _call_deployment_processor(self, params):
        """调用部署进度处理器"""
        from services.deployment_tracker_service import DeploymentTrackerService
        service = DeploymentTrackerService()
        return service.get_deployment_progress()

    def _call_log_processor(self, params):
        """调用日志处理器"""
        from services.log_collector_service import LogCollectorService
        service = LogCollectorService()
        limit = params.get('limit', 30)
        level = params.get('level')
        return service.get_recent_logs(limit, level)

    def _call_alert_processor(self, params):
        """调用告警处理器"""
        from services.alert_collector_service import AlertCollectorService
        service = AlertCollectorService()
        return service.get_active_alerts()

    def _call_script_processor(self, params):
        """调用脚本执行处理器"""
        from services.script_executor_service import ScriptExecutorService
        service = ScriptExecutorService()
        script_id = params.get('script_id')
        if not script_id:
            raise ValueError("缺少 script_id 参数")
        return service.execute_script(script_id)

    def _call_cache_processor(self, params):
        """调用缓存清理处理器"""
        from services.cache_manager_service import CacheManagerService
        service = CacheManagerService()
        return service.clear_cache()

    def _call_modules_processor(self, params):
        """调用模块状态处理器"""
        from services.module_status_service import ModuleStatusService
        service = ModuleStatusService()
        return service.get_modules_status()

    def _call_config_processor(self, params):
        """调用配置服务处理器"""
        from services.config_service import ConfigService
        service = ConfigService()
        return service.get_system_config()

    def _create_response(self, status, data, service_name):
        """创建统一响应格式"""
        return {
            'status': status,
            'data': data,
            'error': '' if status == 'success' else data,
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'meta': {
                'version': '1.0',
                'request_id': self._generate_request_id()
            }
        }

    def _generate_request_id(self):
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())

class WebSocketDispatcher:
    """WebSocket 事件调度器"""

    def __init__(self, socketio, router):
        self.socketio = socketio
        self.router = router
        self.setup_events()

    def setup_events(self):
        """设置 WebSocket 事件"""

        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {'message': '已连接到监控服务'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            pass

        @self.socketio.on('request_update')
        def handle_update_request(data):
            """处理更新请求 - 调度到对应服务"""
            update_type = data.get('type', 'all')

            try:
                if update_type in ['health', 'all']:
                    result = self.router._call_health_processor({})
                    emit('health_update', result)

                if update_type in ['system', 'all']:
                    result = self.router._call_system_processor({})
                    emit('system_update', result)

                if update_type in ['deployment', 'all']:
                    result = self.router._call_deployment_processor({})
                    emit('deployment_update', result)

                if update_type in ['logs', 'all']:
                    result = self.router._call_log_processor({'limit': 10})
                    emit('log_update', result)

                if update_type in ['alerts', 'all']:
                    result = self.router._call_alert_processor({})
                    emit('alert_update', result)

                if update_type in ['modules', 'all']:
                    result = self.router._call_modules_processor({})
                    emit('modules_update', result)

            except Exception as e:
                emit('error', {'message': str(e)})

class ARMonitorApp:
    """AR 系统监控应用 - 纯路由调度器"""

    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'ar-monitor-secret-key-2026'

        # 启用 CORS
        CORS(self.app)

        # 初始化 SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # 初始化路由调度器
        self.router = MonitorRouter(self.app, self.socketio)

        # 初始化 WebSocket 调度器
        self.ws_dispatcher = WebSocketDispatcher(self.socketio, self.router)

        # 设置日志
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ARMonitorApp')

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """启动应用"""
        self.logger.info(f"启动 AR 监控服务 (路由调度模式) - {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

# 工厂函数
def create_app():
    """创建应用实例"""
    return ARMonitorApp()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
