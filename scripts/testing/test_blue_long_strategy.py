#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小藍多頭策略測試
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.modules.strategies import BlueLongStrategy
from src.modules.technical_indicators import TechnicalIndicators


class TestBlueLongStrategy(unittest.TestCase):
    """小藍多頭策略測試類"""

    def setUp(self):
        """測試前準備"""
        # 創建測試配置
        self.config = {
            "indicators": {
                "blue_line": 20,  # 測試用較小週期
                "green_line": 40,
                "orange_line": 60,
            },
            "strategies": {
                "blue_bull": {
                    "enabled": True,
                    "min_signal_strength": 0.7,
                    "entry_threshold": 0.02,
                }
            },
        }

        # 創建測試數據
        self.test_data = self._create_test_data()

        # 初始化技術指標計算器
        self.tech_indicators = TechnicalIndicators(self.config)

        # 計算技術指標
        self.data_with_indicators = self.tech_indicators.calculate_all_indicators(
            self.test_data
        )

        # 初始化策略
        self.strategy = BlueLongStrategy(self.config)

    def _create_test_data(self) -> pd.DataFrame:
        """創建測試用的K線數據"""
        from .test_data_generator import test_data_generator

        return test_data_generator.create_bull_trend_data(periods=100, base_price=100.0)

    def test_strategy_initialization(self):
        """測試策略初始化"""
        # 檢查策略基本信息
        strategy_info = self.strategy.get_strategy_info()

        self.assertEqual(strategy_info["name"], "Blue Long Strategy")
        self.assertTrue(strategy_info["enabled"])
        self.assertEqual(strategy_info["min_signal_strength"], 0.7)
        self.assertEqual(strategy_info["entry_threshold"], 0.02)

        # 檢查策略特定參數
        self.assertEqual(self.strategy.volume_breakout_threshold, 1.5)
        self.assertEqual(self.strategy.deviation_threshold, 5.0)
        self.assertEqual(self.strategy.stop_loss_bars, 3)
        self.assertEqual(self.strategy.take_profit_deviation, 8.0)

    def test_data_validation(self):
        """測試數據驗證"""
        # 測試有效數據
        self.assertTrue(self.strategy.validate_data(self.data_with_indicators))

        # 測試無效數據（缺少列）
        invalid_data = self.data_with_indicators.drop(columns=["blue_line"])
        self.assertFalse(self.strategy.validate_data(invalid_data))

        # 測試數據量不足
        short_data = self.data_with_indicators.head(30)
        self.assertFalse(self.strategy.validate_data(short_data))

    def test_signal_strength_calculation(self):
        """測試信號強度計算"""
        # 測試信號強度計算
        strength = self.strategy.calculate_signal_strength(
            self.data_with_indicators, 80
        )

        # 信號強度應該在0-1之間
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)

        # 由於是上升趨勢，信號強度應該較高
        self.assertGreater(strength, 0.3)

    def test_entry_conditions(self):
        """測試入場條件"""
        # 測試入場條件檢查
        entry_valid, entry_price = self.strategy.check_entry_conditions(
            self.data_with_indicators, 80
        )

        # 由於我們創建的是多頭排列的數據，應該有入場機會
        if entry_valid:
            self.assertGreater(entry_price, 0)
            self.assertIsInstance(entry_price, (int, float))

    def test_exit_conditions(self):
        """測試出場條件"""
        # 創建模擬持倉
        position = {"entry_price": 110.0, "highest_price": 115.0}

        # 測試出場條件檢查
        exit_valid, exit_reason = self.strategy.check_exit_conditions(
            self.data_with_indicators, 80, position
        )

        # 檢查返回值類型
        self.assertIsInstance(exit_valid, bool)
        self.assertIsInstance(exit_reason, str)

    def test_signal_generation(self):
        """測試信號生成"""
        # 生成交易信號
        signals = self.strategy.generate_signals(self.data_with_indicators)

        # 檢查信號列表
        self.assertIsInstance(signals, list)

        # 如果有信號，檢查信號結構
        if signals:
            signal = signals[0]
            required_keys = [
                "timestamp",
                "symbol",
                "signal_type",
                "strategy",
                "strength",
                "price",
                "reason",
                "conditions",
            ]

            for key in required_keys:
                self.assertIn(key, signal)

            # 檢查信號類型
            self.assertEqual(signal["signal_type"], "buy")
            self.assertEqual(signal["strategy"], "Blue Long Strategy")

            # 檢查信號強度
            self.assertGreaterEqual(signal["strength"], 0.7)
            self.assertLessEqual(signal["strength"], 1.0)

    def test_stop_loss_logic(self):
        """測試停損邏輯"""
        # 創建一個連續下跌的數據來測試停損
        stop_loss_data = self.data_with_indicators.copy()

        # 模擬連續3根K線無法站上小藍線
        for i in range(80, 83):
            if i < len(stop_loss_data):
                # 將收盤價設為低於小藍線
                stop_loss_data.loc[stop_loss_data.index[i], "close"] = (
                    stop_loss_data.loc[stop_loss_data.index[i], "blue_line"] - 2
                )

        # 測試停損檢查
        should_stop = self.strategy._check_stop_loss(stop_loss_data, 82)
        self.assertTrue(should_stop)

    def test_take_profit_logic(self):
        """測試獲利了結邏輯"""
        # 創建一個乖離率過大的數據來測試獲利了結
        take_profit_data = self.data_with_indicators.copy()

        # 模擬乖離率過大
        take_profit_data.loc[take_profit_data.index[80], "blue_deviation"] = 10.0

        # 測試獲利了結檢查
        should_take_profit = self.strategy._check_take_profit(
            take_profit_data, 80, 110.0
        )
        self.assertTrue(should_take_profit)

    def test_trailing_stop_logic(self):
        """測試移動停利邏輯"""
        # 創建一個價格回調的數據來測試移動停利
        trailing_stop_data = self.data_with_indicators.copy()

        # 模擬價格回調超過5%
        current_price = 100.0
        highest_price = 110.0
        trailing_stop_data.loc[trailing_stop_data.index[80], "close"] = current_price

        position = {"entry_price": 100.0, "highest_price": highest_price}

        # 測試移動停利檢查
        should_trailing_stop = self.strategy._check_trailing_stop(
            trailing_stop_data, 80, position
        )

        # 由於回調超過5%，應該觸發移動停利
        self.assertTrue(should_trailing_stop)

    def test_health_check(self):
        """測試健康檢查"""
        health_status = self.strategy.health_check()

        self.assertIn("healthy", health_status)
        self.assertIn("message", health_status)
        self.assertIn("strategy_info", health_status)

        self.assertTrue(health_status["healthy"])
        self.assertIn("Blue Long Strategy", health_status["message"])

    def test_entry_reason_generation(self):
        """測試入場原因生成"""
        # 測試入場原因生成
        reason = self.strategy._get_entry_reason(self.data_with_indicators, 80)

        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)

        # 檢查是否包含關鍵詞
        self.assertIn("小藍線呈正斜率", reason)

    def test_entry_conditions_summary(self):
        """測試入場條件摘要"""
        # 測試入場條件摘要生成
        summary = self.strategy._get_entry_conditions_summary(
            self.data_with_indicators, 80
        )

        self.assertIsInstance(summary, dict)
        self.assertIn("ma_alignment", summary)
        self.assertIn("volume_breakout", summary)
        self.assertIn("price_position", summary)
        self.assertIn("trend_strength", summary)

        # 檢查均線排列信息
        ma_info = summary["ma_alignment"]
        self.assertIn("blue_line", ma_info)
        self.assertIn("green_line", ma_info)
        self.assertIn("orange_line", ma_info)


if __name__ == "__main__":
    # 設置日誌
    import logging

    logging.basicConfig(level=logging.INFO)

    # 運行測試
    unittest.main(verbosity=2)
