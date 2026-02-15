# YL-Monitor 中文文档编写规范

**版本**: 1.0.0  
**创建时间**: 2026-02-08  
**适用范围**: 全项目所有代码文件和文档

---

## 一、文件头规范

### 1.1 必需的文件头信息

每个Python文件必须在文件开头包含以下注释块：

```python
"""
【文件功能】
简要描述文件的主要功能和职责

【作者信息】
作者: [姓名/ID]
创建时间: YYYY-MM-DD
最后更新: YYYY-MM-DD

【版本历史】
- v1.0.0 (YYYY-MM-DD): 初始版本，实现核心功能
- v1.0.1 (YYYY-MM-DD): 修复XXX问题，优化XXX性能

【依赖说明】
- 外部库: xxx
- 内部模块: xxx

【使用示例】
```python
# 示例代码
```
"""
```

### 1.2 文件头模板

```python
"""
【文件功能】
[在此描述文件的主要功能，1-2句话]

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本

【依赖说明】
- 标准库: asyncio, typing, datetime
- 第三方库: fastapi, pydantic
- 内部模块: app.models, app.utils

【使用示例】
```python
async def main():
    service = MyService()
    result = await service.process()
```
"""
```

---

## 二、类注释规范

### 2.1 类注释模板

```python
class MyClass:
    """
    【类职责】
    简要描述类的职责和用途
    
    【主要功能】
    1. 功能A: 描述功能A的作用
    2. 功能B: 描述功能B的作用
    
    【属性说明】
    - attr1 (str): 属性1的说明
    - attr2 (int): 属性2的说明
    
    【使用示例】
    ```python
    obj = MyClass(param1="value")
    result = obj.method()
    ```
    
    【注意事项】
    - 注意点1
    - 注意点2
    """
```

### 2.2 示例

```python
class CleanupManager:
    """
    【类职责】
    清理管理器，负责沉积内容清理、重复内容检测、错误恢复和队列监控
    
    【主要功能】
    1. 沉积内容清理: 自动识别并清理临时文件、日志、缓存等
    2. 重复内容检测: 检测并合并重复文件和配置
    3. 错误恢复: 提供脚本失败和系统错误的恢复策略
    4. 队列监控: 监控任务队列状态，提供拥塞告警
    
    【属性说明】
    - project_root (Path): 项目根目录路径
    - _cleanup_rules (List): 清理规则列表
    - _queue_monitors (Dict): 队列监控函数字典
    
    【使用示例】
    ```python
    manager = CleanupManager("/path/to/project")
    results = await manager.run_cleanup(dry_run=True)
    ```
    
    【注意事项】
    - 清理操作前建议先使用dry_run模式预览
    - 重要文件请添加到排除模式
    """
```

---

## 三、方法/函数注释规范

### 3.1 方法注释模板

```python
def method_name(self, param1: str, param2: int = 0) -> bool:
    """
    【方法功能】
    简要描述方法的功能
    
    【参数说明】
    - param1 (str): 参数1的说明
    - param2 (int, 可选): 参数2的说明，默认为0
    
    【返回值】
    - bool: 返回值的说明
    
    【异常说明】
    - ValueError: 参数无效时抛出
    - RuntimeError: 执行失败时抛出
    
    【使用示例】
    ```python
    result = obj.method_name("test", 10)
    ```
    """
```

### 3.2 异步方法注释

```python
async def async_method(self, data: Dict) -> List[str]:
    """
    【方法功能】
    异步处理方法，处理数据并返回结果列表
    
    【参数说明】
    - data (Dict): 输入数据字典，包含以下键：
        - key1: 键1的说明
        - key2: 键2的说明
    
    【返回值】
    - List[str]: 处理结果字符串列表
    
    【性能说明】
    - 时间复杂度: O(n)
    - 空间复杂度: O(n)
    - 典型执行时间: <100ms
    
    【使用示例】
    ```python
    data = {"key1": "value1", "key2": "value2"}
    results = await obj.async_method(data)
    ```
    """
```

---

## 四、代码块注释规范

### 4.1 复杂逻辑注释

```python
def complex_operation(self):
    """
    【方法功能】
    执行复杂的数据处理操作
    """
    # 【步骤1】数据预处理
    # 清理无效数据，统一数据格式
    cleaned_data = self._preprocess(raw_data)
    
    # 【步骤2】核心算法执行
    # 使用XXX算法进行计算，时间复杂度O(n log n)
    # 注意：此处需要保持线程安全
    result = self._core_algorithm(cleaned_data)
    
    # 【步骤3】结果后处理
    # 格式化输出，添加元数据
    formatted_result = self._postprocess(result)
    
    return formatted_result
```

### 4.2 条件判断注释

```python
def check_condition(self, value: int) -> str:
    """
    【方法功能】
    根据数值范围返回不同的状态
    """
    # 【阈值判断逻辑】
    # 0-30: 低负载，系统运行正常
    # 31-70: 中等负载，需要关注
    # 71-90: 高负载，建议优化
    # 91-100: 极高负载，需要立即处理
    if value <= 30:
        return "正常"
    elif value <= 70:
        return "关注"
    elif value <= 90:
        return "警告"
    else:
        return "紧急"
```

---

## 五、常量与配置注释

### 5.1 常量定义

```python
# 【超时配置】
# 单位：秒
# 说明：网络请求超时时间，根据网络环境调整
DEFAULT_TIMEOUT = 30
MAX_RETRY_COUNT = 3  # 最大重试次数

# 【阈值配置】
# CPU使用率告警阈值（百分比）
CPU_ALERT_THRESHOLD = 80
# 内存使用率告警阈值（百分比）
MEMORY_ALERT_THRESHOLD = 85
```

### 5.2 配置类

```python
@dataclass
class SystemConfig:
    """
    【配置类】
    系统配置参数，包含所有可配置项
    
    【配置项说明】
    - debug_mode: 调试模式开关，生产环境必须关闭
    - log_level: 日志级别，可选DEBUG/INFO/WARNING/ERROR
    - max_workers: 最大工作线程数，建议设置为CPU核心数的2倍
    """
    debug_mode: bool = False  # 【调试模式】True开启，False关闭
    log_level: str = "INFO"   # 【日志级别】控制日志输出详细程度
    max_workers: int = 4      # 【工作线程】并行处理任务数
```

---

## 六、类型注解规范

### 6.1 基本类型注解

```python
from typing import Dict, List, Optional, Union, Callable, Any

def process_data(
    data: Dict[str, Any],           # 【输入数据】字典格式
    options: Optional[List[str]] = None,  # 【选项列表】可选参数
    callback: Callable[[str], None] = None  # 【回调函数】处理完成时调用
) -> Union[str, None]:              # 【返回值】字符串或None
    """
    【方法功能】
    处理数据并返回结果
    """
    pass
```

### 6.2 复杂类型注解

```python
from typing import TypedDict, Protocol

class DataItem(TypedDict):
    """【数据项类型】单个数据项的结构定义"""
    id: int           # 【ID】唯一标识
    name: str         # 【名称】显示名称
    value: float      # 【数值】数据值
    timestamp: str    # 【时间戳】ISO格式

class Processor(Protocol):
    """【处理器协议】定义处理器接口"""
    def process(self, data: DataItem) -> bool:
        """
        【方法功能】
        处理单个数据项
        
        【参数说明】
        - data (DataItem): 数据项
        
        【返回值】
        - bool: 处理是否成功
        """
        ...
```

---

## 七、异常处理注释

### 7.1 异常抛出说明

```python
def risky_operation(self, param: str) -> Dict:
    """
    【方法功能】
    执行可能有风险的操作
    
    【参数说明】
    - param (str): 输入参数
    
    【返回值】
    - Dict: 操作结果
    
    【异常说明】
    - ValueError: 参数格式无效时抛出
    - FileNotFoundError: 文件不存在时抛出
    - PermissionError: 权限不足时抛出
    - RuntimeError: 操作执行失败时抛出
    """
    if not param:
        raise ValueError("【参数错误】参数不能为空")  # 【验证失败】
    
    try:
        result = self._execute(param)
    except FileNotFoundError as e:
        # 【文件缺失】记录错误并重新抛出
        self._log_error(f"文件未找到: {e}")
        raise
    except PermissionError:
        # 【权限不足】尝试使用备用方案
        self._log_warning("权限不足，尝试备用方案")
        result = self._fallback_execute(param)
    
    return result
```

---

## 八、文档检查清单

### 8.1 文件提交前检查

- [ ] 文件头信息完整（功能、作者、时间、版本、依赖、示例）
- [ ] 所有类包含职责说明和功能列表
- [ ] 所有公共方法包含参数、返回值、异常说明
- [ ] 复杂逻辑包含步骤注释
- [ ] 常量包含用途说明
- [ ] 类型注解完整
- [ ] 中文术语使用规范（参考术语表）

### 8.2 术语使用检查

- [ ] 使用"沉积内容"而非"垃圾文件"
- [ ] 使用"仪表盘"而非"控制面板"
- [ ] 使用"告警"而非"警报"
- [ ] 使用"脚本"而非"程序"
- [ ] 使用"节点"而非"顶点"（DAG相关）

---

## 九、工具使用

### 9.1 文档检查工具

```bash
# 检查单个文件
python scripts/tools/doc_linter.py app/services/cleanup_manager.py

# 检查整个目录
python scripts/tools/doc_linter.py app/services/ --recursive

# 生成检查报告
python scripts/tools/doc_linter.py --report docs/lint-report.md
```

### 9.2 术语检查工具

```bash
# 检查术语一致性
python scripts/tools/term_checker.py app/

# 生成术语使用报告
python scripts/tools/term_checker.py --report docs/term-report.md
```

---

## 十、附录

### 10.1 参考文档

- [术语表](./terminology-glossary.md)
- [代码风格指南](./frontend-style-guide.md)
- [API规范](./api-standard.md)

### 10.2 更新记录

| 版本 | 时间 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-02-08 | 初始版本，建立基础规范 |

---

**维护者**: AI Assistant  
**审核状态**: 待审核
