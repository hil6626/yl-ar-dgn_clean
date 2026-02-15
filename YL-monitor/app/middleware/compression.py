"""
响应压缩中间件

功能:
- Gzip压缩响应
- 压缩级别控制
- 内容类型过滤
- 性能监控

作者: AI Assistant
版本: 1.0.0
"""

import gzip
import logging
from typing import Optional, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    响应压缩中间件
    
    自动压缩符合条件的响应，减少传输大小
    """
    
    # 默认压缩的最小大小 (字节)
    MINIMUM_SIZE = 500
    
    # 默认压缩级别 (1-9, 9最大压缩率但最慢)
    COMPRESS_LEVEL = 6
    
    # 需要压缩的内容类型
    COMPRESSIBLE_TYPES: Set[str] = {
        "text/plain",
        "text/html",
        "text/css",
        "text/javascript",
        "text/xml",
        "text/json",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
        "application/x-javascript",
        "application/x-json",
        "application/ld+json",
    }
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = MINIMUM_SIZE,
        compress_level: int = COMPRESS_LEVEL,
        compressible_types: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = max(1, min(9, compress_level))
        self.compressible_types = compressible_types or self.COMPRESSIBLE_TYPES.copy()
        
        logger.info(
            f"压缩中间件已初始化: "
            f"min_size={minimum_size}, "
            f"level={compress_level}"
        )
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查客户端是否支持gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        supports_gzip = "gzip" in accept_encoding.lower()
        
        # 继续处理请求
        response = await call_next(request)
        
        # 如果不支持gzip或响应已压缩，直接返回
        if not supports_gzip or self._is_already_compressed(response):
            return response
        
        # 检查是否应该压缩
        if not self._should_compress(response):
            return response
        
        # 执行压缩
        try:
            compressed_response = await self._compress_response(response)
            
            # 添加压缩统计日志
            original_size = len(response.body)
            compressed_size = len(compressed_response.body)
            ratio = (1 - compressed_size / original_size) * 100
            
            logger.debug(
                f"响应已压缩: {original_size} -> {compressed_size} bytes "
                f"({ratio:.1f}% 减少)"
            )
            
            return compressed_response
            
        except Exception as e:
            logger.error(f"响应压缩失败: {e}")
            return response
    
    def _is_already_compressed(self, response: Response) -> bool:
        """检查响应是否已压缩"""
        content_encoding = response.headers.get("content-encoding", "")
        return "gzip" in content_encoding or "br" in content_encoding or "deflate" in content_encoding
    
    def _should_compress(self, response: Response) -> bool:
        """检查是否应该压缩响应"""
        # 检查内容类型
        content_type = response.headers.get("content-type", "").lower()
        
        # 提取主内容类型
        if ";" in content_type:
            content_type = content_type.split(";")[0].strip()
        
        if content_type not in self.compressible_types:
            return False
        
        # 检查响应大小
        body = response.body
        if len(body) < self.minimum_size:
            return False
        
        # 检查状态码 (只压缩成功响应)
        if response.status_code < 200 or response.status_code >= 300:
            return False
        
        return True
    
    async def _compress_response(self, response: Response) -> Response:
        """压缩响应"""
        body = response.body
        
        # 压缩内容
        compressed = gzip.compress(
            body,
            compresslevel=self.compress_level
        )
        
        # 创建新响应
        compressed_response = Response(
            content=compressed,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
        
        # 更新头信息
        compressed_response.headers["content-encoding"] = "gzip"
        compressed_response.headers["content-length"] = str(len(compressed))
        compressed_response.headers["vary"] = "accept-encoding"
        
        # 移除不必要的头
        if "content-md5" in compressed_response.headers:
            del compressed_response.headers["content-md5"]
        
        return compressed_response


class CompressionConfig:
    """压缩配置"""
    
    def __init__(
        self,
        enabled: bool = True,
        minimum_size: int = 500,
        compress_level: int = 6,
        exclude_paths: Optional[Set[str]] = None,
        exclude_extensions: Optional[Set[str]] = None
    ):
        self.enabled = enabled
        self.minimum_size = minimum_size
        self.compress_level = compress_level
        self.exclude_paths = exclude_paths or set()
        self.exclude_extensions = exclude_extensions or {
            ".jpg", ".jpeg", ".png", ".gif", ".webp",  # 图片
            ".mp4", ".webm", ".avi", ".mov",           # 视频
            ".mp3", ".wav", ".ogg",                    # 音频
            ".zip", ".gz", ".rar", ".7z",              # 已压缩
            ".pdf", ".doc", ".docx",                   # 文档
        }
    
    def should_compress_path(self, path: str) -> bool:
        """检查路径是否应该压缩"""
        # 检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # 检查文件扩展名
        path_lower = path.lower()
        for ext in self.exclude_extensions:
            if path_lower.endswith(ext):
                return False
        
        return True


# 压缩统计
class CompressionStats:
    """压缩统计"""
    
    def __init__(self):
        self.total_requests = 0
        self.compressed_requests = 0
        self.total_original_size = 0
        self.total_compressed_size = 0
    
    def record_compression(
        self,
        original_size: int,
        compressed_size: int
    ):
        """记录压缩统计"""
        self.total_requests += 1
        self.compressed_requests += 1
        self.total_original_size += original_size
        self.total_compressed_size += compressed_size
    
    def record_skip(self):
        """记录跳过压缩"""
        self.total_requests += 1
    
    @property
    def compression_ratio(self) -> float:
        """计算压缩率"""
        if self.total_original_size == 0:
            return 0.0
        return (1 - self.total_compressed_size / self.total_original_size) * 100
    
    @property
    def compression_rate(self) -> float:
        """计算压缩比例"""
        if self.total_requests == 0:
            return 0.0
        return self.compressed_requests / self.total_requests * 100
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "compressed_requests": self.compressed_requests,
            "compression_rate": f"{self.compression_rate:.1f}%",
            "total_original_size": self.total_original_size,
            "total_compressed_size": self.total_compressed_size,
            "compression_ratio": f"{self.compression_ratio:.1f}%",
        }


# 全局统计实例
_compression_stats = CompressionStats()


def get_compression_stats() -> CompressionStats:
    """获取压缩统计"""
    return _compression_stats


# 辅助函数
def compress_data(data: bytes, level: int = 6) -> bytes:
    """压缩数据"""
    return gzip.compress(data, compresslevel=level)


def decompress_data(data: bytes) -> bytes:
    """解压数据"""
    return gzip.decompress(data)


# 压缩级别建议
COMPRESSION_LEVELS = {
    "fast": 1,      # 最快，压缩率最低
    "balanced": 6,  # 平衡
    "best": 9,      # 最佳压缩率，最慢
}


def get_compression_level(level_name: str) -> int:
    """获取压缩级别"""
    return COMPRESSION_LEVELS.get(level_name, 6)


# 性能建议
COMPRESSION_TIPS = {
    "min_size": "设置合理的min_size，小响应压缩可能反而增加大小",
    "level": "根据CPU和带宽权衡选择压缩级别",
    "exclude_binary": "排除已压缩的二进制文件(图片、视频等)",
    "vary_header": "确保设置Vary: Accept-Encoding头",
    "precompressed": "对于静态资源，考虑预压缩",
}
