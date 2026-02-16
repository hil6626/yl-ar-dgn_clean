#!/bin/bash
# ============================================================================
# YL-Monitor 备份脚本
# 功能：数据库备份、日志归档、配置文件备份
# 用法: ./scripts/backup.sh [full|db|logs|config]
# ============================================================================

set -e

# 配置
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/yl-monitor}"
DATA_DIR="${DATA_DIR:-./data}"
LOGS_DIR="${LOGS_DIR:-./logs}"
CONFIG_DIR="${CONFIG_DIR:-./config}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="yl-monitor_backup_${DATE}"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 创建备份目录
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    if [ -f "${DATA_DIR}/monitor.db" ]; then
        cp "${DATA_DIR}/monitor.db" "${BACKUP_DIR}/${BACKUP_NAME}/monitor.db"
        log_info "✓ 数据库备份完成"
    else
        log_warn "⚠ 数据库文件不存在: ${DATA_DIR}/monitor.db"
    fi
    
    # 备份数据库Schema（如果有）
    if command -v sqlite3 &> /dev/null && [ -f "${DATA_DIR}/monitor.db" ]; then
        sqlite3 "${DATA_DIR}/monitor.db" .schema > "${BACKUP_DIR}/${BACKUP_NAME}/schema.sql"
        log_info "✓ 数据库Schema导出完成"
    fi
}

# 备份日志
backup_logs() {
    log_info "备份日志..."
    
    if [ -d "${LOGS_DIR}" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/logs.tar.gz" -C "${LOGS_DIR}" .
        log_info "✓ 日志备份完成"
    else
        log_warn "⚠ 日志目录不存在: ${LOGS_DIR}"
    fi
}

# 备份配置
backup_config() {
    log_info "备份配置文件..."
    
    # 备份.env文件
    if [ -f ".env" ]; then
        cp ".env" "${BACKUP_DIR}/${BACKUP_NAME}/.env"
        log_info "✓ 环境配置备份完成"
    fi
    
    # 备份nginx配置
    if [ -d "nginx" ]; then
        cp -r nginx "${BACKUP_DIR}/${BACKUP_NAME}/"
        log_info "✓ Nginx配置备份完成"
    fi
    
    # 备份systemd配置
    if [ -d "systemd" ]; then
        cp -r systemd "${BACKUP_DIR}/${BACKUP_NAME}/"
        log_info "✓ Systemd配置备份完成"
    fi
    
    # 备份docker配置
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "${BACKUP_DIR}/${BACKUP_NAME}/"
        log_info "✓ Docker配置备份完成"
    fi
}

# 备份脚本
backup_scripts() {
    log_info "备份自定义脚本..."
    
    if [ -d "scripts" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/scripts.tar.gz" -C scripts .
        log_info "✓ 脚本备份完成"
    fi
}

# 创建备份清单
create_manifest() {
    log_info "创建备份清单..."
    
    cat > "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt" << EOF
YL-Monitor 备份清单
===================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份名称: ${BACKUP_NAME}
备份类型: ${BACKUP_TYPE:-full}

包含内容:
EOF
    
    [ -f "${BACKUP_DIR}/${BACKUP_NAME}/monitor.db" ] && echo "- 数据库文件" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    [ -f "${BACKUP_DIR}/${BACKUP_NAME}/logs.tar.gz" ] && echo "- 日志文件" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    [ -f "${BACKUP_DIR}/${BACKUP_NAME}/.env" ] && echo "- 环境配置" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    [ -d "${BACKUP_DIR}/${BACKUP_NAME}/nginx" ] && echo "- Nginx配置" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    [ -f "${BACKUP_DIR}/${BACKUP_NAME}/scripts.tar.gz" ] && echo "- 自定义脚本" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    
    # 计算备份大小
    BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)
    echo "" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    echo "备份大小: ${BACKUP_SIZE}" >> "${BACKUP_DIR}/${BACKUP_NAME}/MANIFEST.txt"
    
    log_info "✓ 备份清单创建完成"
}

# 压缩备份
compress_backup() {
    log_info "压缩备份..."
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    rm -rf "${BACKUP_NAME}"
    
    log_info "✓ 备份压缩完成: ${BACKUP_NAME}.tar.gz"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份 (保留${RETENTION_DAYS}天)..."
    
    find "${BACKUP_DIR}" -name "yl-monitor_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
    
    log_info "✓ 旧备份清理完成"
}

# 完整备份
full_backup() {
    log_info "开始完整备份..."
    BACKUP_TYPE="full"
    
    backup_database
    backup_logs
    backup_config
    backup_scripts
    create_manifest
    compress_backup
    cleanup_old_backups
    
    log_info "✅ 完整备份完成: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
}

# 仅数据库备份
db_backup() {
    log_info "开始数据库备份..."
    BACKUP_TYPE="db"
    
    backup_database
    create_manifest
    compress_backup
    
    log_info "✅ 数据库备份完成"
}

# 仅日志备份
logs_backup() {
    log_info "开始日志备份..."
    BACKUP_TYPE="logs"
    
    backup_logs
    create_manifest
    compress_backup
    
    log_info "✅ 日志备份完成"
}

# 仅配置备份
config_backup() {
    log_info "开始配置备份..."
    BACKUP_TYPE="config"
    
    backup_config
    create_manifest
    compress_backup
    
    log_info "✅ 配置备份完成"
}

# 显示帮助
show_help() {
    echo "YL-Monitor 备份脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  full    - 完整备份（数据库+日志+配置+脚本）"
    echo "  db      - 仅备份数据库"
    echo "  logs    - 仅备份日志"
    echo "  config  - 仅备份配置"
    echo "  help    - 显示帮助信息"
    echo ""
    echo "环境变量:"
    echo "  BACKUP_DIR     - 备份目录 (默认: /opt/backups/yl-monitor)"
    echo "  DATA_DIR       - 数据目录 (默认: ./data)"
    echo "  LOGS_DIR       - 日志目录 (默认: ./logs)"
    echo "  RETENTION_DAYS - 保留天数 (默认: 30)"
}

# 主函数
main() {
    case "${1:-full}" in
        full)
            full_backup
            ;;
        db|database)
            db_backup
            ;;
        logs)
            logs_backup
            ;;
        config|configuration)
            config_backup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
