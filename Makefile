# YL-AR-DGN Makefile
# Common commands for development and deployment

.PHONY: help ci cd deploy test clean status logs health-check

help:
	@echo "YL-AR-DGN 开发与部署命令"
	@echo ""
	@echo "可用命令:"
	@echo ""
	@echo "  📦 CI/CD 命令:"
	@echo "    make ci-check    - 运行CI检查"
	@echo "    make test        - 运行测试"
	@echo "    make lint        - 代码检查"
	@echo ""
	@echo "  🚀 部署命令:"
	@echo "    make deploy-staging   - 部署到预发布环境"
	@echo "    make deploy-prod      - 部署到生产环境"
	@echo "    make rollback         - 回滚到上一个版本"
	@echo ""
	@echo "  🔧 开发命令:"
	@echo "    make start      - 启动所有服务"
	@echo "    make stop       - 停止所有服务"
	@echo "    make restart    - 重启所有服务"
	@echo "    make status     - 检查服务状态"
	@echo "    make logs       - 查看服务日志"
	@echo "    make health     - 健康检查"
	@echo ""
	@echo "  🧹 清理命令:"
	@echo "    make clean      - 清理临时文件"
	@echo "    make clean-all  - 清理所有（包括镜像）"

# CI/CD commands
ci-check: lint test
	@echo "✅ CI检查完成"

lint:
	@echo "运行代码检查..."
	flake8 . --max-line-length=100 --ignore=E501,W503 || true
	black --check . || true
	mypy . || true

test:
	@echo "运行测试..."
	pytest -v test/ --cov=. --cov-report=term --cov-report=html

test-unit:
	@echo "运行单元测试..."
	pytest test/ -v --ignore=test/integration/

test-integration:
	@echo "运行集成测试..."
	pytest test/integration/ -v

test-coverage:
	@echo "运行测试并生成覆盖率报告..."
	pytest --cov=. --cov-report=xml --cov-report=html --cov-report=term

# Deployment commands
deploy-staging:
	@echo "部署到预发布环境..."
	./scripts/deploy.sh staging

deploy-prod:
	@echo "部署到生产环境..."
	./scripts/deploy.sh production

rollback:
	@echo "执行回滚..."
	./scripts/rollback.sh production latest

# Development commands
start:
	@echo "启动所有服务..."
	docker-compose up -d

stop:
	@echo "停止所有服务..."
	docker-compose down

restart:
	@echo "重启所有服务..."
	docker-compose restart

status:
	@echo "检查服务状态..."
	@docker-compose ps

logs:
	@echo "查看服务日志（最近100行）..."
	docker-compose logs --tail=100 -f

logs-ar-backend:
	@echo "查看AR-backend日志..."
	docker-compose logs -f ar-backend

logs-monitor:
	@echo "查看监控服务日志..."
	docker-compose logs -f prometheus grafana

health:
	@echo "运行健康检查..."
	@echo ""
	@echo "AR-backend:"
	curl -sf http://0.0.0.0:8000/health && echo " ✅ 健康" || echo " ❌ 不健康"
	@echo ""
	@echo "Prometheus:"
	curl -sf http://0.0.0.0:9090/api/v1/query?query=up && echo " ✅ 健康" || echo " ❌ 不健康"
	@echo ""
	@echo "Grafana:"
	curl -sf http://0.0.0.0:3000/api/health && echo " ✅ 健康" || echo " ❌ 不健康"

# Cleanup commands
clean:
	@echo "清理临时文件..."
	docker-compose down
	rm -rf *.pyc __pycache__
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	@echo "清理所有Docker资源..."
	docker system prune -af --volumes
	docker image prune -af

# Database commands
db-backup:
	@echo "备份数据库..."
	mkdir -p backups
	docker-compose exec -T postgres pg_dump -U ar_dgn ar_dgn > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "恢复数据库..."
	@echo "请指定备份文件:"
	@ls backups/
	@read -p "请输入文件名: " file; \
	docker-compose exec -T postgres psql -U ar_dgn -d ar_dgn < backups/$$file

# Monitoring commands
monitor-dashboard:
	@echo "打开Grafana仪表板..."
	@echo "访问 http://0.0.0.0:3000"
	@echo "用户名: admin"
	@echo "密码: admin"

monitor-prometheus:
	@echo "打开Prometheus..."
	@echo "访问 http://0.0.0.0:9090"

# Security commands
security-scan:
	@echo "运行安全扫描..."
	bandit -r AR-backend/ || true
	safety check -r AR-backend/requirements/requirements.txt || true

# Build commands
build:
	@echo "构建所有Docker镜像..."
	docker-compose build

build-ar-backend:
	@echo "构建AR-backend镜像..."
	docker-compose build ar-backend

build-monitor:
	@echo "构建监控服务镜像..."
	docker-compose build prometheus grafana

# Update commands
pull:
	@echo "拉取最新镜像..."
	docker-compose pull

update:
	@echo "更新所有服务..."
	make pull
	make restart
	make health

# Information commands
info:
	@echo "项目信息"
	@echo "========="
	@echo "项目: YL-AR-DGN"
	@echo "版本: 1.0.0"
	@echo ""
	@echo "服务端口:"
	@echo "  - AR-backend: http://0.0.0.0:8000"
	@echo "  - Prometheus: http://0.0.0.0:9090"
	@echo "  - Grafana: http://0.0.0.0:3000"
	@echo "  - Alertmanager: http://0.0.0.0:9093"

# Docker commands
docker-login:
	@echo "登录Docker Hub..."
	@docker login

docker-push:
	@echo "推送镜像到Docker Hub..."
	@docker-compose push

# Git commands
git-status:
	@echo "Git状态"
	git status

git-branch:
	@echo "当前分支"
	git branch

git-log:
	@echo "最近提交"
	git log --oneline -10

# Documentation commands
docs:
	@echo "打开项目文档..."
	@echo "访问 docs/README.md"

