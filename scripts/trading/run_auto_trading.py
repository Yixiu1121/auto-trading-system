#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動交易執行腳本
用於執行每日自動交易流程
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
        "logs/auto_trading.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def main():
    """主函數"""
    print("=== 自動交易系統 ===")

    # 設置日誌
    setup_logging()

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    print("✅ 配置文件加載成功")

    try:
        # 創建自動交易器
        auto_trader = AutoTrader(config)
        print("✅ 自動交易器創建成功")

        # 檢查是否為交易時間
        now = datetime.now()
        if now.hour < 9 or now.hour > 13 or (now.hour == 13 and now.minute > 30):
            print("⚠️  非交易時間，系統將在交易時間自動運行")
            return

        # 執行每日交易流程
        print(f"\n--- 開始執行自動交易流程 ---")
        print(f"時間: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        auto_trader.run_daily_trading()

        # 顯示交易摘要
        summary = auto_trader.get_trading_summary()
        print(f"\n--- 交易摘要 ---")
        print(f"監控股票數: {summary['monitoring_count']}")
        print(f"待處理訂單: {summary['pending_orders']}")
        print(f"已完成交易: {summary['completed_trades']}")

        print("✅ 自動交易流程執行完成")

    except Exception as e:
        logger.error(f"自動交易執行失敗: {e}")
        print(f"❌ 自動交易執行失敗: {e}")


if __name__ == "__main__":
    main()


