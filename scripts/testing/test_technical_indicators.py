#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技術指標模組測試
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.modules.technical_indicators import TechnicalIndicators
from src.modules.technical_indicators.indicators import (
    MovingAverage,
    SlopeAnalyzer,
    DeviationAnalyzer,
    CrossSignalAnalyzer,
    VolumeAnalyzer,
)


class TestTechnicalIndicators(unittest.TestCase):
    """技術指標測試類"""

    def setUp(self):
        """測試前準備"""
        from .test_data_generator import test_data_generator

        # 創建測試配置
        self.config = test_data_generator.get_test_config()

        # 創建測試數據
        self.test_data = self._create_test_data()

        # 初始化技術指標計算器
        self.tech_indicators = TechnicalIndicators(self.config)

    def _create_test_data(self) -> pd.DataFrame:
        """創建測試用的K線數據"""
        # 創建時間序列
        start_date = datetime(2024, 1, 1)
        dates = [start_date + timedelta(hours=4 * i) for i in range(100)]

        # 創建價格數據（上升趨勢）
        np.random.seed(42)  # 固定隨機種子
        base_price = 100.0
        trend = np.linspace(0, 20, 100)  # 上升趨勢
        noise = np.random.normal(0, 2, 100)
        prices = base_price + trend + noise

        # 創建OHLC數據
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # 模擬真實的OHLC
            high = price + abs(np.random.normal(0, 1))
            low = price - abs(np.random.normal(0, 1))
            open_price = price + np.random.normal(0, 0.5)
            close = price
            volume = np.random.randint(1000, 10000)

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

    def test_moving_average_calculation(self):
        """測試移動平均線計算"""
        # 測試移動平均計算器
        ma_calculator = MovingAverage(self.config["indicators"])
        result_df = ma_calculator.calculate_all_ma(self.test_data.copy())

        # 檢查是否計算了所有均線
        self.assertIn("blue_line", result_df.columns)
        self.assertIn("green_line", result_df.columns)
        self.assertIn("orange_line", result_df.columns)

        # 檢查均線值是否合理
        self.assertTrue(result_df["blue_line"].notna().sum() > 0)
        self.assertTrue(result_df["green_line"].notna().sum() > 0)
        self.assertTrue(result_df["orange_line"].notna().sum() > 0)

        # 檢查均線週期
        self.assertEqual(
            result_df["blue_line"].notna().sum(), len(result_df) - 19
        )  # 20週期
        self.assertEqual(
            result_df["green_line"].notna().sum(), len(result_df) - 39
        )  # 40週期
        self.assertEqual(
            result_df["orange_line"].notna().sum(), len(result_df) - 59
        )  # 60週期

    def test_slope_calculation(self):
        """測試斜率計算"""
        # 先計算移動平均
        ma_calculator = MovingAverage(self.config["indicators"])
        df_with_ma = ma_calculator.calculate_all_ma(self.test_data.copy())

        # 測試斜率計算器
        slope_calculator = SlopeAnalyzer(lookback_period=5)
        result_df = slope_calculator.calculate_slopes(df_with_ma)

        # 檢查是否計算了所有斜率
        self.assertIn("blue_slope", result_df.columns)
        self.assertIn("green_slope", result_df.columns)
        self.assertIn("orange_slope", result_df.columns)

        # 檢查斜率值是否合理
        self.assertTrue(result_df["blue_slope"].notna().sum() > 0)

        # 由於是上升趨勢，斜率應該主要為正
        positive_slopes = (result_df["blue_slope"] > 0).sum()
        total_slopes = result_df["blue_slope"].notna().sum()
        if total_slopes > 0:
            positive_ratio = positive_slopes / total_slopes
            self.assertGreater(positive_ratio, 0.5)  # 至少50%為正斜率

    def test_deviation_calculation(self):
        """測試乖離率計算"""
        # 先計算移動平均
        ma_calculator = MovingAverage(self.config["indicators"])
        df_with_ma = ma_calculator.calculate_all_ma(self.test_data.copy())

        # 測試乖離率計算器
        deviation_calculator = DeviationAnalyzer()
        result_df = deviation_calculator.calculate_deviations(df_with_ma)

        # 檢查是否計算了所有乖離率
        self.assertIn("blue_deviation", result_df.columns)
        self.assertIn("green_deviation", result_df.columns)
        self.assertIn("orange_deviation", result_df.columns)

        # 檢查乖離率值是否合理（應該在-20%到20%之間）
        blue_deviations = result_df["blue_deviation"].dropna()
        if len(blue_deviations) > 0:
            self.assertGreater(blue_deviations.max(), -20)
            self.assertLess(blue_deviations.min(), 20)

    def test_volume_analysis(self):
        """測試成交量分析"""
        # 測試成交量分析器
        volume_calculator = VolumeAnalyzer(volume_threshold=1.5)
        result_df = volume_calculator.calculate_volume_indicators(self.test_data.copy())

        # 檢查是否計算了成交量指標
        self.assertIn("volume_ma", result_df.columns)
        self.assertIn("volume_ratio", result_df.columns)
        self.assertIn("volume_breakout", result_df.columns)

        # 檢查成交量比率是否合理
        volume_ratios = result_df["volume_ratio"].dropna()
        if len(volume_ratios) > 0:
            self.assertGreaterEqual(volume_ratios.min(), 0)  # 比率應該非負

    def test_cross_signal_analysis(self):
        """測試交叉信號分析"""
        # 先計算移動平均
        ma_calculator = MovingAverage(self.config["indicators"])
        df_with_ma = ma_calculator.calculate_all_ma(self.test_data.copy())

        # 測試交叉信號分析器
        cross_calculator = CrossSignalAnalyzer()
        result_df = cross_calculator.calculate_cross_signals(df_with_ma)

        # 檢查是否計算了交叉信號
        self.assertIn("cross_signal", result_df.columns)
        self.assertIn("golden_cross", result_df.columns)
        self.assertIn("death_cross", result_df.columns)

    def test_complete_technical_indicators(self):
        """測試完整的技術指標計算"""
        # 測試主類
        result_df = self.tech_indicators.calculate_all_indicators(self.test_data)

        # 檢查所有必要的列是否存在
        required_columns = [
            "blue_line",
            "green_line",
            "orange_line",
            "blue_slope",
            "green_slope",
            "orange_slope",
            "blue_deviation",
            "green_deviation",
            "orange_deviation",
            "trend_strength",
            "volume_ratio",
            "cross_signal",
        ]

        for col in required_columns:
            self.assertIn(col, result_df.columns, f"缺少列: {col}")

        # 檢查數據完整性
        self.assertEqual(len(result_df), len(self.test_data))

        # 檢查是否有計算結果
        self.assertTrue(result_df["trend_strength"].notna().sum() > 0)

    def test_health_check(self):
        """測試健康檢查"""
        health_status = self.tech_indicators.health_check()

        self.assertIn("healthy", health_status)
        self.assertIn("message", health_status)
        self.assertIn("modules", health_status)

        self.assertTrue(health_status["healthy"])
        self.assertTrue(len(health_status["modules"]) > 0)

    def test_indicators_summary(self):
        """測試指標摘要"""
        # 先計算技術指標
        result_df = self.tech_indicators.calculate_all_indicators(self.test_data)

        # 獲取摘要
        summary = self.tech_indicators.get_indicators_summary(result_df)

        # 檢查摘要內容
        self.assertIn("current_price", summary)
        self.assertIn("blue_line", summary)
        self.assertIn("trend_strength", summary)
        self.assertIn("timestamp", summary)


if __name__ == "__main__":
    # 設置日誌
    import logging

    logging.basicConfig(level=logging.INFO)

    # 運行測試
    unittest.main(verbosity=2)
