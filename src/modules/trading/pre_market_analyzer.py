#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
開盤前分析器
負責在開盤前計算所有策略信號，設置買賣點並準備自動下單
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger
import pytz

from ..strategies.executor import StrategyExecutor
from .fubon_api_client import FubonAPIClient


class PreMarketAnalyzer:
    """開盤前分析器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化開盤前分析器

        Args:
            config: 配置字典
        """
        self.config = config
        self.strategy_executor = None
        self.fubon_client = None
        self.pre_market_signals = []
        self.price_monitors = {}
        self.monitoring_active = False
        self.monitor_thread = None

        # 初始化組件
        self._init_components()

        logger.info("開盤前分析器初始化完成")

    def _init_components(self):
        """初始化組件"""
        try:
            # 初始化策略執行器
            db_config = self.config.get("database", {})
            self.strategy_executor = StrategyExecutor(db_config)

            # 初始化富邦API客戶端
            self.fubon_client = FubonAPIClient(self.config)

            logger.info("開盤前分析器組件初始化成功")

        except Exception as e:
            logger.error(f"初始化組件失敗: {e}")
            raise

    def analyze_pre_market_signals(
        self, stock_symbols: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        分析開盤前策略信號

        Args:
            stock_symbols: 股票代碼列表，預設使用配置中的股票池

        Returns:
            List[Dict]: 預測的交易信號列表
        """
        if stock_symbols is None:
            stock_symbols = self._get_default_stock_pool()

        all_signals = []

        try:
            logger.info(f"開始分析 {len(stock_symbols)} 支股票的開盤前信號")

            for symbol in stock_symbols:
                logger.info(f"分析股票 {symbol} 的策略信號...")

                # 為每個股票執行所有策略
                symbol_signals = self.strategy_executor.execute_all_strategies(
                    symbol,
                    start_date=(datetime.now() - timedelta(days=90)).strftime(
                        "%Y-%m-%d"
                    ),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                )

                # 處理策略結果
                for strategy_name, result in symbol_signals.items():
                    if result.get("success") and result.get("signals"):
                        for signal in result["signals"]:
                            # 轉換為統一的信號格式
                            formatted_signal = {
                                "symbol": symbol,
                                "strategy": strategy_name,
                                "action": signal["signal"]["action"],
                                "signal_strength": signal["signal"]["strength"],
                                "target_price": signal["price"],
                                "current_price": None,  # 將在開盤後更新
                                "quantity": self._calculate_position_size(
                                    symbol, signal
                                ),
                                "timestamp": signal["date"],
                                "reason": signal["signal"]["reason"],
                                "ma_blue": signal.get("ma_blue"),
                                "ma_green": signal.get("ma_green"),
                                "ma_orange": signal.get("ma_orange"),
                                "status": "pending",  # pending, active, executed, cancelled
                                "created_at": datetime.now(),
                            }
                            all_signals.append(formatted_signal)

                logger.info(
                    f"股票 {symbol} 分析完成，產生 {len([s for s in all_signals if s['symbol'] == symbol])} 個信號"
                )

            # 過濾和排序信號
            filtered_signals = self._filter_and_rank_signals(all_signals)

            # 保存信號
            self.pre_market_signals = filtered_signals

            logger.info(
                f"開盤前信號分析完成，總共產生 {len(filtered_signals)} 個有效信號"
            )

            # 如果配置允許，立即執行開盤前下單
            if self.config.get("trading", {}).get("enable_pre_market_orders", True):
                self._execute_pre_market_orders(filtered_signals)

            return filtered_signals

        except Exception as e:
            logger.error(f"開盤前信號分析失敗: {e}")
            return []

    def _filter_and_rank_signals(
        self, signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        過濾和排序信號

        Args:
            signals: 原始信號列表

        Returns:
            List[Dict]: 過濾和排序後的信號列表
        """
        try:
            # 過濾條件
            min_signal_strength = self.config.get("trading", {}).get(
                "min_signal_strength", 0.6
            )
            max_signals_per_stock = self.config.get("trading", {}).get(
                "max_signals_per_stock", 2
            )

            # 過濾弱信號
            filtered_signals = [
                signal
                for signal in signals
                if abs(signal["signal_strength"]) >= min_signal_strength
            ]

            # 按股票分組，每支股票只保留最強的幾個信號
            stock_signals = {}
            for signal in filtered_signals:
                symbol = signal["symbol"]
                if symbol not in stock_signals:
                    stock_signals[symbol] = []
                stock_signals[symbol].append(signal)

            # 每支股票按信號強度排序並限制數量
            final_signals = []
            for symbol, symbol_signal_list in stock_signals.items():
                # 按信號強度排序
                symbol_signal_list.sort(
                    key=lambda x: abs(x["signal_strength"]), reverse=True
                )
                # 限制每支股票的信號數量
                final_signals.extend(symbol_signal_list[:max_signals_per_stock])

            # 按總體信號強度排序
            final_signals.sort(key=lambda x: abs(x["signal_strength"]), reverse=True)

            logger.info(f"信號過濾完成：{len(signals)} -> {len(final_signals)}")
            return final_signals

        except Exception as e:
            logger.error(f"信號過濾失敗: {e}")
            return signals

    def _calculate_position_size(self, symbol: str, signal: Dict[str, Any]) -> int:
        """
        計算倉位大小

        Args:
            symbol: 股票代碼
            signal: 信號信息

        Returns:
            int: 建議的股數
        """
        try:
            # 基礎倉位大小
            default_quantity = self.config.get("trading", {}).get(
                "default_quantity", 1000
            )

            # 根據信號強度調整
            signal_strength = abs(signal["signal"]["strength"])
            strength_multiplier = min(signal_strength / 0.5, 2.0)  # 最大2倍

            # 根據風險管理調整
            max_position_size = self.config.get("risk_management", {}).get(
                "max_position_size", 10000
            )

            calculated_quantity = int(default_quantity * strength_multiplier)
            final_quantity = min(calculated_quantity, max_position_size)

            # 確保是1000的倍數（台股交易單位）
            final_quantity = (final_quantity // 1000) * 1000

            return max(final_quantity, 1000)  # 最少1000股

        except Exception as e:
            logger.error(f"計算倉位大小失敗: {e}")
            return 1000

    def start_price_monitoring(self):
        """開始價格監控"""
        if self.monitoring_active:
            logger.warning("價格監控已在運行中")
            return

        if not self.pre_market_signals:
            logger.warning("沒有需要監控的信號")
            return

        try:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._price_monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            logger.info(f"開始監控 {len(self.pre_market_signals)} 個信號的價格條件")

        except Exception as e:
            logger.error(f"啟動價格監控失敗: {e}")
            self.monitoring_active = False

    def stop_price_monitoring(self):
        """停止價格監控"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("價格監控已停止")

    def _price_monitoring_loop(self):
        """價格監控主循環"""
        logger.info("價格監控循環開始")

        while self.monitoring_active:
            try:
                # 檢查是否在交易時間
                if not self._is_trading_time():
                    time.sleep(60)  # 非交易時間，每分鐘檢查一次
                    continue

                # 檢查每個待執行的信號
                for signal in self.pre_market_signals:
                    if signal["status"] != "pending":
                        continue

                    symbol = signal["symbol"]

                    # 獲取當前價格
                    current_price = self.fubon_client.get_real_time_price(symbol)
                    if current_price is None:
                        continue

                    signal["current_price"] = current_price

                    # 檢查是否達到執行條件
                    if self._check_execution_conditions(signal, current_price):
                        logger.info(
                            f"信號達到執行條件: {signal['symbol']} {signal['action']} @ {current_price}"
                        )

                        # 執行交易
                        self._execute_signal(signal)

                # 每30秒檢查一次價格
                time.sleep(30)

            except Exception as e:
                logger.error(f"價格監控循環錯誤: {e}")
                time.sleep(60)

        logger.info("價格監控循環結束")

    def _check_execution_conditions(
        self, signal: Dict[str, Any], current_price: float
    ) -> bool:
        """
        檢查信號執行條件

        Args:
            signal: 交易信號
            current_price: 當前價格

        Returns:
            bool: 是否應該執行
        """
        try:
            target_price = signal["target_price"]
            action = signal["action"]

            # 價格容忍度
            price_tolerance = self.config.get("trading", {}).get(
                "price_tolerance", 0.01
            )  # 1%

            if action == "buy":
                # 買入：當前價格低於或接近目標價格
                max_buy_price = target_price * (1 + price_tolerance)
                return current_price <= max_buy_price

            elif action == "sell":
                # 賣出：當前價格高於或接近目標價格
                min_sell_price = target_price * (1 - price_tolerance)
                return current_price >= min_sell_price

            return False

        except Exception as e:
            logger.error(f"檢查執行條件失敗: {e}")
            return False

    def _execute_signal(self, signal: Dict[str, Any]) -> bool:
        """
        執行交易信號

        Args:
            signal: 交易信號

        Returns:
            bool: 執行是否成功
        """
        try:
            # 更新信號狀態
            signal["status"] = "executing"
            signal["execution_time"] = datetime.now()

            # 檢查風險限制
            if not self._check_risk_limits(signal):
                logger.warning(f"信號被風險管理阻止: {signal}")
                signal["status"] = "blocked"
                return False

            # 準備下單參數
            order_params = {
                "symbol": signal["symbol"],
                "action": signal["action"],
                "quantity": signal["quantity"],
                "price": signal["current_price"],
                "order_type": "limit",  # 限價單
            }

            # 實際下單
            if self.config.get("trading", {}).get("real_trading", False):
                # 真實交易
                result = self.fubon_client.place_order(**order_params)
            else:
                # 模擬交易
                result = self._simulate_order(order_params)

            if result and result.get("success"):
                signal["status"] = "executed"
                signal["order_id"] = result.get("order_id")
                signal["executed_price"] = signal["current_price"]
                signal["executed_quantity"] = signal["quantity"]

                logger.info(
                    f"交易執行成功: {signal['symbol']} {signal['action']} {signal['quantity']}股 @ {signal['current_price']}"
                )
                return True
            else:
                signal["status"] = "failed"
                logger.error(f"交易執行失敗: {result}")
                return False

        except Exception as e:
            logger.error(f"執行交易信號失敗: {e}")
            signal["status"] = "error"
            return False

    def _simulate_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """模擬下單"""
        return {
            "success": True,
            "order_id": f"SIM_{int(time.time())}",
            "message": "模擬交易執行成功",
        }

    def _check_risk_limits(self, signal: Dict[str, Any]) -> bool:
        """檢查風險限制"""
        try:
            # 檢查單筆訂單金額限制
            max_order_amount = self.config.get("risk_management", {}).get(
                "max_position_size", 100000
            )
            order_amount = signal["quantity"] * signal["current_price"]

            if order_amount > max_order_amount:
                logger.warning(f"訂單金額超過限制: {order_amount} > {max_order_amount}")
                return False

            # 檢查每日交易次數限制
            max_daily_trades = self.config.get("trading", {}).get(
                "max_orders_per_day", 10
            )
            today_trades = len(
                [
                    s
                    for s in self.pre_market_signals
                    if s.get("execution_time")
                    and s["execution_time"].date() == datetime.now().date()
                    and s["status"] == "executed"
                ]
            )

            if today_trades >= max_daily_trades:
                logger.warning(
                    f"每日交易次數達到限制: {today_trades} >= {max_daily_trades}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"檢查風險限制失敗: {e}")
            return False

    def _is_trading_time(self) -> bool:
        """檢查是否為交易時間"""
        taiwan_tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(taiwan_tz)

        # 週一到週五，9:00-13:30
        weekday = now.weekday()
        if weekday >= 5:  # 週末
            return False

        time_str = now.strftime("%H:%M")
        return "09:00" <= time_str <= "13:30"

    def _get_default_stock_pool(self) -> List[str]:
        """獲取預設股票池"""
        return self.config.get("trading", {}).get(
            "stock_pool", ["2330", "0050", "1101"]
        )

    def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        return {
            "monitoring_active": self.monitoring_active,
            "total_signals": len(self.pre_market_signals),
            "pending_signals": len(
                [s for s in self.pre_market_signals if s["status"] == "pending"]
            ),
            "executed_signals": len(
                [s for s in self.pre_market_signals if s["status"] == "executed"]
            ),
            "failed_signals": len(
                [s for s in self.pre_market_signals if s["status"] == "failed"]
            ),
            "current_time": datetime.now().isoformat(),
            "is_trading_time": self._is_trading_time(),
        }

    def _execute_pre_market_orders(self, signals: List[Dict[str, Any]]):
        """
        執行開盤前下單

        Args:
            signals: 交易信號列表
        """
        if not signals:
            logger.info("沒有信號需要執行開盤前下單")
            return

        try:
            logger.info(f"開始執行 {len(signals)} 個開盤前下單...")

            executed_count = 0
            failed_count = 0

            for signal in signals:
                try:
                    # 檢查風險限制
                    if not self._check_pre_market_risk_limits(signal):
                        logger.warning(f"開盤前下單被風險管理阻止: {signal['symbol']}")
                        signal["status"] = "blocked"
                        continue

                    # 計算下單價格（開盤前可能需要調整價格策略）
                    order_price = self._calculate_pre_market_price(signal)

                    # 執行開盤前下單
                    result = self.fubon_client.place_pre_market_order(
                        symbol=signal["symbol"],
                        side=signal["action"],
                        quantity=signal["quantity"],
                        price=order_price,
                        order_type="limit",  # 開盤前建議使用限價單
                    )

                    if result and result.get("success"):
                        # 更新信號狀態
                        signal["status"] = "pre_market_ordered"
                        signal["order_id"] = result.get("order_id")
                        signal["order_price"] = order_price
                        signal["order_time"] = datetime.now()

                        executed_count += 1
                        logger.info(
                            f"✅ 開盤前下單成功: {signal['symbol']} {signal['action']} "
                            f"{signal['quantity']}股 @ {order_price:.2f}"
                        )
                    else:
                        signal["status"] = "pre_market_failed"
                        signal["error"] = (
                            result.get("error", "未知錯誤") if result else "API調用失敗"
                        )
                        failed_count += 1
                        logger.error(
                            f"❌ 開盤前下單失敗: {signal['symbol']} - {signal.get('error')}"
                        )

                except Exception as e:
                    signal["status"] = "pre_market_error"
                    signal["error"] = str(e)
                    failed_count += 1
                    logger.error(f"❌ 開盤前下單異常: {signal['symbol']} - {e}")

            # 總結報告
            logger.info(
                f"🎯 開盤前下單完成 - 成功: {executed_count}, 失敗: {failed_count}"
            )

            if executed_count > 0:
                self._display_pre_market_orders_summary(signals)

        except Exception as e:
            logger.error(f"執行開盤前下單失敗: {e}")

    def _check_pre_market_risk_limits(self, signal: Dict[str, Any]) -> bool:
        """
        檢查開盤前下單風險限制

        Args:
            signal: 交易信號

        Returns:
            bool: 是否通過風險檢查
        """
        try:
            # 檢查是否為開盤前時間
            if not self.fubon_client.is_pre_market_time():
                logger.warning("非開盤前時間，無法進行開盤前下單")
                return False

            # 檢查單筆訂單金額限制
            max_order_amount = self.config.get("risk_management", {}).get(
                "max_position_size", 100000
            )
            order_amount = signal["quantity"] * signal["target_price"]

            if order_amount > max_order_amount:
                logger.warning(
                    f"開盤前訂單金額超過限制: {order_amount} > {max_order_amount}"
                )
                return False

            # 檢查開盤前交易次數限制
            max_pre_market_orders = self.config.get("trading", {}).get(
                "max_pre_market_orders_per_day", 5
            )
            today_pre_market_orders = len(
                [
                    s
                    for s in self.pre_market_signals
                    if s.get("order_time")
                    and s["order_time"].date() == datetime.now().date()
                    and s["status"] == "pre_market_ordered"
                ]
            )

            if today_pre_market_orders >= max_pre_market_orders:
                logger.warning(
                    f"開盤前交易次數達到限制: {today_pre_market_orders} >= {max_pre_market_orders}"
                )
                return False

            # 檢查信號強度是否足夠（開盤前下單要求更高的信號強度）
            min_pre_market_strength = self.config.get("trading", {}).get(
                "min_pre_market_signal_strength", 0.8
            )
            if abs(signal["signal_strength"]) < min_pre_market_strength:
                logger.warning(
                    f"信號強度不足以進行開盤前下單: {signal['signal_strength']} < {min_pre_market_strength}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"檢查開盤前風險限制失敗: {e}")
            return False

    def _calculate_pre_market_price(self, signal: Dict[str, Any]) -> float:
        """
        計算開盤前下單價格

        Args:
            signal: 交易信號

        Returns:
            float: 建議的下單價格
        """
        try:
            target_price = signal["target_price"]
            action = signal["action"]

            # 開盤前價格調整策略
            price_adjustment = self.config.get("trading", {}).get(
                "pre_market_price_adjustment", 0.005  # 0.5%
            )

            if action == "buy":
                # 買入時，略微提高價格以增加成交機會
                adjusted_price = target_price * (1 + price_adjustment)
            else:  # sell
                # 賣出時，略微降低價格以增加成交機會
                adjusted_price = target_price * (1 - price_adjustment)

            # 四捨五入到合理的價格精度
            adjusted_price = round(adjusted_price, 2)

            logger.debug(
                f"價格調整: {target_price:.2f} -> {adjusted_price:.2f} ({action})"
            )
            return adjusted_price

        except Exception as e:
            logger.error(f"計算開盤前價格失敗: {e}")
            return signal["target_price"]

    def _display_pre_market_orders_summary(self, signals: List[Dict[str, Any]]):
        """
        顯示開盤前下單摘要

        Args:
            signals: 信號列表
        """
        try:
            ordered_signals = [
                s for s in signals if s["status"] == "pre_market_ordered"
            ]

            if not ordered_signals:
                return

            logger.info("📋 開盤前下單摘要:")
            logger.info("-" * 60)

            total_amount = 0
            for signal in ordered_signals:
                amount = signal["quantity"] * signal["order_price"]
                total_amount += amount

                logger.info(
                    f"🏷️  {signal['symbol']} | {signal['action'].upper()} | "
                    f"{signal['quantity']}股 @ {signal['order_price']:.2f} | "
                    f"金額: {amount:,.0f} | 訂單號: {signal.get('order_id', 'N/A')}"
                )

            logger.info("-" * 60)
            logger.info(f"📊 總下單金額: {total_amount:,.0f}")
            logger.info(f"📈 等待開盤執行...")

        except Exception as e:
            logger.error(f"顯示開盤前下單摘要失敗: {e}")

    def get_pre_market_orders_status(self) -> Dict[str, Any]:
        """
        獲取開盤前下單狀態

        Returns:
            Dict: 下單狀態摘要
        """
        try:
            ordered_signals = [
                s
                for s in self.pre_market_signals
                if s["status"] == "pre_market_ordered"
            ]
            failed_signals = [
                s
                for s in self.pre_market_signals
                if s["status"] in ["pre_market_failed", "pre_market_error"]
            ]

            total_amount = sum(
                s["quantity"] * s.get("order_price", s["target_price"])
                for s in ordered_signals
            )

            return {
                "total_signals": len(self.pre_market_signals),
                "ordered_count": len(ordered_signals),
                "failed_count": len(failed_signals),
                "total_order_amount": total_amount,
                "orders": ordered_signals,
                "is_pre_market_time": (
                    self.fubon_client.is_pre_market_time()
                    if self.fubon_client
                    else False
                ),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"獲取開盤前下單狀態失敗: {e}")
            return {
                "total_signals": 0,
                "ordered_count": 0,
                "failed_count": 0,
                "total_order_amount": 0,
                "orders": [],
                "is_pre_market_time": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def get_pre_market_signals(self) -> List[Dict[str, Any]]:
        """獲取開盤前信號列表"""
        return self.pre_market_signals.copy()
