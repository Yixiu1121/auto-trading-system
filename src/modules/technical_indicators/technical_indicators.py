#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技術指標計算模組 - 主類
計算交易策略所需的各種技術指標
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger

from .indicators import (
    MovingAverage,
    SlopeAnalyzer,
    DeviationAnalyzer,
    CrossSignalAnalyzer,
    VolumeAnalyzer,
)


class TechnicalIndicators:
    """技術指標計算主類"""

    def __init__(self, config: Dict):
        """初始化技術指標計算器"""
        self.config = config
        self.indicators_config = config.get("indicators", {})

        # 初始化各指標計算器
        self.moving_average = MovingAverage(self.indicators_config)
        self.slope_analyzer = SlopeAnalyzer()
        self.deviation_analyzer = DeviationAnalyzer()
        self.cross_signal_analyzer = CrossSignalAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()

        logger.info("技術指標計算模組初始化完成")

    def calculate_all_indicators(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """計算所有技術指標"""
        try:
            logger.info("開始計算技術指標...")

            # 複製數據避免修改原始數據
            df = market_data.copy()

            # 1. 計算移動平均線
            df = self.moving_average.calculate_all_ma(df)

            # 2. 計算斜率
            df = self.slope_analyzer.calculate_slopes(df)

            # 3. 計算乖離率
            df = self.deviation_analyzer.calculate_deviations(df)

            # 4. 計算交叉信號
            df = self.cross_signal_analyzer.calculate_cross_signals(df)

            # 5. 計算成交量指標
            df = self.volume_analyzer.calculate_volume_indicators(df)

            # 6. 計算綜合指標
            df = self._calculate_composite_indicators(df)

            logger.info(f"技術指標計算完成，共處理 {len(df)} 條記錄")
            return df

        except Exception as e:
            logger.error(f"技術指標計算失敗: {e}")
            raise

    def _calculate_composite_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算綜合指標"""
        try:
            # 計算趨勢強度
            df["trend_strength"] = self._calculate_trend_strength(df)

            # 計算支撐阻力位
            df["support_resistance"] = self._calculate_support_resistance(df)

            # 計算波動率
            df["volatility"] = self._calculate_volatility(df)

            return df

        except Exception as e:
            logger.error(f"綜合指標計算失敗: {e}")
            return df

    def _calculate_trend_strength(self, df: pd.DataFrame) -> pd.Series:
        """計算趨勢強度"""
        try:
            # 基於均線排列和斜率計算趨勢強度
            trend_strength = pd.Series(index=df.index, dtype=float)

            for i in range(len(df)):
                if i < 20:  # 需要足夠的數據
                    trend_strength.iloc[i] = 0
                    continue

                # 檢查均線排列
                ma_alignment = 0
                if (
                    df["blue_line"].iloc[i]
                    > df["green_line"].iloc[i]
                    > df["orange_line"].iloc[i]
                ):
                    ma_alignment = 1  # 多頭排列
                elif (
                    df["blue_line"].iloc[i]
                    < df["green_line"].iloc[i]
                    < df["orange_line"].iloc[i]
                ):
                    ma_alignment = -1  # 空頭排列

                # 檢查斜率
                slope_score = 0
                if df["blue_slope"].iloc[i] > 0:
                    slope_score += 1
                if df["green_slope"].iloc[i] > 0:
                    slope_score += 1
                if df["orange_slope"].iloc[i] > 0:
                    slope_score += 1

                # 計算綜合趨勢強度 (-3 到 3)
                trend_strength.iloc[i] = ma_alignment * slope_score

            return trend_strength

        except Exception as e:
            logger.error(f"趨勢強度計算失敗: {e}")
            return pd.Series(0, index=df.index)

    def _calculate_support_resistance(self, df: pd.DataFrame) -> pd.Series:
        """計算支撐阻力位"""
        try:
            # 簡單的支撐阻力位計算
            support_resistance = pd.Series(index=df.index, dtype=float)

            for i in range(20, len(df)):
                # 使用前20根K線的高低點
                recent_high = df["high"].iloc[i - 20 : i].max()
                recent_low = df["low"].iloc[i - 20 : i].min()

                current_price = df["close"].iloc[i]

                # 計算距離支撐阻力位的百分比
                if current_price > recent_high:
                    support_resistance.iloc[i] = (
                        current_price - recent_high
                    ) / recent_high
                elif current_price < recent_low:
                    support_resistance.iloc[i] = (
                        recent_low - current_price
                    ) / recent_low
                else:
                    support_resistance.iloc[i] = 0

            return support_resistance

        except Exception as e:
            logger.error(f"支撐阻力位計算失敗: {e}")
            return pd.Series(0, index=df.index)

    def _calculate_volatility(self, df: pd.DataFrame) -> pd.Series:
        """計算波動率"""
        try:
            # 使用20根K線的收盤價標準差計算波動率
            volatility = pd.Series(index=df.index, dtype=float)

            for i in range(20, len(df)):
                recent_prices = df["close"].iloc[i - 20 : i]
                volatility.iloc[i] = recent_prices.std() / recent_prices.mean()

            return volatility

        except Exception as e:
            logger.error(f"波動率計算失敗: {e}")
            return pd.Series(0, index=df.index)

    def get_indicators_summary(self, df: pd.DataFrame) -> Dict:
        """獲取技術指標摘要"""
        try:
            latest = df.iloc[-1]

            summary = {
                "current_price": latest["close"],
                "blue_line": latest["blue_line"],
                "green_line": latest["green_line"],
                "orange_line": latest["orange_line"],
                "trend_strength": latest["trend_strength"],
                "volume_ratio": latest["volume_ratio"],
                "blue_deviation": latest["blue_deviation"],
                "cross_signal": latest["cross_signal"],
                "timestamp": latest.name,
            }

            return summary

        except Exception as e:
            logger.error(f"獲取指標摘要失敗: {e}")
            return {}

    def health_check(self) -> Dict:
        """健康檢查"""
        try:
            return {
                "healthy": True,
                "message": "技術指標計算模組運行正常",
                "modules": {
                    "moving_average": self.moving_average is not None,
                    "slope_analyzer": self.slope_analyzer is not None,
                    "deviation_analyzer": self.deviation_analyzer is not None,
                    "cross_signal_analyzer": self.cross_signal_analyzer is not None,
                    "volume_analyzer": self.volume_analyzer is not None,
                },
            }
        except Exception as e:
            return {"healthy": False, "message": f"技術指標計算模組異常: {e}"}


