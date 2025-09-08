#!/usr/bin/env python3
"""
超簡單策略測試 - 只測試基本功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_simple_data():
    """創建簡單的測試數據"""
    print("🔍 創建簡單測試數據...")

    # 只創建100根K線
    dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")
    dates = [d for d in dates if d.hour in [9, 13]]  # 只保留9:00和13:00

    print(f"📊 生成 {len(dates)} 根4小時K線")

    # 簡單的價格數據
    base_price = 500
    prices = []
    for i in range(len(dates)):
        price = base_price + i * 0.5 + np.random.normal(0, 1)  # 簡單上升趨勢
        prices.append(round(price, 2))

    # 創建DataFrame
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        data.append(
            {
                "date": date,
                "open": close + np.random.normal(0, 0.5),
                "high": close + abs(np.random.normal(0, 1)),
                "low": close - abs(np.random.normal(0, 1)),
                "close": close,
                "volume": int(np.random.normal(1000000, 100000)),
            }
        )

    df = pd.DataFrame(data)
    print(f"✅ 數據創建完成: {len(df)} 根K線")
    return df


def test_simple_strategy():
    """測試單一策略"""
    try:
        print("🔧 超簡單策略測試")
        print("=" * 40)

        # 創建數據
        df = create_simple_data()

        # 使用很小的均線週期
        config = {
            "blue_line": 5,  # 5根K線
            "green_line": 10,  # 10根K線
            "orange_line": 20,  # 20根K線
            "volume_threshold": 1.2,
            "break_days": 3,
            "profit_target": 0.1,
            "stop_loss": 0.05,
        }

        print(f"\n📋 測試參數:")
        print(f"  小藍線: {config['blue_line']} 根K線")
        print(f"  小綠線: {config['green_line']} 根K線")
        print(f"  小橘線: {config['orange_line']} 根K線")

        # 只測試一個策略
        print("\n🔍 測試小綠多頭策略...")
        from src.modules.strategies.green_long import GreenLongStrategy

        strategy = GreenLongStrategy(config)
        signals = strategy.generate_signals(df.copy())

        print(f"✅ 策略測試完成: 生成 {len(signals)} 個信號")

        if signals:
            print("\n📊 信號詳情:")
            for i, signal in enumerate(signals[:3]):  # 只顯示前3個
                print(
                    f"  {i+1}. {signal['date']}: {signal['action']} @ {signal['price']:.2f}"
                )

        print("\n🎉 測試成功！")
        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_simple_strategy()
