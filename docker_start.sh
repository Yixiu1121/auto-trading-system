#!/bin/bash
# Docker Compose 自動交易系統啟動腳本

echo "🐳 Docker 自動交易系統啟動"
echo "=========================="

# 檢查Docker是否運行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未運行，請先啟動Docker"
    exit 1
fi

echo "📋 請選擇啟動模式："
echo "1. 完整系統啟動 (數據庫 + 交易系統)"
echo "2. 僅啟動數據庫服務"
echo "3. 數據遷移 + 完整系統"
echo "4. 演示模式啟動"
echo "5. 查看系統狀態"
echo "6. 停止所有服務"
echo ""

read -p "請輸入選項 (1-6): " choice

case $choice in
    1)
        echo "🚀 啟動完整系統..."
        docker-compose up --build
        ;;
    2)
        echo "📊 僅啟動數據庫服務..."
        docker-compose up -d postgres redis
        echo "✅ 數據庫服務已啟動"
        docker-compose ps
        ;;
    3)
        echo "📦 數據遷移 + 完整系統啟動..."
        # 先啟動數據庫
        docker-compose up -d postgres redis
        echo "⏰ 等待數據庫初始化..."
        sleep 15
        
        # 運行數據遷移
        echo "📈 執行數據遷移..."
        docker-compose run --rm data_migrate python scripts/data_migration/sync_daily_data.py init
        
        # 啟動交易系統
        echo "🚀 啟動交易系統..."
        docker-compose up trading_system
        ;;
    4)
        echo "🎬 演示模式啟動..."
        # 先建構並啟動基礎服務
        docker-compose up -d postgres redis
        echo "⏰ 等待數據庫初始化..."
        sleep 15
        
        # 運行演示
        docker-compose run --rm trading_system python scripts/trading/demo_auto_trading_schedule.py
        ;;
    5)
        echo "📊 系統狀態："
        docker-compose ps
        echo ""
        echo "📋 容器日誌（最近10行）："
        if docker ps --format "table {{.Names}}" | grep -q auto_trading_system; then
            echo "=== 交易系統日誌 ==="
            docker-compose logs --tail=10 trading_system
        fi
        if docker ps --format "table {{.Names}}" | grep -q trading_db; then
            echo "=== 數據庫日誌 ==="
            docker-compose logs --tail=5 postgres
        fi
        ;;
    6)
        echo "🛑 停止所有服務..."
        docker-compose down
        echo "✅ 所有服務已停止"
        ;;
    *)
        echo "❌ 無效選項，預設啟動完整系統..."
        docker-compose up --build
        ;;
esac

echo ""
echo "📝 有用的Docker命令："
echo "  查看狀態: docker-compose ps"
echo "  查看日誌: docker-compose logs -f trading_system"
echo "  進入容器: docker-compose exec trading_system bash"
echo "  停止服務: docker-compose down"
echo "  重建容器: docker-compose up --build"
