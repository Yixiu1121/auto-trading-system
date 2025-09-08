#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試數據生成器
提供各種測試場景的數據生成功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional


class TestDataGenerator:
    """測試數據生成器"""

    def __init__(self, seed: int = 42):
        """初始化測試數據生成器"""
        self.seed = seed
        np.random.seed(seed)

    def create_bull_trend_data(
        self,
        periods: int = 100,
        base_price: float = 100.0,
        start_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        創建多頭趨勢的測試數據

        Args:
            periods: K線數量
            base_price: 基礎價格
            start_date: 開始日期

        Returns:
            包含OHLCV數據的DataFrame
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)

        # 創建時間序列（4小時K線）
        dates = [start_date + timedelta(hours=4 * i) for i in range(periods)]

        # 創建三條均線的趨勢
        blue_trend = np.linspace(0, 15, periods)  # 小藍線趨勢（月線）
        green_trend = np.linspace(0, 10, periods)  # 小綠線趨勢（季線）
        orange_trend = np.linspace(0, 5, periods)  # 小橘線趨勢（年線）

        # 創建價格數據（跟隨小藍線）
        prices = base_price + blue_trend + np.random.normal(0, 1, periods)

        # 創建OHLC數據
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # 模擬真實的OHLC
            high = price + abs(np.random.normal(0, 1))
            low = price - abs(np.random.normal(0, 1))
            open_price = price + np.random.normal(0, 0.5)
            close = price

            # 模擬爆量（某些時點）
            if i > 50 and i % 10 == 0:  # 每10根K線有一次爆量
                volume = np.random.randint(15000, 25000)  # 爆量
            else:
                volume = np.random.randint(1000, 8000)  # 正常量

            data.append(
                {
                    "timestamp": date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def create_bear_trend_data(
        self,
        periods: int = 100,
        base_price: float = 100.0,
        start_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        創建空頭趨勢的測試數據

        Args:
            periods: K線數量
            base_price: 基礎價格
            start_date: 開始日期

        Returns:
            包含OHLCV數據的DataFrame
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)

        # 創建時間序列（4小時K線）
        dates = [start_date + timedelta(hours=4 * i) for i in range(periods)]

        # 創建三條均線的下降趨勢（確保空頭排列）
        blue_trend = np.linspace(0, -15, periods)  # 小藍線趨勢（月線）
        green_trend = np.linspace(0, -10, periods)  # 小綠線趨勢（季線）
        orange_trend = np.linspace(0, -5, periods)  # 小橘線趨勢（年線）

        # 創建價格數據（跟隨小藍線，但確保均線排列正確）
        # 藍線 < 綠線 < 橘線（空頭排列）
        blue_line = base_price + blue_trend
        green_line = base_price + green_trend + 2  # 綠線比藍線高2點
        orange_line = base_price + orange_trend + 5  # 橘線比藍線高5點

        # 價格跟隨藍線，但在某些時點創建跌破
        prices = blue_line + np.random.normal(0, 1, periods)

        # 在後期創建一些跌破前低的價格
        for i in range(60, periods):
            if i % 15 == 0:  # 每15根K線有一次跌破
                # 創建一個明顯跌破前期的價格
                prices[i] = prices[i] - 3  # 額外下跌3點

        # 創建OHLC數據
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # 模擬真實的OHLC
            high = price + abs(np.random.normal(0, 1))
            low = price - abs(np.random.normal(0, 1))
            open_price = price + np.random.normal(0, 0.5)
            close = price

            # 模擬爆量跌破（某些時點）
            if i > 50 and i % 10 == 0:  # 每10根K線有一次爆量
                volume = np.random.randint(15000, 25000)  # 爆量
            else:
                volume = np.random.randint(1000, 8000)  # 正常量

            data.append(
                {
                    "timestamp": date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "blue_line": blue_line[i],
                    "green_line": green_line[i],
                    "orange_line": orange_line[i],
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def create_sideways_data(
        self,
        periods: int = 100,
        base_price: float = 100.0,
        start_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        創建橫盤整理的測試數據

        Args:
            periods: K線數量
            base_price: 基礎價格
            start_date: 開始日期

        Returns:
            包含OHLCV數據的DataFrame
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)

        # 創建時間序列（4小時K線）
        dates = [start_date + timedelta(hours=4 * i) for i in range(periods)]

        # 創建橫盤價格數據
        prices = base_price + np.random.normal(0, 2, periods)

        # 創建OHLC數據
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # 模擬真實的OHLC
            high = price + abs(np.random.normal(0, 1))
            low = price - abs(np.random.normal(0, 1))
            open_price = price + np.random.normal(0, 0.5)
            close = price

            # 模擬正常成交量
            volume = np.random.randint(1000, 8000)

            data.append(
                {
                    "timestamp": date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def create_breakout_data(
        self,
        periods: int = 100,
        base_price: float = 100.0,
        start_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        創建突破形態的測試數據

        Args:
            periods: K線數量
            base_price: 基礎價格
            start_date: 開始日期

        Returns:
            包含OHLCV數據的DataFrame
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)

        # 創建時間序列（4小時K線）
        dates = [start_date + timedelta(hours=4 * i) for i in range(periods)]

        # 前60%時間橫盤整理
        consolidation_periods = int(periods * 0.6)
        consolidation_prices = base_price + np.random.normal(
            0, 1, consolidation_periods
        )

        # 後40%時間突破上漲
        breakout_periods = periods - consolidation_periods
        breakout_trend = np.linspace(0, 20, breakout_periods)
        breakout_prices = (
            base_price + breakout_trend + np.random.normal(0, 1, breakout_periods)
        )

        # 合併價格
        prices = np.concatenate([consolidation_prices, breakout_prices])

        # 創建OHLC數據
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # 模擬真實的OHLC
            high = price + abs(np.random.normal(0, 1))
            low = price - abs(np.random.normal(0, 1))
            open_price = price + np.random.normal(0, 0.5)
            close = price

            # 突破時爆量
            if i >= consolidation_periods:
                volume = np.random.randint(15000, 25000)  # 突破爆量
            else:
                volume = np.random.randint(1000, 8000)  # 整理期正常量

            data.append(
                {
                    "timestamp": date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def get_test_config(self, ma_periods: Optional[Dict] = None) -> Dict:
        """
        獲取測試配置

        Args:
            ma_periods: 移動平均線週期設定

        Returns:
            測試配置字典
        """
        if ma_periods is None:
            ma_periods = {
                "blue_line": 20,  # 測試用較小週期
                "green_line": 40,
                "orange_line": 60,
            }

        return {
            "indicators": ma_periods,
            "strategies": {
                "blue_bull": {
                    "enabled": True,
                    "min_signal_strength": 0.7,
                    "entry_threshold": 0.02,
                },
                "blue_short": {
                    "enabled": True,
                    "min_signal_strength": 0.7,
                    "entry_threshold": 0.02,
                    "volume_breakout_threshold": 1.5,
                    "deviation_threshold": 5.0,
                    "stop_loss_bars": 3,
                    "take_profit_deviation": 8.0,
                    "trailing_stop_ratio": 0.05,
                },
            },
        }

    def reset_seed(self, seed: Optional[int] = None):
        """重置隨機種子"""
        if seed is not None:
            self.seed = seed
        np.random.seed(self.seed)


# 創建全局實例
test_data_generator = TestDataGenerator()
