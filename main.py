#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動化程式交易系統 - 主程式控制模組
基於富邦證券 API 的藍綠橘交易策略系統
"""

import os
import sys
import time
import signal
import schedule
import yaml
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import pytz

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# 導入自定義模組
from src.modules.strategies.executor import StrategyExecutor
from src.modules.data_fetcher import FinMindFetcher
from src.modules.technical_indicators.calculator import TechnicalIndicatorCalculator
from src.modules.technical_indicators.storage import TechnicalIndicatorStorage
from src.modules.trading.trading_orchestrator import TradingOrchestrator


class TradingSystem:
    """自動化程式交易系統主控制器"""

    def __init__(self, config_path="config.yaml"):
        """初始化交易系統"""
        self.config = self._load_config(config_path)
        self.running = False
        self.modules = {}

        # 設置日誌
        self._setup_logging()

        # 初始化模組
        self._initialize_modules()

        # 設置信號處理
        self._setup_signal_handlers()

        logger.info("交易系統初始化完成")

    def _load_config(self, config_path):
        """載入配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
            logger.info(f"配置文件載入成功: {config_path}")
            return config
        except Exception as e:
            logger.error(f"配置文件載入失敗: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """設置日誌系統"""
        # 創建日誌目錄
        os.makedirs("logs", exist_ok=True)

        # 配置日誌
        logger.add(
            "logs/trading_system.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    def _initialize_modules(self):
        """初始化所有模組"""
        try:
            # 初始化策略執行器
            db_config = self.config.get("database", {})
            self.modules["strategy_executor"] = StrategyExecutor(db_config)

            # 初始化數據獲取器
            self.modules["data_fetcher"] = FinMindFetcher(self.config)

            # 初始化技術指標計算器
            self.modules["indicator_calculator"] = TechnicalIndicatorCalculator()

            # 初始化技術指標存儲器
            self.modules["indicator_storage"] = TechnicalIndicatorStorage(db_config)

            # 初始化交易協調器
            self.modules["trading_orchestrator"] = TradingOrchestrator(self.config)

            logger.info("所有模組初始化完成")

        except Exception as e:
            logger.error(f"模組初始化失敗: {e}")
            raise

    def _setup_signal_handlers(self):
        """設置信號處理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"收到信號 {signum}，正在關閉系統...")
        self.stop()

    def run_strategies(
        self, stock_id="2330", start_date="2024-01-01", end_date="2025-08-29"
    ):
        """執行策略分析"""
        print("=== 交易策略執行工具 ===")

        try:
            executor = self.modules["strategy_executor"]
            print("✅ 策略執行器創建成功")

            print(f"\n--- 執行策略參數 ---")
            print(f"股票代碼: {stock_id}")
            print(f"時間範圍: {start_date} 到 {end_date}")

            # 執行所有策略
            print(f"\n--- 開始執行策略 ---")
            results = executor.execute_all_strategies(stock_id, start_date, end_date)

            # 顯示結果
            print(f"\n=== 策略執行完成 ===")
            for strategy_name, result in results.items():
                self._print_strategy_result(result)

            # 總結
            print(f"\n=== 執行總結 ===")
            total_signals = sum(
                r.get("total_signals", 0)
                for r in results.values()
                if r.get("success", False)
            )
            successful_strategies = sum(
                1 for r in results.values() if r.get("success", False)
            )

            print(f"成功執行的策略: {successful_strategies}/{len(results)}")
            print(f"總信號數: {total_signals}")

            if total_signals > 0:
                print(f"✅ 策略執行成功，產生了 {total_signals} 個交易信號")
            else:
                print(f"⚠️  策略執行完成，但沒有產生交易信號")

            return results

        except Exception as e:
            logger.error(f"策略執行過程中發生錯誤: {e}")
            print(f"❌ 策略執行失敗: {e}")
            return None

    def _print_strategy_result(self, result: dict):
        """打印策略執行結果"""
        if not result.get("success", False):
            print(f"❌ 策略執行失敗: {result.get('error', '未知錯誤')}")
            return

        print(f"\n=== {result['strategy_name'].upper()} 策略執行結果 ===")
        print(f"股票代碼: {result['stock_id']}")
        print(f"數據期間: {result['data_period']}")
        print(f"數據點數: {result['total_data_points']}")
        print(f"總信號數: {result['total_signals']}")
        print(f"買入信號: {result['buy_signals']}")
        print(f"賣出信號: {result['sell_signals']}")

        # 顯示最新數據
        latest = result["latest_data"]
        print(f"\n最新數據:")
        print(f"  日期: {latest['date']}")
        print(f"  收盤價: {latest['close']:.2f}")

        # 安全地格式化數值
        ma_blue_str = (
            f"{latest['ma_blue']:.2f}" if latest["ma_blue"] is not None else "N/A"
        )
        ma_green_str = (
            f"{latest['ma_green']:.2f}" if latest["ma_green"] is not None else "N/A"
        )
        ma_orange_str = (
            f"{latest['ma_orange']:.2f}" if latest["ma_orange"] is not None else "N/A"
        )
        trend_str = (
            f"{latest['trend_strength']:.2f}"
            if latest["trend_strength"] is not None
            else "N/A"
        )

        print(f"  藍線: {ma_blue_str}")
        print(f"  綠線: {ma_green_str}")
        print(f"  橘線: {ma_orange_str}")
        print(f"  趨勢強度: {trend_str}")

        # 顯示最近的信號
        if result["signals"]:
            print(f"\n最近的信號:")
            for signal in result["signals"][-5:]:  # 顯示最近5個信號
                # 安全地格式化信號數據
                ma_blue_str = (
                    f"{signal['ma_blue']:.2f}"
                    if signal["ma_blue"] is not None
                    else "N/A"
                )
                print(
                    f"  {signal['date']} | {signal['signal']['action'].upper()} | 價格: {signal['price']:.2f} | 藍線: {ma_blue_str}"
                )
        else:
            print(f"\n⚠️  在指定期間內沒有產生任何交易信號")

    def calculate_indicators(self, stock_id="2330"):
        """計算技術指標"""
        print("=== 技術指標計算工具 ===")

        try:
            calculator = self.modules["indicator_calculator"]
            storage = self.modules["indicator_storage"]

            print("✅ 技術指標計算器創建成功")
            print("✅ 技術指標存儲器創建成功")

            print(f"\n--- 開始處理股票 {stock_id} 的技術指標 ---")

            # 獲取價格數據
            fetcher = self.modules["data_fetcher"]
            df_price = fetcher.get_stock_data(stock_id, "2022-01-01", "2025-08-29")

            if df_price is None or df_price.empty:
                print(f"❌ 無法獲取股票 {stock_id} 的價格數據")
                return False

            # 計算技術指標
            df_indicators = calculator.calculate_all_indicators(df_price)

            if df_indicators is None or df_indicators.empty:
                print(f"❌ 無法計算股票 {stock_id} 的技術指標")
                return False

            # 顯示指標摘要
            summary = calculator.get_indicator_summary(df_indicators)
            if summary:
                print("技術指標摘要:")
                print(f"  最新日期: {summary['latest_date']}")
                print(f"  最新收盤: {summary['latest_close']:.2f}")
                print(
                    f"  藍線: {summary['ma_blue']:.2f if summary['ma_blue'] else 'N/A'}"
                )
                print(
                    f"  綠線: {summary['ma_green']:.2f if summary['ma_green'] else 'N/A'}"
                )
                print(
                    f"  橘線: {summary['ma_orange']:.2f if summary['ma_orange'] else 'N/A'}"
                )
                print(f"  趨勢方向: {summary['trend_direction']}")
                print(f"  均線排列: {summary['ma_alignment']}")

            # 存儲技術指標
            success = storage.store_technical_indicators(stock_id, df_indicators)

            if success:
                print(f"✅ 股票 {stock_id} 技術指標計算和存儲成功")
                return True
            else:
                print(f"❌ 股票 {stock_id} 技術指標存儲失敗")
                return False

        except Exception as e:
            logger.error(f"技術指標計算過程中發生錯誤: {e}")
            print(f"❌ 技術指標計算失敗: {e}")
            return False

    def start_auto_trading(self):
        """啟動自動交易"""
        print("=== 啟動自動交易系統 ===")

        try:
            orchestrator = self.modules["trading_orchestrator"]

            print("✅ 交易協調器創建成功")
            print("🔄 正在啟動自動交易系統...")

            # 啟動交易協調器
            orchestrator.start()

            print("✅ 自動交易系統啟動成功")
            print("📊 系統正在監控市場並執行交易策略")
            print("⏰ 按 Ctrl+C 停止系統")

            # 保持系統運行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 收到停止信號，正在關閉系統...")
                orchestrator.stop()
                print("✅ 自動交易系統已停止")

        except Exception as e:
            logger.error(f"自動交易系統啟動失敗: {e}")
            print(f"❌ 自動交易系統啟動失敗: {e}")

    def get_system_status(self):
        """獲取系統狀態"""
        print("=== 系統狀態檢查 ===")

        try:
            # 檢查各個模組狀態
            for name, module in self.modules.items():
                if hasattr(module, "get_status"):
                    status = module.get_status()
                    print(f"✅ {name}: {status.get('running', 'unknown')}")
                else:
                    print(f"ℹ️  {name}: 無狀態信息")

            # 檢查交易協調器詳細狀態
            if "trading_orchestrator" in self.modules:
                orchestrator = self.modules["trading_orchestrator"]
                status = orchestrator.get_status()

                print(f"\n📊 交易系統狀態:")
                print(f"  運行狀態: {'運行中' if status.get('running') else '已停止'}")
                print(f"  最後更新: {status.get('timestamp', 'N/A')}")

                # 顯示模組狀態
                modules_status = status.get("modules", {})
                for module_name, module_status in modules_status.items():
                    print(f"  {module_name}: {module_status}")

        except Exception as e:
            logger.error(f"獲取系統狀態失敗: {e}")
            print(f"❌ 獲取系統狀態失敗: {e}")

    def start(self):
        """啟動交易系統"""
        if self.running:
            logger.warning("系統已在運行中")
            return

        try:
            logger.info("啟動自動化程式交易系統...")
            self.running = True
            logger.info("系統啟動成功")

        except Exception as e:
            logger.error(f"系統啟動失敗: {e}")
            raise

    def stop(self):
        """停止交易系統"""
        if not self.running:
            return

        logger.info("正在關閉交易系統...")
        self.running = False

        # 關閉各模組
        for name, module in self.modules.items():
            try:
                if hasattr(module, "stop"):
                    module.stop()
                    logger.debug(f"模組 {name} 已關閉")
            except Exception as e:
                logger.error(f"關閉模組 {name} 時發生錯誤: {e}")

        logger.info("交易系統已關閉")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="自動化程式交易系統")
    parser.add_argument(
        "--mode",
        choices=["strategies", "indicators", "auto-trading", "status", "interactive"],
        default="interactive",
        help="運行模式",
    )
    parser.add_argument("--stock", default="2330", help="股票代碼")
    parser.add_argument("--start-date", default="2024-01-01", help="開始日期")
    parser.add_argument("--end-date", default="2025-08-29", help="結束日期")

    args = parser.parse_args()

    try:
        # 創建交易系統
        trading_system = TradingSystem()

        if args.mode == "strategies":
            # 執行策略模式
            trading_system.run_strategies(args.stock, args.start_date, args.end_date)

        elif args.mode == "indicators":
            # 計算技術指標模式
            trading_system.calculate_indicators(args.stock)

        elif args.mode == "auto-trading":
            # 自動交易模式
            trading_system.start_auto_trading()

        elif args.mode == "status":
            # 系統狀態檢查模式
            trading_system.get_system_status()

        elif args.mode == "interactive":
            # 互動模式
            print("=== 自動化程式交易系統 ===")
            print("請選擇功能:")
            print("1. 執行策略分析")
            print("2. 計算技術指標")
            print("3. 啟動自動交易")
            print("4. 系統狀態檢查")
            print("5. 退出")

            while True:
                choice = input("\n請輸入選項 (1-5): ").strip()

                if choice == "1":
                    stock = input("請輸入股票代碼 (預設: 2330): ").strip() or "2330"
                    start_date = (
                        input("請輸入開始日期 (預設: 2024-01-01): ").strip()
                        or "2024-01-01"
                    )
                    end_date = (
                        input("請輸入結束日期 (預設: 2025-08-29): ").strip()
                        or "2025-08-29"
                    )

                    trading_system.run_strategies(stock, start_date, end_date)

                elif choice == "2":
                    stock = input("請輸入股票代碼 (預設: 2330): ").strip() or "2330"
                    trading_system.calculate_indicators(stock)

                elif choice == "3":
                    trading_system.start_auto_trading()

                elif choice == "4":
                    trading_system.get_system_status()

                elif choice == "5":
                    print("謝謝使用！")
                    break

                else:
                    print("無效選項，請重新輸入")

    except Exception as e:
        logger.error(f"系統運行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
