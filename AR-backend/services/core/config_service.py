#!/usr/bin/env python3
"""
配置服务处理器 - 业务逻辑实现
被路由调度器调用，不直接暴露接口
"""

import logging
import json
import os
from datetime import datetime

class ConfigService:
    """配置服务业务逻辑"""

    def __init__(self, config_files=None):
        self.logger = logging.getLogger(__name__)
        self.config_files = config_files or [
            'config/app_config.json',
            'config/database_config.json',
            'config/logging_config.yaml',
            'config/monitoring_config.json',
            'config/security_config.json',
            'config/version.json'
        ]

    def get_system_config(self):
        """获取系统配置"""
        self.logger.info("获取系统配置")
        config_data = {}
        
        for config_file in self.config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        if config_file.endswith('.json'):
                            config_data[os.path.basename(config_file)] = json.load(f)
                        elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                            # 这里简化处理，实际应用中需要解析YAML
                            config_data[os.path.basename(config_file)] = f.read()
                        else:
                            config_data[os.path.basename(config_file)] = f.read()
                except Exception as e:
                    self.logger.error(f"读取配置文件 {config_file} 失败: {str(e)}")
                    config_data[os.path.basename(config_file)] = {'error': str(e)}
            else:
                config_data[os.path.basename(config_file)] = {'status': 'not_found'}
        
        return {
            'config': config_data,
            'timestamp': datetime.now().isoformat()
        }

    def get_config_summary(self):
        """获取配置摘要"""
        summary = {}
        for config_file in self.config_files:
            if os.path.exists(config_file):
                try:
                    stat = os.stat(config_file)
                    summary[os.path.basename(config_file)] = {
                        'exists': True,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'permissions': oct(stat.st_mode)[-3:]
                    }
                except Exception as e:
                    summary[os.path.basename(config_file)] = {
                        'exists': True,
                        'error': str(e)
                    }
            else:
                summary[os.path.basename(config_file)] = {
                    'exists': False
                }
        
        return {
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }

    def validate_config(self):
        """验证配置"""
        validation_results = {}
        
        # 验证必需的配置文件
        required_configs = ['config/app_config.json', 'config/version.json']
        for config_file in required_configs:
            validation_results[config_file] = {
                'exists': os.path.exists(config_file),
                'valid': self._validate_config_file(config_file)
            }
        
        return {
            'validation': validation_results,
            'timestamp': datetime.now().isoformat()
        }

    def _validate_config_file(self, config_file):
        """验证配置文件"""
        if not os.path.exists(config_file):
            return False
            
        try:
            if config_file.endswith('.json'):
                with open(config_file, 'r') as f:
                    json.load(f)  # 尝试解析JSON
            return True
        except Exception:
            return False
