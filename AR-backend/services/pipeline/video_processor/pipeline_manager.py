"""
流水线管理器
统一管理和调度图像、视频等处理流水线
"""

import time
import logging
from enum import Enum
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """流水线阶段枚举"""
    INPUT = "input"
    PREPROCESS = "preprocess"
    PROCESS = "process"
    POSTPROCESS = "postprocess"
    OUTPUT = "output"


@dataclass
class StageResult:
    """阶段执行结果"""
    stage: str
    status: str  # 'success', 'failed', 'skipped'
    elapsed: float
    output: Optional[Any] = None
    error: Optional[str] = None


class PipelineManager:
    """
    流水线管理器
    
    用于管理和调度处理流水线，支持：
    - 多阶段流水线
    - 依赖管理
    - 执行监控
    - 错误恢复
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化流水线管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.stages: List[Dict] = []
        self.config = self._load_config(config_path)
        self.execution_history: List[Dict] = []
        
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置"""
        import yaml
        
        default_config = {
            'enabled': True,
            'timeout': 300,
            'retry': 3,
            'parallel': False,
            'max_workers': 4
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    return {**default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                return default_config
        
        return default_config
    
    def add_stage(self, name: str, handler: Callable, 
                  stage_type: PipelineStage = PipelineStage.PROCESS,
                  dependencies: List[str] = None,
                  config: Dict = None) -> bool:
        """
        添加流水线阶段
        
        Args:
            name: 阶段名称
            handler: 处理函数
            stage_type: 阶段类型
            dependencies: 依赖的阶段名称
            config: 阶段配置
            
        Returns:
            bool: 是否成功
        """
        try:
            stage = {
                'name': name,
                'handler': handler,
                'type': stage_type,
                'dependencies': dependencies or [],
                'config': config or {},
                'enabled': True
            }
            self.stages.append(stage)
            logger.info(f"Added pipeline stage: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add stage {name}: {e}")
            return False
    
    def remove_stage(self, name: str) -> bool:
        """移除流水线阶段"""
        for i, stage in enumerate(self.stages):
            if stage['name'] == name:
                self.stages.pop(i)
                logger.info(f"Removed pipeline stage: {name}")
                return True
        return False
    
    def get_stage(self, name: str) -> Optional[Dict]:
        """获取阶段信息"""
        for stage in self.stages:
            if stage['name'] == name:
                return stage
        return None
    
    def execute(self, input_data: Any, 
                stage_name: str = None) -> Dict[str, Any]:
        """
        执行流水线
        
        Args:
            input_data: 输入数据
            stage_name: 可选，只执行特定阶段
            
        Returns:
            Dict: 执行结果
        """
        start_time = time.time()
        results = []
        current = input_data
        
        # 确定要执行的阶段
        stages_to_execute = self.stages
        if stage_name:
            stages_to_execute = [s for s in self.stages if s['name'] == stage_name]
            if not stages_to_execute:
                return {
                    'success': False,
                    'error': f"Stage not found: {stage_name}"
                }
        
        # 按依赖顺序排序
        sorted_stages = self._topological_sort(stages_to_execute)
        
        # 执行各阶段
        for stage in sorted_stages:
            if not stage['enabled']:
                results.append(StageResult(
                    stage=stage['name'],
                    status='skipped',
                    elapsed=0
                ))
                continue
            
            stage_start = time.time()
            try:
                # 检查依赖
                if not self._check_dependencies(stage, results):
                    results.append(StageResult(
                        stage=stage['name'],
                        status='skipped',
                        elapsed=0,
                        error='Dependencies not met'
                    ))
                    continue
                
                # 执行处理函数
                current = stage['handler'](current)
                elapsed = time.time() - stage_start
                
                results.append(StageResult(
                    stage=stage['name'],
                    status='success',
                    elapsed=elapsed,
                    output=current
                ))
                
            except Exception as e:
                elapsed = time.time() - stage_start
                logger.error(f"Stage {stage['name']} failed: {e}")
                results.append(StageResult(
                    stage=stage['name'],
                    status='failed',
                    elapsed=elapsed,
                    error=str(e)
                ))
                
                # 如果配置了重试
                if stage['config'].get('retry', 0) > 0:
                    for retry in range(stage['config']['retry']):
                        try:
                            time.sleep(stage['config'].get('retry_delay', 1))
                            current = stage['handler'](current)
                            results[-1] = StageResult(
                                stage=stage['name'],
                                status='success',
                                elapsed=time.time() - stage_start,
                                output=current
                            )
                            break
                        except Exception as retry_e:
                            logger.warning(f"Retry {retry + 1} failed: {retry_e}")
        
        elapsed_total = time.time() - start_time
        
        result = {
            'input': input_data,
            'results': [
                {'stage': r.stage, 'status': r.status, 'elapsed': r.elapsed, 
                 'output': str(r.output)[:100] if r.output else None,
                 'error': r.error}
                for r in results
            ],
            'success': all(r.status == 'success' for r in results if r.status != 'skipped'),
            'total_elapsed': elapsed_total
        }
        
        self.execution_history.append(result)
        
        return result
    
    def _topological_sort(self, stages: List[Dict]) -> List[Dict]:
        """拓扑排序，按依赖顺序排列阶段"""
        if not stages:
            return []
        
        # 构建依赖图
        deps = {s['name']: set(s['dependencies']) for s in stages}
        
        # 找出没有依赖的阶段
        result = []
        remaining = {s['name']: s for s in stages}
        
        while remaining:
            # 找出所有依赖都已完成的阶段
            ready = [s for s in remaining.values() 
                    if all(d not in remaining for d in s['dependencies'])]
            
            if not ready:
                # 存在循环依赖
                logger.warning("Circular dependency detected")
                break
            
            # 按依赖数量排序
            ready.sort(key=lambda x: len(x['dependencies']))
            
            for stage in ready:
                result.append(stage)
                remaining.pop(stage['name'])
        
        return result
    
    def _check_dependencies(self, stage: Dict, results: List[StageResult]) -> bool:
        """检查阶段依赖是否满足"""
        for dep in stage['dependencies']:
            dep_result = next((r for r in results if r.stage == dep), None)
            if dep_result and dep_result.status != 'success':
                return False
        return True
    
    def get_status(self) -> Dict:
        """获取流水线状态"""
        return {
            'total_stages': len(self.stages),
            'enabled_stages': len([s for s in self.stages if s['enabled']]),
            'execution_count': len(self.execution_history),
            'success_rate': self._calculate_success_rate(),
            'stages': [
                {
                    'name': s['name'],
                    'type': s['type'].value,
                    'enabled': s['enabled'],
                    'dependencies': s['dependencies']
                }
                for s in self.stages
            ]
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.execution_history:
            return 1.0
        
        successes = sum(1 for h in self.execution_history if h['success'])
        return successes / len(self.execution_history)
    
    def reset(self):
        """重置流水线"""
        self.execution_history.clear()
        logger.info("Pipeline manager reset")


# 便捷函数：创建基本流水线
def create_basic_pipeline(config_path: str = None) -> PipelineManager:
    """创建基本流水线管理器"""
    return PipelineManager(config_path)
