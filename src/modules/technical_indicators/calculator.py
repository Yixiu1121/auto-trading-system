#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技術指標計算器
負責計算藍綠橘三線及相關技術指標
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger

from ..database.models import PeriodType


class TechnicalIndicatorCalculator:
    """技術指標計算器"""

    def __init__(self):
        """初始化技術指標計算器"""
        # 藍綠橘三線的週期設定 (基於4小時K線)
        # 調整為符合標準的週期，基於4小時K線數據
        self.ma_periods = {
            "blue": 120,  # 小藍線（月線）- 120根4小時K線，約1個月
            "green": 360,  # 小綠線（季線）- 360根4小時K線，約3個月
            "orange": 1440,  # 小橘線（年線）- 1440根4小時K線，約6個月
        }

        logger.info("技術指標計算器初始化完成")

    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算藍綠橘三線移動平均

        Args:
            df: 包含 OHLCV 數據的 DataFrame，按時間排序

        Returns:
            添加了移動平均線的 DataFrame
        """
        try:
            df = df.copy()

            # 確保數據按時間排序
            df = df.sort_values("date").reset_index(drop=True)

            # 計算藍線 (月線)
            df["ma_blue"] = df["close"].rolling(window=self.ma_periods["blue"]).mean()

            # 計算綠線 (季線)
            df["ma_green"] = df["close"].rolling(window=self.ma_periods["green"]).mean()

            # 計算橘線 (年線)
            df["ma_orange"] = (
                df["close"].rolling(window=self.ma_periods["orange"]).mean()
            )

            logger.info(
                f"成功計算移動平均線 - 藍線: {self.ma_periods['blue']}, 綠線: {self.ma_periods['green']}, 橘線: {self.ma_periods['orange']}"
            )

            return df

        except Exception as e:
            logger.error(f"計算移動平均線時發生錯誤: {e}")
            return df

    def calculate_slopes(
        self, df: pd.DataFrame, slope_periods: int = 5
    ) -> pd.DataFrame:
        """
        計算各均線的斜率

        Args:
            df: 包含移動平均線的 DataFrame
            slope_periods: 計算斜率的週期數

        Returns:
            添加了斜率的 DataFrame
        """
        try:
            df = df.copy()

            # 計算藍線斜率
            df["ma_blue_slope"] = df["ma_blue"].diff(slope_periods) / slope_periods

            # 計算綠線斜率
            df["ma_green_slope"] = df["ma_green"].diff(slope_periods) / slope_periods

            # 計算橘線斜率
            df["ma_orange_slope"] = df["ma_orange"].diff(slope_periods) / slope_periods

            logger.info(f"成功計算均線斜率，斜率週期: {slope_periods}")

            return df

        except Exception as e:
            logger.error(f"計算均線斜率時發生錯誤: {e}")
            return df

    def calculate_deviations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算價格與各均線的乖離率

        Args:
            df: 包含移動平均線的 DataFrame

        Returns:
            添加了乖離率的 DataFrame
        """
        try:
            df = df.copy()

            # 計算與藍線的乖離率
            df["blue_deviation"] = (df["close"] - df["ma_blue"]) / df["ma_blue"]

            # 計算與綠線的乖離率
            df["green_deviation"] = (df["close"] - df["ma_green"]) / df["ma_green"]

            # 計算與橘線的乖離率
            df["orange_deviation"] = (df["close"] - df["ma_orange"]) / df["ma_orange"]

            logger.info("成功計算價格乖離率")

            return df

        except Exception as e:
            logger.error(f"計算價格乖離率時發生錯誤: {e}")
            return df

    def calculate_volume_ratios(
        self, df: pd.DataFrame, volume_periods: int = 20
    ) -> pd.DataFrame:
        """
        計算成交量比率

        Args:
            df: 包含成交量數據的 DataFrame
            volume_periods: 計算成交量平均的週期數

        Returns:
            添加了成交量比率的 DataFrame
        """
        try:
            df = df.copy()

            # 計算成交量移動平均
            df["volume_ma"] = df["volume"].rolling(window=volume_periods).mean()

            # 計算成交量比率 (當前成交量 / 移動平均成交量)
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # 計算成交量變化率
            df["volume_change"] = df["volume"].pct_change()

            logger.info(f"成功計算成交量比率，週期: {volume_periods}")

            return df

        except Exception as e:
            logger.error(f"計算成交量比率時發生錯誤: {e}")
            return df

    def calculate_cross_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算均線交叉信號

        Args:
            df: 包含移動平均線的 DataFrame

        Returns:
            添加了交叉信號的 DataFrame
        """
        try:
            df = df.copy()

            # 初始化交叉信號列
            df["price_ma_cross"] = 0  # 價格與均線交叉
            df["blue_green_cross"] = 0  # 藍線與綠線交叉
            df["blue_orange_cross"] = 0  # 藍線與橘線交叉
            df["green_orange_cross"] = 0  # 綠線與橘線交叉

            # 計算價格與藍線的交叉
            for i in range(1, len(df)):
                prev_close = df.loc[df.index[i - 1], "close"]
                prev_ma_blue = df.loc[df.index[i - 1], "ma_blue"]
                curr_close = df.loc[df.index[i], "close"]
                curr_ma_blue = df.loc[df.index[i], "ma_blue"]

                # 黃金交叉 (價格從下方突破藍線)
                if prev_close <= prev_ma_blue and curr_close > curr_ma_blue:
                    df.loc[df.index[i], "price_ma_cross"] = 1
                # 死亡交叉 (價格從上方跌破藍線)
                elif prev_close >= prev_ma_blue and curr_close < curr_ma_blue:
                    df.loc[df.index[i], "price_ma_cross"] = -1

            # 計算均線之間的交叉
            for i in range(1, len(df)):
                # 藍線與綠線交叉
                prev_blue = df.loc[df.index[i - 1], "ma_blue"]
                prev_green = df.loc[df.index[i - 1], "ma_green"]
                curr_blue = df.loc[df.index[i], "ma_blue"]
                curr_green = df.loc[df.index[i], "ma_green"]

                if prev_blue <= prev_green and curr_blue > curr_green:
                    df.loc[df.index[i], "blue_green_cross"] = 1  # 黃金交叉
                elif prev_blue >= prev_green and curr_blue < curr_green:
                    df.loc[df.index[i], "blue_green_cross"] = -1  # 死亡交叉

                # 藍線與橘線交叉
                prev_orange = df.loc[df.index[i - 1], "ma_orange"]
                curr_orange = df.loc[df.index[i], "ma_orange"]

                if prev_blue <= prev_orange and curr_blue > curr_orange:
                    df.loc[df.index[i], "blue_orange_cross"] = 1  # 黃金交叉
                elif prev_blue >= prev_orange and curr_blue < curr_orange:
                    df.loc[df.index[i], "blue_orange_cross"] = -1  # 死亡交叉

                # 綠線與橘線交叉
                if prev_green <= prev_orange and curr_green > curr_orange:
                    df.loc[df.index[i], "green_orange_cross"] = 1  # 黃金交叉
                elif prev_green >= prev_orange and curr_green < curr_orange:
                    df.loc[df.index[i], "green_orange_cross"] = -1  # 死亡交叉

            logger.info("成功計算均線交叉信號")

            return df

        except Exception as e:
            logger.error(f"計算均線交叉信號時發生錯誤: {e}")
            return df

    def calculate_trend_strength(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算趨勢強度指標

        Args:
            df: 包含移動平均線和斜率的 DataFrame

        Returns:
            添加了趨勢強度指標的 DataFrame
        """
        try:
            df = df.copy()

            # 計算趨勢強度 (基於斜率的一致性)
            df["trend_strength"] = 0.0

            for i in range(len(df)):
                blue_slope = df.loc[df.index[i], "ma_blue_slope"]
                green_slope = df.loc[df.index[i], "ma_green_slope"]
                orange_slope = df.loc[df.index[i], "ma_orange_slope"]

                # 如果三個斜率都為正，趨勢強度為正
                if blue_slope > 0 and green_slope > 0 and orange_slope > 0:
                    df.loc[df.index[i], "trend_strength"] = 1.0
                # 如果三個斜率都為負，趨勢強度為負
                elif blue_slope < 0 and green_slope < 0 and orange_slope < 0:
                    df.loc[df.index[i], "trend_strength"] = -1.0
                # 如果斜率不一致，趨勢強度為0
                else:
                    df.loc[df.index[i], "trend_strength"] = 0.0

            # 計算趨勢一致性 (連續同向趨勢的數量)
            df["trend_consistency"] = 0

            for i in range(1, len(df)):
                prev_strength = df.loc[df.index[i - 1], "trend_strength"]
                curr_strength = df.loc[df.index[i], "trend_strength"]

                if prev_strength == curr_strength and curr_strength != 0:
                    df.loc[df.index[i], "trend_consistency"] = (
                        df.loc[df.index[i - 1], "trend_consistency"] + 1
                    )
                else:
                    df.loc[df.index[i], "trend_consistency"] = 0

            logger.info("成功計算趨勢強度指標")

            return df

        except Exception as e:
            logger.error(f"計算趨勢強度指標時發生錯誤: {e}")
            return df

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算所有技術指標

        Args:
            df: 包含 OHLCV 數據的 DataFrame

        Returns:
            包含所有技術指標的 DataFrame
        """
        try:
            logger.info("開始計算所有技術指標...")

            # 1. 計算移動平均線
            df = self.calculate_moving_averages(df)

            # 2. 計算斜率
            df = self.calculate_slopes(df)

            # 3. 計算乖離率
            df = self.calculate_deviations(df)

            # 4. 計算成交量比率
            df = self.calculate_volume_ratios(df)

            # 5. 計算交叉信號
            df = self.calculate_cross_signals(df)

            # 6. 計算趨勢強度
            df = self.calculate_trend_strength(df)

            # 清理 NaN 值
            df = df.dropna()

            logger.info(f"所有技術指標計算完成，有效數據: {len(df)} 筆")

            return df

        except Exception as e:
            logger.error(f"計算所有技術指標時發生錯誤: {e}")
            return df

    def get_indicator_summary(self, df: pd.DataFrame) -> Dict:
        """
        獲取技術指標摘要

        Args:
            df: 包含技術指標的 DataFrame

        Returns:
            技術指標摘要字典
        """
        try:
            if df.empty:
                return {}

            # 獲取最新的指標值
            latest = df.iloc[-1]

            summary = {
                "latest_date": latest["date"],
                "latest_close": latest["close"],
                "ma_blue": latest.get("ma_blue", None),
                "ma_green": latest.get("ma_green", None),
                "ma_orange": latest.get("ma_orange", None),
                "blue_slope": latest.get("ma_blue_slope", None),
                "green_slope": latest.get("ma_green_slope", None),
                "orange_slope": latest.get("ma_orange_slope", None),
                "blue_deviation": latest.get("blue_deviation", None),
                "trend_strength": latest.get("trend_strength", None),
                "trend_consistency": latest.get("trend_consistency", None),
                "volume_ratio": latest.get("volume_ratio", None),
            }

            # 計算趨勢方向
            if summary["trend_strength"] == 1.0:
                summary["trend_direction"] = "上升趨勢"
            elif summary["trend_strength"] == -1.0:
                summary["trend_direction"] = "下降趨勢"
            else:
                summary["trend_direction"] = "盤整"

            # 計算均線排列
            if summary["ma_blue"] and summary["ma_green"] and summary["ma_orange"]:
                if summary["ma_blue"] > summary["ma_green"] > summary["ma_orange"]:
                    summary["ma_alignment"] = "多頭排列"
                elif summary["ma_blue"] < summary["ma_green"] < summary["ma_orange"]:
                    summary["ma_alignment"] = "空頭排列"
                else:
                    summary["ma_alignment"] = "混亂排列"
            else:
                summary["ma_alignment"] = "數據不足"

            return summary

        except Exception as e:
            logger.error(f"獲取技術指標摘要時發生錯誤: {e}")
            return {}
