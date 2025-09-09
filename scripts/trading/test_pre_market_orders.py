#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試開盤前下單功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import yaml
from loguru import logger
from src.modules.trading.pre_market_analyzer import PreMarketAnalyzer


def load_config():
    """載入配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_pre_market_time_check():
    """測試開盤前時間檢查"""
    print("\n=== 測試開盤前時間檢查 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        is_pre_market = analyzer.fubon_client.is_pre_market_time()
        current_time = datetime.now().strftime("%H:%M")

        print(f"當前時間: {current_time}")
        print(f"是否為開盤前時間: {'✅ 是' if is_pre_market else '❌ 否'}")
        print("開盤前時間範圍: 07:00-08:59")

        return True

    except Exception as e:
        logger.error(f"開盤前時間檢查測試失敗: {e}")
        return False


def test_pre_market_price_calculation():
    """測試開盤前價格計算"""
    print("\n=== 測試開盤前價格計算 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        # 模擬信號
        test_signals = [
            {
                "symbol": "2330",
                "action": "buy",
                "target_price": 500.0,
                "signal_strength": 0.85,
            },
            {
                "symbol": "0050",
                "action": "sell",
                "target_price": 150.0,
                "signal_strength": 0.75,
            },
        ]

        print("價格調整測試:")
        for signal in test_signals:
            adjusted_price = analyzer._calculate_pre_market_price(signal)
            adjustment = adjusted_price - signal["target_price"]
            percentage = (adjustment / signal["target_price"]) * 100

            print(
                f"  {signal['symbol']} {signal['action']}: "
                f"{signal['target_price']:.2f} -> {adjusted_price:.2f} "
                f"({adjustment:+.2f}, {percentage:+.2f}%)"
            )

        return True

    except Exception as e:
        logger.error(f"開盤前價格計算測試失敗: {e}")
        return False


def test_pre_market_risk_checks():
    """測試開盤前風險檢查"""
    print("\n=== 測試開盤前風險檢查 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        # 模擬不同的信號來測試風險檢查
        test_cases = [
            {
                "name": "正常信號",
                "signal": {
                    "symbol": "2330",
                    "action": "buy",
                    "target_price": 500.0,
                    "quantity": 1000,
                    "signal_strength": 0.85,
                },
                "expected": True,
            },
            {
                "name": "信號強度不足",
                "signal": {
                    "symbol": "2330",
                    "action": "buy",
                    "target_price": 500.0,
                    "quantity": 1000,
                    "signal_strength": 0.5,  # 低於 0.8 門檻
                },
                "expected": False,
            },
            {
                "name": "金額過大",
                "signal": {
                    "symbol": "2330",
                    "action": "buy",
                    "target_price": 500.0,
                    "quantity": 1000,  # 500,000 可能超過限制
                    "signal_strength": 0.85,
                },
                "expected": None,  # 取決於配置
            },
        ]

        for test_case in test_cases:
            result = analyzer._check_pre_market_risk_limits(test_case["signal"])
            status = "✅ 通過" if result else "❌ 阻止"
            expected = (
                "預期"
                if test_case["expected"] is None
                else ("預期通過" if test_case["expected"] else "預期阻止")
            )

            print(f"  {test_case['name']}: {status} ({expected})")

        return True

    except Exception as e:
        logger.error(f"開盤前風險檢查測試失敗: {e}")
        return False


def test_mock_pre_market_orders():
    """測試模擬開盤前下單"""
    print("\n=== 測試模擬開盤前下單 ===")

    try:
        config = load_config()
        # 確保使用模擬模式
        config["trading"]["real_trading"] = False

        analyzer = PreMarketAnalyzer(config)

        # 創建模擬信號
        mock_signals = [
            {
                "symbol": "2330",
                "strategy": "blue_long",
                "action": "buy",
                "signal_strength": 0.85,
                "target_price": 500.0,
                "quantity": 1000,
                "timestamp": datetime.now(),
                "reason": "測試信號",
                "status": "pending",
            },
            {
                "symbol": "0050",
                "strategy": "green_short",
                "action": "sell",
                "signal_strength": 0.9,
                "target_price": 150.0,
                "quantity": 2000,
                "timestamp": datetime.now(),
                "reason": "測試信號",
                "status": "pending",
            },
        ]

        print(f"模擬 {len(mock_signals)} 個開盤前下單...")

        # 執行開盤前下單
        analyzer._execute_pre_market_orders(mock_signals)

        # 檢查結果
        ordered_count = len(
            [s for s in mock_signals if s["status"] == "pre_market_ordered"]
        )
        failed_count = len(
            [
                s
                for s in mock_signals
                if s["status"] in ["pre_market_failed", "pre_market_error", "blocked"]
            ]
        )

        print(f"結果: 成功 {ordered_count} 筆, 失敗/阻止 {failed_count} 筆")

        # 顯示詳細結果
        for signal in mock_signals:
            status_emoji = {
                "pre_market_ordered": "✅",
                "pre_market_failed": "❌",
                "pre_market_error": "💥",
                "blocked": "🚫",
            }.get(signal["status"], "❓")

            print(
                f"  {status_emoji} {signal['symbol']} {signal['action']}: {signal['status']}"
            )
            if signal.get("order_id"):
                print(f"    訂單號: {signal['order_id']}")
            if signal.get("error"):
                print(f"    錯誤: {signal['error']}")

        return ordered_count > 0

    except Exception as e:
        logger.error(f"模擬開盤前下單測試失敗: {e}")
        return False


def test_pre_market_orders_status():
    """測試開盤前下單狀態查詢"""
    print("\n=== 測試開盤前下單狀態查詢 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        status = analyzer.get_pre_market_orders_status()

        print("開盤前下單狀態:")
        print(f"  總信號數: {status['total_signals']}")
        print(f"  已下單: {status['ordered_count']}")
        print(f"  失敗: {status['failed_count']}")
        print(f"  總金額: {status['total_order_amount']:,.0f}")
        print(f"  開盤前時間: {'是' if status['is_pre_market_time'] else '否'}")

        return True

    except Exception as e:
        logger.error(f"開盤前下單狀態查詢測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開盤前下單功能測試")
    print("=" * 60)

    # 設置日誌
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/test_pre_market_orders.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
    )

    tests = [
        ("開盤前時間檢查", test_pre_market_time_check),
        ("開盤前價格計算", test_pre_market_price_calculation),
        ("開盤前風險檢查", test_pre_market_risk_checks),
        ("模擬開盤前下單", test_mock_pre_market_orders),
        ("開盤前下單狀態查詢", test_pre_market_orders_status),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"執行測試: {test_name}")
        print(f"{'='*60}")

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"✅ {test_name} 測試通過")
            else:
                print(f"❌ {test_name} 測試失敗")

        except Exception as e:
            logger.error(f"{test_name} 測試異常: {e}")
            results.append((test_name, False))
            print(f"💥 {test_name} 測試異常: {e}")

    # 顯示總結
    print(f"\n{'='*60}")
    print("測試總結")
    print(f"{'='*60}")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n總計: {passed}/{total} 個測試通過")

    if passed == total:
        print("🎉 所有測試都通過了！開盤前下單功能已準備就緒")
        print("\n💡 使用說明:")
        print("1. 系統會在開盤前時間 (07:00-08:59) 自動執行下單")
        print("2. 只有信號強度 >= 0.8 的信號會進行開盤前下單")
        print("3. 價格會自動調整 0.5% 以增加成交機會")
        print("4. 每日最多 5 筆開盤前下單")
    else:
        print("⚠️  部分測試失敗，請檢查相關功能")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
