#!/usr/bin/env python3
"""
完整系統測試
測試所有模組的整合和功能
"""

import sys
import os
import yaml
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_system_integration():
    """測試系統整合"""
    print("=" * 60)
    print("完整系統整合測試")
    print("=" * 60)

    try:
        # 讀取配置
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        print("✅ 配置文件載入成功")

        # 測試各個模組
        test_results = {}

        # 1. 測試數據獲取器
        print("\n1. 測試數據獲取器...")
        try:
            from src.modules.data_fetcher import FinMindFetcher

            fetcher = FinMindFetcher(config)
            data = fetcher.get_stock_data("2330", "2024-01-01", "2024-12-31")
            test_results["data_fetcher"] = data is not None and not data.empty
            print(f"   {'✅' if test_results['data_fetcher'] else '❌'} 數據獲取器測試")
        except Exception as e:
            test_results["data_fetcher"] = False
            print(f"   ❌ 數據獲取器測試失敗: {e}")

        # 2. 測試策略執行器
        print("\n2. 測試策略執行器...")
        try:
            from src.modules.strategies.executor import StrategyExecutor

            db_config = config.get("database", {})
            executor = StrategyExecutor(db_config)
            test_results["strategy_executor"] = True
            print("   ✅ 策略執行器測試")
        except Exception as e:
            test_results["strategy_executor"] = False
            print(f"   ❌ 策略執行器測試失敗: {e}")

        # 3. 測試技術指標計算器
        print("\n3. 測試技術指標計算器...")
        try:
            from src.modules.technical_indicators.calculator import (
                TechnicalIndicatorCalculator,
            )

            calculator = TechnicalIndicatorCalculator()
            test_results["indicator_calculator"] = True
            print("   ✅ 技術指標計算器測試")
        except Exception as e:
            test_results["indicator_calculator"] = False
            print(f"   ❌ 技術指標計算器測試失敗: {e}")

        # 4. 測試富邦證券 API 客戶端
        print("\n4. 測試富邦證券 API 客戶端...")
        try:
            from src.modules.trading.fubon_api_client import FubonAPIClient

            client = FubonAPIClient(config)
            health = client.health_check()
            test_results["fubon_client"] = health.get("sdk_available", False)
            print(
                f"   {'✅' if test_results['fubon_client'] else '❌'} 富邦證券 API 客戶端測試"
            )
        except Exception as e:
            test_results["fubon_client"] = False
            print(f"   ❌ 富邦證券 API 客戶端測試失敗: {e}")

        # 5. 測試自動交易器
        print("\n5. 測試自動交易器...")
        try:
            from src.modules.trading.auto_trader import AutoTrader

            trader = AutoTrader(config)
            test_results["auto_trader"] = True
            print("   ✅ 自動交易器測試")
        except Exception as e:
            test_results["auto_trader"] = False
            print(f"   ❌ 自動交易器測試失敗: {e}")

        # 6. 測試風險管理器
        print("\n6. 測試風險管理器...")
        try:
            from src.modules.risk_manager.risk_manager import RiskManager

            risk_manager = RiskManager(config)
            test_results["risk_manager"] = True
            print("   ✅ 風險管理器測試")
        except Exception as e:
            test_results["risk_manager"] = False
            print(f"   ❌ 風險管理器測試失敗: {e}")

        # 7. 測試市場監控器
        print("\n7. 測試市場監控器...")
        try:
            from src.modules.monitor.market_monitor import MarketMonitor

            monitor = MarketMonitor(config)
            test_results["market_monitor"] = True
            print("   ✅ 市場監控器測試")
        except Exception as e:
            test_results["market_monitor"] = False
            print(f"   ❌ 市場監控器測試失敗: {e}")

        # 8. 測試交易協調器
        print("\n8. 測試交易協調器...")
        try:
            from src.modules.trading.trading_orchestrator import TradingOrchestrator

            orchestrator = TradingOrchestrator(config)
            test_results["trading_orchestrator"] = True
            print("   ✅ 交易協調器測試")
        except Exception as e:
            test_results["trading_orchestrator"] = False
            print(f"   ❌ 交易協調器測試失敗: {e}")

        # 總結測試結果
        print("\n" + "=" * 60)
        print("測試結果總結")
        print("=" * 60)

        total_tests = len(test_results)
        passed_tests = sum(test_results.values())

        for module, result in test_results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"{module}: {status}")

        print(f"\n總體結果: {passed_tests}/{total_tests} 個模組測試通過")

        if passed_tests == total_tests:
            print("🎉 所有模組測試通過！系統整合成功")
        else:
            print("⚠️  部分模組測試失敗，需要檢查相關問題")

        return test_results

    except Exception as e:
        print(f"❌ 系統整合測試失敗: {e}")
        return {}


def test_strategy_execution():
    """測試策略執行"""
    print("\n" + "=" * 60)
    print("策略執行測試")
    print("=" * 60)

    try:
        # 讀取配置
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 測試策略執行
        from src.modules.strategies.executor import StrategyExecutor

        db_config = config.get("database", {})
        executor = StrategyExecutor(db_config)

        # 執行策略
        results = executor.execute_strategies(["2330"])

        if results:
            print(f"✅ 策略執行成功，產生 {len(results)} 個信號")

            # 顯示前幾個信號
            for i, signal in enumerate(results[:3]):
                print(
                    f"  信號 {i+1}: {signal.get('symbol')} - {signal.get('signal', {}).get('action', 'unknown')}"
                )
        else:
            print("⚠️  策略執行完成，但沒有產生信號")

        return True

    except Exception as e:
        print(f"❌ 策略執行測試失敗: {e}")
        return False


def test_risk_management():
    """測試風險管理"""
    print("\n" + "=" * 60)
    print("風險管理測試")
    print("=" * 60)

    try:
        # 讀取配置
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 測試風險管理
        from src.modules.risk_manager.risk_manager import RiskManager

        risk_manager = RiskManager(config)

        # 測試交易限制檢查
        test_signal = {
            "symbol": "2330",
            "signal": {"action": "buy"},
            "quantity": 1000,
            "price": 100.0,
        }

        allowed = risk_manager.check_trade_allowed(test_signal)
        print(f"✅ 風險管理測試: 交易{'允許' if allowed else '拒絕'}")

        # 獲取風險指標
        metrics = risk_manager.get_risk_metrics()
        print(f"✅ 風險指標獲取成功: 總資金 = {metrics.get('total_capital', 0):,.0f}")

        return True

    except Exception as e:
        print(f"❌ 風險管理測試失敗: {e}")
        return False


def test_market_monitoring():
    """測試市場監控"""
    print("\n" + "=" * 60)
    print("市場監控測試")
    print("=" * 60)

    try:
        # 讀取配置
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 測試市場監控
        from src.modules.monitor.market_monitor import MarketMonitor

        monitor = MarketMonitor(config)

        # 獲取市場狀態
        status = monitor.get_market_status()
        print(f"✅ 市場狀態獲取成功: 開盤狀態 = {status.get('is_open', False)}")

        # 添加價格警報
        monitor.add_price_alert("2330", 100.0, "above")
        print("✅ 價格警報添加成功")

        return True

    except Exception as e:
        print(f"❌ 市場監控測試失敗: {e}")
        return False


if __name__ == "__main__":
    print("完整系統測試")
    print("=" * 60)

    # 測試系統整合
    integration_results = test_system_integration()

    # 測試策略執行
    strategy_success = test_strategy_execution()

    # 測試風險管理
    risk_success = test_risk_management()

    # 測試市場監控
    monitor_success = test_market_monitoring()

    # 最終總結
    print("\n" + "=" * 60)
    print("最終測試總結")
    print("=" * 60)

    total_modules = len(integration_results)
    passed_modules = sum(integration_results.values())

    print(f"系統整合: {passed_modules}/{total_modules} 個模組正常")
    print(f"策略執行: {'✅ 正常' if strategy_success else '❌ 失敗'}")
    print(f"風險管理: {'✅ 正常' if risk_success else '❌ 失敗'}")
    print(f"市場監控: {'✅ 正常' if monitor_success else '❌ 失敗'}")

    if (
        passed_modules == total_modules
        and strategy_success
        and risk_success
        and monitor_success
    ):
        print("\n🎉 所有測試通過！系統準備就緒")
        print("💡 可以開始使用自動交易功能")
    else:
        print("\n⚠️  部分測試失敗，請檢查相關問題")
        print("💡 建議先解決問題再使用自動交易功能")
