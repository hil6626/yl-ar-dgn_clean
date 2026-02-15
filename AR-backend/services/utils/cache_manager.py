#!/usr/bin/env python3
"""
缓存管理处理器 - 业务逻辑实现
被路由调度器调用，不直接暴露接口
"""

import logging
import os
import shutil
from datetime import datetime

class CacheManagerService:
    """缓存管理业务逻辑"""

    def __init__(self, cache_directories=None):
        self.logger = logging.getLogger(__name__)
        self.cache_directories = cache_directories or [
            '/tmp/ar_cache',
            'cache',
            '.cache'
        ]

    def clear_cache(self):
        """清除缓存"""
        self.logger.info("清除缓存")
        cleared_stats = {}
        
        for cache_dir in self.cache_directories:
            if os.path.exists(cache_dir):
                try:
                    # 获取清除前的大小
                    size_before = self._get_directory_size(cache_dir)
                    
                    # 清除目录内容
                    for filename in os.listdir(cache_dir):
                        file_path = os.path.join(cache_dir, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception as e:
                            self.logger.warning(f"删除 {file_path} 失败: {str(e)}")
                    
                    # 获取清除后的大小
                    size_after = self._get_directory_size(cache_dir)
                    
                    cleared_stats[cache_dir] = {
                        'cleared': size_before - size_after,
                        'remaining': size_after,
                        'status': 'success'
                    }
                except Exception as e:
                    self.logger.error(f"清除缓存目录 {cache_dir} 失败: {str(e)}")
                    cleared_stats[cache_dir] = {
                        'cleared': 0,
                        'remaining': 0,
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                cleared_stats[cache_dir] = {
                    'cleared': 0,
                    'remaining': 0,
                    'status': 'not_found'
                }
        
        return {
            'stats': cleared_stats,
            'timestamp': datetime.now().isoformat()
        }

    def _get_directory_size(self, directory):
        """获取目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
        except Exception as e:
            self.logger.warning(f"计算目录 {directory} 大小失败: {str(e)}")
        return total_size

    def get_cache_stats(self):
        """获取缓存统计信息"""
        stats = {}
        for cache_dir in self.cache_directories:
            if os.path.exists(cache_dir):
                size = self._get_directory_size(cache_dir)
                file_count = len([f for f in os.listdir(cache_dir) 
                                if os.path.isfile(os.path.join(cache_dir, f))])
                stats[cache_dir] = {
                    'size': size,
                    'file_count': file_count
                }
            else:
                stats[cache_dir] = {
                    'size': 0,
                    'file_count': 0
                }
        
        return {
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
