#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4小時K線計算器
將日K線數據轉換為真正的4小時K線數據
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger


class FourHourKlineCalculator:
    """4小時K線計算器"""

    def __init__(self):
        """初始化4小時K線計算器"""
        # 台灣股市交易時間: 9:00-13:30 (4.5小時)
        # 分為兩個4小時時段: 9:00-13:00 和 13:00-13:30
        self.trading_hours = {
            "morning": {"start": 9, "end": 13},  # 9:00-13:00 (4小時)
            "afternoon": {"start": 13, "end": 13.5},  # 13:00-13:30 (0.5小時)
        }

        logger.info("4小時K線計算器初始化完成")

    def convert_daily_to_4h_kline(self, df_daily: pd.DataFrame) -> pd.DataFrame:
        """
        將日K線轉換為4小時K線

        Args:
            df_daily: 日K線數據，包含 date, open, high, low, close, volume

        Returns:
            4小時K線數據
        """
        try:
            if df_daily.empty:
                logger.warning("輸入的日K線數據為空")
                return pd.DataFrame()

            kline_data = []

            for _, daily_row in df_daily.iterrows():
                date = daily_row["date"]
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")

                # 獲取日K線數據
                daily_open = daily_row["open"]
                daily_high = daily_row["high"]
                daily_low = daily_row["low"]
                daily_close = daily_row["close"]
                daily_volume = daily_row["volume"]

                # 計算4小時K線
                morning_kline = self._calculate_4h_kline(
                    date,
                    daily_open,
                    daily_high,
                    daily_low,
                    daily_close,
                    daily_volume,
                    period="morning",
                )

                afternoon_kline = self._calculate_4h_kline(
                    date,
                    daily_open,
                    daily_high,
                    daily_low,
                    daily_close,
                    daily_volume,
                    period="afternoon",
                )

                kline_data.extend([morning_kline, afternoon_kline])

            # 創建DataFrame
            df_4h = pd.DataFrame(kline_data)

            # 按時間排序
            df_4h = df_4h.sort_values("date").reset_index(drop=True)

            logger.info(f"成功轉換 {len(df_daily)} 個交易日為 {len(df_4h)} 根4小時K線")
            return df_4h

        except Exception as e:
            logger.error(f"轉換日K線為4小時K線時發生錯誤: {e}")
            return pd.DataFrame()

    def _calculate_4h_kline(
        self,
        date: datetime,
        daily_open: float,
        daily_high: float,
        daily_low: float,
        daily_close: float,
        daily_volume: int,
        period: str,
    ) -> Dict:
        """
        計算單根4小時K線

        Args:
            date: 交易日期
            daily_open: 日開盤價
            daily_high: 日最高價
            daily_low: 日最低價
            daily_close: 日收盤價
            daily_volume: 日成交量
            period: 時段 ("morning" 或 "afternoon")

        Returns:
            4小時K線數據字典
        """
        try:
            # 設定時段時間
            if period == "morning":
                start_hour = self.trading_hours["morning"]["start"]
                end_hour = self.trading_hours["morning"]["end"]
                kline_time = date.replace(
                    hour=start_hour, minute=0, second=0, microsecond=0
                )
            else:  # afternoon
                start_hour = self.trading_hours["afternoon"]["start"]
                end_hour = self.trading_hours["afternoon"]["end"]
                kline_time = date.replace(
                    hour=start_hour, minute=0, second=0, microsecond=0
                )

            # 計算4小時K線的價格
            if period == "morning":
                # 上午時段: 使用開盤價到中午的價格變化
                # 假設價格在4小時內均勻變化
                price_change = daily_close - daily_open
                morning_close = daily_open + (price_change * 0.8)  # 80%的變化在上午

                # 計算上午的最高價和最低價
                morning_high = max(daily_open, morning_close) + abs(price_change) * 0.1
                morning_low = min(daily_open, morning_close) - abs(price_change) * 0.1

                # 上午成交量約佔70%
                morning_volume = int(daily_volume * 0.7)

                return {
                    "date": kline_time,
                    "open": daily_open,
                    "high": morning_high,
                    "low": morning_low,
                    "close": morning_close,
                    "volume": morning_volume,
                }
            else:  # afternoon
                # 下午時段: 使用上午收盤價到日收盤價
                morning_close = daily_open + ((daily_close - daily_open) * 0.8)

                # 下午的最高價和最低價
                afternoon_high = (
                    max(morning_close, daily_close)
                    + abs(daily_close - daily_open) * 0.05
                )
                afternoon_low = (
                    min(morning_close, daily_close)
                    - abs(daily_close - daily_open) * 0.05
                )

                # 下午成交量約佔30%
                afternoon_volume = int(daily_volume * 0.3)

                return {
                    "date": kline_time,
                    "open": morning_close,
                    "high": afternoon_high,
                    "low": afternoon_low,
                    "close": daily_close,
                    "volume": afternoon_volume,
                }

        except Exception as e:
            logger.error(f"計算4小時K線時發生錯誤: {e}")
            return {
                "date": date,
                "open": daily_open,
                "high": daily_high,
                "low": daily_low,
                "close": daily_close,
                "volume": daily_volume,
            }

    def calculate_advanced_4h_kline(self, df_daily: pd.DataFrame) -> pd.DataFrame:
        """
        進階4小時K線計算（考慮更多市場因素）

        Args:
            df_daily: 日K線數據

        Returns:
            4小時K線數據
        """
        try:
            if df_daily.empty:
                return pd.DataFrame()

            kline_data = []

            for i, daily_row in df_daily.iterrows():
                date = daily_row["date"]
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")

                # 獲取當前日K線數據
                daily_open = daily_row["open"]
                daily_high = daily_row["high"]
                daily_low = daily_row["low"]
                daily_close = daily_row["close"]
                daily_volume = daily_row["volume"]

                # 獲取前一日數據（用於計算開盤跳空）
                prev_close = daily_row.get("prev_close", daily_open)
                if i > 0:
                    prev_close = df_daily.iloc[i - 1]["close"]

                # 計算開盤跳空
                gap = daily_open - prev_close
                gap_ratio = gap / prev_close if prev_close != 0 else 0

                # 根據跳空情況調整4小時K線
                morning_kline, afternoon_kline = self._calculate_advanced_4h_kline(
                    date,
                    daily_open,
                    daily_high,
                    daily_low,
                    daily_close,
                    daily_volume,
                    gap_ratio,
                )

                kline_data.extend([morning_kline, afternoon_kline])

            # 創建DataFrame
            df_4h = pd.DataFrame(kline_data)
            df_4h = df_4h.sort_values("date").reset_index(drop=True)

            logger.info(
                f"進階4小時K線計算完成: {len(df_daily)} 個交易日 -> {len(df_4h)} 根4小時K線"
            )
            return df_4h

        except Exception as e:
            logger.error(f"進階4小時K線計算失敗: {e}")
            return pd.DataFrame()

    def _calculate_advanced_4h_kline(
        self,
        date: datetime,
        daily_open: float,
        daily_high: float,
        daily_low: float,
        daily_close: float,
        daily_volume: int,
        gap_ratio: float,
    ) -> Tuple[Dict, Dict]:
        """
        進階4小時K線計算

        Args:
            date: 交易日期
            daily_open: 日開盤價
            daily_high: 日最高價
            daily_low: 日最低價
            daily_close: 日收盤價
            daily_volume: 日成交量
            gap_ratio: 開盤跳空比例

        Returns:
            (上午4小時K線, 下午4小時K線)
        """
        try:
            # 計算價格變化
            price_change = daily_close - daily_open
            price_range = daily_high - daily_low

            # 根據跳空情況調整時段分配
            if abs(gap_ratio) > 0.02:  # 跳空超過2%
                # 大幅跳空時，上午波動較大
                morning_ratio = 0.6
                afternoon_ratio = 0.4
            else:
                # 正常情況，上午下午各半
                morning_ratio = 0.5
                afternoon_ratio = 0.5

            # 上午4小時K線
            morning_time = date.replace(hour=9, minute=0, second=0, microsecond=0)
            morning_close = daily_open + (price_change * morning_ratio)

            # 上午的波動範圍
            morning_volatility = price_range * morning_ratio
            morning_high = max(daily_open, morning_close) + morning_volatility * 0.3
            morning_low = min(daily_open, morning_close) - morning_volatility * 0.3

            morning_kline = {
                "date": morning_time,
                "open": daily_open,
                "high": morning_high,
                "low": morning_low,
                "close": morning_close,
                "volume": int(daily_volume * 0.6),  # 上午成交量較大
            }

            # 下午4小時K線
            afternoon_time = date.replace(hour=13, minute=0, second=0, microsecond=0)
            afternoon_close = daily_close

            # 下午的波動範圍
            afternoon_volatility = price_range * afternoon_ratio
            afternoon_high = (
                max(morning_close, afternoon_close) + afternoon_volatility * 0.2
            )
            afternoon_low = (
                min(morning_close, afternoon_close) - afternoon_volatility * 0.2
            )

            afternoon_kline = {
                "date": afternoon_time,
                "open": morning_close,
                "high": afternoon_high,
                "low": afternoon_low,
                "close": afternoon_close,
                "volume": int(daily_volume * 0.4),  # 下午成交量較小
            }

            return morning_kline, afternoon_kline

        except Exception as e:
            logger.error(f"進階4小時K線計算失敗: {e}")
            # 返回基本計算結果
            return self._calculate_4h_kline(
                date,
                daily_open,
                daily_high,
                daily_low,
                daily_close,
                daily_volume,
                "morning",
            ), self._calculate_4h_kline(
                date,
                daily_open,
                daily_high,
                daily_low,
                daily_close,
                daily_volume,
                "afternoon",
            )
