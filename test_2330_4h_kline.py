#!/usr/bin/env python3
"""
使用資料庫中的2330資料測試4小時K線算法
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import psycopg2
from datetime import datetime
from loguru import logger


def load_config():
    """載入配置文件"""
    import yaml

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_2330_data_from_db():
    """從資料庫獲取2330的日K線資料"""
    try:
        config = load_config()
        db_config = config.get("database", {})

        # 連接資料庫
        conn = psycopg2.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            database=db_config.get("database", "trading_system"),
            user=db_config.get("user", "trading_user"),
            password=db_config.get("password", "trading_password"),
        )

        cursor = conn.cursor()

        # 查詢2330的價格資料
        query = """
        SELECT timestamp as date, open_price, high_price, low_price, close_price, volume
        FROM price_data
        WHERE symbol = '2330'
        ORDER BY timestamp DESC
        LIMIT 10
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("❌ 資料庫中沒有2330的資料")
            return pd.DataFrame()

        # 轉換為DataFrame
        df = pd.DataFrame(
            results, columns=["date", "open", "high", "low", "close", "volume"]
        )

        print(f"✅ 從資料庫獲取到 {len(df)} 筆2330資料")

        cursor.close()
        conn.close()

        return df

    except Exception as e:
        print(f"❌ 從資料庫獲取資料失敗: {e}")
        return pd.DataFrame()


def test_2330_4h_kline():
    """測試2330的4小時K線算法"""
    try:
        print("🔧 使用資料庫中的2330資料測試4小時K線算法")
        print("=" * 60)

        # 從資料庫獲取資料
        print("🔍 從資料庫獲取2330資料...")
        df_daily = get_2330_data_from_db()

        if df_daily.empty:
            print("❌ 無法獲取2330資料，測試終止")
            return False

        # 顯示原始日K線資料
        print("\n📊 2330日K線資料 (最近10筆):")
        for _, row in df_daily.iterrows():
            print(
                f"  {row['date'].strftime('%Y-%m-%d')}: 開{row['open']:.2f} 高{row['high']:.2f} 低{row['low']:.2f} 收{row['close']:.2f} 量{row['volume']:,}"
            )

        # 導入4小時K線計算器
        print("\n🔍 初始化4小時K線計算器...")
        from src.modules.kline.four_hour_calculator import FourHourKlineCalculator

        calculator = FourHourKlineCalculator()

        # 測試基本4小時K線計算
        print("\n🔍 測試基本4小時K線計算...")
        df_4h_basic = calculator.convert_daily_to_4h_kline(df_daily)

        if not df_4h_basic.empty:
            print(
                f"✅ 基本算法: {len(df_daily)} 個交易日 -> {len(df_4h_basic)} 根4小時K線"
            )
            print("\n📊 基本4小時K線資料:")
            for _, row in df_4h_basic.iterrows():
                print(
                    f"  {row['date'].strftime('%Y-%m-%d %H:%M')}: 開{row['open']:.2f} 高{row['high']:.2f} 低{row['low']:.2f} 收{row['close']:.2f} 量{row['volume']:,}"
                )
        else:
            print("❌ 基本算法失敗")

        # 測試進階4小時K線計算
        print("\n🔍 測試進階4小時K線計算...")
        df_4h_advanced = calculator.calculate_advanced_4h_kline(df_daily)

        if not df_4h_advanced.empty:
            print(
                f"✅ 進階算法: {len(df_daily)} 個交易日 -> {len(df_4h_advanced)} 根4小時K線"
            )
            print("\n📊 進階4小時K線資料:")
            for _, row in df_4h_advanced.iterrows():
                print(
                    f"  {row['date'].strftime('%Y-%m-%d %H:%M')}: 開{row['open']:.2f} 高{row['high']:.2f} 低{row['low']:.2f} 收{row['close']:.2f} 量{row['volume']:,}"
                )
        else:
            print("❌ 進階算法失敗")

        # 分析結果
        if not df_4h_basic.empty and not df_4h_advanced.empty:
            print("\n🔍 分析結果:")

            # 計算統計資料
            daily_avg_price = df_daily["close"].mean()
            basic_avg_price = df_4h_basic["close"].mean()
            advanced_avg_price = df_4h_advanced["close"].mean()

            print(f"  日K線平均價格: {daily_avg_price:.2f}")
            print(f"  基本4小時K線平均價格: {basic_avg_price:.2f}")
            print(f"  進階4小時K線平均價格: {advanced_avg_price:.2f}")

            # 計算價格差異
            basic_diff = abs(basic_avg_price - daily_avg_price)
            advanced_diff = abs(advanced_avg_price - daily_avg_price)

            print(f"  基本算法與日K線價格差異: {basic_diff:.2f}")
            print(f"  進階算法與日K線價格差異: {advanced_diff:.2f}")

            # 計算成交量統計
            daily_total_volume = df_daily["volume"].sum()
            basic_total_volume = df_4h_basic["volume"].sum()
            advanced_total_volume = df_4h_advanced["volume"].sum()

            print(f"  日K線總成交量: {daily_total_volume:,}")
            print(f"  基本4小時K線總成交量: {basic_total_volume:,}")
            print(f"  進階4小時K線總成交量: {advanced_total_volume:,}")

            # 成交量差異
            basic_volume_diff = abs(basic_total_volume - daily_total_volume)
            advanced_volume_diff = abs(advanced_total_volume - daily_total_volume)

            print(f"  基本算法成交量差異: {basic_volume_diff:,}")
            print(f"  進階算法成交量差異: {advanced_volume_diff:,}")

        print("\n🎉 2330資料4小時K線測試完成！")
        return True

    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_2330_4h_kline()
    if success:
        print("\n✅ 2330資料4小時K線測試完成！")
    else:
        print("\n⚠️ 測試過程中出現問題！")
