#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小藍空頭策略測試
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加src目錄到Python路徑
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.modules.strategies import BlueShortStrategy
from src.modules.technical_indicators import TechnicalIndicators
from test_data_generator import test_data_generator


class TestBlueShortStrategy(unittest.TestCase):
    """測試小藍空頭策略"""

    def setUp(self):
        """測試前準備"""
        from test_data_generator import test_data_generator

        # 創建測試配置
        self.config = test_data_generator.get_test_config()

        # 創建測試數據（空頭趨勢）
        self.test_data = self._create_test_data()

        # 計算技術指標
        self.tech_indicators = TechnicalIndicators(self.config)
        self.df_with_indicators = self.tech_indicators.calculate_all_indicators(
            self.test_data
        )

        # 初始化空頭策略
        self.strategy = BlueShortStrategy(self.config)

    def _create_test_data(self) -> pd.DataFrame:
        """創建測試用的K線數據（空頭趨勢）"""
        from test_data_generator import test_data_generator

        return test_data_generator.create_bear_trend_data(periods=100, base_price=100.0)

    def test_strategy_initialization(self):
        """測試策略初始化"""
        self.assertEqual(self.strategy.strategy_name, "Blue Short Strategy")
        self.assertEqual(self.strategy.strategy_type, "SHORT")
        self.assertEqual(self.strategy.volume_breakout_threshold, 1.5)
        self.assertEqual(self.strategy.deviation_threshold, 5.0)
        self.assertEqual(self.strategy.stop_loss_bars, 3)
        self.assertEqual(self.strategy.take_profit_deviation, 8.0)
        self.assertEqual(self.strategy.trailing_stop_ratio, 0.05)

    def test_data_validation(self):
        """測試數據驗證"""
        # 測試有效數據
        self.assertTrue(self.strategy.validate_data(self.df_with_indicators))

        # 測試無效數據
        empty_df = pd.DataFrame()
        self.assertFalse(self.strategy.validate_data(empty_df))

    def test_signal_strength_calculation(self):
        """測試信號強度計算"""
        # 測試正常情況
        strength = self.strategy.calculate_signal_strength(self.df_with_indicators, 80)
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)

        # 測試數據不足的情況
        strength = self.strategy.calculate_signal_strength(self.df_with_indicators, 10)
        self.assertEqual(strength, 0.0)

    def test_entry_conditions(self):
        """測試入場條件檢查"""
        # 測試正常情況
        entry_valid, entry_price = self.strategy.check_entry_conditions(
            self.df_with_indicators, 80
        )
        self.assertIsInstance(entry_valid, bool)
        self.assertIsInstance(entry_price, float)

        # 測試數據不足的情況
        entry_valid, entry_price = self.strategy.check_entry_conditions(
            self.df_with_indicators, 10
        )
        self.assertFalse(entry_valid)
        self.assertEqual(entry_price, 0.0)

    def test_exit_conditions(self):
        """測試出場條件檢查"""
        # 模擬持倉
        position = {"entry_price": 95.0, "lowest_price": 90.0}

        # 測試正常情況
        exit_valid, exit_reason = self.strategy.check_exit_conditions(
            self.df_with_indicators, 80, position
        )
        self.assertIsInstance(exit_valid, bool)
        self.assertIsInstance(exit_reason, str)

        # 測試數據不足的情況
        exit_valid, exit_reason = self.strategy.check_exit_conditions(
            self.df_with_indicators, 10, position
        )
        self.assertFalse(exit_valid)
        self.assertEqual(exit_reason, "")

    def test_signal_generation(self):
        """測試信號生成"""
        signals = self.strategy.generate_signals(self.df_with_indicators)

        # 檢查返回的DataFrame結構
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertIn("short_signal", signals.columns)
        self.assertIn("short_strength", signals.columns)
        self.assertIn("entry_price", signals.columns)
        self.assertIn("exit_price", signals.columns)
        self.assertIn("exit_reason", signals.columns)

        # 檢查信號值範圍
        self.assertTrue(all(signals["short_signal"].isin([0, -1])))
        self.assertTrue(all(signals["short_strength"] >= 0.0))
        self.assertTrue(all(signals["short_strength"] <= 1.0))

    def test_stop_loss_logic(self):
        """測試停損邏輯"""
        # 創建一個模擬的連續站回小藍線的情況
        test_df = self.df_with_indicators.copy()

        # 模擬連續3根K線站回小藍線
        for i in range(80, 83):
            if i < len(test_df):
                test_df.loc[test_df.index[i], "close"] = (
                    test_df.loc[test_df.index[i], "blue_line"] + 1.0
                )

        # 測試停損觸發
        position = {"entry_price": 95.0, "lowest_price": 90.0}
        exit_valid, exit_reason = self.strategy.check_exit_conditions(
            test_df, 82, position
        )

        # 應該觸發停損
        self.assertTrue(exit_valid)
        self.assertIn("停損", exit_reason)

    def test_take_profit_logic(self):
        """測試獲利了結邏輯"""
        # 創建一個模擬的乖離率過大的情況
        test_df = self.df_with_indicators.copy()

        # 模擬乖離率過大
        test_df.loc[test_df.index[80], "blue_deviation"] = -10.0  # 超過8%的閾值

        # 測試獲利了結觸發
        position = {"entry_price": 95.0, "lowest_price": 90.0}
        exit_valid, exit_reason = self.strategy.check_exit_conditions(
            test_df, 80, position
        )

        # 應該觸發獲利了結
        self.assertTrue(exit_valid)
        self.assertIn("獲利了結", exit_reason)

    def test_trailing_stop_logic(self):
        """測試移動停利邏輯"""
        # 創建一個模擬的反彈過大的情況
        test_df = self.df_with_indicators.copy()

        # 模擬從最低點反彈超過5%
        test_df.loc[test_df.index[80], "close"] = 94.5  # 從90反彈到94.5，超過5%

        # 測試移動停利觸發
        position = {"entry_price": 95.0, "lowest_price": 90.0}
        exit_valid, exit_reason = self.strategy.check_exit_conditions(
            test_df, 80, position
        )

        # 應該觸發移動停利
        self.assertTrue(exit_valid)
        self.assertIn("移動停利", exit_reason)

    def test_pressure_test_logic(self):
        """測試壓力測試邏輯"""
        # 創建一個模擬的價格反彈到小藍線附近的情況
        test_df = self.df_with_indicators.copy()

        # 模擬前一根K線反彈到小藍線附近但收盤價仍然在下方
        test_df.loc[test_df.index[79], "high"] = (
            test_df.loc[test_df.index[79], "blue_line"] + 0.5
        )
        test_df.loc[test_df.index[79], "close"] = (
            test_df.loc[test_df.index[79], "blue_line"] - 1.0
        )

        # 測試壓力測試通過
        pressure_test_ok = self.strategy._check_pressure_test(test_df, 80)
        self.assertTrue(pressure_test_ok)

    def test_health_check(self):
        """測試健康檢查"""
        health_info = self.strategy.health_check()

        self.assertEqual(health_info["strategy_name"], "Blue Short Strategy")
        self.assertEqual(health_info["strategy_type"], "SHORT")
        self.assertEqual(health_info["status"], "healthy")
        self.assertIn("parameters", health_info)
        self.assertIn("version", health_info)

    def test_entry_reason(self):
        """測試入場原因說明"""
        reason = self.strategy.get_entry_reason(self.df_with_indicators, 80)

        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)

    def test_conditions_summary(self):
        """測試條件檢查摘要"""
        summary = self.strategy.get_conditions_summary(self.df_with_indicators, 80)

        self.assertIsInstance(summary, dict)
        self.assertIn("ma_alignment", summary)
        self.assertIn("volume_breakout", summary)
        self.assertIn("price_breakdown", summary)
        self.assertIn("pressure_test", summary)
        self.assertIn("deviation_check", summary)
        self.assertIn("overall_status", summary)

        # 檢查每個條件的結構
        for condition_key in [
            "ma_alignment",
            "volume_breakout",
            "price_breakdown",
            "pressure_test",
            "deviation_check",
        ]:
            condition = summary[condition_key]
            self.assertIn("status", condition)
            self.assertIn("description", condition)
            self.assertIn("details", condition)

    def test_strategy_info(self):
        """測試策略信息獲取"""
        info = self.strategy.get_strategy_info()

        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertIn("type", info)
        self.assertIn("description", info)
        self.assertIn("parameters", info)

    def test_bear_trend_scenario(self):
        """測試空頭趨勢場景"""
        # 直接使用setUp中已經計算好的數據
        signals = self.strategy.generate_signals(self.df_with_indicators)

        # 檢查是否有放空信號
        short_signals = signals[signals["short_signal"] == -1]
        self.assertGreater(len(short_signals), 0, "空頭趨勢應該產生放空信號")

        # 檢查信號強度
        for _, signal in short_signals.iterrows():
            self.assertGreater(signal["short_strength"], 0.0)
            self.assertLessEqual(signal["short_strength"], 1.0)


if __name__ == "__main__":
    unittest.main()
