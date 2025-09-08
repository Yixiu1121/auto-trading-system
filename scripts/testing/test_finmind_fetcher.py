#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 FinMind 數據獲取器
"""

import os
import sys
import yaml
from datetime import datetime, timedelta

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.modules.data_fetcher import FinMindFetcher


def load_config():
    """加載配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def test_finmind_fetcher():
    """測試 FinMind 數據獲取器"""
    print("=== 測試 FinMind 數據獲取器 ===")

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    # 檢查 FinMind API Token
    finmind_token = os.getenv("FINMIND_TOKEN")
    if not finmind_token:
        print("⚠️  環境變量 FINMIND_TOKEN 未設置")
        print("請設置環境變量: export FINMIND_TOKEN='your_token_here'")
        print("或者將 token 添加到 config.yaml 文件中")
        return

    print(f"✅ FinMind API Token 已設置")

    # 創建數據獲取器
    try:
        fetcher = FinMindFetcher(config)
        print("✅ FinMind 數據獲取器創建成功")
    except Exception as e:
        print(f"❌ 創建 FinMind 數據獲取器失敗: {e}")
        return

    # 健康檢查
    print("\n--- 健康檢查 ---")
    health_status = fetcher.health_check()
    print(f"API 狀態: {health_status['api_status']}")
    print(f"數據庫狀態: {health_status['database_status']}")

    if health_status["api_status"] != "healthy":
        print("❌ FinMind API 連接失敗")
        return

    # 測試獲取股票列表
    print("\n--- 測試獲取股票列表 ---")
    try:
        stocks = fetcher.get_stock_list()
        if stocks:
            print(f"✅ 成功獲取 {len(stocks)} 支股票")
            print(f"前5支股票: {[stock['stock_id'] for stock in stocks[:5]]}")
        else:
            print("❌ 獲取股票列表失敗")
            return
    except Exception as e:
        print(f"❌ 獲取股票列表時發生錯誤: {e}")
        return

    # 測試獲取單支股票數據
    print("\n--- 測試獲取單支股票數據 ---")
    test_stock_id = "2330"  # 台積電
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        df = fetcher.get_stock_data(test_stock_id, start_date, end_date)
        if df is not None and not df.empty:
            print(f"✅ 成功獲取 {test_stock_id} 的 {len(df)} 筆數據")
            print(f"數據範圍: {df['date'].min()} 到 {df['date'].max()}")
            print(f"數據列: {list(df.columns)}")
            print(f"前3筆數據:")
            print(df.head(3))
        else:
            print(f"❌ 獲取股票 {test_stock_id} 數據失敗")
            return
    except Exception as e:
        print(f"❌ 獲取股票數據時發生錯誤: {e}")
        return

    # 測試數據庫連接
    print("\n--- 測試數據庫連接 ---")
    if fetcher.connect_database():
        print("✅ 數據庫連接成功")

        # 測試存儲數據
        print("\n--- 測試數據存儲 ---")
        if fetcher.store_stock_data(test_stock_id, df):
            print("✅ 數據存儲成功")
        else:
            print("❌ 數據存儲失敗")

        fetcher.close_database()
    else:
        print("❌ 數據庫連接失敗")
        print("請確保 PostgreSQL 數據庫正在運行")
        print("可以使用 ./start_db.sh 啟動數據庫服務")

    print("\n=== 測試完成 ===")


def test_initialization():
    """測試數據庫初始化"""
    print("\n=== 測試數據庫初始化 ===")

    config = load_config()
    if not config:
        return

    finmind_token = os.getenv("FINMIND_TOKEN")
    if not finmind_token:
        print("⚠️  環境變量 FINMIND_TOKEN 未設置，跳過初始化測試")
        return

    fetcher = FinMindFetcher(config)

    # 測試初始化（只處理少量股票）
    print("開始初始化數據庫（測試模式，只處理3支股票）")
    test_stocks = ["2330", "2317", "2454"]  # 台積電、鴻海、聯發科

    success = fetcher.initialize_database(stock_ids=test_stocks, days_back=7)
    if success:
        print("✅ 數據庫初始化成功")
    else:
        print("❌ 數據庫初始化失敗")


if __name__ == "__main__":
    # 測試基本功能
    test_finmind_fetcher()

    # 詢問是否要測試初始化
    print("\n" + "=" * 50)
    response = input("是否要測試數據庫初始化？(y/n): ").lower().strip()
    if response in ["y", "yes", "是"]:
        test_initialization()
    else:
        print("跳過初始化測試")

    print("\n測試腳本執行完成！")
