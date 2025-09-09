#!/bin/bash
# 重啟交易系統服務腳本

echo "🔄 重啟交易系統服務..."

# 方法1: 簡單重啟 (使用現有映像)
restart_simple() {
    echo "📋 方法1: 簡單重啟"
    docker-compose restart trading_system
    echo "✅ 交易系統重啟完成"
}

# 方法2: 重新構建並重啟 (有程式碼更新時)
restart_rebuild() {
    echo "📋 方法2: 重新構建並重啟"
    echo "🏗️  停止交易系統..."
    docker-compose stop trading_system
    
    echo "🗑️  移除舊容器..."
    docker-compose rm -f trading_system
    
    echo "🔨 重新構建映像..."
    docker-compose build trading_system
    
    echo "🚀 啟動新容器..."
    docker-compose up -d trading_system
    
    echo "✅ 交易系統重新構建並啟動完成"
}

# 方法3: 強制重新創建容器
restart_recreate() {
    echo "📋 方法3: 強制重新創建"
    docker-compose up -d --force-recreate trading_system
    echo "✅ 交易系統重新創建完成"
}

# 檢查服務狀態
check_status() {
    echo "📊 檢查服務狀態..."
    docker-compose ps trading_system
    echo ""
    echo "📝 查看最新日誌..."
    docker-compose logs --tail=10 trading_system
}

# 主選單
echo "請選擇重啟方式："
echo "1) 簡單重啟 (快速，適用於配置更改)"
echo "2) 重新構建並重啟 (適用於程式碼更新)"
echo "3) 強制重新創建 (解決容器問題)"
echo "4) 檢查服務狀態"
echo "q) 退出"

read -p "請輸入選項 [1-4,q]: " choice

case $choice in
    1)
        restart_simple
        check_status
        ;;
    2)
        restart_rebuild
        check_status
        ;;
    3)
        restart_recreate
        check_status
        ;;
    4)
        check_status
        ;;
    q|Q)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac
