#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場數據獲取測試腳本
用於測試富邦證券 API 的市場數據獲取功能
"""

import os
import sys
import yaml
from datetime import datetime, timedelta
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from modules.trading.fubon_api_client import FubonAPIClient


def load_config():
    """加載配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"配置文件 {config_path} 不存在")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def setup_logging():
    """設置日誌"""
    # 創建日誌目錄
    os.makedirs("logs", exist_ok=True)

    # 配置日誌
    logger.add(
        "logs/test_market_data.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def test_market_type_detection():
    """測試市場類型檢測"""
    print("=== 測試市場類型檢測 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        # 測試不同市場的股票
        test_symbols = [
            "2330",
            "0050",
            "2317",
            "2454",
        ]  # 台積電、元大台灣50、鴻海、聯發科

        for symbol in test_symbols:
            if client.real_trading and client.sdk:
                market = client._get_market_type(symbol)
                print(f"  股票 {symbol}: {market}")
            else:
                print(f"  股票 {symbol}: 模擬模式")

    except Exception as e:
        print(f"❌ 測試市場類型檢測異常: {e}")


def test_real_time_price():
    """測試實時價格獲取"""
    print("\n=== 測試實時價格獲取 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        # 測試獲取台積電的實時價格
        symbol = "2330"
        price = client.get_real_time_price(symbol)

        if price:
            print(f"✅ {symbol} 實時價格: {price}")
        else:
            print(f"❌ 獲取 {symbol} 實時價格失敗")

    except Exception as e:
        print(f"❌ 測試實時價格異常: {e}")


def test_market_data():
    """測試市場數據獲取"""
    print("\n=== 測試市場數據獲取 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        # 測試獲取台積電的市場數據
        symbol = "2330"
        market_data = client.get_market_data(symbol)

        if market_data:
            print(f"✅ 成功獲取 {symbol} 市場數據:")
            print(f"   最新價格: {market_data.get('last_price', 'N/A')}")
            print(f"   開盤價: {market_data.get('open', 'N/A')}")
            print(f"   最高價: {market_data.get('high', 'N/A')}")
            print(f"   最低價: {market_data.get('low', 'N/A')}")
            print(f"   成交量: {market_data.get('volume', 'N/A')}")
            print(f"   漲跌: {market_data.get('change', 'N/A')}")
            print(f"   漲跌幅: {market_data.get('change_percent', 'N/A')}%")
        else:
            print(f"❌ 獲取 {symbol} 市場數據失敗")

    except Exception as e:
        print(f"❌ 測試市場數據異常: {e}")


def test_historical_data():
    """測試歷史數據獲取"""
    print("\n=== 測試歷史數據獲取 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        # 測試獲取台積電的歷史數據（最近5天）
        symbol = "2330"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

        historical_data = client.get_historical_data(symbol, start_date, end_date)

        if historical_data:
            print(f"✅ 成功獲取 {symbol} 歷史數據 ({start_date} 到 {end_date}):")
            print(f"   數據筆數: {len(historical_data)}")

            # 顯示最新的幾筆數據
            for i, data in enumerate(historical_data[-3:]):
                print(f"   第 {len(historical_data) - 2 + i} 筆:")
                print(f"     日期: {data.get('date', 'N/A')}")
                print(f"     開盤: {data.get('open', 'N/A')}")
                print(f"     最高: {data.get('high', 'N/A')}")
                print(f"     最低: {data.get('low', 'N/A')}")
                print(f"     收盤: {data.get('close', 'N/A')}")
                print(f"     成交量: {data.get('volume', 'N/A')}")
        else:
            print(f"❌ 獲取 {symbol} 歷史數據失敗")

    except Exception as e:
        print(f"❌ 測試歷史數據異常: {e}")


def test_multiple_symbols():
    """測試多個股票的數據獲取"""
    print("\n=== 測試多個股票數據獲取 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        # 測試多個股票
        symbols = ["2330", "0050", "2317", "2454"]

        for symbol in symbols:
            print(f"\n--- {symbol} ---")

            # 獲取實時價格
            price = client.get_real_time_price(symbol)
            if price:
                print(f"  實時價格: {price}")
            else:
                print(f"  實時價格: 無法獲取")

            # 獲取市場數據
            market_data = client.get_market_data(symbol)
            if market_data:
                print(f"  開盤價: {market_data.get('open', 'N/A')}")
                print(f"  最高價: {market_data.get('high', 'N/A')}")
                print(f"  最低價: {market_data.get('low', 'N/A')}")
                print(f"  成交量: {market_data.get('volume', 'N/A')}")
            else:
                print(f"  市場數據: 無法獲取")

    except Exception as e:
        print(f"❌ 測試多個股票異常: {e}")


def main():
    """主函數"""
    print("=== 市場數據獲取測試 ===")

    # 設置日誌
    setup_logging()

    # 測試各個功能
    test_market_type_detection()
    test_real_time_price()
    test_market_data()
    test_historical_data()
    test_multiple_symbols()

    print("\n=== 測試完成 ===")
    print("\n📝 注意事項:")
    print("1. 如果使用模擬模式，所有數據都是模擬的")
    print("2. 要獲取真實數據，請配置有效的富邦證券登入憑證")
    print("3. 交易時間外可能無法獲取實時數據")


if __name__ == "__main__":
    main()


