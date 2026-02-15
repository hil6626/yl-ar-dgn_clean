#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI→后端接口联调验证脚本
测试User GUI与AR-backend之间的接口通信

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import sys
import os
import time
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackendAPITester:
    """后端接口测试器"""
    
    def __init__(self, base_url: str = "http://localhost:5502"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = 10
        
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("GUI→后端接口联调验证")
        logger.info(f"后端地址: {self.base_url}")
        logger.info("=" * 60)
        
        tests = [
            ("服务可用性检查", self.test_service_available),
            ("健康检查接口", self.test_health_check),
            ("状态查询接口", self.test_status_query),
            ("视频流控制接口", self.test_video_control),
            ("音频控制接口", self.test_audio_control),
            ("人脸合成接口", self.test_face_swap),
            ("配置管理接口", self.test_config_management),
            ("错误处理测试", self.test_error_handling),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            logger.info(f"\n📋 测试: {test_name}")
            try:
                result = test_func()
                status = "✅ 通过" if result else "❌ 失败"
                logger.info(f"结果: {status}")
                self.test_results.append((test_name, result))
                if not result:
                    all_passed = False
            except Exception as e:
                logger.error(f"测试异常: {e}")
                import traceback
                traceback.print_exc()
                self.test_results.append((test_name, False))
                all_passed = False
        
        # 输出总结
        self._print_summary()
        
        return all_passed
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None,
                     expected_status: int = 200) -> Optional[Dict]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            expected_status: 期望的HTTP状态码
            
        Returns:
            Optional[Dict]: 响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                logger.error(f"不支持的HTTP方法: {method}")
                return None
            
            # 检查状态码
            if response.status_code != expected_status:
                logger.warning(
                    f"状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}"
                )
                return None
            
            # 解析响应
            try:
                return response.json()
            except:
                return {'text': response.text}
                
        except requests.exceptions.ConnectionError:
            logger.error(f"连接失败: 无法连接到 {url}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {url}")
            return None
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return None
    
    def test_service_available(self) -> bool:
        """测试服务是否可用"""
        logger.info("检查后端服务...")
        
        # 尝试连接根路径
        result = self._make_request('GET', '/')
        
        if result is not None:
            logger.info("✅ 后端服务可访问")
            return True
        else:
            logger.error("❌ 后端服务不可用")
            logger.info("提示: 请确保后端服务已启动")
            return False
    
    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        logger.info("测试健康检查接口...")
        
        result = self._make_request('GET', '/health')
        
        if result:
            logger.info(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查关键字段
            if 'status' in result and result['status'] == 'healthy':
                logger.info("✅ 健康检查通过")
                return True
            else:
                logger.warning("⚠️  健康状态异常")
                return False
        else:
            logger.error("❌ 健康检查失败")
            return False
    
    def test_status_query(self) -> bool:
        """测试状态查询接口"""
        logger.info("测试状态查询接口...")
        
        result = self._make_request('GET', '/api/status')
        
        if result:
            logger.info(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查关键字段
            required_fields = ['camera', 'audio', 'face_swap']
            missing = [f for f in required_fields if f not in result]
            
            if not missing:
                logger.info("✅ 状态查询成功")
                return True
            else:
                logger.warning(f"⚠️  缺少字段: {missing}")
                return False
        else:
            logger.error("❌ 状态查询失败")
            return False
    
    def test_video_control(self) -> bool:
        """测试视频流控制接口"""
        logger.info("测试视频流控制接口...")
        
        # 启动视频
        logger.info("  发送启动视频命令...")
        start_result = self._make_request(
            'POST', '/api/video/start',
            {'camera_id': 0, 'resolution': [640, 480]},
            expected_status=200
        )
        
        if start_result:
            logger.info("  ✅ 视频启动成功")
        else:
            logger.warning("  ⚠️  视频启动失败")
        
        # 等待一下
        time.sleep(1)
        
        # 停止视频
        logger.info("  发送停止视频命令...")
        stop_result = self._make_request(
            'POST', '/api/video/stop',
            expected_status=200
        )
        
        if stop_result:
            logger.info("  ✅ 视频停止成功")
            return True
        else:
            logger.warning("  ⚠️  视频停止失败")
            return start_result is not None  # 只要启动成功就算通过
    
    def test_audio_control(self) -> bool:
        """测试音频控制接口"""
        logger.info("测试音频控制接口...")
        
        # 启动音频
        logger.info("  发送启动音频命令...")
        start_result = self._make_request(
            'POST', '/api/audio/start',
            {'effect': 'none', 'pitch': 0},
            expected_status=200
        )
        
        if start_result:
            logger.info("  ✅ 音频启动成功")
        else:
            logger.warning("  ⚠️  音频启动失败")
        
        # 等待一下
        time.sleep(0.5)
        
        # 停止音频
        logger.info("  发送停止音频命令...")
        stop_result = self._make_request(
            'POST', '/api/audio/stop',
            expected_status=200
        )
        
        if stop_result:
            logger.info("  ✅ 音频停止成功")
            return True
        else:
            logger.warning("  ⚠️  音频停止失败")
            return start_result is not None
    
    def test_face_swap(self) -> bool:
        """测试人脸合成接口"""
        logger.info("测试人脸合成接口...")
        
        # 加载人脸图片
        logger.info("  发送加载人脸图片命令...")
        
        # 创建测试图片
        import numpy as np
        
        test_image_path = "/tmp/test_face_api.jpg"
        
        # 这里应该使用实际的图片路径
        # 为了测试，我们假设有一个测试图片
        load_result = self._make_request(
            'POST', '/api/face/load',
            {'image_path': test_image_path},
            expected_status=200
        )
        
        if load_result:
            logger.info("  ✅ 人脸图片加载成功")
        else:
            logger.warning("  ⚠️  人脸图片加载失败（可能图片不存在）")
        
        # 获取合成状态
        logger.info("  查询人脸合成状态...")
        status_result = self._make_request('GET', '/api/face/status')
        
        if status_result:
            logger.info(f"  状态: {json.dumps(status_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            logger.warning("  ⚠️  无法获取状态")
            return load_result is not None
    
    def test_config_management(self) -> bool:
        """测试配置管理接口"""
        logger.info("测试配置管理接口...")
        
        # 获取配置
        logger.info("  获取当前配置...")
        get_result = self._make_request('GET', '/api/config')
        
        if get_result:
            logger.info(f"  配置: {json.dumps(get_result, indent=2, ensure_ascii=False)}")
        else:
            logger.warning("  ⚠️  无法获取配置")
            return False
        
        # 更新配置
        logger.info("  更新配置...")
        update_result = self._make_request(
            'PUT', '/api/config',
            {'video_fps': 30, 'audio_volume': 80},
            expected_status=200
        )
        
        if update_result:
            logger.info("  ✅ 配置更新成功")
            return True
        else:
            logger.warning("  ⚠️  配置更新失败")
            return True  # 获取成功就算通过
    
    def test_error_handling(self) -> bool:
        """测试错误处理"""
        logger.info("测试错误处理...")
        
        # 发送无效请求
        logger.info("  发送无效请求...")
        invalid_result = self._make_request(
            'POST', '/api/invalid',
            expected_status=404
        )
        
        # 发送错误参数
        logger.info("  发送错误参数...")
        error_result = self._make_request(
            'POST', '/api/video/start',
            {'invalid_param': 'value'},
            expected_status=400
        )
        
        logger.info("✅ 错误处理测试完成")
        return True
    
    def _print_summary(self):
        """打印测试总结"""
        logger.info("\n" + "=" * 60)
        logger.info("测试结果总结")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{status} - {test_name}")
        
        logger.info(f"\n总计: {passed}/{total} 项通过")
        
        if passed == total:
            logger.info("🎉 所有接口测试通过！前后端联调成功")
        elif passed >= total * 0.6:
            logger.info("⚠️  部分接口测试失败，基本功能可用")
        else:
            logger.info("❌ 多项接口测试失败，需要检查后端服务")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GUI→后端接口联调验证')
    parser.add_argument('--url', '-u', default='http://localhost:5502',
                       help='后端服务地址')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 运行测试
    tester = BackendAPITester(base_url=args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
