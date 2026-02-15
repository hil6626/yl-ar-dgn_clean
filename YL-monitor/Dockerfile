# ============================================================================
# YL-Monitor Dockerfile
# 生产环境部署镜像
# ============================================================================

FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# 生产镜像
# ============================================================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从builder复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 创建非root用户
RUN groupadd -r ylmonitor && useradd -r -g ylmonitor ylmonitor

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/scripts && \
    chown -R ylmonitor:ylmonitor /app

# 复制应用代码
COPY --chown=ylmonitor:ylmonitor app/ ./app/
COPY --chown=ylmonitor:ylmonitor static/ ./static/
COPY --chown=ylmonitor:ylmonitor templates/ ./templates/
COPY --chown=ylmonitor:ylmonitor migrations/ ./migrations/

# 复制脚本目录（如果存在）
COPY --chown=ylmonitor:ylmonitor scripts/ ./scripts/

# 切换到非root用户
USER ylmonitor

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    YL_MONITOR_PORT=8000 \
    YL_MONITOR_HOST=0.0.0.0 \
    YL_MONITOR_WORKERS=4 \
    DATABASE_URL=sqlite:///data/monitor.db \
    YL_MONITOR_LOG_LEVEL=info

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["sh", "-c", "python3 migrations/001_create_function_mappings.py && \
     python3 migrations/002_create_scripts_table.py && \
     uvicorn app.main:app --host ${YL_MONITOR_HOST} --port ${YL_MONITOR_PORT} --workers ${YL_MONITOR_WORKERS}"]
