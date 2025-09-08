#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富邦證券 API 測試腳本
用於測試富邦證券 API 連接和功能
"""

import os
import sys
import yaml
from datetime import datetime
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
        "logs/test_fubon_api.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def test_api_connection():
    """測試 API 連接"""
    print("=== 測試富邦證券 API 連接 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return False

    try:
        client = FubonAPIClient(config["fubon"])
        print("✅ 富邦證券 API 客戶端創建成功")
        return True
    except Exception as e:
        print(f"❌ 創建 API 客戶端失敗: {e}")
        return False


def test_account_info():
    """測試獲取帳戶信息"""
    print("\n=== 測試獲取帳戶信息 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])
        account_info = client.get_account_info()

        if account_info:
            print("✅ 成功獲取帳戶信息:")
            print(f"   帳戶 ID: {account_info.get('account_id', 'N/A')}")
            print(f"   帳戶類型: {account_info.get('account_type', 'N/A')}")
            print(f"   狀態: {account_info.get('status', 'N/A')}")
        else:
            print("❌ 獲取帳戶信息失敗")

    except Exception as e:
        print(f"❌ 測試帳戶信息異常: {e}")


def test_positions():
    """測試獲取持倉信息"""
    print("\n=== 測試獲取持倉信息 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])
        positions = client.get_positions()

        if positions:
            print("✅ 成功獲取持倉信息:")
            if isinstance(positions, list):
                print(f"   持倉數量: {len(positions)}")
                for pos in positions[:3]:  # 只顯示前3個
                    print(
                        f"   股票: {pos.get('symbol', 'N/A')}, 數量: {pos.get('quantity', 0)}"
                    )
            else:
                print(f"   持倉數據: {positions}")
        else:
            print("❌ 獲取持倉信息失敗")

    except Exception as e:
        print(f"❌ 測試持倉信息異常: {e}")


def test_market_data():
    """測試獲取市場數據"""
    print("\n=== 測試獲取市場數據 ===")

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
        else:
            print(f"❌ 獲取 {symbol} 市場數據失敗")

    except Exception as e:
        print(f"❌ 測試市場數據異常: {e}")


def test_real_time_price():
    """測試獲取實時價格"""
    print("\n=== 測試獲取實時價格 ===")

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


def test_trading_conditions():
    """測試交易條件檢查"""
    print("\n=== 測試交易條件檢查 ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        symbol = "2330"
        target_price = 800.0

        # 測試買入條件
        buy_condition = client.check_trading_conditions(symbol, target_price, "buy")
        print(
            f"買入條件檢查 (目標價 {target_price}): {'✅ 滿足' if buy_condition else '❌ 不滿足'}"
        )

        # 測試賣出條件
        sell_condition = client.check_trading_conditions(symbol, target_price, "sell")
        print(
            f"賣出條件檢查 (目標價 {target_price}): {'✅ 滿足' if sell_condition else '❌ 不滿足'}"
        )

    except Exception as e:
        print(f"❌ 測試交易條件異常: {e}")


def test_order_placement():
    """測試下單功能（模擬）"""
    print("\n=== 測試下單功能（模擬） ===")

    config = load_config()
    if not config or not config.get("fubon"):
        print("❌ 未配置富邦證券 API")
        return

    try:
        client = FubonAPIClient(config["fubon"])

        # 模擬下單數據
        order_data = {
            "symbol": "2330",
            "side": "buy",
            "quantity": 1000,
            "price": 800.0,
            "order_type": "limit",
            "time_in_force": "day",
        }

        print(f"模擬下單: {order_data}")

        # 注意：這裡不會真正下單，只是測試 API 調用
        # 如果要真正下單，需要有效的 API 憑證
        print("⚠️  注意：這是模擬測試，不會真正下單")

    except Exception as e:
        print(f"❌ 測試下單功能異常: {e}")


def main():
    """主函數"""
    print("=== 富邦證券 API 測試 ===")

    # 設置日誌
    setup_logging()

    # 測試各個功能
    if test_api_connection():
        test_account_info()
        test_positions()
        test_market_data()
        test_real_time_price()
        test_trading_conditions()
        test_order_placement()

    print("\n=== 測試完成 ===")
    print("\n📝 注意事項:")
    print("1. 要進行真實交易，請在 config.yaml 中填入有效的 API 憑證")
    print("2. 建議先在模擬環境中測試所有功能")
    print("3. 請確保了解交易風險，謹慎使用自動交易功能")


if __name__ == "__main__":
    main()


