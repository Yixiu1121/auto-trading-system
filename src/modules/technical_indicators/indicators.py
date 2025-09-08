#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技術指標計算器類
包含移動平均、斜率分析、乖離率、交叉信號、成交量分析等
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from loguru import logger


class MovingAverage:
    """移動平均線計算器"""

    def __init__(self, config: Dict):
        """初始化移動平均計算器"""
        self.config = config
        # 4小時K線的週期設定
        self.blue_period = config.get(
            "blue_line", 120
        )  # 小藍線（月線）- 120根4小時K線，約1個月
        self.green_period = config.get(
            "green_line", 360
        )  # 小綠線（季線）- 360根4小時K線，約3個月
        self.orange_period = config.get(
            "orange_line", 1440
        )  # 小橘線（年線）- 1440根4小時K線，約6個月

        logger.info(
            f"移動平均計算器初始化: 藍線({self.blue_period}), 綠線({self.green_period}), 橘線({self.orange_period})"
        )

    def calculate_all_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算所有移動平均線"""
        try:
            # 計算小藍線（月線）
            df["blue_line"] = df["close"].rolling(window=self.blue_period).mean()

            # 計算小綠線（季線）
            df["green_line"] = df["close"].rolling(window=self.green_period).mean()

            # 計算小橘線（年線）
            df["orange_line"] = df["close"].rolling(window=self.orange_period).mean()

            logger.debug("移動平均線計算完成")
            return df

        except Exception as e:
            logger.error(f"移動平均線計算失敗: {e}")
            return df


class SlopeAnalyzer:
    """斜率分析器"""

    def __init__(self, lookback_period: int = 5):
        """初始化斜率分析器"""
        self.lookback_period = lookback_period
        logger.info(f"斜率分析器初始化，回看週期: {lookback_period}")

    def calculate_slopes(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算各均線的斜率"""
        try:
            # 計算小藍線斜率
            df["blue_slope"] = self._calculate_slope(df["blue_line"])

            # 計算小綠線斜率
            df["green_slope"] = self._calculate_slope(df["green_line"])

            # 計算小橘線斜率
            df["orange_slope"] = self._calculate_slope(df["orange_line"])

            logger.debug("斜率計算完成")
            return df

        except Exception as e:
            logger.error(f"斜率計算失敗: {e}")
            return df

    def _calculate_slope(self, series: pd.Series) -> pd.Series:
        """計算斜率"""
        try:
            slope = pd.Series(index=series.index, dtype=float)

            for i in range(self.lookback_period, len(series)):
                if pd.notna(series.iloc[i]) and pd.notna(
                    series.iloc[i - self.lookback_period]
                ):
                    # 使用線性回歸計算斜率
                    x = np.arange(self.lookback_period + 1)
                    y = series.iloc[i - self.lookback_period : i + 1].values

                    if len(y) == self.lookback_period + 1 and not np.any(np.isnan(y)):
                        slope.iloc[i] = np.polyfit(x, y, 1)[0]
                    else:
                        slope.iloc[i] = np.nan
                else:
                    slope.iloc[i] = np.nan

            return slope

        except Exception as e:
            logger.error(f"斜率計算異常: {e}")
            return pd.Series(np.nan, index=series.index)


class DeviationAnalyzer:
    """乖離率分析器"""

    def __init__(self):
        """初始化乖離率分析器"""
        logger.info("乖離率分析器初始化")

    def calculate_deviations(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算價格與均線的乖離率"""
        try:
            # 計算價格與小藍線的乖離率
            df["blue_deviation"] = (
                (df["close"] - df["blue_line"]) / df["blue_line"] * 100
            )

            # 計算價格與小綠線的乖離率
            df["green_deviation"] = (
                (df["close"] - df["green_line"]) / df["green_line"] * 100
            )

            # 計算價格與小橘線的乖離率
            df["orange_deviation"] = (
                (df["close"] - df["orange_line"]) / df["orange_line"] * 100
            )

            logger.debug("乖離率計算完成")
            return df

        except Exception as e:
            logger.error(f"乖離率計算失敗: {e}")
            return df


class CrossSignalAnalyzer:
    """交叉信號分析器"""

    def __init__(self):
        """初始化交叉信號分析器"""
        logger.info("交叉信號分析器初始化")

    def calculate_cross_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算均線交叉信號"""
        try:
            # 初始化交叉信號列
            df["cross_signal"] = 0
            df["golden_cross"] = False
            df["death_cross"] = False

            # 分析小藍線與小綠線的交叉
            df = self._analyze_ma_cross(
                df, "blue_line", "green_line", "blue_green_cross"
            )

            # 分析小綠線與小橘線的交叉
            df = self._analyze_ma_cross(
                df, "green_line", "orange_line", "green_orange_cross"
            )

            # 分析價格與小藍線的交叉
            df = self._analyze_price_cross(df, "blue_line")

            logger.debug("交叉信號計算完成")
            return df

        except Exception as e:
            logger.error(f"交叉信號計算失敗: {e}")
            return df

    def _analyze_ma_cross(
        self, df: pd.DataFrame, ma1: str, ma2: str, cross_col: str
    ) -> pd.DataFrame:
        """分析兩條均線的交叉"""
        try:
            df[cross_col] = 0

            for i in range(1, len(df)):
                if (
                    pd.notna(df[ma1].iloc[i - 1])
                    and pd.notna(df[ma2].iloc[i - 1])
                    and pd.notna(df[ma1].iloc[i])
                    and pd.notna(df[ma2].iloc[i])
                ):

                    # 黃金交叉：短期均線上穿長期均線
                    if (
                        df[ma1].iloc[i - 1] <= df[ma2].iloc[i - 1]
                        and df[ma1].iloc[i] > df[ma2].iloc[i]
                    ):
                        df[cross_col].iloc[i] = 1  # 黃金交叉
                        df["golden_cross"].iloc[i] = True

                    # 死亡交叉：短期均線下穿長期均線
                    elif (
                        df[ma1].iloc[i - 1] >= df[ma2].iloc[i - 1]
                        and df[ma1].iloc[i] < df[ma2].iloc[i]
                    ):
                        df[cross_col].iloc[i] = -1  # 死亡交叉
                        df["death_cross"].iloc[i] = True

            return df

        except Exception as e:
            logger.error(f"均線交叉分析失敗: {e}")
            return df

    def _analyze_price_cross(self, df: pd.DataFrame, ma: str) -> pd.DataFrame:
        """分析價格與均線的交叉"""
        try:
            df["price_ma_cross"] = 0

            for i in range(1, len(df)):
                if (
                    pd.notna(df["close"].iloc[i - 1])
                    and pd.notna(df[ma].iloc[i - 1])
                    and pd.notna(df["close"].iloc[i])
                    and pd.notna(df[ma].iloc[i])
                ):

                    # 價格上穿均線
                    if (
                        df["close"].iloc[i - 1] <= df[ma].iloc[i - 1]
                        and df["close"].iloc[i] > df[ma].iloc[i]
                    ):
                        df["price_ma_cross"].iloc[i] = 1

                    # 價格下穿均線
                    elif (
                        df["close"].iloc[i - 1] >= df[ma].iloc[i - 1]
                        and df["close"].iloc[i] < df[ma].iloc[i]
                    ):
                        df["price_ma_cross"].iloc[i] = -1

            return df

        except Exception as e:
            logger.error(f"價格均線交叉分析失敗: {e}")
            return df


class VolumeAnalyzer:
    """成交量分析器"""

    def __init__(self, volume_threshold: float = 1.5):
        """初始化成交量分析器"""
        self.volume_threshold = volume_threshold
        logger.info(f"成交量分析器初始化，爆量閾值: {volume_threshold}")

    def calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算成交量指標"""
        try:
            # 計算成交量移動平均
            df["volume_ma"] = df["volume"].rolling(window=20).mean()

            # 計算成交量比率
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # 識別爆量突破
            df["volume_breakout"] = df["volume_ratio"] > self.volume_threshold

            # 計算成交量趨勢
            df["volume_trend"] = self._calculate_volume_trend(df)

            logger.debug("成交量指標計算完成")
            return df

        except Exception as e:
            logger.error(f"成交量指標計算失敗: {e}")
            return df

    def _calculate_volume_trend(self, df: pd.DataFrame) -> pd.Series:
        """計算成交量趨勢"""
        try:
            volume_trend = pd.Series(index=df.index, dtype=float)

            for i in range(20, len(df)):
                recent_volumes = df["volume"].iloc[i - 20 : i]
                if len(recent_volumes) == 20:
                    # 使用線性回歸計算成交量趨勢
                    x = np.arange(20)
                    y = recent_volumes.values

                    if not np.any(np.isnan(y)):
                        slope = np.polyfit(x, y, 1)[0]
                        volume_trend.iloc[i] = slope
                    else:
                        volume_trend.iloc[i] = np.nan
                else:
                    volume_trend.iloc[i] = np.nan

            return volume_trend

        except Exception as e:
            logger.error(f"成交量趨勢計算失敗: {e}")
            return pd.Series(np.nan, index=df.index)
