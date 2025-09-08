#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易策略基類
定義所有策略的通用接口和功能
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger


class BaseStrategy(ABC):
    """交易策略基類"""

    def __init__(self, config: Dict, name: str):
        """初始化策略"""
        self.config = config
        self.name = name
        self.enabled = config.get("enabled", True)
        self.min_signal_strength = config.get("min_signal_strength", 0.7)
        self.entry_threshold = config.get("entry_threshold", 0.02)

        logger.info(f"策略 {name} 初始化完成")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """生成交易信號 - 子類必須實現"""
        pass

    @abstractmethod
    def check_entry_conditions(
        self, data: pd.DataFrame, index: int
    ) -> Tuple[bool, float]:
        """檢查入場條件 - 子類必須實現"""
        pass

    @abstractmethod
    def check_exit_conditions(
        self, data: pd.DataFrame, index: int, position: Dict
    ) -> Tuple[bool, str]:
        """檢查出場條件 - 子類必須實現"""
        pass

    def calculate_signal_strength(self, data: pd.DataFrame, index: int) -> float:
        """計算信號強度 (0.0 - 1.0)"""
        try:
            if index < 20:  # 需要足夠的數據
                return 0.0

            # 基礎信號強度計算
            strength = 0.0

            # 趨勢強度貢獻 (0-0.4)
            trend_strength = abs(data["trend_strength"].iloc[index])
            strength += min(trend_strength / 3.0, 1.0) * 0.4

            # 成交量貢獻 (0-0.3)
            volume_ratio = data["volume_ratio"].iloc[index]
            if volume_ratio > 1.5:
                strength += min((volume_ratio - 1.5) / 2.0, 1.0) * 0.3

            # 乖離率貢獻 (0-0.3)
            deviation = abs(data["blue_deviation"].iloc[index])
            if deviation < 5.0:  # 乖離率適中
                strength += (1.0 - deviation / 5.0) * 0.3

            return min(strength, 1.0)

        except Exception as e:
            logger.error(f"信號強度計算失敗: {e}")
            return 0.0

    def validate_data(self, data: pd.DataFrame) -> bool:
        """驗證數據完整性"""
        try:
            required_columns = [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "blue_line",
                "green_line",
                "orange_line",
                "blue_slope",
                "green_slope",
                "orange_slope",
                "trend_strength",
                "volume_ratio",
                "blue_deviation",
            ]

            for col in required_columns:
                if col not in data.columns:
                    logger.error(f"缺少必要列: {col}")
                    return False

            if len(data) < 50:
                logger.error("數據量不足")
                return False

            return True

        except Exception as e:
            logger.error(f"數據驗證失敗: {e}")
            return False

    def get_strategy_info(self) -> Dict:
        """獲取策略信息"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "min_signal_strength": self.min_signal_strength,
            "entry_threshold": self.entry_threshold,
            "type": self.__class__.__name__,
            "description": self.get_strategy_description(),
            "parameters": self.get_strategy_parameters(),
        }

    def get_strategy_parameters(self) -> Dict:
        """獲取策略參數 - 子類可以重寫"""
        return {
            "min_signal_strength": self.min_signal_strength,
            "entry_threshold": self.entry_threshold,
        }

    def get_strategy_description(self) -> str:
        """獲取策略描述 - 子類可以重寫"""
        return f"{self.name} - 基於技術指標的交易策略"

    def health_check(self) -> Dict:
        """健康檢查"""
        try:
            return {
                "healthy": True,
                "message": f"策略 {self.name} 運行正常",
                "strategy_info": self.get_strategy_info(),
            }
        except Exception as e:
            return {"healthy": False, "message": f"策略 {self.name} 異常: {e}"}
