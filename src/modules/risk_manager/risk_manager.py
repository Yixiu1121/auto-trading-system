#!/usr/bin/env python3
"""
風險管理器
負責資金管理、風險控制和交易限制
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger
import json


@dataclass
class RiskLimits:
    """風險限制配置"""

    max_position_size: float = 100000  # 最大倉位大小
    max_risk_per_trade: float = 0.02  # 每筆交易最大風險比例
    max_daily_loss: float = 0.05  # 每日最大虧損比例
    max_open_positions: int = 5  # 最大同時持倉數量
    min_risk_reward_ratio: float = 2.0  # 最小風險報酬比
    max_sector_exposure: float = 0.3  # 最大行業暴露度


@dataclass
class Position:
    """持倉信息"""

    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    side: str  # "long" or "short"
    pnl: float = 0.0
    unrealized_pnl: float = 0.0


class RiskManager:
    """風險管理器"""

    def __init__(self, config: Dict):
        """初始化風險管理器"""
        self.config = config
        self.running = False

        # 風險限制
        risk_config = config.get("risk_management", {})
        self.risk_limits = RiskLimits(
            max_position_size=risk_config.get("max_position_size", 100000),
            max_risk_per_trade=risk_config.get("max_risk_per_trade", 0.02),
            max_daily_loss=risk_config.get("max_daily_loss", 0.05),
            max_open_positions=risk_config.get("max_open_positions", 5),
            min_risk_reward_ratio=risk_config.get("min_risk_reward_ratio", 2.0),
            max_sector_exposure=risk_config.get("max_sector_exposure", 0.3),
        )

        # 當前狀態
        self.positions: Dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_capital = 1000000  # 總資金

        # 風險警報
        self.alerts = []

        logger.info("風險管理器初始化完成")

    def start(self):
        """啟動風險管理器"""
        if self.running:
            logger.warning("風險管理器已在運行中")
            return

        self.running = True
        logger.info("風險管理器已啟動")

    def stop(self):
        """停止風險管理器"""
        if not self.running:
            return

        self.running = False
        logger.info("風險管理器已停止")

    def check_trade_allowed(self, signal: Dict) -> bool:
        """檢查是否允許交易"""
        try:
            # 檢查基本風險限制
            if not self._check_basic_limits(signal):
                return False

            # 檢查資金限制
            if not self._check_capital_limits(signal):
                return False

            # 檢查持倉限制
            if not self._check_position_limits(signal):
                return False

            # 檢查風險報酬比
            if not self._check_risk_reward_ratio(signal):
                return False

            # 檢查行業暴露度
            if not self._check_sector_exposure(signal):
                return False

            return True

        except Exception as e:
            logger.error(f"檢查交易限制失敗: {e}")
            return False

    def _check_basic_limits(self, signal: Dict) -> bool:
        """檢查基本風險限制"""
        try:
            # 檢查每日虧損限制
            if self.daily_pnl < -(self.total_capital * self.risk_limits.max_daily_loss):
                logger.warning(f"達到每日虧損限制: {self.daily_pnl}")
                return False

            # 檢查交易頻率
            if self.daily_trades >= 50:  # 每日最大交易次數
                logger.warning("達到每日最大交易次數")
                return False

            return True

        except Exception as e:
            logger.error(f"檢查基本限制失敗: {e}")
            return False

    def _check_capital_limits(self, signal: Dict) -> bool:
        """檢查資金限制"""
        try:
            # 計算所需資金
            quantity = signal.get("quantity", 1000)
            price = signal.get("price", 0)
            required_capital = quantity * price

            # 檢查是否超過最大倉位大小
            if required_capital > self.risk_limits.max_position_size:
                logger.warning(f"超過最大倉位大小: {required_capital}")
                return False

            # 檢查可用資金
            available_capital = self._get_available_capital()
            if required_capital > available_capital:
                logger.warning(
                    f"資金不足: 需要 {required_capital}, 可用 {available_capital}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"檢查資金限制失敗: {e}")
            return False

    def _check_position_limits(self, signal: Dict) -> bool:
        """檢查持倉限制"""
        try:
            symbol = signal.get("symbol", "")
            action = signal.get("signal", {}).get("action", "")

            # 檢查最大同時持倉數量
            if len(self.positions) >= self.risk_limits.max_open_positions:
                logger.warning(f"達到最大持倉數量: {len(self.positions)}")
                return False

            # 檢查是否已有相同股票的持倉
            if symbol in self.positions:
                existing_position = self.positions[symbol]

                # 如果是相反方向的交易，允許
                if (action == "buy" and existing_position.side == "short") or (
                    action == "sell" and existing_position.side == "long"
                ):
                    return True

                # 如果是相同方向，檢查是否超過限制
                logger.warning(f"已有相同股票持倉: {symbol}")
                return False

            return True

        except Exception as e:
            logger.error(f"檢查持倉限制失敗: {e}")
            return False

    def _check_risk_reward_ratio(self, signal: Dict) -> bool:
        """檢查風險報酬比"""
        try:
            # 這裡可以根據策略信號計算風險報酬比
            # 暫時返回 True，實際實現需要根據具體策略
            return True

        except Exception as e:
            logger.error(f"檢查風險報酬比失敗: {e}")
            return False

    def _check_sector_exposure(self, signal: Dict) -> bool:
        """檢查行業暴露度"""
        try:
            # 這裡可以檢查行業暴露度
            # 暫時返回 True，實際實現需要根據股票分類
            return True

        except Exception as e:
            logger.error(f"檢查行業暴露度失敗: {e}")
            return False

    def _get_available_capital(self) -> float:
        """獲取可用資金"""
        try:
            # 計算已用資金
            used_capital = sum(
                pos.quantity * pos.current_price for pos in self.positions.values()
            )

            return self.total_capital - used_capital

        except Exception as e:
            logger.error(f"計算可用資金失敗: {e}")
            return 0.0

    def update_position(self, symbol: str, quantity: int, price: float, side: str):
        """更新持倉信息"""
        try:
            if symbol in self.positions:
                # 更新現有持倉
                position = self.positions[symbol]
                position.quantity += quantity
                position.current_price = price

                # 如果是平倉
                if position.quantity == 0:
                    del self.positions[symbol]
                    logger.info(f"平倉完成: {symbol}")
                else:
                    # 更新未實現損益
                    position.unrealized_pnl = self._calculate_unrealized_pnl(position)
                    logger.info(f"持倉更新: {symbol}, 數量: {position.quantity}")
            else:
                # 新建持倉
                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price,
                    entry_time=datetime.now(),
                    side=side,
                )
                self.positions[symbol] = position
                logger.info(f"新建持倉: {symbol}, 數量: {quantity}")

        except Exception as e:
            logger.error(f"更新持倉失敗: {e}")

    def _calculate_unrealized_pnl(self, position: Position) -> float:
        """計算未實現損益"""
        try:
            if position.side == "long":
                return (
                    position.current_price - position.entry_price
                ) * position.quantity
            else:  # short
                return (
                    position.entry_price - position.current_price
                ) * position.quantity

        except Exception as e:
            logger.error(f"計算未實現損益失敗: {e}")
            return 0.0

    def record_trade(self, trade_result: Dict):
        """記錄交易結果"""
        try:
            # 更新每日統計
            self.daily_trades += 1

            # 更新損益
            if trade_result.get("success"):
                pnl = trade_result.get("pnl", 0.0)
                self.daily_pnl += pnl

                # 更新總資金
                self.total_capital += pnl

                logger.info(f"交易記錄: PnL = {pnl}, 總資金 = {self.total_capital}")

        except Exception as e:
            logger.error(f"記錄交易失敗: {e}")

    def add_alert(self, alert_type: str, message: str, level: str = "warning"):
        """添加風險警報"""
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "type": alert_type,
                "message": message,
                "level": level,
            }

            self.alerts.append(alert)

            # 只保留最近100個警報
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

            logger.warning(f"風險警報: {message}")

        except Exception as e:
            logger.error(f"添加警報失敗: {e}")

    def get_risk_metrics(self) -> Dict:
        """獲取風險指標"""
        try:
            total_unrealized_pnl = sum(
                pos.unrealized_pnl for pos in self.positions.values()
            )

            total_position_value = sum(
                pos.quantity * pos.current_price for pos in self.positions.values()
            )

            return {
                "total_capital": self.total_capital,
                "available_capital": self._get_available_capital(),
                "total_position_value": total_position_value,
                "daily_pnl": self.daily_pnl,
                "total_unrealized_pnl": total_unrealized_pnl,
                "position_count": len(self.positions),
                "daily_trades": self.daily_trades,
                "risk_limits": {
                    "max_position_size": self.risk_limits.max_position_size,
                    "max_risk_per_trade": self.risk_limits.max_risk_per_trade,
                    "max_daily_loss": self.risk_limits.max_daily_loss,
                    "max_open_positions": self.risk_limits.max_open_positions,
                },
            }

        except Exception as e:
            logger.error(f"獲取風險指標失敗: {e}")
            return {}

    def update_risk_parameters(self):
        """更新風險參數"""
        try:
            # 每日重置
            self.daily_pnl = 0.0
            self.daily_trades = 0

            # 清理過期警報
            cutoff_time = datetime.now() - timedelta(days=7)
            self.alerts = [
                alert
                for alert in self.alerts
                if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
            ]

            logger.info("風險參數更新完成")

        except Exception as e:
            logger.error(f"更新風險參數失敗: {e}")

    def get_status(self) -> Dict:
        """獲取狀態"""
        return {
            "running": self.running,
            "risk_metrics": self.get_risk_metrics(),
            "alert_count": len(self.alerts),
            "timestamp": datetime.now().isoformat(),
        }
