#!/bin/bash

# 自動化程式交易系統 - 數據庫啟動腳本

echo "🚀 啟動自動化程式交易系統數據庫..."

# 檢查Docker是否運行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未運行，請先啟動Docker"
    exit 1
fi

# 檢查Docker Compose是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安裝，請先安裝Docker Compose"
    exit 1
fi

# 創建必要的目錄
echo "📁 創建必要的目錄..."
mkdir -p logs
mkdir -p data
mkdir -p init-scripts

# 啟動服務
echo "🐳 啟動Docker服務..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

# 檢查數據庫連接
echo "🔌 測試數據庫連接..."
sleep 5

# 使用Docker exec測試PostgreSQL連接
if docker exec trading_system_db pg_isready -U trading_user -d trading_system > /dev/null 2>&1; then
    echo "✅ PostgreSQL數據庫連接成功"
else
    echo "❌ PostgreSQL數據庫連接失敗"
fi

# 檢查Redis連接
if docker exec trading_system_cache redis-cli --raw incr ping > /dev/null 2>&1; then
    echo "✅ Redis緩存連接成功"
else
    echo "❌ Redis緩存連接失敗"
fi

echo ""
echo "🎉 數據庫啟動完成！"
echo ""
echo "📊 服務信息："
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   pgAdmin: http://localhost:8080"
echo ""
echo "🔑 數據庫憑證："
echo "   數據庫: trading_system"
echo "   用戶名: trading_user"
echo "   密碼: trading_password123"
echo ""
echo "🔑 Redis密碼: trading_redis123"
echo ""
echo "🔑 pgAdmin憑證："
echo "   郵箱: admin@trading.com"
echo "   密碼: admin123"
echo ""
echo "📝 常用命令："
echo "   查看日誌: docker-compose logs -f"
echo "   停止服務: docker-compose down"
echo "   重啟服務: docker-compose restart"
echo "   查看狀態: docker-compose ps"
