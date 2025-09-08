#!/bin/bash

# 自動交易系統部署腳本
# 用於在虛擬機上部署完整的交易系統

echo "🚀 開始部署自動交易系統到虛擬機..."

# 檢查Docker是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安裝，正在安裝..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker安裝完成"
fi

# 檢查Docker Compose是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安裝，正在安裝..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose安裝完成"
fi

# 啟動Docker服務
echo "🔄 啟動Docker服務..."
systemctl start docker
systemctl enable docker

# 創建必要的目錄
echo "📁 創建必要的目錄..."
mkdir -p /opt/trading_system
mkdir -p /opt/trading_system/certs
mkdir -p /opt/trading_system/logs
mkdir -p /opt/trading_system/data

# 複製項目文件到虛擬機
echo "📋 複製項目文件..."
# 這裡需要手動複製項目文件到虛擬機，或者使用scp

# 進入項目目錄
cd /opt/trading_system

# 構建Docker鏡像
echo "🔨 構建Docker鏡像..."
docker build -t trading_system .

# 啟動服務
echo "🚀 啟動交易系統服務..."
docker-compose up -d

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

# 顯示日誌
echo "📊 顯示系統日誌..."
docker-compose logs --tail=50

echo "✅ 部署完成！"
echo "📝 使用以下命令管理服務："
echo "  查看日誌: docker-compose logs -f"
echo "  停止服務: docker-compose down"
echo "  重啟服務: docker-compose restart"
echo "  查看狀態: docker-compose ps"
