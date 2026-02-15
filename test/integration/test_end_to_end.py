#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端测试"""

import unittest
import sys
from pathlib import Path
from typing import Dict, Any

TEST_DIR: Path = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()

from system_integrator.system_integrator import SystemIntegrator


class EndToEndTest(unittest.TestCase):
    """端到端测试类"""

    def setUp(self) -> None:
        """测试前准备"""
        self.integrator: SystemIntegrator = None

    def tearDown(self) -> None:
        """测试后清理"""
        if self.integrator:
            try:
                # 清理资源
                pass
            except Exception:
                pass

    def test_system_integrator_status(self) -> None:
        """测试系统集成器状态"""
        try:
            self.integrator = SystemIntegrator({})
            self.assertTrue(self.integrator.initialize(), "系统集成器初始化失败")

            status: Dict[str, Any] = self.integrator.get_system_status()
            self.assertIn('initialized', status, "状态中缺少初始化字段")
            self.assertTrue(status['initialized'], "系统集成器未正确初始化")
        except Exception as e:
            self.fail(f"系统集成器状态测试失败: {e}")


if __name__ == '__main__':
    unittest.main()
