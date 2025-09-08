#!/usr/bin/env python3
"""
測試新創建的策略：小綠多頭、小綠空頭、小橘多頭、小橘空頭
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger


def create_test_data():
    """創建測試用的K線數據"""
    # 創建模擬的2330台積電數據 - 擴展到3年以滿足小橘線需求
    dates = pd.date_range(start="2022-01-01", end="2024-12-31", freq="4H")
    dates = [d for d in dates if d.hour in [9, 13]]  # 只保留9:00和13:00的4小時K線

    print(f"🔍 生成 {len(dates)} 根4小時K線數據")

    # 生成模擬價格數據
    np.random.seed(42)
    base_price = 500
    prices = [base_price]

    for i in range(1, len(dates)):
        # 模擬價格波動
        change = np.random.normal(0, 2)  # 平均0，標準差2的隨機變化
        new_price = prices[-1] + change

        # 確保價格不會太離譜
        if new_price < base_price * 0.7:
            new_price = base_price * 0.7
        elif new_price > base_price * 1.5:
            new_price = base_price * 1.5

        prices.append(new_price)

    # 創建OHLCV數據
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成開盤、最高、最低價
        open_price = close + np.random.normal(0, 1)
        high_price = max(open_price, close) + abs(np.random.normal(0, 1))
        low_price = min(open_price, close) - abs(np.random.normal(0, 1))

        # 生成成交量
        volume = int(np.random.normal(1000000, 200000))
        volume = max(volume, 100000)  # 確保成交量為正

        data.append(
            {
                "date": date,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close, 2),
                "volume": volume,
            }
        )

    df = pd.DataFrame(data)
    logger.info(f"創建測試數據: {len(df)} 根4小時K線")
    return df


def test_strategies():
    """測試所有新策略"""
    try:
        print("🔧 測試新創建的策略")
        print("=" * 60)

        # 創建測試數據
        print("🔍 創建測試數據...")
        df = create_test_data()

        # 顯示測試數據概況
        print(f"📊 測試數據概況:")
        print(f"  時間範圍: {df['date'].min()} 到 {df['date'].max()}")
        print(f"  價格範圍: {df['close'].min():.2f} - {df['close'].max():.2f}")
        print(f"  平均成交量: {df['volume'].mean():,.0f}")

        # 策略配置
        strategy_config = {
            "blue_line": 120,  # 小藍線（月線）- 120根4小時K線，約1個月
            "green_line": 360,  # 小綠線（季線）- 360根4小時K線，約3個月
            "orange_line": 1440,  # 小橘線（年線）- 1440根4小時K線，約6個月
            "volume_threshold": 1.5,
            "break_days": 5,
            "profit_target": 0.15,
            "stop_loss": 0.08,
        }

        # 測試小綠多頭策略
        print("\n🔍 測試小綠多頭策略...")
        from src.modules.strategies.green_long import GreenLongStrategy

        green_long = GreenLongStrategy(strategy_config)
        green_long_signals = green_long.generate_signals(df.copy())

        print(f"✅ 小綠多頭策略: 生成 {len(green_long_signals)} 個信號")
        if green_long_signals:
            for signal in green_long_signals[:3]:  # 顯示前3個信號
                print(
                    f"  {signal['date']}: {signal['action']} @ {signal['price']:.2f} - {signal['reason']}"
                )

        # 測試小綠空頭策略
        print("\n🔍 測試小綠空頭策略...")
        from src.modules.strategies.green_short import GreenShortStrategy

        green_short = GreenShortStrategy(strategy_config)
        green_short_signals = green_short.generate_signals(df.copy())

        print(f"✅ 小綠空頭策略: 生成 {len(green_short_signals)} 個信號")
        if green_short_signals:
            for signal in green_short_signals[:3]:  # 顯示前3個信號
                print(
                    f"  {signal['date']}: {signal['action']} @ {signal['price']:.2f} - {signal['reason']}"
                )

        # 測試小橘多頭策略
        print("\n🔍 測試小橘多頭策略...")
        from src.modules.strategies.orange_long import OrangeLongStrategy

        orange_long = OrangeLongStrategy(strategy_config)
        orange_long_signals = orange_long.generate_signals(df.copy())

        print(f"✅ 小橘多頭策略: 生成 {len(orange_long_signals)} 個信號")
        if orange_long_signals:
            for signal in orange_long_signals[:3]:  # 顯示前3個信號
                print(
                    f"  {signal['date']}: {signal['action']} @ {signal['price']:.2f} - {signal['reason']}"
                )

        # 測試小橘空頭策略
        print("\n🔍 測試小橘空頭策略...")
        from src.modules.strategies.orange_short import OrangeShortStrategy

        orange_short = OrangeShortStrategy(strategy_config)
        orange_short_signals = orange_short.generate_signals(df.copy())

        print(f"✅ 小橘空頭策略: 生成 {len(orange_short_signals)} 個信號")
        if orange_short_signals:
            for signal in orange_short_signals[:3]:  # 顯示前3個信號
                print(
                    f"  {signal['date']}: {signal['action']} @ {signal['price']:.2f} - {signal['reason']}"
                )

        # 策略信息總結
        print("\n📋 策略信息總結:")
        strategies = [
            ("小綠多頭", green_long),
            ("小綠空頭", green_short),
            ("小橘多頭", orange_long),
            ("小橘空頭", orange_short),
        ]

        for name, strategy in strategies:
            info = strategy.get_strategy_info()
            print(f"\n{name}:")
            print(f"  描述: {info['description']}")
            print(f"  參數: {info['parameters']}")
            print(f"  入場條件: {len(info['entry_conditions'])} 個")
            print(f"  出場條件: {len(info['exit_conditions'])} 個")

        print("\n🎉 所有策略測試完成！")
        return True

    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_strategies()
    if success:
        print("\n✅ 策略測試完成！")
    else:
        print("\n⚠️ 測試過程中出現問題！")
