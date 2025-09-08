#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據遷移腳本
用於將 FinMind 數據遷移到 PostgreSQL 數據庫
"""

import os
import sys
import yaml
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# 直接導入模組，不使用 src. 前綴
from modules.data_fetcher import FinMindFetcher


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
        result = os.getenv(env_var, default_value)
        logger.info(f"環境變量替換: {env_var} -> {result}")
        return result

    # 替換 ${VAR:-default} 格式的環境變量
    # 先打印原始內容進行調試
    logger.info("原始配置文件內容:")
    logger.info(content)
    
    # 使用更簡單的正則表達式
    pattern = r'\$\{([^:}]+):-([^}]*)\}'
    matches = re.findall(pattern, content)
    logger.info(f"找到的環境變量匹配: {matches}")
    
    content = re.sub(pattern, replace_env_vars, content)

    # 調試：打印替換後的內容
    logger.info("配置文件內容（替換環境變量後）:")
    logger.info(content)

    config = yaml.safe_load(content)
    return config


def setup_logging():
    """設置日誌"""
    # 創建日誌目錄
    os.makedirs("logs", exist_ok=True)

    # 配置日誌
    logger.add(
        "logs/data_migrate.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def migrate_single_stock(
    fetcher: FinMindFetcher, stock_id: str, target_date: str = None
):
    """
    遷移單支股票的數據，從日K線計算4小時K線

    Args:
        fetcher: FinMind 數據獲取器
        stock_id: 股票代碼
        target_date: 目標日期 (YYYY-MM-DD)，如果為 None 則使用今天

    Returns:
        bool: 遷移是否成功
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"開始遷移股票 {stock_id} 的數據，日期: {target_date}")

    try:
        # 獲取股票日K線數據
        df_daily = fetcher.get_stock_data(stock_id, target_date, target_date)

        if df_daily is None or df_daily.empty:
            logger.warning(f"股票 {stock_id} 在 {target_date} 沒有日K線數據")
            return False

        logger.info(f"成功獲取股票 {stock_id} 的 {len(df_daily)} 筆日K線數據")

        # 顯示日K線數據詳情
        logger.info(f"日K線數據詳情:")
        for _, row in df_daily.iterrows():
            logger.info(
                f"  日期: {row['date'].strftime('%Y-%m-%d')}, "
                f"開盤: {row['open']:.2f}, "
                f"最高: {row['high']:.2f}, "
                f"最低: {row['low']:.2f}, "
                f"收盤: {row['close']:.2f}, "
                f"成交量: {row['volume']:,}"
            )

        # 轉換日K線為4小時K線格式
        df_kline = convert_daily_to_4h_kline(df_daily, target_date)

        if df_kline is None or df_kline.empty:
            logger.error(f"無法轉換股票 {stock_id} 的日K線數據")
            return False

        logger.info(f"成功轉換 {len(df_kline)} 筆K線數據")

        # 顯示K線數據詳情
        logger.info(f"K線數據詳情:")
        for _, row in df_kline.iterrows():
            logger.info(
                f"  時間: {row['date'].strftime('%Y-%m-%d %H:%M')}, "
                f"開盤: {row['open']:.2f}, "
                f"最高: {row['high']:.2f}, "
                f"最低: {row['low']:.2f}, "
                f"收盤: {row['close']:.2f}, "
                f"成交量: {row['volume']:,}"
            )

        # 連接到數據庫
        if not fetcher.connect_database():
            logger.error("無法連接到數據庫")
            return False

        # 存儲K線數據
        success = fetcher.store_stock_data(stock_id, df_kline)

        if success:
            logger.info(f"✅ 股票 {stock_id} K線數據遷移成功")
            return True
        else:
            logger.error(f"❌ 股票 {stock_id} K線數據遷移失敗")
            return False

    except Exception as e:
        logger.error(f"遷移股票 {stock_id} 數據時發生錯誤: {e}")
        return False
    finally:
        fetcher.close_database()


def migrate_single_stock_range(
    fetcher: FinMindFetcher, stock_id: str, start_date: str, end_date: str
):
    """
    遷移單支股票在指定日期範圍內的數據

    Args:
        fetcher: FinMind 數據獲取器
        stock_id: 股票代碼
        start_date: 開始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)

    Returns:
        bool: 遷移是否成功
    """
    logger.info(f"開始遷移股票 {stock_id} 的數據，日期範圍: {start_date} 到 {end_date}")

    try:
        # 獲取股票日K線數據
        df_daily = fetcher.get_stock_data(stock_id, start_date, end_date)

        if df_daily is None or df_daily.empty:
            logger.warning(f"股票 {stock_id} 在指定日期範圍內沒有日K線數據")
            return False

        logger.info(f"成功獲取股票 {stock_id} 的 {len(df_daily)} 筆日K線數據")

        # 顯示數據統計
        logger.info(f"數據統計:")
        logger.info(f"  總筆數: {len(df_daily)}")
        logger.info(f"  日期範圍: {df_daily['date'].min()} 到 {df_daily['date'].max()}")
        logger.info(
            f"  價格範圍: {df_daily['low'].min():.2f} - {df_daily['high'].max():.2f}"
        )
        logger.info(f"  總成交量: {df_daily['volume'].sum():,}")

        # 轉換日K線為4小時K線格式
        df_kline = convert_daily_to_4h_kline_range(df_daily)

        if df_kline is None or df_kline.empty:
            logger.error(f"無法轉換股票 {stock_id} 的日K線數據")
            return False

        logger.info(f"成功轉換 {len(df_kline)} 筆K線數據")

        # 連接到數據庫
        if not fetcher.connect_database():
            logger.error("無法連接到數據庫")
            return False

        # 存儲K線數據
        success = fetcher.store_stock_data(stock_id, df_kline)

        if success:
            logger.info(f"✅ 股票 {stock_id} K線數據遷移成功")
            return True
        else:
            logger.error(f"❌ 股票 {stock_id} K線數據遷移失敗")
            return False

    except Exception as e:
        logger.error(f"遷移股票 {stock_id} 數據時發生錯誤: {e}")
        return False
    finally:
        fetcher.close_database()


def convert_daily_to_4h_kline(df_daily: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """
    將日K線轉換為4小時K線格式

    Args:
        df_daily: 日K線數據
        target_date: 目標日期

    Returns:
        4小時K線格式的DataFrame
    """
    try:
        # 導入4小時K線計算器
        from modules.kline.four_hour_calculator import FourHourKlineCalculator

        # 初始化計算器
        calculator = FourHourKlineCalculator()

        # 使用進階算法計算4小時K線
        df_kline = calculator.calculate_advanced_4h_kline(df_daily)

        logger.info(
            f"成功將日K線轉換為4小時K線: {len(df_daily)} 個交易日 -> {len(df_kline)} 根4小時K線"
        )
        return df_kline

    except Exception as e:
        logger.error(f"轉換日K線為4小時K線格式時發生錯誤: {e}")
        return pd.DataFrame()


def convert_daily_to_4h_kline_range(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    將多日K線轉換為4小時K線格式

    Args:
        df_daily: 多日日K線數據

    Returns:
        4小時K線格式的DataFrame
    """
    try:
        # 導入4小時K線計算器
        from modules.kline.four_hour_calculator import FourHourKlineCalculator

        # 初始化計算器
        calculator = FourHourKlineCalculator()

        # 使用進階算法計算4小時K線
        df_kline = calculator.calculate_advanced_4h_kline(df_daily)

        logger.info(
            f"成功將多日日K線轉換為4小時K線: {len(df_daily)} 個交易日 -> {len(df_kline)} 根4小時K線"
        )
        return df_kline

    except Exception as e:
        logger.error(f"轉換多日日K線為4小時K線格式時發生錯誤: {e}")
        return pd.DataFrame()


def verify_data_in_db(fetcher: FinMindFetcher, stock_id: str):
    """
    驗證數據庫中的數據

    Args:
        fetcher: FinMind 數據獲取器
        stock_id: 股票代碼

    Returns:
        bool: 驗證是否成功
    """
    logger.info(f"驗證股票 {stock_id} 在數據庫中的數據")

    try:
        if not fetcher.connect_database():
            logger.error("無法連接到數據庫")
            return False

        cursor = fetcher.db_conn.cursor()

        # 查詢股票基本信息
        cursor.execute("SELECT * FROM stocks WHERE symbol = %s", (stock_id,))
        stock_info = cursor.fetchone()

        if stock_info:
            logger.info(f"✅ 股票 {stock_id} 基本信息已存在於數據庫")
            logger.info(f"  股票代碼: {stock_info[0]}, 名稱: {stock_info[1]}")
        else:
            logger.warning(f"⚠️ 股票 {stock_id} 基本信息不存在於數據庫")

        # 查詢價格數據
        cursor.execute(
            """
            SELECT timestamp, open_price, high, low, close, volume 
            FROM price_data 
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 10
            """,
            (stock_id,),
        )
        price_data = cursor.fetchall()

        if price_data:
            logger.info(f"✅ 找到 {len(price_data)} 筆價格數據")
            logger.info("最近10筆數據:")
            for row in price_data:
                logger.info(
                    f"  {row[0]} | O:{row[1]:.2f} H:{row[2]:.2f} "
                    f"L:{row[3]:.2f} C:{row[4]:.2f} V:{row[5]:,}"
                )
        else:
            logger.warning(f"⚠️ 股票 {stock_id} 沒有價格數據")

        cursor.close()
        return True

    except Exception as e:
        logger.error(f"驗證數據時發生錯誤: {e}")
        return False
    finally:
        fetcher.close_database()


def main():
    """主函數"""
    print("=== FinMind 數據遷移工具 ===")

    # 設置日誌
    setup_logging()

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    # 檢查 FinMind API Token
    finmind_token = config.get("finmind", {}).get("token", "")
    if not finmind_token or finmind_token == "YOUR_FINMIND_TOKEN":
        print("❌ FinMind API Token 未設置")
        print("請在 config.yaml 中設置正確的 api_token")
        return

    print("✅ FinMind API Token 已設置")

    try:
        # 創建數據獲取器
        fetcher = FinMindFetcher(config)
        print("✅ FinMind 數據獲取器創建成功")

        # 健康檢查
        print("\n--- 系統健康檢查 ---")
        health_status = fetcher.health_check()
        print(f"API 狀態: {health_status['api_status']}")
        print(f"數據庫狀態: {health_status['database_status']}")

        if health_status["api_status"] != "healthy":
            print("❌ FinMind API 連接失敗")
            return

        if health_status["database_status"] != "healthy":
            print("❌ 數據庫連接失敗")
            print("請確保 PostgreSQL 數據庫正在運行")
            print("可以使用 ./start_db.sh 啟動數據庫服務")
            return

        print("✅ 系統健康檢查通過")

        # 開始數據遷移
        print("\n--- 開始數據遷移 ---")

        # 遷移台積電的歷史數據
        stock_id = "2330"  # 台積電
        start_date = "2022-01-01"  # 從 2022 年開始
        end_date = "2025-08-29"  # 到 2025/8/29

        print(f"遷移股票: {stock_id}")
        print(f"日期範圍: {start_date} 到 {end_date}")

        # 執行遷移
        success = migrate_single_stock_range(fetcher, stock_id, start_date, end_date)

        if success:
            print(f"✅ 股票 {stock_id} 數據遷移成功")

            # 驗證數據
            print("\n--- 驗證數據 ---")
            verify_success = verify_data_in_db(fetcher, stock_id)

            if verify_success:
                print("✅ 數據驗證完成")
            else:
                print("❌ 數據驗證失敗")
        else:
            print(f"❌ 股票 {stock_id} 數據遷移失敗")

    except Exception as e:
        logger.error(f"數據遷移過程中發生錯誤: {e}")
        print(f"❌ 數據遷移失敗: {e}")

    print("\n=== 數據遷移完成 ===")


if __name__ == "__main__":
    main()
