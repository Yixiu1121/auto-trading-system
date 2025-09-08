#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小橘空頭策略 (Orange Short Strategy)
基於小橘線的長期避險策略，用於長期趨勢保護
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from loguru import logger


class OrangeShortStrategy:
    """小橘空頭策略"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化小橘空頭策略

        Args:
            config: 策略配置參數
        """
        self.config = config
        self.name = "小橘空頭策略"

        # 策略參數
        self.orange_line_period = config.get(
            "orange_line", 1440
        )  # 小橘線週期（1440根4小時K線，約6個月）
        self.green_line_period = config.get(
            "green_line", 360
        )  # 小綠線週期（360根4小時K線，約3個月）
        self.blue_line_period = config.get(
            "blue_line", 120
        )  # 小藍線週期（120根4小時K線，約1個月）

        # 成交量參數
        self.volume_threshold = config.get(
            "volume_threshold", 0.8
        )  # 成交量萎縮閾值（長期趨勢確認）

        # 出場條件參數
        self.break_days = config.get(
            "break_days", 10
        )  # 連續站回天數（長期策略容忍度較高）
        self.profit_target = config.get("profit_target", 0.20)  # 獲利目標 20%
        self.stop_loss = config.get("stop_loss", 0.10)  # 停損點 10%

        logger.info(f"{self.name} 初始化完成")
        logger.info(
            f"小橘線週期: {self.orange_line_period}, 小綠線週期: {self.green_line_period}, 小藍線週期: {self.blue_line_period}"
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

        if (
            len(df)
            < max(
                self.orange_line_period, self.green_line_period, self.blue_line_period
            )
            + 10
        ):
            logger.warning(
                f"數據不足，需要至少 {max(self.orange_line_period, self.green_line_period, self.blue_line_period) + 10} 根K線"
            )
            return signals

        try:
            # 計算移動平均線
            df["orange_line"] = (
                df["close"].rolling(window=self.orange_line_period).mean()
            )
            df["green_line"] = df["close"].rolling(window=self.green_line_period).mean()
            df["blue_line"] = df["close"].rolling(window=self.blue_line_period).mean()

            # 計算斜率
            df["orange_slope"] = (
                df["orange_line"].diff(10) / 10
            )  # 10根K線的斜率（長期趨勢）
            df["green_slope"] = df["green_line"].diff(5) / 5
            df["blue_slope"] = df["blue_line"].diff(5) / 5

            # 計算成交量移動平均
            df["volume_ma"] = df["volume"].rolling(window=50).mean()  # 長期成交量平均
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # 計算價格位置
            df["above_orange"] = df["close"] > df["orange_line"]
            df["below_orange"] = df["close"] < df["orange_line"]

            # 計算三線排列
            df["bullish_alignment"] = (df["blue_line"] > df["green_line"]) & (
                df["green_line"] > df["orange_line"]
            )
            df["bearish_alignment"] = (df["blue_line"] < df["green_line"]) & (
                df["green_line"] < df["orange_line"]
            )

            # 計算連續站回天數
            df["consecutive_above"] = 0
            for i in range(1, len(df)):
                if df.iloc[i]["above_orange"]:
                    df.iloc[i, df.columns.get_loc("consecutive_above")] = (
                        df.iloc[i - 1]["consecutive_above"] + 1
                    )
                else:
                    df.iloc[i, df.columns.get_loc("consecutive_above")] = 0

            # 生成信號
            for i in range(
                max(
                    self.orange_line_period,
                    self.green_line_period,
                    self.blue_line_period,
                ),
                len(df),
            ):
                current_row = df.iloc[i]
                prev_row = df.iloc[i - 1]

                # 空頭入場條件
                entry_conditions = [
                    current_row["below_orange"],  # 價格跌破小橘線且無法收復
                    current_row["orange_slope"] < 0,  # 小橘線呈現明顯負斜率
                    current_row["bearish_alignment"],  # 藍綠橘三線呈空頭排列
                    current_row["volume_ratio"]
                    < self.volume_threshold,  # 長期成交量萎縮確認趨勢
                ]

                # 如果滿足入場條件
                if all(entry_conditions):
                    signal = {
                        "date": current_row["date"],
                        "action": "sell",
                        "price": current_row["close"],
                        "reason": "小橘空頭入場",
                        "details": {
                            "below_orange": current_row["below_orange"],
                            "orange_slope": current_row["orange_slope"],
                            "bearish_alignment": current_row["bearish_alignment"],
                            "volume_ratio": current_row["volume_ratio"],
                        },
                    }
                    signals.append(signal)
                    logger.info(
                        f"生成空頭入場信號: {current_row['date']} @ {current_row['close']:.2f}"
                    )

                # 空頭出場條件
                exit_conditions = [
                    current_row["consecutive_above"]
                    >= self.break_days,  # 價格重新站回小橘線上
                    current_row["orange_slope"] > 0,  # 小橘線轉為正斜率
                    current_row["bullish_alignment"],  # 三線排列轉為多頭
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
                        exit_reason = f"達成預設獲利目標 {profit_rate:.2%}"
                    elif profit_rate <= -self.stop_loss:
                        exit_conditions.append(True)
                        exit_reason = f"觸及止損點 {profit_rate:.2%}"
                    else:
                        exit_reason = "其他出場條件"

                # 如果滿足出場條件
                if any(exit_conditions):
                    signal = {
                        "date": current_row["date"],
                        "action": "buy",
                        "price": current_row["close"],
                        "reason": (
                            exit_reason if "exit_reason" in locals() else "小橘空頭出場"
                        ),
                        "details": {
                            "consecutive_above": current_row["consecutive_above"],
                            "orange_slope": current_row["orange_slope"],
                            "bullish_alignment": current_row["bullish_alignment"],
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

    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "name": self.name,
            "description": "基於小橘線的長期避險策略，用於長期趨勢保護",
            "parameters": {
                "orange_line_period": self.orange_line_period,
                "green_line_period": self.green_line_period,
                "blue_line_period": self.blue_line_period,
                "volume_threshold": self.volume_threshold,
                "break_days": self.break_days,
                "profit_target": self.profit_target,
                "stop_loss": self.stop_loss,
            },
            "entry_conditions": [
                "價格跌破小橘線且無法收復",
                "小橘線呈現明顯負斜率",
                "藍綠橘三線呈空頭排列",
                "長期成交量萎縮確認趨勢",
            ],
            "exit_conditions": [
                "價格重新站回小橘線上",
                "小橘線轉為正斜率",
                "三線排列轉為多頭",
                "達成預設獲利目標或止損",
            ],
        }
