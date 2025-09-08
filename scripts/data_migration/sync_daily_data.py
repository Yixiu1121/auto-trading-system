#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日數據同步腳本
用於從 FinMind API 獲取最新的股票數據並更新到數據庫
"""

import os
import sys
import yaml
import schedule
import time
from datetime import datetime, timedelta
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from modules.data_fetcher import FinMindFetcher


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
        "logs/daily_sync.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def sync_daily_data():
    """同步每日數據"""
    logger.info("開始同步每日數據")

    config = load_config()
    if not config:
        logger.error("無法加載配置文件")
        return False

    # 檢查 FinMind API Token
    finmind_token = os.getenv("FINMIND_TOKEN")
    if not finmind_token:
        logger.error("環境變量 FINMIND_TOKEN 未設置")
        return False

    try:
        # 創建數據獲取器
        fetcher = FinMindFetcher(config)

        # 執行每日數據更新
        success = fetcher.update_daily_data()

        if success:
            logger.info("每日數據同步完成")
            return True
        else:
            logger.error("每日數據同步失敗")
            return False

    except Exception as e:
        logger.error(f"同步每日數據時發生錯誤: {e}")
        return False


def sync_initial_data():
    """同步初始數據（用於首次運行）"""
    logger.info("開始同步初始數據")

    config = load_config()
    if not config:
        logger.error("無法加載配置文件")
        return False

    # 檢查 FinMind API Token
    finmind_token = os.getenv("FINMIND_TOKEN")
    if not finmind_token:
        logger.error("環境變量 FINMIND_TOKEN 未設置")
        return False

    try:
        # 創建數據獲取器
        fetcher = FinMindFetcher(config)

        # 執行初始數據同步（獲取過去30天的數據）
        success = fetcher.initialize_database(days_back=30)

        if success:
            logger.info("初始數據同步完成")
            return True
        else:
            logger.error("初始數據同步失敗")
            return False

    except Exception as e:
        logger.error(f"同步初始數據時發生錯誤: {e}")
        return False


def run_scheduler():
    """運行定時任務調度器"""
    logger.info("啟動數據同步調度器")

    # 設置每日同步時間（市場收盤後）
    schedule.every().day.at("14:00").do(sync_daily_data)

    # 設置每小時的健康檢查
    schedule.every().hour.do(lambda: logger.info("數據同步服務運行中..."))

    logger.info("數據同步調度器已啟動")
    logger.info("每日同步時間: 14:00 (市場收盤後)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉調度器...")
    except Exception as e:
        logger.error(f"調度器運行時發生錯誤: {e}")


def main():
    """主函數"""
    print("=== FinMind 數據同步系統 ===")

    # 設置日誌
    setup_logging()

    # 檢查命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "init":
            # 初始化模式
            print("執行初始數據同步...")
            success = sync_initial_data()
            if success:
                print("✅ 初始數據同步完成")
            else:
                print("❌ 初始數據同步失敗")
                sys.exit(1)

        elif command == "daily":
            # 執行一次每日同步
            print("執行每日數據同步...")
            success = sync_daily_data()
            if success:
                print("✅ 每日數據同步完成")
            else:
                print("❌ 每日數據同步失敗")
                sys.exit(1)

        elif command == "schedule":
            # 啟動調度器模式
            print("啟動數據同步調度器...")
            run_scheduler()

        else:
            print(f"未知命令: {command}")
            print("可用命令:")
            print("  init     - 執行初始數據同步")
            print("  daily    - 執行一次每日數據同步")
            print("  schedule - 啟動定時調度器")
            sys.exit(1)

    else:
        # 交互模式
        print("請選擇操作:")
        print("1. 執行初始數據同步")
        print("2. 執行一次每日數據同步")
        print("3. 啟動定時調度器")
        print("4. 退出")

        while True:
            try:
                choice = input("\n請輸入選項 (1-4): ").strip()

                if choice == "1":
                    print("執行初始數據同步...")
                    success = sync_initial_data()
                    if success:
                        print("✅ 初始數據同步完成")
                    else:
                        print("❌ 初始數據同步失敗")
                    break

                elif choice == "2":
                    print("執行每日數據同步...")
                    success = sync_daily_data()
                    if success:
                        print("✅ 每日數據同步完成")
                    else:
                        print("❌ 每日數據同步失敗")
                    break

                elif choice == "3":
                    print("啟動數據同步調度器...")
                    run_scheduler()
                    break

                elif choice == "4":
                    print("退出程序")
                    break

                else:
                    print("無效選項，請重新輸入")

            except KeyboardInterrupt:
                print("\n收到中斷信號，退出程序")
                break
            except Exception as e:
                print(f"發生錯誤: {e}")
                break


if __name__ == "__main__":
    main()
