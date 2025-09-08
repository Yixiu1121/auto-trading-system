#!/bin/bash

# 自動交易系統部署腳本
# 用於在虛擬機上部署完整的自動交易系統

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
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

# 檢查 Docker 是否安裝
check_docker() {
    log_info "檢查 Docker 安裝狀態..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    
    log_success "Docker 和 Docker Compose 已安裝"
}

# 創建必要的目錄
create_directories() {
    log_info "創建必要的目錄..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p certs
    
    log_success "目錄創建完成"
}

# 檢查配置文件
check_config() {
    log_info "檢查配置文件..."
    
    if [ ! -f "config.yaml" ]; then
        log_error "config.yaml 文件不存在"
        exit 1
    fi
    
    log_success "配置文件檢查完成"
}

# 構建 Docker 鏡像
build_image() {
    log_info "構建 Docker 鏡像..."
    
    docker-compose build
    
    log_success "Docker 鏡像構建完成"
}

# 啟動數據庫
start_database() {
    log_info "啟動數據庫服務..."
    
    docker-compose up -d postgres redis
    
    # 等待數據庫啟動
    log_info "等待數據庫啟動..."
    sleep 10
    
    log_success "數據庫服務啟動完成"
}

# 初始化數據庫
init_database() {
    log_info "初始化數據庫..."
    
    # 運行數據庫初始化腳本
    docker-compose run --rm trading_system python scripts/database/init_database.py
    
    log_success "數據庫初始化完成"
}

# 數據遷移
migrate_data() {
    log_info "執行數據遷移..."
    
    docker-compose --profile migrate up data_migrate
    
    log_success "數據遷移完成"
}

# 計算技術指標
calculate_indicators() {
    log_info "計算技術指標..."
    
    docker-compose --profile indicators up calculate_indicators
    
    log_success "技術指標計算完成"
}

# 執行策略
run_strategies() {
    log_info "執行策略分析..."
    
    docker-compose --profile strategies up run_strategies
    
    log_success "策略分析完成"
}

# 啟動自動交易系統
start_trading_system() {
    log_info "啟動自動交易系統..."
    
    docker-compose up -d trading_system
    
    log_success "自動交易系統啟動完成"
}

# 檢查服務狀態
check_services() {
    log_info "檢查服務狀態..."
    
    docker-compose ps
    
    log_success "服務狀態檢查完成"
}

# 顯示日誌
show_logs() {
    log_info "顯示系統日誌..."
    
    docker-compose logs -f trading_system
}

# 停止服務
stop_services() {
    log_info "停止所有服務..."
    
    docker-compose down
    
    log_success "所有服務已停止"
}

# 清理資源
cleanup() {
    log_info "清理 Docker 資源..."
    
    docker system prune -f
    docker volume prune -f
    
    log_success "清理完成"
}

# 顯示幫助信息
show_help() {
    echo "自動交易系統部署腳本"
    echo ""
    echo "使用方法:"
    echo "  $0 [選項]"
    echo ""
    echo "選項:"
    echo "  deploy      完整部署（包括數據庫、數據遷移、指標計算、策略執行）"
    echo "  start       啟動自動交易系統"
    echo "  stop        停止所有服務"
    echo "  restart     重啟所有服務"
    echo "  logs        顯示日誌"
    echo "  status      檢查服務狀態"
    echo "  migrate     執行數據遷移"
    echo "  indicators  計算技術指標"
    echo "  strategies  執行策略分析"
    echo "  cleanup     清理 Docker 資源"
    echo "  help        顯示此幫助信息"
    echo ""
}

# 主函數
main() {
    case "$1" in
        "deploy")
            log_info "開始完整部署..."
            check_docker
            create_directories
            check_config
            build_image
            start_database
            init_database
            migrate_data
            calculate_indicators
            run_strategies
            start_trading_system
            check_services
            log_success "完整部署完成！"
            ;;
        "start")
            start_trading_system
            check_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            start_trading_system
            check_services
            ;;
        "logs")
            show_logs
            ;;
        "status")
            check_services
            ;;
        "migrate")
            migrate_data
            ;;
        "indicators")
            calculate_indicators
            ;;
        "strategies")
            run_strategies
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"


