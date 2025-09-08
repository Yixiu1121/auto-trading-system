#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技術指標計算和存儲腳本
用於計算台積電的藍綠橘三線及相關技術指標
"""

import os
import sys
import yaml
import pandas as pd
from datetime import datetime
from loguru import logger
from typing import Optional

# 添加 src 目錄到 Python 路徑
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, src_path)

from modules.data_fetcher import FinMindFetcher
from modules.technical_indicators.calculator import TechnicalIndicatorCalculator
from modules.technical_indicators.storage import TechnicalIndicatorStorage


def load_config():
    """加載配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"配置文件 {config_path} 不存在")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 處理環境變量替換
    import re
    def replace_env_vars(match):
        env_var = match.group(1)
        default_value = match.group(2) if match.group(2) else ""
        return os.getenv(env_var, default_value)
    
    # 替換 ${VAR:-default} 格式的環境變量
    content = re.sub(r'\$\{([^:}]+):-([^}]*)\}', replace_env_vars, content)
    
    config = yaml.safe_load(content)
    return config


def setup_logging():
    """設置日誌"""
    # 創建日誌目錄
    os.makedirs("logs", exist_ok=True)

    # 配置日誌
    logger.add(
        "logs/calculate_indicators.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def get_price_data_from_db(
    fetcher: FinMindFetcher, stock_id: str
) -> Optional[pd.DataFrame]:
    """
    從數據庫獲取價格數據

    Args:
        fetcher: FinMind 數據獲取器
        stock_id: 股票代碼

    Returns:
        包含價格數據的 DataFrame，如果失敗則返回 None
    """
    try:
        if not fetcher.connect_database():
            logger.error("無法連接到數據庫")
            return None

        cursor = fetcher.db_conn.cursor()

        # 查詢價格數據
        query = """
        SELECT symbol, timestamp, open_price, high, low, close, volume, period, created_at
        FROM price_data 
        WHERE symbol = %s
        ORDER BY timestamp ASC
        """

        cursor.execute(query, (stock_id,))
        results = cursor.fetchall()

        if results:
            # 創建 DataFrame
            columns = [
                "symbol",
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "period",
                "created_at",
            ]
            df = pd.DataFrame(results, columns=columns)

            # 轉換數據類型
            df["date"] = pd.to_datetime(df["date"])
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            logger.info(f"成功從數據庫獲取 {stock_id} 的 {len(df)} 筆價格數據")
            return df
        else:
            logger.warning(f"股票 {stock_id} 沒有找到價格數據")
            return None

    except Exception as e:
        logger.error(f"從數據庫獲取價格數據時發生錯誤: {e}")
        return None
    finally:
        fetcher.close_database()


def calculate_and_store_indicators(
    stock_id: str,
    calculator: TechnicalIndicatorCalculator,
    storage: TechnicalIndicatorStorage,
) -> bool:
    """
    計算並存儲技術指標

    Args:
        stock_id: 股票代碼
        calculator: 技術指標計算器
        storage: 技術指標存儲器

    Returns:
        處理是否成功
    """
    try:
        logger.info(f"開始處理股票 {stock_id} 的技術指標...")

        # 1. 從數據庫獲取價格數據
        fetcher = FinMindFetcher({"database": storage.db_config})
        df_price = get_price_data_from_db(fetcher, stock_id)

        if df_price is None or df_price.empty:
            logger.error(f"無法獲取股票 {stock_id} 的價格數據")
            return False

        # 2. 計算技術指標
        logger.info("開始計算技術指標...")
        df_indicators = calculator.calculate_all_indicators(df_price)

        if df_indicators is None or df_indicators.empty:
            logger.error(f"無法計算股票 {stock_id} 的技術指標")
            return False

        # 3. 顯示指標摘要
        summary = calculator.get_indicator_summary(df_indicators)
        if summary:
            logger.info("技術指標摘要:")
            logger.info(f"  最新日期: {summary['latest_date']}")
            logger.info(f"  最新收盤: {summary['latest_close']:.2f}")

            # 安全地格式化數值
            ma_blue_str = (
                f"{summary['ma_blue']:.2f}" if summary["ma_blue"] is not None else "N/A"
            )
            ma_green_str = (
                f"{summary['ma_green']:.2f}"
                if summary["ma_green"] is not None
                else "N/A"
            )
            ma_orange_str = (
                f"{summary['ma_orange']:.2f}"
                if summary["ma_orange"] is not None
                else "N/A"
            )
            volume_ratio_str = (
                f"{summary['volume_ratio']:.2f}"
                if summary["volume_ratio"] is not None
                else "N/A"
            )

            logger.info(f"  藍線: {ma_blue_str}")
            logger.info(f"  綠線: {ma_green_str}")
            logger.info(f"  橘線: {ma_orange_str}")
            logger.info(f"  趨勢方向: {summary['trend_direction']}")
            logger.info(f"  均線排列: {summary['ma_alignment']}")
            logger.info(f"  成交量比率: {volume_ratio_str}")

        # 4. 存儲技術指標到數據庫
        logger.info("開始存儲技術指標到數據庫...")
        if not storage.connect_database():
            logger.error("無法連接到數據庫")
            return False

        success = storage.store_technical_indicators(stock_id, df_indicators)

        if success:
            logger.info(f"✅ 股票 {stock_id} 技術指標計算和存儲成功")

            # 5. 獲取存儲統計信息
            stats = storage.get_indicator_statistics(stock_id)
            if stats:
                logger.info("存儲統計信息:")
                logger.info(f"  總記錄數: {stats['total_records']}")
                logger.info(f"  最早日期: {stats['earliest_date']}")
                logger.info(f"  最新日期: {stats['latest_date']}")
                # 安全地格式化統計信息
                avg_blue_str = (
                    f"{stats['avg_blue_line']:.2f}"
                    if stats["avg_blue_line"] is not None
                    else "N/A"
                )
                avg_green_str = (
                    f"{stats['avg_green_line']:.2f}"
                    if stats["avg_green_line"] is not None
                    else "N/A"
                )
                avg_orange_str = (
                    f"{stats['avg_orange_line']:.2f}"
                    if stats["avg_orange_line"] is not None
                    else "N/A"
                )
                avg_rsi_str = (
                    f"{stats['avg_rsi']:.2f}" if stats["avg_rsi"] is not None else "N/A"
                )

                logger.info(f"  平均藍線: {avg_blue_str}")
                logger.info(f"  平均綠線: {avg_green_str}")
                logger.info(f"  平均橘線: {avg_orange_str}")
                logger.info(f"  平均RSI: {avg_rsi_str}")

            return True
        else:
            logger.error(f"❌ 股票 {stock_id} 技術指標存儲失敗")
            return False

    except Exception as e:
        logger.error(f"處理股票 {stock_id} 技術指標時發生錯誤: {e}")
        return False
    finally:
        storage.close_database()


def main():
    """主函數"""
    print("=== 技術指標計算和存儲工具 ===")

    # 設置日誌
    setup_logging()

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    print("✅ 配置文件加載成功")

    try:
        # 創建技術指標計算器
        calculator = TechnicalIndicatorCalculator()
        print("✅ 技術指標計算器創建成功")

        # 創建技術指標存儲器
        db_config = config.get("database", {})
        storage = TechnicalIndicatorStorage(db_config)
        print("✅ 技術指標存儲器創建成功")

        # 處理台積電的技術指標
        stock_id = "2330"  # 台積電
        print(f"\n--- 開始處理股票 {stock_id} 的技術指標 ---")

        success = calculate_and_store_indicators(stock_id, calculator, storage)

        if success:
            print(f"✅ 股票 {stock_id} 技術指標處理完成")

            # 顯示最終結果
            print("\n--- 技術指標處理結果 ---")
            print("現在可以使用以下 SQL 語法查看技術指標：")
            print("\n1. 查看技術指標表結構：")
            print("   \\d technical_indicators")
            print("\n2. 查看台積電的技術指標：")
            print(
                "   SELECT * FROM technical_indicators WHERE symbol = '2330' ORDER BY timestamp DESC LIMIT 10;"
            )
            print("\n3. 查看最新的技術指標：")
            print(
                "   SELECT * FROM technical_indicators WHERE symbol = '2330' ORDER BY timestamp DESC LIMIT 1;"
            )
            print("\n4. 查看技術指標統計：")
            print("   SELECT COUNT(*) FROM technical_indicators WHERE symbol = '2330';")

        else:
            print(f"❌ 股票 {stock_id} 技術指標處理失敗")

    except Exception as e:
        logger.error(f"技術指標處理過程中發生錯誤: {e}")
        print(f"❌ 技術指標處理失敗: {e}")

    print("\n=== 技術指標計算和存儲完成 ===")


if __name__ == "__main__":
    main()
