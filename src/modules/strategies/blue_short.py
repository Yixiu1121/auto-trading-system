#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小藍空頭策略
基於小藍線的空頭交易策略，當價格跌破小藍線且呈負斜率時產生放空信號
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
from loguru import logger
from .strategy_base import BaseStrategy


class BlueShortStrategy(BaseStrategy):
    """小藍空頭策略"""

    def __init__(self, config: Dict):
        """
        初始化小藍空頭策略

        Args:
            config: 策略配置字典
        """
        super().__init__(config, "Blue Short Strategy")

        # 策略特定參數
        self.strategy_name = "Blue Short Strategy"
        self.strategy_type = "SHORT"

        # 空頭策略參數
        self.volume_breakout_threshold = (
            config.get("strategies", {})
            .get("blue_short", {})
            .get("volume_breakout_threshold", 1.5)
        )
        self.deviation_threshold = (
            config.get("strategies", {})
            .get("blue_short", {})
            .get("deviation_threshold", 5.0)
        )
        self.stop_loss_bars = (
            config.get("strategies", {}).get("blue_short", {}).get("stop_loss_bars", 3)
        )
        self.take_profit_deviation = (
            config.get("strategies", {})
            .get("blue_short", {})
            .get("take_profit_deviation", 8.0)
        )
        self.trailing_stop_ratio = (
            config.get("strategies", {})
            .get("blue_short", {})
            .get("trailing_stop_ratio", 0.05)
        )

        logger.info(f"小藍空頭策略初始化完成")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成空頭交易信號

        Args:
            df: 包含技術指標的DataFrame

        Returns:
            包含信號的DataFrame
        """
        signals = pd.DataFrame(index=df.index)
        signals["short_signal"] = 0
        signals["short_strength"] = 0.0
        signals["entry_price"] = np.nan
        signals["exit_price"] = np.nan
        signals["exit_reason"] = ""

        for i in range(len(df)):
            if i < 50:  # 需要足夠的數據計算指標
                continue

            # 檢查入場條件
            entry_valid, entry_price = self.check_entry_conditions(df, i)
            if entry_valid:
                signals.loc[df.index[i], "short_signal"] = -1  # -1表示放空信號
                signals.loc[df.index[i], "entry_price"] = entry_price
                signals.loc[df.index[i], "short_strength"] = (
                    self.calculate_signal_strength(df, i)
                )

        return signals

    def check_entry_conditions(
        self, df: pd.DataFrame, index: int
    ) -> Tuple[bool, float]:
        """
        檢查空頭入場條件

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引

        Returns:
            (是否滿足條件, 入場價格)
        """
        if index < 50:
            return False, 0.0

        current = df.iloc[index]

        # 條件1: 藍綠橘均線呈空頭排列且為負斜率
        ma_alignment_ok = (
            current["blue_line"] < current["green_line"] < current["orange_line"]
            and current["blue_slope"] < 0
            and current["green_slope"] < 0
            and current["orange_slope"] < 0
        )

        if not ma_alignment_ok:
            return False, 0.0

        # 條件2: 爆量跌破（成交量 > 前日1.5倍 且跌破前低）
        volume_breakout_ok = current["volume_ratio"] > self.volume_breakout_threshold

        # 檢查是否跌破前20根K線的低點
        recent_low = df["low"].iloc[max(0, index - 20) : index].min()
        price_breakdown_ok = current["close"] < recent_low

        if not (volume_breakout_ok and price_breakdown_ok):
            return False, 0.0

        # 條件3: K線收盤跌破小藍線
        price_below_blue_ok = current["close"] < current["blue_line"]

        if not price_below_blue_ok:
            return False, 0.0

        # 條件4: 價格反彈至小藍線遇壓回的放空信號（可選條件）
        # 檢查前幾根K線是否有反彈到小藍線附近
        pressure_test_ok = self._check_pressure_test(df, index)

        # 如果沒有壓力測試，仍然可以入場（放寬條件）
        # if not pressure_test_ok:
        #     return False, 0.0

        # 檢查乖離率是否適中（避免過度超賣）
        deviation_ok = abs(current["blue_deviation"]) < self.deviation_threshold

        if not deviation_ok:
            return False, 0.0

        # 所有條件都滿足，返回入場價格
        entry_price = current["close"]
        return True, entry_price

    def check_exit_conditions(
        self, df: pd.DataFrame, index: int, position: Dict
    ) -> Tuple[bool, str]:
        """
        檢查空頭出場條件

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引
            position: 持倉信息字典

        Returns:
            (是否應該出場, 出場原因)
        """
        if index < 50:
            return False, ""

        current = df.iloc[index]
        entry_price = position.get("entry_price", 0)
        lowest_price = position.get("lowest_price", float("inf"))

        # 更新最低價格
        if current["low"] < lowest_price:
            lowest_price = current["low"]
            position["lowest_price"] = lowest_price

        # 條件1: 連續3根K線站回小藍線上（停損信號）
        if self._check_stop_loss(df, index):
            return True, "連續3根K線站回小藍線（停損）"

        # 條件2: 與小藍乖離超過設定比例時部分獲利了結
        if self._check_take_profit(df, index, entry_price):
            return True, "與小藍乖離過大（獲利了結）"

        # 條件3: 移動停利策略執行
        if self._check_trailing_stop(df, index, position):
            return True, "移動停利觸發"

        return False, ""

    def _check_pressure_test(self, df: pd.DataFrame, index: int) -> bool:
        """
        檢查價格反彈至小藍線遇壓回的情況

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引

        Returns:
            是否通過壓力測試
        """
        # 檢查前5根K線是否有反彈到小藍線附近
        lookback = min(5, index)
        for i in range(index - lookback, index):
            if i < 0:
                continue

            kline = df.iloc[i]
            blue_line = kline["blue_line"]

            # 檢查是否有K線反彈到小藍線附近（上下1%範圍內）
            if (
                kline["high"] >= blue_line * 0.99
                and kline["high"] <= blue_line * 1.01
                and kline["close"] < blue_line
            ):  # 收盤價仍然在小藍線下方
                return True

        return False

    def _check_stop_loss(self, df: pd.DataFrame, index: int) -> bool:
        """
        檢查停損條件：連續3根K線站回小藍線上

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引

        Returns:
            是否觸發停損
        """
        if index < self.stop_loss_bars:
            return False

        # 檢查連續3根K線是否都站回小藍線上
        consecutive_above = 0
        for i in range(index - self.stop_loss_bars + 1, index + 1):
            if i < 0:
                continue

            kline = df.iloc[i]
            if kline["close"] > kline["blue_line"]:
                consecutive_above += 1
            else:
                consecutive_above = 0

        return consecutive_above >= self.stop_loss_bars

    def _check_take_profit(
        self, df: pd.DataFrame, index: int, entry_price: float
    ) -> bool:
        """
        檢查獲利了結條件：與小藍乖離超過設定比例

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引
            entry_price: 入場價格

        Returns:
            是否應該獲利了結
        """
        current = df.iloc[index]

        # 計算與小藍線的乖離率
        deviation = abs(current["blue_deviation"])

        # 如果乖離率超過設定比例，考慮獲利了結
        if deviation > self.take_profit_deviation:
            # 檢查是否有獲利（價格下跌）
            if current["close"] < entry_price:
                return True

        return False

    def _check_trailing_stop(
        self, df: pd.DataFrame, index: int, position: Dict
    ) -> bool:
        """
        檢查移動停利條件

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引
            position: 持倉信息字典

        Returns:
            是否觸發移動停利
        """
        current = df.iloc[index]
        lowest_price = position.get("lowest_price", float("inf"))

        if lowest_price == float("inf"):
            return False

        # 計算從最低點的反彈幅度
        if lowest_price > 0:
            bounce_ratio = (current["close"] - lowest_price) / lowest_price

            # 如果反彈超過設定比例，觸發移動停利
            if bounce_ratio > self.trailing_stop_ratio:
                return True

        return False

    def calculate_signal_strength(self, df: pd.DataFrame, index: int) -> float:
        """
        計算空頭信號強度

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引

        Returns:
            信號強度 (0.0 - 1.0)
        """
        if index < 50:
            return 0.0

        current = df.iloc[index]
        strength = 0.0

        # 均線排列強度 (30%)
        if current["blue_line"] < current["green_line"] < current["orange_line"]:
            ma_strength = 0.3
            # 根據斜率強度調整
            slope_strength = min(abs(current["blue_slope"]), 2.0) / 2.0
            ma_strength *= 0.5 + 0.5 * slope_strength
        else:
            ma_strength = 0.0

        # 成交量突破強度 (25%)
        if current["volume_ratio"] > self.volume_breakout_threshold:
            volume_strength = min(current["volume_ratio"] / 3.0, 1.0) * 0.25
        else:
            volume_strength = 0.0

        # 價格位置強度 (25%)
        if current["close"] < current["blue_line"]:
            # 根據跌破程度調整
            price_strength = min(abs(current["blue_deviation"]) / 10.0, 1.0) * 0.25
        else:
            price_strength = 0.0

        # 趨勢強度 (20%)
        trend_strength = (
            1.0 - current["trend_strength"]
        ) * 0.2  # 空頭策略，趨勢強度越低越好

        strength = ma_strength + volume_strength + price_strength + trend_strength

        return min(strength, 1.0)

    def get_entry_reason(self, df: pd.DataFrame, index: int) -> str:
        """
        獲取入場原因說明

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引

        Returns:
            入場原因說明
        """
        if index < 50:
            return "數據不足"

        current = df.iloc[index]
        reasons = []

        # 檢查各項條件
        if (
            current["blue_line"] < current["green_line"] < current["orange_line"]
            and current["blue_slope"] < 0
            and current["green_slope"] < 0
            and current["orange_slope"] < 0
        ):
            reasons.append("均線空頭排列")

        if current["volume_ratio"] > self.volume_breakout_threshold:
            reasons.append("爆量跌破")

        if current["close"] < current["blue_line"]:
            reasons.append("跌破小藍線")

        if self._check_pressure_test(df, index):
            reasons.append("遇壓回測")

        if reasons:
            return " + ".join(reasons)
        else:
            return "條件不滿足"

    def get_conditions_summary(self, df: pd.DataFrame, index: int) -> Dict:
        """
        獲取條件檢查摘要

        Args:
            df: 包含技術指標的DataFrame
            index: 當前K線索引

        Returns:
            條件檢查摘要字典
        """
        if index < 50:
            return {"error": "數據不足"}

        current = df.iloc[index]

        # 檢查均線排列
        ma_alignment = (
            current["blue_line"] < current["green_line"] < current["orange_line"]
            and current["blue_slope"] < 0
            and current["green_slope"] < 0
            and current["orange_slope"] < 0
        )

        # 檢查爆量跌破
        volume_breakout = current["volume_ratio"] > self.volume_breakout_threshold

        # 檢查價格跌破
        price_breakdown = current["close"] < current["blue_line"]

        # 檢查壓力測試
        pressure_test = self._check_pressure_test(df, index)

        # 檢查乖離率
        deviation_ok = abs(current["blue_deviation"]) < self.deviation_threshold

        return {
            "ma_alignment": {
                "status": ma_alignment,
                "description": "藍綠橘均線呈空頭排列且為負斜率",
                "details": {
                    "blue_slope": current["blue_slope"],
                    "green_slope": current["green_slope"],
                    "orange_slope": current["orange_slope"],
                },
            },
            "volume_breakout": {
                "status": volume_breakout,
                "description": f"成交量比率 > {self.volume_breakout_threshold}",
                "details": {
                    "volume_ratio": current["volume_ratio"],
                    "threshold": self.volume_breakout_threshold,
                },
            },
            "price_breakdown": {
                "status": price_breakdown,
                "description": "K線收盤跌破小藍線",
                "details": {
                    "close": current["close"],
                    "blue_line": current["blue_line"],
                    "deviation": current["blue_deviation"],
                },
            },
            "pressure_test": {
                "status": pressure_test,
                "description": "價格反彈至小藍線遇壓回",
                "details": {"passed": pressure_test},
            },
            "deviation_check": {
                "status": deviation_ok,
                "description": f"乖離率 < {self.deviation_threshold}%",
                "details": {
                    "deviation": current["blue_deviation"],
                    "threshold": self.deviation_threshold,
                },
            },
            "overall_status": all(
                [
                    ma_alignment,
                    volume_breakout,
                    price_breakdown,
                    pressure_test,
                    deviation_ok,
                ]
            ),
        }

    def health_check(self) -> Dict:
        """策略健康檢查"""
        return {
            "strategy_name": self.strategy_name,
            "strategy_type": self.strategy_type,
            "status": "healthy",
            "parameters": {
                "volume_breakout_threshold": self.volume_breakout_threshold,
                "deviation_threshold": self.deviation_threshold,
                "stop_loss_bars": self.stop_loss_bars,
                "take_profit_deviation": self.take_profit_deviation,
                "trailing_stop_ratio": self.trailing_stop_ratio,
            },
            "version": "1.0.0",
        }
