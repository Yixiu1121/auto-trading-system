#!/usr/bin/env python3
"""
自動交易系統
整合策略執行和富邦證券 API
"""

import time
import schedule
from typing import Dict, List, Optional, Any
from loguru import logger

from src.modules.trading.fubon_api_client import FubonAPIClient
from src.modules.strategies.executor import StrategyExecutor


class AutoTrader:
    """自動交易系統"""

    def __init__(self, config: Dict[str, Any], real_trading: bool = False):
        """
        初始化自動交易系統

        Args:
            config: 配置字典
            real_trading: 是否進行真實交易
        """
        self.config = config
        self.real_trading = real_trading
        self.fubon_client = None
        self.strategy_executor = None
        self.is_running = False

        # 初始化富邦證券 API 客戶端
        self._init_fubon_client()

        # 初始化策略執行器
        self._init_strategy_executor()

        logger.info(
            f"自動交易系統初始化完成（{'真實交易' if real_trading else '模擬交易'}模式）"
        )

    def _init_fubon_client(self):
        """初始化富邦證券 API 客戶端"""
        try:
            self.fubon_client = FubonAPIClient(self.config)

            # 如果是真實交易模式，嘗試登入
            if self.real_trading:
                if self.fubon_client._login_and_setup():
                    logger.info("富邦證券 API 登入成功")
                else:
                    logger.warning("富邦證券 API 登入失敗，將使用模擬模式")
                    self.real_trading = False
            else:
                logger.info("使用模擬交易模式")

        except Exception as e:
            logger.error(f"初始化富邦證券 API 客戶端失敗: {e}")
            self.fubon_client = None
            self.real_trading = False

    def _init_strategy_executor(self):
        """初始化策略執行器"""
        try:
            self.strategy_executor = StrategyExecutor(self.config)
            logger.info("策略執行器初始化成功")
        except Exception as e:
            logger.error(f"初始化策略執行器失敗: {e}")
            self.strategy_executor = None

    def calculate_next_day_signals(
        self, symbols: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        計算隔天的買賣信號

        Args:
            symbols: 股票代碼列表，如果為 None 則使用配置中的股票池

        Returns:
            List[Dict]: 信號列表
        """
        if not self.strategy_executor:
            logger.error("策略執行器未初始化")
            return []

        try:
            # 執行策略分析
            signals = self.strategy_executor.execute_strategies(symbols)

            # 過濾出有效的信號
            valid_signals = []
            for signal in signals:
                if signal.get("signal_strength", 0) > 0:
                    valid_signals.append(signal)

            logger.info(f"計算出 {len(valid_signals)} 個有效信號")
            return valid_signals

        except Exception as e:
            logger.error(f"計算隔天信號失敗: {e}")
            return []

    def execute_trade(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        執行交易

        Args:
            signal: 交易信號

        Returns:
            Dict: 交易結果
        """
        try:
            symbol = signal.get("symbol")
            action = signal.get("action")  # 'buy' 或 'sell'
            quantity = signal.get("quantity", 1000)  # 預設 1000 股
            price = signal.get("target_price")

            if not all([symbol, action, quantity]):
                logger.error(f"信號參數不完整: {signal}")
                return None

            # 檢查市場是否開放
            if not self.fubon_client.is_market_open():
                logger.warning(f"市場未開放，跳過交易: {symbol}")
                return {
                    "success": False,
                    "message": "市場未開放",
                    "symbol": symbol,
                    "action": action,
                }

            # 獲取當前價格
            current_price = self.fubon_client.get_real_time_price(symbol)
            if current_price is None:
                logger.warning(f"無法獲取 {symbol} 的當前價格")
                return None

            # 檢查交易條件
            if action == "buy":
                if current_price > price:
                    logger.info(
                        f"{symbol} 當前價格 {current_price} 高於目標價格 {price}，跳過買入"
                    )
                    return {
                        "success": False,
                        "message": "價格條件不滿足",
                        "symbol": symbol,
                        "action": action,
                        "current_price": current_price,
                        "target_price": price,
                    }
            elif action == "sell":
                if current_price < price:
                    logger.info(
                        f"{symbol} 當前價格 {current_price} 低於目標價格 {price}，跳過賣出"
                    )
                    return {
                        "success": False,
                        "message": "價格條件不滿足",
                        "symbol": symbol,
                        "action": action,
                        "current_price": current_price,
                        "target_price": price,
                    }

            # 執行交易
            if self.real_trading and self.fubon_client:
                # 真實交易
                order_type = "limit" if price else "market"
                result = self.fubon_client.place_order(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    side=action,
                    order_type=order_type,
                )

                if result and result.get("success"):
                    logger.info(f"真實交易成功: {symbol} {action} {quantity} @ {price}")
                    return {
                        "success": True,
                        "message": "真實交易成功",
                        "order_no": result.get("order_no"),
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity,
                        "price": price,
                        "current_price": current_price,
                    }
                else:
                    logger.error(f"真實交易失敗: {result}")
                    return result
            else:
                # 模擬交易
                logger.info(f"模擬交易: {symbol} {action} {quantity} @ {price}")
                return {
                    "success": True,
                    "message": "模擬交易成功",
                    "order_no": f"SIM_{int(time.time())}",
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": price,
                    "current_price": current_price,
                    "simulated": True,
                }

        except Exception as e:
            logger.error(f"執行交易失敗: {e}")
            return {
                "success": False,
                "message": str(e),
                "symbol": signal.get("symbol"),
                "action": signal.get("action"),
            }

    def calculate_order_quantity(
        self, signal: Dict[str, Any], available_capital: float = None
    ) -> int:
        """
        計算訂單數量

        Args:
            signal: 交易信號
            available_capital: 可用資金

        Returns:
            int: 訂單數量
        """
        try:
            # 從信號中獲取建議數量
            suggested_quantity = signal.get("quantity", 1000)

            if self.real_trading and self.fubon_client:
                # 真實交易：檢查帳戶餘額
                try:
                    account_info = self.fubon_client.get_account_info()
                    if account_info:
                        # 這裡需要根據實際的帳戶信息來計算可用資金
                        # 暫時使用建議數量
                        return suggested_quantity
                except Exception as e:
                    logger.warning(f"無法獲取帳戶信息，使用建議數量: {e}")
                    return suggested_quantity
            else:
                # 模擬交易：使用建議數量
                return suggested_quantity

        except Exception as e:
            logger.error(f"計算訂單數量失敗: {e}")
            return 1000  # 預設 1000 股

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        獲取當前價格

        Args:
            symbol: 股票代碼

        Returns:
            float: 當前價格
        """
        if self.fubon_client:
            return self.fubon_client.get_real_time_price(symbol)
        return None

    def check_trading_conditions(self) -> Dict[str, Any]:
        """
        檢查交易條件

        Returns:
            Dict: 交易條件狀態
        """
        if self.fubon_client:
            return self.fubon_client.check_trading_conditions()
        else:
            # 模擬交易條件檢查
            import time

            now = time.localtime()
            weekday = now.tm_wday
            hour = now.tm_hour
            minute = now.tm_min

            is_trading_day = weekday < 5
            is_trading_time = (9 <= hour < 13) or (hour == 13 and minute <= 30)

            return {
                "is_trading_day": is_trading_day,
                "is_trading_time": is_trading_time,
                "is_market_open": is_trading_day and is_trading_time,
                "current_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

    def run_daily_trading(self):
        """執行每日交易流程"""
        try:
            logger.info("開始執行每日交易流程")

            # 檢查交易條件
            conditions = self.check_trading_conditions()
            if not conditions["is_market_open"]:
                logger.info("市場未開放，跳過交易")
                return

            # 計算隔天信號
            signals = self.calculate_next_day_signals()
            if not signals:
                logger.info("沒有有效的交易信號")
                return

            # 執行交易
            for signal in signals:
                try:
                    result = self.execute_trade(signal)
                    if result:
                        logger.info(f"交易結果: {result}")
                    else:
                        logger.warning(f"交易失敗: {signal}")
                except Exception as e:
                    logger.error(f"執行交易信號失敗: {e}")

            logger.info("每日交易流程完成")

        except Exception as e:
            logger.error(f"每日交易流程失敗: {e}")

    def start(self):
        """啟動自動交易系統"""
        if self.is_running:
            logger.warning("自動交易系統已在運行中")
            return

        try:
            self.is_running = True
            logger.info("啟動自動交易系統")

            # 設置定時任務
            # 每天早上 9:00 執行交易
            schedule.every().day.at("09:00").do(self.run_daily_trading)

            # 每小時檢查一次市場狀態
            schedule.every().hour.do(self.check_trading_conditions)

            # 運行調度器
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次

        except KeyboardInterrupt:
            logger.info("收到中斷信號，停止自動交易系統")
        except Exception as e:
            logger.error(f"自動交易系統運行失敗: {e}")
        finally:
            self.stop()

    def stop(self):
        """停止自動交易系統"""
        self.is_running = False
        logger.info("自動交易系統已停止")

    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查

        Returns:
            Dict: 健康狀態
        """
        status = {
            "is_running": self.is_running,
            "real_trading": self.real_trading,
            "fubon_client_available": self.fubon_client is not None,
            "strategy_executor_available": self.strategy_executor is not None,
        }

        if self.fubon_client:
            status["fubon_health"] = self.fubon_client.health_check()

        return status
