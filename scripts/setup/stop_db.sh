#!/bin/bash

# 自動化程式交易系統 - 數據庫停止腳本

echo "🛑 停止自動化程式交易系統數據庫..."

# 檢查Docker Compose是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安裝"
    exit 1
fi

# 停止並移除服務
echo "🐳 停止Docker服務..."
docker-compose down

# 可選：移除數據卷（會刪除所有數據）
if [ "$1" = "--clean" ]; then
    echo "🧹 清理數據卷..."
    docker-compose down -v
    echo "⚠️  警告：所有數據已被刪除！"
fi

echo ""
echo "✅ 數據庫服務已停止"
echo ""
echo "📝 常用命令："
echo "   啟動服務: ./start_db.sh"
echo "   查看狀態: docker-compose ps"
echo "   查看日誌: docker-compose logs"
echo "   清理數據: ./stop_db.sh --clean"
