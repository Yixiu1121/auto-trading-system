#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小綠空頭策略 (Green Short Strategy)
基於小綠線的中期空頭策略，用於中期趨勢放空
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from loguru import logger


class GreenShortStrategy:
    """小綠空頭策略"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化小綠空頭策略

        Args:
            config: 策略配置參數
        """
        self.config = config
        self.name = "小綠空頭策略"

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
        self.break_days = config.get("break_days", 5)  # 連續站回天數
        self.profit_target = config.get("profit_target", 0.12)  # 獲利目標 12%
        self.stop_loss = config.get("stop_loss", 0.06)  # 停損點 6%

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

            # 計算連續站回天數
            df["consecutive_above"] = 0
            for i in range(1, len(df)):
                if df.iloc[i]["above_green"]:
                    df.iloc[i, df.columns.get_loc("consecutive_above")] = (
                        df.iloc[i - 1]["consecutive_above"] + 1
                    )
                else:
                    df.iloc[i, df.columns.get_loc("consecutive_above")] = 0

            # 生成信號
            for i in range(max(self.green_line_period, self.blue_line_period), len(df)):
                current_row = df.iloc[i]
                prev_row = df.iloc[i - 1]

                # 空頭入場條件
                entry_conditions = [
                    current_row["green_slope"] < 0,  # 小綠線呈負斜率
                    current_row["below_green"],  # 價格跌破小綠線
                    current_row["death_cross"],  # 小藍線與小綠線死亡交叉
                    current_row["volume_ratio"] > self.volume_threshold,  # 成交量放大
                ]

                # 檢查K線型態（簡化版）
                kline_bearish = self._check_bearish_kline_pattern(df, i)
                entry_conditions.append(kline_bearish)

                # 如果滿足入場條件
                if all(entry_conditions):
                    signal = {
                        "date": current_row["date"],
                        "action": "sell",
                        "price": current_row["close"],
                        "reason": "小綠空頭入場",
                        "details": {
                            "green_slope": current_row["green_slope"],
                            "below_green": current_row["below_green"],
                            "death_cross": current_row["death_cross"],
                            "volume_ratio": current_row["volume_ratio"],
                            "kline_bearish": kline_bearish,
                        },
                    }
                    signals.append(signal)
                    logger.info(
                        f"生成空頭入場信號: {current_row['date']} @ {current_row['close']:.2f}"
                    )

                # 空頭出場條件
                exit_conditions = [
                    current_row["golden_cross"],  # 小藍線與小綠線黃金交叉
                    current_row["consecutive_above"]
                    >= self.break_days,  # 連續站回小綠線
                    current_row["green_slope"] > 0,  # 小綠線轉為正斜率
                ]

                # 檢查獲利/停損
                if len(signals) > 0 and signals[-1]["action"] == "sell":
                    entry_price = signals[-1]["price"]
                    current_price = current_row["close"]
                    profit_rate = (
                        entry_price - current_price
                    ) / entry_price  # 空頭獲利計算

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
                        "action": "buy",
                        "price": current_row["close"],
                        "reason": (
                            exit_reason if "exit_reason" in locals() else "小綠空頭出場"
                        ),
                        "details": {
                            "golden_cross": current_row["golden_cross"],
                            "consecutive_above": current_row["consecutive_above"],
                            "green_slope": current_row["green_slope"],
                            "profit_rate": (
                                profit_rate if "profit_rate" in locals() else 0
                            ),
                        },
                    }
                    signals.append(signal)
                    logger.info(
                        f"生成空頭出場信號: {current_row['date']} @ {current_row['close']:.2f}"
                    )

            logger.info(f"{self.name} 生成 {len(signals)} 個交易信號")
            return signals

        except Exception as e:
            logger.error(f"{self.name} 生成信號時發生錯誤: {e}")
            return signals

    def _check_bearish_kline_pattern(self, df: pd.DataFrame, index: int) -> bool:
        """
        檢查空頭K線型態

        Args:
            df: K線數據
            index: 當前索引

        Returns:
            是否為空頭型態
        """
        if index < 2:
            return False

        try:
            current = df.iloc[index]
            prev = df.iloc[index - 1]

            # 流星線：上影線長，下影線短，實體小
            shooting_star = (
                current["high"] > current["open"]
                and current["high"] > current["close"]
                and (current["high"] - max(current["open"], current["close"]))
                > (min(current["open"], current["close"]) - current["low"]) * 2
            )

            # 覆蓋線：當前K線完全覆蓋前一根K線
            covering = (
                current["open"] > prev["close"]
                and current["close"] < prev["open"]
                and current["close"] < prev["close"]
                and current["open"] > prev["open"]
            )

            # 黃昏星：三根K線組合
            evening_star = False
            if index >= 2:
                first = df.iloc[index - 2]
                second = df.iloc[index - 1]
                third = current

                evening_star = (
                    first["close"] > first["open"]  # 第一根陽線
                    and abs(second["close"] - second["open"])
                    < (first["close"] - first["open"]) * 0.3  # 第二根小實體
                    and third["close"] < third["open"]  # 第三根陰線
                    and third["close"]
                    < (first["open"] + first["close"]) / 2  # 第三根收盤價低於第一根中點
                )

            return shooting_star or covering or evening_star

        except Exception as e:
            logger.error(f"檢查K線型態時發生錯誤: {e}")
            return False

    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "name": self.name,
            "description": "基於小綠線的中期空頭策略，用於中期趨勢放空",
            "parameters": {
                "green_line_period": self.green_line_period,
                "blue_line_period": self.blue_line_period,
                "volume_threshold": self.volume_threshold,
                "break_days": self.break_days,
                "profit_target": self.profit_target,
                "stop_loss": self.stop_loss,
            },
            "entry_conditions": [
                "小綠線呈負斜率且價格跌破小綠線",
                "小藍線與小綠線死亡交叉",
                "成交量放大確認跌破有效",
                "K線型態出現空頭訊號",
            ],
            "exit_conditions": [
                "小藍線與小綠線黃金交叉",
                "連續5根K線站回小綠線上",
                "小綠線轉為正斜率",
                "達到預設獲利目標或停損點",
            ],
        }
