#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小藍多頭策略
基於小藍線（月線）的多頭交易策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger

from .strategy_base import BaseStrategy


class BlueLongStrategy(BaseStrategy):
    """小藍多頭策略"""

    def __init__(self, config: Dict):
        """初始化小藍多頭策略"""
        strategy_config = config.get("strategies", {}).get("blue_bull", {})
        super().__init__(strategy_config, "Blue Long Strategy")

        # 策略特定參數
        self.volume_breakout_threshold = 1.5  # 爆量突破閾值
        self.deviation_threshold = 5.0  # 乖離率閾值
        self.stop_loss_bars = 3  # 停損K線數
        self.take_profit_deviation = 8.0  # 獲利了結乖離率

        logger.info("小藍多頭策略初始化完成")

    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """生成交易信號"""
        try:
            if not self.validate_data(data):
                return []

            signals = []

            for i in range(50, len(data)):  # 從第50根K線開始分析
                # 檢查入場條件
                entry_valid, entry_price = self.check_entry_conditions(data, i)

                if entry_valid:
                    # 計算信號強度
                    signal_strength = self.calculate_signal_strength(data, i)

                    if signal_strength >= self.min_signal_strength:
                        signal = {
                            "timestamp": data.index[i],
                            "symbol": data.get("symbol", "UNKNOWN"),
                            "signal_type": "buy",
                            "strategy": self.name,
                            "strength": signal_strength,
                            "price": entry_price,
                            "reason": self._get_entry_reason(data, i),
                            "conditions": self._get_entry_conditions_summary(data, i),
                        }
                        signals.append(signal)
                        logger.info(f"生成買入信號: {signal}")

            logger.info(f"小藍多頭策略生成 {len(signals)} 個信號")
            return signals

        except Exception as e:
            logger.error(f"信號生成失敗: {e}")
            return []

    def check_entry_conditions(
        self, data: pd.DataFrame, index: int
    ) -> Tuple[bool, float]:
        """檢查入場條件"""
        try:
            if index < 50:  # 需要足夠的數據
                return False, 0.0

            current = data.iloc[index]

            # 條件1: 藍綠橘均線呈多頭排列且為正斜率
            ma_alignment_ok = (
                current["blue_line"] > current["green_line"] > current["orange_line"]
                and current["blue_slope"] > 0
                and current["green_slope"] > 0
                and current["orange_slope"] > 0
            )

            if not ma_alignment_ok:
                return False, 0.0

            # 條件2: 爆量突破（成交量 > 前日1.5倍 且突破前高）
            volume_breakout = current["volume_ratio"] > self.volume_breakout_threshold

            # 檢查是否突破前高
            recent_high = data["high"].iloc[index - 20 : index].max()
            price_breakout = current["close"] > recent_high

            if not (volume_breakout and price_breakout):
                return False, 0.0

            # 條件3: K線收盤站上小藍線
            price_above_blue = current["close"] > current["blue_line"]

            if not price_above_blue:
                return False, 0.0

            # 條件4: 與小藍線乖離適中
            deviation_ok = abs(current["blue_deviation"]) < self.deviation_threshold

            if not deviation_ok:
                return False, 0.0

            # 所有條件滿足，返回入場價格
            entry_price = current["close"]
            return True, entry_price

        except Exception as e:
            logger.error(f"入場條件檢查失敗: {e}")
            return False, 0.0

    def check_exit_conditions(
        self, data: pd.DataFrame, index: int, position: Dict
    ) -> Tuple[bool, str]:
        """檢查出場條件"""
        try:
            if index < 20:
                return False, ""

            current = data.iloc[index]
            entry_price = position.get("entry_price", 0)

            # 出場條件1: 連續3根K線無法站上小藍（停損信號）
            if self._check_stop_loss(data, index):
                return True, "連續3根K線無法站上小藍線，觸發停損"

            # 出場條件2: 與小藍乖離超過設定比例時部分獲利了結
            if self._check_take_profit(data, index, entry_price):
                return True, "乖離率過大，觸發獲利了結"

            # 出場條件3: 移動停利策略執行
            if self._check_trailing_stop(data, index, position):
                return True, "移動停利觸發"

            return False, ""

        except Exception as e:
            logger.error(f"出場條件檢查失敗: {e}")
            return False, ""

    def _check_stop_loss(self, data: pd.DataFrame, index: int) -> bool:
        """檢查停損條件"""
        try:
            if index < self.stop_loss_bars:
                return False

            # 檢查連續3根K線是否都無法站上小藍線
            for i in range(index - self.stop_loss_bars + 1, index + 1):
                if data["close"].iloc[i] >= data["blue_line"].iloc[i]:
                    return False

            return True

        except Exception as e:
            logger.error(f"停損檢查失敗: {e}")
            return False

    def _check_take_profit(
        self, data: pd.DataFrame, index: int, entry_price: float
    ) -> bool:
        """檢查獲利了結條件"""
        try:
            current = data.iloc[index]
            current_deviation = abs(current["blue_deviation"])

            # 當乖離率超過閾值時觸發獲利了結
            if current_deviation > self.take_profit_deviation:
                return True

            return False

        except Exception as e:
            logger.error(f"獲利了結檢查失敗: {e}")
            return False

    def _check_trailing_stop(
        self, data: pd.DataFrame, index: int, position: Dict
    ) -> bool:
        """檢查移動停利條件"""
        try:
            if "highest_price" not in position:
                return False

            current_price = data["close"].iloc[index]
            highest_price = position["highest_price"]
            trailing_stop_pct = 0.05  # 5%移動停利

            # 如果價格回調超過5%，觸發移動停利
            if current_price < highest_price * (1 - trailing_stop_pct):
                return True

            return False

        except Exception as e:
            logger.error(f"移動停利檢查失敗: {e}")
            return False

    def _get_entry_reason(self, data: pd.DataFrame, index: int) -> str:
        """獲取入場原因"""
        try:
            reasons = []
            current = data.iloc[index]

            if current["blue_slope"] > 0:
                reasons.append("小藍線呈正斜率")

            if current["volume_ratio"] > self.volume_breakout_threshold:
                reasons.append("爆量突破")

            if current["close"] > current["blue_line"]:
                reasons.append("價格站上小藍線")

            return " + ".join(reasons)

        except Exception as e:
            logger.error(f"獲取入場原因失敗: {e}")
            return "未知"

    def _get_entry_conditions_summary(self, data: pd.DataFrame, index: int) -> Dict:
        """獲取入場條件摘要"""
        try:
            current = data.iloc[index]

            return {
                "ma_alignment": {
                    "blue_line": current["blue_line"],
                    "green_line": current["green_line"],
                    "orange_line": current["orange_line"],
                    "blue_slope": current["blue_slope"],
                    "green_slope": current["green_slope"],
                    "orange_slope": current["orange_slope"],
                },
                "volume_breakout": {
                    "volume_ratio": current["volume_ratio"],
                    "threshold": self.volume_breakout_threshold,
                },
                "price_position": {
                    "close": current["close"],
                    "blue_line": current["blue_line"],
                    "deviation": current["blue_deviation"],
                },
                "trend_strength": current["trend_strength"],
            }

        except Exception as e:
            logger.error(f"獲取入場條件摘要失敗: {e}")
            return {}

    def get_strategy_info(self) -> Dict:
        """獲取策略信息"""
        base_info = super().get_strategy_info()
        base_info.update(
            {
                "volume_breakout_threshold": self.volume_breakout_threshold,
                "deviation_threshold": self.deviation_threshold,
                "stop_loss_bars": self.stop_loss_bars,
                "take_profit_deviation": self.take_profit_deviation,
            }
        )
        return base_info


