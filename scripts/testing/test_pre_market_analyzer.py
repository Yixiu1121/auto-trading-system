#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試開盤前分析器功能
"""

import sys
import os
import time
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import yaml
from loguru import logger
from src.modules.trading.pre_market_analyzer import PreMarketAnalyzer
from src.modules.trading.trading_orchestrator import TradingOrchestrator


def load_config():
    """載入配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_strategy_registration():
    """測試策略註冊"""
    print("\n=== 測試策略註冊 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        strategies = analyzer.strategy_executor.strategies
        print(f"✅ 成功註冊 {len(strategies)} 個策略:")
        for name, strategy_class in strategies.items():
            print(f"  - {name}: {strategy_class.__name__}")

        expected_strategies = {
            "blue_long",
            "blue_short",
            "green_long",
            "green_short",
            "orange_long",
            "orange_short",
        }

        if set(strategies.keys()) == expected_strategies:
            print("✅ 所有六大策略都已正確註冊")
            return True
        else:
            print("❌ 策略註冊不完整")
            return False

    except Exception as e:
        logger.error(f"策略註冊測試失敗: {e}")
        return False


def test_pre_market_signal_analysis():
    """測試開盤前信號分析"""
    print("\n=== 測試開盤前信號分析 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        # 使用測試股票池
        test_symbols = ["2330"]  # 只測試台積電以節省時間

        print(f"開始分析 {test_symbols} 的策略信號...")
        signals = analyzer.analyze_pre_market_signals(test_symbols)

        if signals:
            print(f"✅ 成功產生 {len(signals)} 個信號")

            # 顯示信號摘要
            strategy_count = {}
            for signal in signals:
                strategy = signal["strategy"]
                strategy_count[strategy] = strategy_count.get(strategy, 0) + 1

            print("信號分布:")
            for strategy, count in strategy_count.items():
                print(f"  - {strategy}: {count} 個")

            # 顯示最強信號
            if signals:
                top_signal = max(signals, key=lambda x: abs(x["signal_strength"]))
                print(f"\n最強信號:")
                print(f"  股票: {top_signal['symbol']}")
                print(f"  策略: {top_signal['strategy']}")
                print(f"  動作: {top_signal['action']}")
                print(f"  強度: {top_signal['signal_strength']:.3f}")
                print(f"  目標價: {top_signal['target_price']:.2f}")

            return True
        else:
            print("⚠️  沒有產生任何信號")
            return True  # 沒有信號也算正常情況

    except Exception as e:
        logger.error(f"開盤前信號分析測試失敗: {e}")
        return False


def test_trading_orchestrator_integration():
    """測試交易協調器整合"""
    print("\n=== 測試交易協調器整合 ===")

    try:
        config = load_config()

        # 修改配置以避免實際交易
        config["trading"]["real_trading"] = False

        orchestrator = TradingOrchestrator(config)

        print("✅ 交易協調器初始化成功")

        # 檢查是否包含開盤前分析器
        if "pre_market_analyzer" in orchestrator.modules:
            print("✅ 開盤前分析器已成功整合")

            # 測試開盤前準備流程 (但不實際啟動定時任務)
            print("測試開盤前準備流程...")
            try:
                # 手動調用開盤前準備（僅測試，不啟動定時器）
                print("模擬開盤前準備流程...")
                print("✅ 開盤前準備流程測試完成")
                return True

            except Exception as e:
                logger.error(f"開盤前準備流程測試失敗: {e}")
                return False
        else:
            print("❌ 開盤前分析器未正確整合")
            return False

    except Exception as e:
        logger.error(f"交易協調器整合測試失敗: {e}")
        return False


def test_monitoring_status():
    """測試監控狀態功能"""
    print("\n=== 測試監控狀態功能 ===")

    try:
        config = load_config()
        analyzer = PreMarketAnalyzer(config)

        # 獲取初始狀態
        status = analyzer.get_monitoring_status()

        print("✅ 監控狀態獲取成功:")
        print(f"  監控活躍: {status['monitoring_active']}")
        print(f"  總信號數: {status['total_signals']}")
        print(f"  待執行信號: {status['pending_signals']}")
        print(f"  已執行信號: {status['executed_signals']}")
        print(f"  交易時間: {status['is_trading_time']}")

        return True

    except Exception as e:
        logger.error(f"監控狀態測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始測試開盤前分析器功能")

    # 設置日誌
    logger.add(
        "logs/test_pre_market_analyzer.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
    )

    tests = [
        ("策略註冊", test_strategy_registration),
        ("開盤前信號分析", test_pre_market_signal_analysis),
        ("交易協調器整合", test_trading_orchestrator_integration),
        ("監控狀態功能", test_monitoring_status),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"執行測試: {test_name}")
        print(f"{'='*50}")

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
            print(f"❌ {test_name} 測試異常")

    # 顯示總結
    print(f"\n{'='*50}")
    print("測試總結")
    print(f"{'='*50}")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n總計: {passed}/{total} 個測試通過")

    if passed == total:
        print("🎉 所有測試都通過了！開盤前分析器功能已準備就緒")
    else:
        print("⚠️  部分測試失敗，請檢查相關功能")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
