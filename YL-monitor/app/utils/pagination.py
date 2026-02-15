"""
分页优化工具

功能:
- 游标分页 (Cursor-based Pagination)
- 偏移分页 (Offset Pagination)
- 字段筛选
- 批量操作支持

作者: AI Assistant
版本: 1.0.0
"""

import base64
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, Callable, Union
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PaginationType(str, Enum):
    """分页类型"""
    OFFSET = "offset"    # 传统偏移分页
    CURSOR = "cursor"    # 游标分页 (推荐大数据量)


@dataclass
class PageInfo:
    """分页信息"""
    has_next_page: bool = False
    has_previous_page: bool = False
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
    total_count: Optional[int] = None  # 游标分页时可能为None


@dataclass
class PaginatedResult(Generic[T]):
    """分页结果"""
    items: List[T]
    page_info: PageInfo
    pagination_type: PaginationType
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "items": self.items,
            "page_info": {
                "has_next_page": self.page_info.has_next_page,
                "has_previous_page": self.page_info.has_previous_page,
                "start_cursor": self.page_info.start_cursor,
                "end_cursor": self.page_info.end_cursor,
                "total_count": self.page_info.total_count,
            },
            "pagination_type": self.pagination_type.value,
        }


class CursorEncoder:
    """游标编码器"""
    
    @staticmethod
    def encode(data: Dict[str, Any]) -> str:
        """编码游标"""
        try:
            json_str = json.dumps(data, sort_keys=True)
            return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip('=')
        except Exception as e:
            logger.error(f"游标编码失败: {e}")
            return ""
    
    @staticmethod
    def decode(cursor: str) -> Optional[Dict[str, Any]]:
        """解码游标"""
        try:
            # 添加填充
            padding = 4 - len(cursor) % 4
            if padding != 4:
                cursor += '=' * padding
            
            json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"游标解码失败: {e}")
            return None


class OffsetPaginator(Generic[T]):
    """
    偏移分页器
    
    适用于中小数据量，简单直观
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.max_page_size = max_page_size
    
    def get_offset(self) -> int:
        """获取偏移量"""
        return (self.page - 1) * self.page_size
    
    def get_limit(self) -> int:
        """获取限制数"""
        return self.page_size
    
    def paginate(
        self,
        items: List[T],
        total_count: int
    ) -> PaginatedResult[T]:
        """执行分页"""
        # 计算分页信息
        total_pages = (total_count + self.page_size - 1) // self.page_size
        has_next = self.page < total_pages
        has_previous = self.page > 1
        
        page_info = PageInfo(
            has_next_page=has_next,
            has_previous_page=has_previous,
            total_count=total_count
        )
        
        return PaginatedResult(
            items=items,
            page_info=page_info,
            pagination_type=PaginationType.OFFSET
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "page": self.page,
            "page_size": self.page_size,
            "offset": self.get_offset(),
        }


class CursorPaginator(Generic[T]):
    """
    游标分页器
    
    适用于大数据量，性能优秀，无偏移问题
    """
    
    def __init__(
        self,
        cursor: Optional[str] = None,
        page_size: int = 20,
        max_page_size: int = 100,
        sort_field: str = "id",
        sort_direction: str = "desc"
    ):
        self.cursor = cursor
        self.page_size = min(max(1, page_size), max_page_size)
        self.max_page_size = max_page_size
        self.sort_field = sort_field
        self.sort_direction = sort_direction.lower()
        
        # 解码游标
        self.cursor_data: Optional[Dict[str, Any]] = None
        if cursor:
            self.cursor_data = CursorEncoder.decode(cursor)
    
    def get_filter_condition(self) -> Optional[Dict[str, Any]]:
        """获取过滤条件"""
        if not self.cursor_data:
            return None
        
        # 构建游标过滤条件
        cursor_value = self.cursor_data.get(self.sort_field)
        if cursor_value is None:
            return None
        
        operator = "lt" if self.sort_direction == "desc" else "gt"
        return {
            "field": self.sort_field,
            "operator": operator,
            "value": cursor_value
        }
    
    def create_cursor(self, item: Dict[str, Any]) -> str:
        """为项目创建游标"""
        cursor_data = {
            self.sort_field: item.get(self.sort_field)
        }
        return CursorEncoder.encode(cursor_data)
    
    def paginate(
        self,
        items: List[T],
        has_more: bool = False
    ) -> PaginatedResult[T]:
        """执行分页"""
        # 创建游标
        start_cursor = None
        end_cursor = None
        
        if items:
            if isinstance(items[0], dict):
                start_cursor = self.create_cursor(items[0])
                end_cursor = self.create_cursor(items[-1])
            else:
                # 假设对象有to_dict方法或属性访问
                try:
                    first_item = items[0]
                    last_item = items[-1]
                    
                    if hasattr(first_item, 'dict'):
                        start_cursor = self.create_cursor(first_item.dict())
                        end_cursor = self.create_cursor(last_item.dict())
                    elif hasattr(first_item, '__dict__'):
                        start_cursor = self.create_cursor(first_item.__dict__)
                        end_cursor = self.create_cursor(last_item.__dict__)
                except Exception as e:
                    logger.warning(f"创建游标失败: {e}")
        
        page_info = PageInfo(
            has_next_page=has_more,
            has_previous_page=self.cursor is not None,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
            total_count=None  # 游标分页通常不返回总数
        )
        
        return PaginatedResult(
            items=items,
            page_info=page_info,
            pagination_type=PaginationType.CURSOR
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cursor": self.cursor,
            "page_size": self.page_size,
            "sort_field": self.sort_field,
            "sort_direction": self.sort_direction,
        }


class FieldSelector:
    """字段选择器"""
    
    def __init__(self, fields: Optional[str] = None):
        """
        初始化字段选择器
        
        fields: 逗号分隔的字段名，如 "id,name,status"
        """
        self.fields: Optional[List[str]] = None
        if fields:
            self.fields = [f.strip() for f in fields.split(',') if f.strip()]
    
    def select(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """选择字段"""
        if not self.fields:
            return item
        
        return {k: v for k, v in item.items() if k in self.fields}
    
    def select_from_list(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从列表中选择字段"""
        if not self.fields:
            return items
        
        return [self.select(item) for item in items]
    
    def validate_fields(self, allowed_fields: List[str]) -> bool:
        """验证字段是否允许"""
        if not self.fields:
            return True
        
        invalid = set(self.fields) - set(allowed_fields)
        if invalid:
            logger.warning(f"无效的字段: {invalid}")
            return False
        return True


class BatchOperator(Generic[T]):
    """批量操作器"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = min(max(1, batch_size), 1000)
    
    async def batch_process(
        self,
        items: List[T],
        processor: Callable[[List[T]], Any]
    ) -> List[Any]:
        """
        批量处理项目
        
        processor: 处理函数，接收一批项目
        """
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            try:
                result = await processor(batch)
                results.append(result)
            except Exception as e:
                logger.error(f"批量处理失败 (batch {i//self.batch_size + 1}): {e}")
                raise
        
        return results
    
    def split_batches(self, items: List[T]) -> List[List[T]]:
        """将项目分割成批次"""
        return [
            items[i:i + self.batch_size] 
            for i in range(0, len(items), self.batch_size)
        ]


# 分页参数解析
def parse_pagination_params(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    cursor: Optional[str] = None,
    fields: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc"
) -> Dict[str, Any]:
    """
    解析分页参数
    
    如果提供了cursor，使用游标分页
    否则使用偏移分页
    """
    result = {
        "fields": FieldSelector(fields),
    }
    
    if cursor:
        # 游标分页
        result["paginator"] = CursorPaginator(
            cursor=cursor,
            page_size=page_size or 20,
            sort_field=sort_by or "id",
            sort_direction=sort_order or "desc"
        )
        result["type"] = PaginationType.CURSOR
    else:
        # 偏移分页
        result["paginator"] = OffsetPaginator(
            page=page or 1,
            page_size=page_size or 20
        )
        result["type"] = PaginationType.OFFSET
    
    return result


# 常用分页配置
PAGINATION_CONFIGS = {
    "small": {
        "default_page_size": 10,
        "max_page_size": 50,
    },
    "medium": {
        "default_page_size": 20,
        "max_page_size": 100,
    },
    "large": {
        "default_page_size": 50,
        "max_page_size": 500,
    },
    "xlarge": {
        "default_page_size": 100,
        "max_page_size": 1000,
    },
}


def get_pagination_config(size: str) -> Dict[str, int]:
    """获取分页配置"""
    return PAGINATION_CONFIGS.get(size, PAGINATION_CONFIGS["medium"])


# 分页响应辅助函数
def create_page_response(
    items: List[T],
    paginator: Union[OffsetPaginator[T], CursorPaginator[T]],
    total_count: Optional[int] = None,
    has_more: bool = False
) -> Dict[str, Any]:
    """创建分页响应"""
    if isinstance(paginator, OffsetPaginator):
        result = paginator.paginate(items, total_count or len(items))
    else:
        result = paginator.paginate(items, has_more)
    
    return result.to_dict()


# 性能建议
PAGINATION_TIPS = {
    "use_cursor_for_large_data": "大数据量(>10000条)建议使用游标分页",
    "limit_page_size": "限制最大页大小以防止资源耗尽",
    "avoid_count": "游标分页避免COUNT查询以提升性能",
    "index_sort_field": "确保排序字段有索引",
    "select_only_needed": "只选择需要的字段减少数据传输",
}
