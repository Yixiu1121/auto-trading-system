#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動交易測試腳本
用於測試自動交易功能
"""

import os
import sys
import yaml
from datetime import datetime
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from modules.trading.auto_trader import AutoTrader


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
        "logs/test_auto_trading.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def test_signal_calculation():
    """測試信號計算"""
    print("=== 測試信號計算 ===")

    config = load_config()
    if not config:
        return

    auto_trader = AutoTrader(config)

    # 計算隔日買賣點
    signals = auto_trader.calculate_next_day_signals("2330")

    print(f"計算到 {len(signals)} 個信號:")
    for signal in signals:
        print(f"  策略: {signal['strategy']}")
        print(f"  動作: {signal['signal']['signal']['action']}")
        print(f"  價格: {signal['signal']['price']}")
        print(f"  日期: {signal['signal']['date']}")
        print()


def test_price_monitoring():
    """測試價格監控"""
    print("=== 測試價格監控 ===")

    config = load_config()
    if not config:
        return

    auto_trader = AutoTrader(config)

    # 模擬一些信號
    mock_signals = [
        {
            "strategy": "blue_short",
            "signal": {"signal": {"action": "sell"}, "price": 800.0},
            "stock_id": "2330",
        },
        {
            "strategy": "blue_long",
            "signal": {"signal": {"action": "buy"}, "price": 1200.0},
            "stock_id": "2330",
        },
    ]

    # 設置監控
    auto_trader.setup_price_monitoring(mock_signals)

    print(f"設置了 {len(auto_trader.monitoring_stocks)} 個監控:")
    for monitor in auto_trader.monitoring_stocks:
        print(f"  股票: {monitor['stock_id']}")
        print(f"  動作: {monitor['action']}")
        print(f"  目標價格: {monitor['target_price']}")
        print(f"  策略: {monitor['strategy']}")
        print()


def test_order_quantity_calculation():
    """測試訂單數量計算"""
    print("=== 測試訂單數量計算 ===")

    config = load_config()
    if not config:
        return

    auto_trader = AutoTrader(config)

    # 測試不同價格的買入數量
    test_prices = [500, 800, 1200, 1500]

    for price in test_prices:
        quantity = auto_trader.calculate_order_quantity("2330", price, "buy")
        amount = quantity * price
        print(f"  價格: {price}, 數量: {quantity}, 金額: {amount:,}")

    # 測試賣出數量
    sell_quantity = auto_trader.calculate_order_quantity("2330", 1000, "sell")
    print(f"  賣出數量: {sell_quantity}")


def main():
    """主函數"""
    print("=== 自動交易系統測試 ===")

    # 設置日誌
    setup_logging()

    # 測試各個功能
    test_signal_calculation()
    test_price_monitoring()
    test_order_quantity_calculation()

    print("=== 測試完成 ===")


if __name__ == "__main__":
    main()


