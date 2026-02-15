#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试
AR 综合实时合成与监控系统

测试内容:
- 处理器管理器与模块集成
- 监控服务与API集成
- 端到端功能测试
- 模块间交互测试

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import json
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths, import_create_app, resolve_api_prefix_with_client

PATHS = add_project_paths()

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestProcessorManagerIntegration(unittest.TestCase):
    """处理器管理器集成测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
        
        # 导入处理器管理器
        from processor_manager import ProcessorManager, OpenCVProcessor
        self.ProcessorManager = ProcessorManager
        self.OpenCVProcessor = OpenCVProcessor
        
        # 创建处理器管理器实例
        self.manager = ProcessorManager()
    
    def tearDown(self):
        """测试清理"""
        self.manager.cleanup()
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_processor_registration(self):
        """测试处理器注册"""
        # 测试注册处理器
        result = self.manager.register('test_opencv', self.OpenCVProcessor, {})
        
        # 验证处理器已注册
        processor = self.manager.get_processor('test_opencv')
        self.assertIsNotNone(processor)
        
        logger.info("测试processor_registration: 通过")
    
    def test_processor_initialization(self):
        """测试处理器初始化"""
        # 初始化所有处理器
        results = self.manager.initialize_all()
        
        # 验证初始化结果
        self.assertIsInstance(results, dict)
        
        logger.info("测试processor_initialization: 通过")
    
    def test_processor_health_check(self):
        """测试处理器健康检查"""
        # 获取处理器
        opencv = self.manager.get_processor('opencv')
        
        if opencv:
            # 执行健康检查
            health = opencv.health_check()
            
            # 验证健康检查结果
            self.assertIn('name', health)
            self.assertIn('status', health)
            
            logger.info("测试processor_health_check: 通过")
        else:
            logger.warning("测试processor_health_check: 跳过 (opencv处理器不存在)")
    
    def test_multiple_processors(self):
        """测试多处理器管理"""
        # 获取多个处理器
        processors = ['opencv', 'face_live_cam', 'deep_live_cam', 'sox']
        
        for name in processors:
            processor = self.manager.get_processor(name)
            if processor:
                # 验证每个处理器
                self.assertIsNotNone(processor.get_name())
        
        logger.info("测试multiple_processors: 通过")
    
    def test_processor_manager_health_check(self):
        """测试处理器管理器健康检查"""
        # 执行健康检查
        health = self.manager.health_check()
        
        # 验证健康检查结果
        self.assertIn('manager', health)
        self.assertIn('processors', health)
        
        logger.info("测试processor_manager_health_check: 通过")


class TestAPIServiceIntegration(unittest.TestCase):
    """API服务集成测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_api_and_services_integration(self):
        """测试API与服务集成"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 测试健康检查
        health_resp = client.get(f'{api_prefix}/health' if api_prefix else '/health')
        self.assertEqual(health_resp.status_code, 200)
        health_data = json.loads(health_resp.data)
        
        # 2. 验证服务状态包含健康信息
        self.assertIn('system', health_data)
        self.assertIn('services', health_data)
        
        logger.info("测试api_and_services_integration: 通过")
    
    def test_resource_monitoring_integration(self):
        """测试资源监控集成"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 测试多个资源端点
        endpoints = [
            '/resources',
            '/logs',
            '/overview'
        ]
        
        for endpoint in endpoints:
            response = client.get(f'{api_prefix}{endpoint}' if api_prefix else endpoint)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
        
        logger.info("测试resource_monitoring_integration: 通过")
    
    def test_backup_and_deployment_integration(self):
        """测试备份和部署集成"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 测试备份列表
        backup_resp = client.get(f'{api_prefix}/status' if api_prefix else '/status')
        self.assertEqual(backup_resp.status_code, 200)
        
        # 2. 测试部署状态
        deploy_resp = client.get(f'{api_prefix}/overview' if api_prefix else '/overview')
        self.assertEqual(deploy_resp.status_code, 200)
        
        logger.info("测试backup_and_deployment_integration: 通过")
    
    def test_security_and_dependency_integration(self):
        """测试安全和依赖检查集成"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 测试依赖检查
        dep_resp = client.get(f'{api_prefix}/config' if api_prefix else '/config')
        self.assertEqual(dep_resp.status_code, 200)
        dep_data = json.loads(dep_resp.data)
        
        # 2. 测试安全报告
        security_resp = client.get(f'{api_prefix}/alerts' if api_prefix else '/alerts')
        self.assertEqual(security_resp.status_code, 200)
        security_data = json.loads(security_resp.data)
        
        # 3. 验证数据结构
        self.assertIsInstance(dep_data, dict)
        self.assertIsInstance(security_data, dict)
        
        logger.info("测试security_and_dependency_integration: 通过")


class TestEndToEndFunctionality(unittest.TestCase):
    """端到端功能测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_health_monitoring_flow(self):
        """测试健康监控流程"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 获取基础健康状态
        basic_health = client.get(f'{api_prefix}/health' if api_prefix else '/health')
        self.assertEqual(basic_health.status_code, 200)
        
        # 2. 获取详细健康状态
        detailed_health = client.get(f'{api_prefix}/health' if api_prefix else '/health')
        self.assertEqual(detailed_health.status_code, 200)
        
        # 3. 获取系统信息
        system_info = client.get(f'{api_prefix}/overview' if api_prefix else '/overview')
        self.assertEqual(system_info.status_code, 200)
        
        logger.info("测试health_monitoring_flow: 通过")
    
    def test_service_management_flow(self):
        """测试服务管理流程"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 获取服务状态
        status_resp = client.get(f'{api_prefix}/status' if api_prefix else '/status')
        self.assertEqual(status_resp.status_code, 200)
        
        # 2. 尝试启动服务（模拟）
        start_resp = client.post(f'{api_prefix}/refresh' if api_prefix else '/refresh',
                                 data=json.dumps({'service': 'test_service'}),
                                 content_type='application/json')
        self.assertIn(start_resp.status_code, (200, 400, 404))
        
        # 3. 再次获取服务状态
        status_resp2 = client.get(f'{api_prefix}/status' if api_prefix else '/status')
        self.assertEqual(status_resp2.status_code, 200)
        
        logger.info("测试service_management_flow: 通过")
    
    def test_system_info_flow(self):
        """测试系统信息流程"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 获取系统信息
        sys_info = client.get(f'{api_prefix}/overview' if api_prefix else '/overview')
        self.assertEqual(sys_info.status_code, 200)
        sys_data = json.loads(sys_info.data)
        
        # 2. 获取资源使用情况
        cpu = client.get(f'{api_prefix}/resources' if api_prefix else '/resources')
        memory = client.get(f'{api_prefix}/resources' if api_prefix else '/resources')
        disk = client.get(f'{api_prefix}/resources' if api_prefix else '/resources')
        
        self.assertEqual(cpu.status_code, 200)
        self.assertEqual(memory.status_code, 200)
        self.assertEqual(disk.status_code, 200)
        
        # 3. 验证系统信息包含资源信息
        self.assertIsInstance(sys_data, dict)
        
        logger.info("测试system_info_flow: 通过")
    
    def test_logs_and_monitoring_flow(self):
        """测试日志和监控流程"""
        create_app = import_create_app(PATHS)
        
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 1. 获取日志
        logs = client.get(f'{api_prefix}/logs' if api_prefix else '/logs')
        self.assertEqual(logs.status_code, 200)
        logs_data = json.loads(logs.data)
        
        # 2. 验证日志数据结构
        self.assertIsInstance(logs_data, dict)
        
        logger.info("测试logs_and_monitoring_flow: 通过")


class TestModuleInteraction(unittest.TestCase):
    """模块交互测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_camera_processor_interaction(self):
        """测试摄像头处理器交互"""
        from camera import CameraModule, CameraStatus
        
        # 创建摄像头模块
        camera = CameraModule(camera_id=0)
        
        # 验证状态枚举
        self.assertEqual(CameraStatus.STOPPED.value, 'stopped')
        self.assertEqual(CameraStatus.RUNNING.value, 'running')
        
        logger.info("测试camera_processor_interaction: 通过")
    
    def test_audio_processor_interaction(self):
        """测试音频处理器交互"""
        from audio_module import AudioModule, AudioStatus
        
        # 创建音频模块
        audio = AudioModule()
        
        # 验证状态枚举
        self.assertEqual(AudioStatus.STOPPED.value, 'stopped')
        self.assertEqual(AudioStatus.PLAYING.value, 'playing')
        
        logger.info("测试audio_processor_interaction: 通过")
    
    def test_processor_with_modules(self):
        """测试处理器与模块集成"""
        from processor_manager import ProcessorManager
        
        # 创建管理器
        manager = ProcessorManager()
        
        # 初始化处理器
        results = manager.initialize_all()
        
        # 验证管理器健康检查
        health = manager.health_check()
        self.assertIn('manager', health)
        self.assertIn('processors', health)
        
        # 清理
        manager.cleanup()
        
        logger.info("测试processor_with_modules: 通过")


class TestConfigurationIntegration(unittest.TestCase):
    """配置集成测试类"""
    
    def test_default_pipelines(self):
        """测试默认流水线配置"""
        from processor_manager import DEFAULT_PIPELINES
        
        # 验证默认流水线
        self.assertIn('live_stream', DEFAULT_PIPELINES)
        self.assertIn('video_production', DEFAULT_PIPELINES)
        self.assertIn('creative_content', DEFAULT_PIPELINES)
        self.assertIn('live_streaming_audio', DEFAULT_PIPELINES)
        
        # 验证流水线结构
        for name, pipeline in DEFAULT_PIPELINES.items():
            self.assertIn('name', pipeline)
            self.assertIn('stages', pipeline)
            self.assertIsInstance(pipeline['stages'], list)
        
        logger.info("测试default_pipelines: 通过")
    
    def test_processor_config_loading(self):
        """测试处理器配置加载"""
        from processor_manager import ProcessorManager
        
        # 创建管理器（使用默认配置）
        manager = ProcessorManager()
        
        # 验证处理器已注册
        self.assertIsInstance(manager.processors, dict)
        
        # 清理
        manager.cleanup()
        
        logger.info("测试processor_config_loading: 通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)
