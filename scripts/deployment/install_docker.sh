#!/bin/bash

# Docker 安裝腳本
# 用於在虛擬機上安裝 Docker 和 Docker Compose

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

# 檢測操作系統
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
            VER=$VERSION_ID
        else
            log_error "無法檢測操作系統"
            exit 1
        fi
    else
        log_error "不支持的操作系統: $OSTYPE"
        exit 1
    fi
}

# 安裝 Docker (Ubuntu/Debian)
install_docker_ubuntu() {
    log_info "在 Ubuntu/Debian 上安裝 Docker..."
    
    # 更新包索引
    sudo apt-get update
    
    # 安裝必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加 Docker 的官方 GPG 密鑰
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 設置穩定版倉庫
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 更新包索引
    sudo apt-get update
    
    # 安裝 Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 啟動 Docker 服務
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 將當前用戶添加到 docker 組
    sudo usermod -aG docker $USER
    
    log_success "Docker 安裝完成"
}

# 安裝 Docker (CentOS/RHEL)
install_docker_centos() {
    log_info "在 CentOS/RHEL 上安裝 Docker..."
    
    # 安裝必要的包
    sudo yum install -y yum-utils
    
    # 設置倉庫
    sudo yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo
    
    # 安裝 Docker Engine
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    
    # 啟動 Docker 服務
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 將當前用戶添加到 docker 組
    sudo usermod -aG docker $USER
    
    log_success "Docker 安裝完成"
}

# 安裝 Docker Compose
install_docker_compose() {
    log_info "安裝 Docker Compose..."
    
    # 下載 Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 設置執行權限
    sudo chmod +x /usr/local/bin/docker-compose
    
    # 創建軟鏈接
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose 安裝完成"
}

# 驗證安裝
verify_installation() {
    log_info "驗證 Docker 安裝..."
    
    # 檢查 Docker 版本
    docker --version
    
    # 檢查 Docker Compose 版本
    docker-compose --version
    
    # 測試 Docker 運行
    sudo docker run hello-world
    
    log_success "Docker 安裝驗證完成"
}

# 顯示安裝後說明
show_post_install_info() {
    echo ""
    log_success "Docker 安裝完成！"
    echo ""
    echo "📝 安裝後說明："
    echo "1. 請重新登入或執行以下命令使 docker 組權限生效："
    echo "   newgrp docker"
    echo ""
    echo "2. 測試 Docker 是否正常工作："
    echo "   docker run hello-world"
    echo ""
    echo "3. 部署自動交易系統："
    echo "   ./scripts/deployment/deploy.sh deploy"
    echo ""
}

# 主函數
main() {
    log_info "開始安裝 Docker..."
    
    # 檢測操作系統
    detect_os
    log_info "檢測到操作系統: $OS $VER"
    
    # 檢查是否已安裝
    if command -v docker &> /dev/null; then
        log_warning "Docker 已安裝"
        docker --version
    else
        # 根據操作系統安裝 Docker
        case $OS in
            *"Ubuntu"*|*"Debian"*)
                install_docker_ubuntu
                ;;
            *"CentOS"*|*"Red Hat"*)
                install_docker_centos
                ;;
            *)
                log_error "不支持的操作系統: $OS"
                exit 1
                ;;
        esac
    fi
    
    # 檢查是否已安裝 Docker Compose
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose 已安裝"
        docker-compose --version
    else
        install_docker_compose
    fi
    
    # 驗證安裝
    verify_installation
    
    # 顯示安裝後說明
    show_post_install_info
}

# 執行主函數
main "$@"


