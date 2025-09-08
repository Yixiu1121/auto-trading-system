#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫初始化腳本
用於創建所有必要的數據庫表和索引
"""

import os
import sys
import yaml
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.modules.database.init_db import DatabaseInitializer


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
        "logs/init_database.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def main():
    """主函數"""
    print("=== 數據庫初始化工具 ===")

    # 設置日誌
    setup_logging()

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    print("✅ 配置文件加載成功")

    try:
        # 創建數據庫初始化器
        db_config = config.get("database", {})
        initializer = DatabaseInitializer(db_config)

        print("\n--- 開始初始化數據庫 ---")

        # 初始化數據庫
        success = initializer.initialize()

        if success:
            print("✅ 數據庫初始化成功")

            # 驗證表
            print("\n--- 驗證數據庫表 ---")
            verify_success = initializer.verify_tables()

            if verify_success:
                print("✅ 數據庫表驗證成功")
                print("\n數據庫初始化完成！")
                print("現在可以使用以下 SQL 語法查看數據庫結構：")
                print("\n1. 查看所有表：")
                print(
                    "   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                )
                print("\n2. 查看表結構：")
                print("   \\d stocks")
                print("   \\d price_data")
                print("   \\d technical_indicators")
                print("   \\d trading_signals")
                print("   \\d trades")
                print("   \\d positions")
                print("   \\d risk_records")
                print("   \\d system_logs")
            else:
                print("❌ 數據庫表驗證失敗")
        else:
            print("❌ 數據庫初始化失敗")

    except Exception as e:
        logger.error(f"數據庫初始化過程中發生錯誤: {e}")
        print(f"❌ 數據庫初始化失敗: {e}")

    print("\n=== 數據庫初始化完成 ===")


if __name__ == "__main__":
    main()
