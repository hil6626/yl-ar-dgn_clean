#!/usr/bin/env python3
"""
集成测试 - 监控整合验证
测试YL-monitor对AR-backend和User GUI的监控功能
"""

import sys
import time
import requests
import unittest
from datetime import datetime

# 配置
YL_MONITOR_URL = "http://localhost:5500"
AR_BACKEND_URL = "http://localhost:5501"
USER_GUI_URL = "http://localhost:5502"

class TestMonitoringIntegration(unittest.TestCase):
    """监控整合集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n" + "="*60)
        print("集成测试 - 监控整合验证")
        print("="*60)
        print(f"测试时间: {datetime.now().isoformat()}")
        print(f"YL-Monitor: {YL_MONITOR_URL}")
        print(f"AR-Backend: {AR_BACKEND_URL}")
        print(f"User GUI: {USER_GUI_URL}")
        print("-"*60)
    
    def test_01_ar_backend_health(self):
        """测试1: AR-backend健康检查"""
        print("\n[测试1] AR-backend健康检查...")
        
        try:
            response = requests.get(
                f"{AR_BACKEND_URL}/health",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data.get('status'), 'healthy')
            self.assertEqual(data.get('service'), 'ar-backend')
            
            print(f"  ✓ 健康检查通过: {data.get('status')}")
            print(f"  ✓ 版本: {data.get('version')}")
            print(f"  ✓ 运行时间: {data.get('uptime', 'N/A')}秒")
            
        except Exception as e:
            self.fail(f"AR-backend健康检查失败: {e}")
    
    def test_02_ar_backend_status(self):
        """测试2: AR-backend状态查询"""
        print("\n[测试2] AR-backend状态查询...")
        
        try:
            response = requests.get(
                f"{AR_BACKEND_URL}/status",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # 验证关键字段
            self.assertIn('camera', data)
            self.assertIn('audio', data)
            self.assertIn('face_modules', data)
            
            print(f"  ✓ 状态查询成功")
            print(f"  ✓ 摄像头状态: {data['camera'].get('status', 'unknown')}")
            print(f"  ✓ 音频状态: {data['audio'].get('status', 'unknown')}")
            
        except Exception as e:
            self.fail(f"AR-backend状态查询失败: {e}")
    
    def test_03_ar_backend_metrics(self):
        """测试3: AR-backend性能指标"""
        print("\n[测试3] AR-backend性能指标...")
        
        try:
            response = requests.get(
                f"{AR_BACKEND_URL}/metrics",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn('system', data)
            system = data['system']
            
            print(f"  ✓ 指标查询成功")
            print(f"  ✓ CPU使用率: {system.get('cpu_percent', 'N/A')}%")
            print(f"  ✓ 内存使用率: {system.get('memory', {}).get('percent', 'N/A')}%")
            
        except Exception as e:
            self.fail(f"AR-backend性能指标查询失败: {e}")
    
    def test_04_user_gui_health(self):
        """测试4: User GUI健康检查"""
        print("\n[测试4] User GUI健康检查...")
        
        try:
            response = requests.get(
                f"{USER_GUI_URL}/health",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data.get('status'), 'healthy')
            
            print(f"  ✓ 健康检查通过: {data.get('status')}")
            print(f"  ✓ 服务: {data.get('service')}")
            
        except Exception as e:
            self.fail(f"User GUI健康检查失败: {e}")
    
    def test_05_user_gui_status(self):
        """测试5: User GUI状态查询"""
        print("\n[测试5] User GUI状态查询...")
        
        try:
            response = requests.get(
                f"{USER_GUI_URL}/status",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn('gui', data)
            
            print(f"  ✓ 状态查询成功")
            print(f"  ✓ GUI状态: {data['gui'].get('status', 'unknown')}")
            
        except Exception as e:
            self.fail(f"User GUI状态查询失败: {e}")
    
    def test_06_yl_monitor_health(self):
        """测试6: YL-monitor健康检查"""
        print("\n[测试6] YL-monitor健康检查...")
        
        try:
            response = requests.get(
                f"{YL_MONITOR_URL}/api/health",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"  ✓ 健康检查通过")
            print(f"  ✓ 状态: {data.get('status')}")
            
        except Exception as e:
            self.fail(f"YL-monitor健康检查失败: {e}")
    
    def test_07_yl_monitor_ar_nodes(self):
        """测试7: YL-monitor AR节点列表"""
        print("\n[测试7] YL-monitor AR节点列表...")
        
        try:
            response = requests.get(
                f"{YL_MONITOR_URL}/api/ar/nodes",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # 验证节点存在
            node_ids = [node.get('id') for node in data]
            self.assertIn('ar-backend', node_ids)
            self.assertIn('user-gui', node_ids)
            
            print(f"  ✓ 节点列表查询成功")
            print(f"  ✓ 节点数量: {len(data)}")
            for node in data:
                print(f"    - {node.get('id')}: {node.get('status')}")
            
        except Exception as e:
            self.fail(f"YL-monitor节点列表查询失败: {e}")
    
    def test_08_yl_monitor_ar_backend_status(self):
        """测试8: YL-monitor AR-backend状态"""
        print("\n[测试8] YL-monitor AR-backend状态...")
        
        try:
            response = requests.get(
                f"{YL_MONITOR_URL}/api/ar/nodes/ar-backend/status",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"  ✓ AR-backend状态查询成功")
            print(f"  ✓ 状态: {data.get('status')}")
            
        except Exception as e:
            self.fail(f"YL-monitor AR-backend状态查询失败: {e}")
    
    def test_09_yl_monitor_user_gui_status(self):
        """测试9: YL-monitor User GUI状态"""
        print("\n[测试9] YL-monitor User GUI状态...")
        
        try:
            response = requests.get(
                f"{YL_MONITOR_URL}/api/ar/nodes/user-gui/status",
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"  ✓ User GUI状态查询成功")
            print(f"  ✓ 状态: {data.get('status')}")
            
        except Exception as e:
            self.fail(f"YL-monitor User GUI状态查询失败: {e}")
    
    def test_10_end_to_end_monitoring(self):
        """测试10: 端到端监控流程"""
        print("\n[测试10] 端到端监控流程...")
        
        try:
            # 步骤1: 获取AR-backend直接状态
            ar_response = requests.get(
                f"{AR_BACKEND_URL}/status",
                timeout=5
            )
            self.assertEqual(ar_response.status_code, 200)
            ar_direct_status = ar_response.json().get('status')
            
            # 步骤2: 获取YL-monitor报告的AR-backend状态
            monitor_response = requests.get(
                f"{YL_MONITOR_URL}/api/ar/nodes/ar-backend/status",
                timeout=5
            )
            self.assertEqual(monitor_response.status_code, 200)
            ar_monitor_status = monitor_response.json().get('status')
            
            # 步骤3: 验证状态一致性
            self.assertEqual(
                ar_direct_status, 
                ar_monitor_status,
                "AR-backend直接状态与监控状态不一致"
            )
            
            print(f"  ✓ 端到端监控流程正常")
            print(f"  ✓ AR-backend状态一致: {ar_direct_status}")
            
        except Exception as e:
            self.fail(f"端到端监控流程测试失败: {e}")

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMonitoringIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {result.testsRun}")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 测试未通过")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
