#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
開盤前分析工具
執行六大策略分析並準備自動交易
"""

import sys
import os
import argparse
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import yaml
from loguru import logger
from datetime import datetime
from src.modules.trading.pre_market_analyzer import PreMarketAnalyzer
from src.modules.trading.trading_orchestrator import TradingOrchestrator


def load_config(config_path="config.yaml"):
    """載入配置文件"""
    config_file = os.path.join(os.path.dirname(__file__), "..", "..", config_path)
    with open(config_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def display_welcome():
    """顯示歡迎信息"""
    print("🚀 開盤前六大策略分析系統")
    print("=" * 60)
    print("本系統將分析以下六大策略的交易信號：")
    print("1. 藍線多頭策略 (blue_long)")
    print("2. 藍線空頭策略 (blue_short)")
    print("3. 綠線多頭策略 (green_long)")
    print("4. 綠線空頭策略 (green_short)")
    print("5. 橘線多頭策略 (orange_long)")
    print("6. 橘線空頭策略 (orange_short)")
    print("=" * 60)


def run_pre_market_analysis(config, stock_symbols=None, mode="analysis"):
    """
    執行開盤前分析

    Args:
        config: 配置字典
        stock_symbols: 股票代碼列表
        mode: 運行模式 ("analysis" 或 "full")
    """
    try:
        print(f"\n📊 開始執行開盤前分析 (模式: {mode})")
        print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 創建開盤前分析器
        analyzer = PreMarketAnalyzer(config)

        # 如果沒有指定股票，使用配置中的股票池
        if stock_symbols is None:
            stock_symbols = config.get("trading", {}).get(
                "stock_pool", ["2330", "0050", "1101"]
            )

        print(f"\n🎯 分析目標股票: {', '.join(stock_symbols)}")

        # 執行策略分析
        signals = analyzer.analyze_pre_market_signals(stock_symbols)

        if not signals:
            print("\n⚠️  沒有產生任何交易信號")
            print("可能原因:")
            print("- 數據庫未連接 (需要啟動 PostgreSQL)")
            print("- 沒有足夠的歷史數據")
            print("- 當前市場條件不符合策略條件")
            return False

        # 顯示分析結果
        display_analysis_results(signals)

        # 檢查是否有開盤前下單
        pre_market_status = analyzer.get_pre_market_orders_status()
        if pre_market_status["ordered_count"] > 0:
            print(f"\n📋 開盤前下單狀態:")
            print(f"  已下單: {pre_market_status['ordered_count']} 筆")
            print(f"  失敗: {pre_market_status['failed_count']} 筆")
            print(f"  總金額: {pre_market_status['total_order_amount']:,.0f}")

        if mode == "full":
            # 完整模式：啟動價格監控
            print("\n🔍 啟動價格監控...")
            analyzer.start_price_monitoring()

            print("📈 價格監控已啟動，將在交易時間自動執行交易")
            print("按 Ctrl+C 停止監控")

            try:
                import time

                while True:
                    time.sleep(30)  # 每30秒顯示一次狀態
                    status = analyzer.get_monitoring_status()
                    if status["is_trading_time"]:
                        print(
                            f"⏰ 交易時間監控中... "
                            f"待執行: {status['pending_signals']} "
                            f"已執行: {status['executed_signals']}"
                        )
                    else:
                        print(f"⏸️  非交易時間，等待開盤...")

            except KeyboardInterrupt:
                print("\n🛑 收到停止信號")
                analyzer.stop_price_monitoring()
                print("✅ 價格監控已停止")

        return True

    except Exception as e:
        logger.error(f"開盤前分析執行失敗: {e}")
        print(f"❌ 分析失敗: {e}")
        return False


def display_analysis_results(signals):
    """顯示分析結果"""
    print(f"\n✅ 成功產生 {len(signals)} 個交易信號")

    # 按策略統計
    strategy_stats = {}
    for signal in signals:
        strategy = signal["strategy"]
        action = signal["action"]

        if strategy not in strategy_stats:
            strategy_stats[strategy] = {"buy": 0, "sell": 0, "total": 0}

        strategy_stats[strategy][action] += 1
        strategy_stats[strategy]["total"] += 1

    print("\n📈 策略信號統計:")
    print("-" * 50)
    for strategy, stats in strategy_stats.items():
        print(
            f"{strategy:15} | 買入: {stats['buy']:2d} | 賣出: {stats['sell']:2d} | 總計: {stats['total']:2d}"
        )

    # 顯示最強信號
    top_signals = sorted(
        signals, key=lambda x: abs(x["signal_strength"]), reverse=True
    )[:10]

    print(f"\n🏆 最強信號前 {min(len(top_signals), 10)} 名:")
    print("-" * 80)
    print(
        f"{'排名':<4} {'股票':<6} {'策略':<12} {'動作':<4} {'強度':<8} {'目標價':<8} {'數量':<6}"
    )
    print("-" * 80)

    for i, signal in enumerate(top_signals, 1):
        print(
            f"{i:<4} {signal['symbol']:<6} {signal['strategy']:<12} "
            f"{signal['action']:<4} {signal['signal_strength']:7.3f} "
            f"{signal['target_price']:7.2f} {signal['quantity']:6d}"
        )

    # 按股票分組顯示
    stock_signals = {}
    for signal in signals:
        symbol = signal["symbol"]
        if symbol not in stock_signals:
            stock_signals[symbol] = []
        stock_signals[symbol].append(signal)

    print(f"\n📊 按股票分組的信號詳情:")
    for symbol, symbol_signals in stock_signals.items():
        print(f"\n🏷️  股票 {symbol} ({len(symbol_signals)} 個信號):")
        for signal in symbol_signals:
            action_emoji = "📈" if signal["action"] == "buy" else "📉"
            print(
                f"  {action_emoji} {signal['strategy']} - "
                f"強度: {signal['signal_strength']:6.3f} - "
                f"目標價: {signal['target_price']:7.2f} - "
                f"數量: {signal['quantity']:4d}股"
            )


def run_orchestrator_mode(config):
    """使用交易協調器模式"""
    print("\n🤖 啟動完整自動交易系統")

    try:
        # 確保使用模擬模式
        config["trading"]["real_trading"] = False

        orchestrator = TradingOrchestrator(config)

        print("✅ 交易協調器初始化成功")
        print("📋 定時任務已設置:")
        print("  - 開盤前準備: 每日 08:30 (台灣時間)")
        print("  - 收盤後清理: 每日 14:00 (台灣時間)")
        print("  - 信號檢查: 每 5 分鐘")

        # 手動執行一次開盤前準備
        print("\n🔧 手動執行開盤前準備...")
        orchestrator._pre_market_preparation()

        print("\n✅ 開盤前準備完成")
        print("💡 提示: 完整的自動交易系統將在指定時間自動執行")

        return True

    except Exception as e:
        logger.error(f"交易協調器模式失敗: {e}")
        print(f"❌ 交易協調器模式失敗: {e}")
        return False


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="開盤前六大策略分析工具")
    parser.add_argument(
        "--stocks",
        nargs="+",
        help="指定要分析的股票代碼 (例如: --stocks 2330 0050 1101)",
    )
    parser.add_argument(
        "--mode",
        choices=["analysis", "full", "orchestrator"],
        default="analysis",
        help="運行模式: analysis=僅分析, full=分析+監控, orchestrator=完整系統",
    )
    parser.add_argument("--config", default="config.yaml", help="配置文件路徑")

    args = parser.parse_args()

    # 設置日誌
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/pre_market_analysis.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
    )

    try:
        # 載入配置
        config = load_config(args.config)

        # 顯示歡迎信息
        display_welcome()

        success = False

        if args.mode == "orchestrator":
            success = run_orchestrator_mode(config)
        else:
            success = run_pre_market_analysis(config, args.stocks, args.mode)

        if success:
            print("\n🎉 開盤前分析系統執行完成")
        else:
            print("\n❌ 系統執行失敗")

        return success

    except KeyboardInterrupt:
        print("\n\n🛑 用戶中斷執行")
        return True
    except Exception as e:
        logger.error(f"系統執行失敗: {e}")
        print(f"\n❌ 系統執行失敗: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
