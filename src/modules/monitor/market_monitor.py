#!/usr/bin/env python3
"""
市場監控器
負責實時監控市場狀態、價格變動和系統警報
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from loguru import logger
import pytz


@dataclass
class PriceAlert:
    """價格警報"""

    symbol: str
    target_price: float
    direction: str  # "above" or "below"
    callback: Optional[Callable] = None
    triggered: bool = False


@dataclass
class MarketStatus:
    """市場狀態"""

    is_open: bool
    current_time: datetime
    last_update: datetime
    active_symbols: List[str]
    price_changes: Dict[str, float]


class MarketMonitor:
    """市場監控器"""

    def __init__(self, config: Dict):
        """初始化市場監控器"""
        self.config = config
        self.running = False

        # 監控配置
        monitor_config = config.get("monitor", {})
        self.update_interval = monitor_config.get("update_interval", 30)  # 秒
        self.price_change_threshold = monitor_config.get(
            "price_change_threshold", 0.02
        )  # 2%

        # 監控狀態
        self.market_status = MarketStatus(
            is_open=False,
            current_time=datetime.now(),
            last_update=datetime.now(),
            active_symbols=[],
            price_changes={},
        )

        # 價格警報
        self.price_alerts: List[PriceAlert] = []

        # 價格歷史
        self.price_history: Dict[str, List[Dict]] = {}

        # 回調函數
        self.callbacks = {
            "price_change": [],
            "market_open": [],
            "market_close": [],
            "alert_triggered": [],
        }

        # 線程
        self.monitor_thread = None

        logger.info("市場監控器初始化完成")

    def start(self):
        """啟動市場監控器"""
        if self.running:
            logger.warning("市場監控器已在運行中")
            return

        self.running = True

        # 啟動監控線程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("市場監控器已啟動")

    def stop(self):
        """停止市場監控器"""
        if not self.running:
            return

        self.running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("市場監控器已停止")

    def _monitor_loop(self):
        """監控主循環"""
        while self.running:
            try:
                # 更新市場狀態
                self._update_market_status()

                # 檢查價格變動
                self._check_price_changes()

                # 檢查價格警報
                self._check_price_alerts()

                # 等待下次更新
                time.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                time.sleep(5)  # 錯誤時等待5秒

    def _update_market_status(self):
        """更新市場狀態"""
        try:
            now = datetime.now(pytz.timezone("Asia/Taipei"))

            # 檢查市場是否開盤
            is_open = self._is_market_open(now)

            # 檢查市場狀態變化
            if is_open != self.market_status.is_open:
                if is_open:
                    self._on_market_open()
                else:
                    self._on_market_close()

            # 更新狀態
            self.market_status.is_open = is_open
            self.market_status.current_time = now
            self.market_status.last_update = now

        except Exception as e:
            logger.error(f"更新市場狀態失敗: {e}")

    def _is_market_open(self, now: datetime) -> bool:
        """檢查市場是否開盤"""
        # 檢查是否為工作日
        if now.weekday() >= 5:  # 週末
            return False

        # 檢查交易時間
        market_hours = self.config.get("trading", {}).get("market_hours", {})
        start_time = market_hours.get("start", "09:00")
        end_time = market_hours.get("end", "13:30")

        current_time = now.strftime("%H:%M")
        return start_time <= current_time <= end_time

    def _on_market_open(self):
        """市場開盤回調"""
        logger.info("市場開盤")

        # 觸發回調
        for callback in self.callbacks["market_open"]:
            try:
                callback()
            except Exception as e:
                logger.error(f"市場開盤回調錯誤: {e}")

    def _on_market_close(self):
        """市場收盤回調"""
        logger.info("市場收盤")

        # 觸發回調
        for callback in self.callbacks["market_close"]:
            try:
                callback()
            except Exception as e:
                logger.error(f"市場收盤回調錯誤: {e}")

    def _check_price_changes(self):
        """檢查價格變動"""
        try:
            # 獲取當前股票池
            stock_pool = self._get_stock_pool()

            for symbol in stock_pool:
                # 獲取最新價格
                current_price = self._get_current_price(symbol)

                if current_price is None:
                    continue

                # 更新價格歷史
                self._update_price_history(symbol, current_price)

                # 檢查價格變動
                price_change = self._calculate_price_change(symbol)

                if price_change is not None:
                    self.market_status.price_changes[symbol] = price_change

                    # 檢查是否超過閾值
                    if abs(price_change) > self.price_change_threshold:
                        self._on_price_change(symbol, current_price, price_change)

        except Exception as e:
            logger.error(f"檢查價格變動失敗: {e}")

    def _get_stock_pool(self) -> List[str]:
        """獲取股票池"""
        try:
            default_pool = ["2330", "0050", "1101"]
            return self.config.get("trading", {}).get("stock_pool", default_pool)
        except Exception as e:
            logger.error(f"獲取股票池失敗: {e}")
            return []

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """獲取當前價格"""
        try:
            # 這裡應該從富邦證券 API 獲取實時價格
            # 暫時返回模擬價格
            import random

            return 100 + random.uniform(-5, 5)

        except Exception as e:
            logger.error(f"獲取價格失敗: {e}")
            return None

    def _update_price_history(self, symbol: str, price: float):
        """更新價格歷史"""
        try:
            if symbol not in self.price_history:
                self.price_history[symbol] = []

            price_record = {"timestamp": datetime.now().isoformat(), "price": price}

            self.price_history[symbol].append(price_record)

            # 只保留最近100個價格記錄
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]

        except Exception as e:
            logger.error(f"更新價格歷史失敗: {e}")

    def _calculate_price_change(self, symbol: str) -> Optional[float]:
        """計算價格變動"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < 2:
                return None

            current_price = self.price_history[symbol][-1]["price"]
            previous_price = self.price_history[symbol][-2]["price"]

            if previous_price == 0:
                return None

            return (current_price - previous_price) / previous_price

        except Exception as e:
            logger.error(f"計算價格變動失敗: {e}")
            return None

    def _on_price_change(self, symbol: str, price: float, change: float):
        """價格變動回調"""
        try:
            logger.info(f"價格變動: {symbol} = {price:.2f} ({change:.2%})")

            # 觸發回調
            for callback in self.callbacks["price_change"]:
                try:
                    callback(symbol, price, change)
                except Exception as e:
                    logger.error(f"價格變動回調錯誤: {e}")

        except Exception as e:
            logger.error(f"處理價格變動失敗: {e}")

    def _check_price_alerts(self):
        """檢查價格警報"""
        try:
            for alert in self.price_alerts:
                if alert.triggered:
                    continue

                current_price = self._get_current_price(alert.symbol)
                if current_price is None:
                    continue

                # 檢查警報條件
                if alert.direction == "above" and current_price >= alert.target_price:
                    self._trigger_price_alert(alert, current_price)
                elif alert.direction == "below" and current_price <= alert.target_price:
                    self._trigger_price_alert(alert, current_price)

        except Exception as e:
            logger.error(f"檢查價格警報失敗: {e}")

    def _trigger_price_alert(self, alert: PriceAlert, current_price: float):
        """觸發價格警報"""
        try:
            alert.triggered = True

            message = f"價格警報: {alert.symbol} 當前價格 {current_price:.2f} {'超過' if alert.direction == 'above' else '低於'} 目標價格 {alert.target_price:.2f}"
            logger.warning(message)

            # 觸發回調
            for callback in self.callbacks["alert_triggered"]:
                try:
                    callback(alert, current_price)
                except Exception as e:
                    logger.error(f"警報回調錯誤: {e}")

            # 執行自定義回調
            if alert.callback:
                try:
                    alert.callback(alert, current_price)
                except Exception as e:
                    logger.error(f"自定義警報回調錯誤: {e}")

        except Exception as e:
            logger.error(f"觸發價格警報失敗: {e}")

    def add_price_alert(
        self,
        symbol: str,
        target_price: float,
        direction: str,
        callback: Optional[Callable] = None,
    ):
        """添加價格警報"""
        try:
            alert = PriceAlert(
                symbol=symbol,
                target_price=target_price,
                direction=direction,
                callback=callback,
            )

            self.price_alerts.append(alert)
            logger.info(f"添加價格警報: {symbol} {direction} {target_price}")

        except Exception as e:
            logger.error(f"添加價格警報失敗: {e}")

    def remove_price_alert(self, symbol: str, target_price: float, direction: str):
        """移除價格警報"""
        try:
            self.price_alerts = [
                alert
                for alert in self.price_alerts
                if not (
                    alert.symbol == symbol
                    and alert.target_price == target_price
                    and alert.direction == direction
                )
            ]
            logger.info(f"移除價格警報: {symbol} {direction} {target_price}")

        except Exception as e:
            logger.error(f"移除價格警報失敗: {e}")

    def add_callback(self, event_type: str, callback: Callable):
        """添加回調函數"""
        try:
            if event_type in self.callbacks:
                self.callbacks[event_type].append(callback)
                logger.info(f"添加回調: {event_type}")
            else:
                logger.warning(f"未知事件類型: {event_type}")

        except Exception as e:
            logger.error(f"添加回調失敗: {e}")

    def remove_callback(self, event_type: str, callback: Callable):
        """移除回調函數"""
        try:
            if event_type in self.callbacks:
                if callback in self.callbacks[event_type]:
                    self.callbacks[event_type].remove(callback)
                    logger.info(f"移除回調: {event_type}")

        except Exception as e:
            logger.error(f"移除回調失敗: {e}")

    def get_market_status(self) -> Dict:
        """獲取市場狀態"""
        return {
            "is_open": self.market_status.is_open,
            "current_time": self.market_status.current_time.isoformat(),
            "last_update": self.market_status.last_update.isoformat(),
            "active_symbols": self.market_status.active_symbols,
            "price_changes": self.market_status.price_changes,
            "alert_count": len(self.price_alerts),
            "active_alerts": len([a for a in self.price_alerts if not a.triggered]),
        }

    def get_price_history(self, symbol: str, limit: int = 50) -> List[Dict]:
        """獲取價格歷史"""
        try:
            if symbol not in self.price_history:
                return []

            return self.price_history[symbol][-limit:]

        except Exception as e:
            logger.error(f"獲取價格歷史失敗: {e}")
            return []

    def get_status(self) -> Dict:
        """獲取狀態"""
        return {
            "running": self.running,
            "market_status": self.get_market_status(),
            "timestamp": datetime.now().isoformat(),
        }
