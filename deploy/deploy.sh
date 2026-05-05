#!/bin/bash
#
# MyCourse 部署脚本
# 部署到阿里云服务器：47.93.44.227
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_IP="47.93.44.227"
SERVER_USER="root"
SSH_PORT="22"
DEPLOY_DIR="/var/www/mycourse"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# 显示使用方法
usage() {
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy     部署到服务器"
    echo "  start      启动服务"
    echo "  stop       停止服务"
    echo "  restart    重启服务"
    echo "  status     查看服务状态"
    echo "  logs       查看日志"
    echo "  update     更新并重新部署"
    echo "  health     健康检查"
    echo ""
    echo "示例:"
    echo "  $0 deploy"
    echo "  $0 restart"
}

# 部署到服务器
deploy() {
    log_info "开始部署 MyCourse 到服务器 ${SERVER_IP}..."

    # 检查本地必要的文件
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found in current directory"
        exit 1
    fi

    # 通过 SSH 部署
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
        set -e

        DEPLOY_DIR="/var/www/mycourse"

        # 创建目录结构
        log_info "创建目录结构..."
        mkdir -p ${DEPLOY_DIR}/{db,logs,data,docker,nginx}

        # 检查 Docker 是否安装
        if ! command -v docker &> /dev/null; then
            log_info "安装 Docker..."
            curl -fsSL https://get.docker.com | sh
            systemctl start docker
            systemctl enable docker
        fi

        # 检查 Docker Compose 是否安装
        if ! command -v docker-compose &> /dev/null; then
            log_info "安装 Docker Compose..."
            curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
        fi

        # 启动 Docker 服务
        systemctl start docker 2>/dev/null || true
        systemctl enable docker 2>/dev/null || true

        log_info "Docker 环境准备完成"
ENDSSH

    # 同步文件到服务器
    log_info "同步部署文件到服务器..."
    rsync -avz -e "ssh -p ${SSH_PORT}" \
        --exclude 'node_modules' \
        --exclude '__pycache__' \
        --exclude '.pytest_cache' \
        --exclude '*.pyc' \
        --exclude '.git' \
        ./ ${SERVER_USER}@${SERVER_IP}:${DEPLOY_DIR}/

    # 在服务器上执行部署
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
        set -e
        cd /var/www/mycourse

        # 设置环境变量（首次需要手动设置）
        if [ -z "$JWT_SECRET_KEY" ]; then
            echo "请设置 JWT_SECRET_KEY 环境变量:"
            echo "export JWT_SECRET_KEY=<your-secret-key>"
            echo ""
            echo "建议使用:"
            # openssl rand -base64 32
            echo "export JWT_SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)"
        fi

        # 停止旧容器
        log_info "停止旧容器..."
        docker-compose down 2>/dev/null || true

        # 构建并启动新容器
        log_info "构建 Docker 镜像..."
        docker-compose build --no-cache

        log_info "启动服务..."
        docker-compose up -d

        # 等待服务启动
        sleep 10

        # 检查容器状态
        docker-compose ps

        log_success "部署完成!"
        log_info "访问 http://47.93.44.227 查看应用"
    ENDSSH

    log_success "部署完成!"
}

# 启动服务
start() {
    log_info "启动 MyCourse 服务..."
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker-compose start"
    log_success "服务已启动"
}

# 停止服务
stop() {
    log_warning "停止 MyCourse 服务..."
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker-compose stop"
    log_success "服务已停止"
}

# 重启服务
restart() {
    log_info "重启 MyCourse 服务..."
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker-compose restart"
    log_success "服务已重启"
}

# 查看状态
status() {
    log_info "MyCourse 服务状态:"
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker-compose ps"
}

# 查看日志
logs() {
    local service=${1:-""}
    log_info "查看日志 (服务: ${service:-all})..."
    if [ -z "$service" ]; then
        ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker-compose logs -f --tail=100"
    else
        ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker-compose logs -f --tail=100 $service"
    fi
}

# 健康检查
health() {
    log_info "执行健康检查..."

    # 检查前端
    echo -n "Frontend: "
    if curl -sf http://${SERVER_IP}/ > /dev/null 2>&1; then
        echo -e "\033[0;32mOK\033[0m"
    else
        echo -e "\033[0;31mFAILED\033[0m"
    fi

    # 检查后端
    echo -n "Backend API: "
    if curl -sf http://${SERVER_IP}/api/health > /dev/null 2>&1; then
        echo -e "\033[0;32mOK\033[0m"
    else
        echo -e "\033[0;31mFAILED\033[0m"
    fi

    # 服务器容器状态
    echo ""
    status
}

# 更新部署
update() {
    log_info "更新 MyCourse..."
    ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
        set -e
        cd /var/www/mycourse

        # 拉取最新代码
        git pull origin main

        # 重新构建
        docker-compose build --no-cache backend1 backend2

        # 重启后端
        docker-compose up -d backend1 backend2

        log_success "更新完成"
ENDSSH
    health
}

# 主函数
main() {
    # 检查必要的命令
    check_command ssh
    check_command rsync

    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    case $1 in
        deploy)
            deploy
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            shift
            logs "$@"
            ;;
        update)
            update
            ;;
        health)
            health
            ;;
        *)
            log_error "未知命令: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
