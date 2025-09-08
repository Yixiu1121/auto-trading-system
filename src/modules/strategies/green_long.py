#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小綠多頭策略 (Green Long Strategy)
基於小綠線（季線）的中期多頭策略，適合波段操作
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from loguru import logger


class GreenLongStrategy:
    """小綠多頭策略"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化小綠多頭策略

        Args:
            config: 策略配置參數
        """
        self.config = config
        self.name = "小綠多頭策略"

        # 策略參數
        self.green_line_period = config.get(
            "green_line", 360
        )  # 小綠線週期（360根4小時K線，約3個月）
        self.blue_line_period = config.get(
            "blue_line", 120
        )  # 小藍線週期（120根4小時K線，約1個月）

        # 成交量參數
        self.volume_threshold = config.get("volume_threshold", 1.5)  # 成交量放大倍數

        # 出場條件參數
        self.break_days = config.get("break_days", 5)  # 連續跌破天數
        self.profit_target = config.get("profit_target", 0.15)  # 獲利目標 15%
        self.stop_loss = config.get("stop_loss", 0.08)  # 停損點 8%

        logger.info(f"{self.name} 初始化完成")
        logger.info(
            f"小綠線週期: {self.green_line_period}, 小藍線週期: {self.blue_line_period}"
        )
        logger.info(
            f"成交量閾值: {self.volume_threshold}, 獲利目標: {self.profit_target}, 停損: {self.stop_loss}"
        )

    def generate_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        生成交易信號

        Args:
            df: 包含技術指標的K線數據

        Returns:
            交易信號列表
        """
        signals = []

        if len(df) < max(self.green_line_period, self.blue_line_period) + 10:
            logger.warning(
                f"數據不足，需要至少 {max(self.green_line_period, self.blue_line_period) + 10} 根K線"
            )
            return signals

        try:
            # 計算移動平均線
            df["green_line"] = df["close"].rolling(window=self.green_line_period).mean()
            df["blue_line"] = df["close"].rolling(window=self.blue_line_period).mean()

            # 計算斜率
            df["green_slope"] = df["green_line"].diff(5) / 5  # 5根K線的斜率
            df["blue_slope"] = df["blue_line"].diff(5) / 5

            # 計算成交量移動平均
            df["volume_ma"] = df["volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # 計算交叉信號
            df["golden_cross"] = (df["blue_line"] > df["green_line"]) & (
                df["blue_line"].shift(1) <= df["green_line"].shift(1)
            )
            df["death_cross"] = (df["blue_line"] < df["green_line"]) & (
                df["blue_line"].shift(1) >= df["green_line"].shift(1)
            )

            # 計算價格位置
            df["above_green"] = df["close"] > df["green_line"]
            df["below_green"] = df["close"] < df["green_line"]

            # 計算連續跌破天數
            df["consecutive_below"] = 0
            for i in range(1, len(df)):
                if df.iloc[i]["below_green"]:
                    df.iloc[i, df.columns.get_loc("consecutive_below")] = (
                        df.iloc[i - 1]["consecutive_below"] + 1
                    )
                else:
                    df.iloc[i, df.columns.get_loc("consecutive_below")] = 0

            # 生成信號
            for i in range(max(self.green_line_period, self.blue_line_period), len(df)):
                current_row = df.iloc[i]
                prev_row = df.iloc[i - 1]

                # 多頭入場條件
                entry_conditions = [
                    current_row["green_slope"] > 0,  # 小綠線呈正斜率
                    current_row["above_green"],  # 價格站上小綠線
                    current_row["golden_cross"],  # 小藍線與小綠線黃金交叉
                    current_row["volume_ratio"] > self.volume_threshold,  # 成交量放大
                ]

                # 檢查K線型態（簡化版）
                kline_bullish = self._check_bullish_kline_pattern(df, i)
                entry_conditions.append(kline_bullish)

                # 如果滿足入場條件
                if all(entry_conditions):
                    signal = {
                        "date": current_row["date"],
                        "action": "buy",
                        "price": current_row["close"],
                        "reason": "小綠多頭入場",
                        "details": {
                            "green_slope": current_row["green_slope"],
                            "above_green": current_row["above_green"],
                            "golden_cross": current_row["golden_cross"],
                            "volume_ratio": current_row["volume_ratio"],
                            "kline_bullish": kline_bullish,
                        },
                    }
                    signals.append(signal)
                    logger.info(
                        f"生成多頭入場信號: {current_row['date']} @ {current_row['close']:.2f}"
                    )

                # 多頭出場條件
                exit_conditions = [
                    current_row["death_cross"],  # 小藍線與小綠線死亡交叉
                    current_row["consecutive_below"]
                    >= self.break_days,  # 連續跌破小綠線
                    current_row["green_slope"] < 0,  # 小綠線轉為負斜率
                ]

                # 檢查獲利/停損
                if len(signals) > 0 and signals[-1]["action"] == "buy":
                    entry_price = signals[-1]["price"]
                    current_price = current_row["close"]
                    profit_rate = (current_price - entry_price) / entry_price

                    if profit_rate >= self.profit_target:
                        exit_conditions.append(True)
                        exit_reason = f"達到獲利目標 {profit_rate:.2%}"
                    elif profit_rate <= -self.stop_loss:
                        exit_conditions.append(True)
                        exit_reason = f"觸及停損點 {profit_rate:.2%}"
                    else:
                        exit_reason = "其他出場條件"

                # 如果滿足出場條件
                if any(exit_conditions):
                    signal = {
                        "date": current_row["date"],
                        "action": "sell",
                        "price": current_row["close"],
                        "reason": (
                            exit_reason if "exit_reason" in locals() else "小綠多頭出場"
                        ),
                        "details": {
                            "death_cross": current_row["death_cross"],
                            "consecutive_below": current_row["consecutive_below"],
                            "green_slope": current_row["green_slope"],
                            "profit_rate": (
                                profit_rate if "profit_rate" in locals() else 0
                            ),
                        },
                    }
                    signals.append(signal)
                    logger.info(
                        f"生成多頭出場信號: {current_row['date']} @ {current_row['close']:.2f}"
                    )

            logger.info(f"{self.name} 生成 {len(signals)} 個交易信號")
            return signals

        except Exception as e:
            logger.error(f"{self.name} 生成信號時發生錯誤: {e}")
            return signals

    def _check_bullish_kline_pattern(self, df: pd.DataFrame, index: int) -> bool:
        """
        檢查多頭K線型態

        Args:
            df: K線數據
            index: 當前索引

        Returns:
            是否為多頭型態
        """
        if index < 2:
            return False

        try:
            current = df.iloc[index]
            prev = df.iloc[index - 1]

            # 錘子線：下影線長，上影線短，實體小
            hammer = (
                current["low"] < current["open"]
                and current["low"] < current["close"]
                and (current["high"] - max(current["open"], current["close"]))
                < (min(current["open"], current["close"]) - current["low"]) * 0.5
            )

            # 吞噬線：當前K線完全包含前一根K線
            engulfing = (
                current["open"] < prev["close"]
                and current["close"] > prev["open"]
                and current["close"] > prev["close"]
                and current["open"] < prev["open"]
            )

            # 晨星：三根K線組合
            morning_star = False
            if index >= 2:
                first = df.iloc[index - 2]
                second = df.iloc[index - 1]
                third = current

                morning_star = (
                    first["close"] < first["open"]  # 第一根陰線
                    and abs(second["close"] - second["open"])
                    < (first["close"] - first["open"]) * 0.3  # 第二根小實體
                    and third["close"] > third["open"]  # 第三根陽線
                    and third["close"]
                    > (first["open"] + first["close"]) / 2  # 第三根收盤價超過第一根中點
                )

            return hammer or engulfing or morning_star

        except Exception as e:
            logger.error(f"檢查K線型態時發生錯誤: {e}")
            return False

    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "name": self.name,
            "description": "基於小綠線（季線）的中期多頭策略，適合波段操作",
            "parameters": {
                "green_line_period": self.green_line_period,
                "blue_line_period": self.blue_line_period,
                "volume_threshold": self.volume_threshold,
                "break_days": self.break_days,
                "profit_target": self.profit_target,
                "stop_loss": self.stop_loss,
            },
            "entry_conditions": [
                "小綠線呈正斜率且價格站上小綠線",
                "小藍線與小綠線黃金交叉",
                "成交量放大確認突破有效",
                "K線型態出現多頭訊號",
            ],
            "exit_conditions": [
                "小藍線與小綠線死亡交叉",
                "連續5根K線跌破小綠線",
                "小綠線轉為負斜率",
                "達到預設獲利目標或停損點",
            ],
        }
