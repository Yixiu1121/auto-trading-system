#!/usr/bin/env python3
"""
富邦證券 API 客戶端
基於 fubon_neo SDK 實現
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger
import pytz

try:
    from fubon_neo.sdk import FubonSDK, Order
    from fubon_neo.constant import (
        TimeInForce,
        OrderType,
        PriceType,
        MarketType,
        BSAction,
    )

    SDK_AVAILABLE = True
except ImportError:
    logger.warning("fubon_neo SDK 不可用，將使用模擬模式")
    SDK_AVAILABLE = False


class FubonAPIClient:
    """富邦證券 API 客戶端"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化富邦證券 API 客戶端

        Args:
            config: 配置字典，包含登入憑證等信息
        """
        self.config = config
        self.sdk = None
        self.accounts = None
        self.is_connected = False
        self.is_logged_in = False

        # 從配置中獲取富邦證券設置
        self.fubon_config = config.get("fubon", {})
        self.account_id = self.fubon_config.get("id")
        self.password = self.fubon_config.get("pwd")
        self.cert_filepath = self.fubon_config.get("cert_filepath")
        self.cert_password = self.fubon_config.get("certpwd")
        self.target_account = self.fubon_config.get("target_account")

        # 延遲初始化 SDK - 只有在實際需要時才初始化
        # 這樣其他模組不會因為富邦SDK連接失敗而受影響
        self.sdk_initialized = False
        logger.info("富邦證券 API 客戶端初始化完成（延遲初始化模式）")

    def _init_sdk(self):
        """初始化 SDK，失敗時優雅降級"""
        # 嘗試不同的初始化方式
        init_methods = [
            {
                "name": "v2.2.1+ 測試環境",
                "func": lambda: FubonSDK(
                    30, 2, url="wss://neoapitest.fbs.com.tw/TASP/XCPXWS"
                ),
            },
            {
                "name": "v2.2.0 以前方式",
                "func": lambda: FubonSDK(url="wss://neoapitest.fbs.com.tw/TASP/XCPXWS"),
            },
            {"name": "預設環境", "func": lambda: FubonSDK()},
        ]

        for method in init_methods:
            try:
                logger.info(f"嘗試 SDK 初始化: {method['name']}")
                self.sdk = method["func"]()
                logger.info(f"富邦證券 SDK 初始化成功 ({method['name']})")
                return  # 成功則退出
            except Exception as e:
                logger.warning(f"SDK 初始化失敗 ({method['name']}): {e}")
                continue

        # 所有方法都失敗
        logger.error("所有 SDK 初始化方法都失敗，將使用模擬模式")
        self.sdk = None

    def _ensure_sdk_initialized(self) -> bool:
        """
        確保SDK已初始化，只在需要時才初始化

        Returns:
            bool: SDK是否可用
        """
        if self.sdk_initialized:
            return self.sdk is not None

        if not SDK_AVAILABLE:
            logger.warning("富邦SDK不可用，使用模擬模式")
            self.sdk_initialized = True
            return False

        try:
            logger.info("首次使用富邦功能，正在初始化SDK...")
            self._init_sdk()
            self.sdk_initialized = True

            if self.sdk is None:
                logger.warning("SDK初始化失敗，將使用模擬模式")
                return False
            else:
                logger.info("富邦SDK初始化成功")
                return True

        except Exception as e:
            logger.error(f"SDK初始化異常: {e}")
            logger.warning("SDK初始化失敗，將使用模擬模式")
            self.sdk = None
            self.sdk_initialized = True
            return False

    def _login_and_setup(self) -> bool:
        """
        登入並設置回調函數

        Returns:
            bool: 登入是否成功
        """
        # 確保SDK已初始化
        if not self._ensure_sdk_initialized():
            logger.warning("SDK 不可用，跳過登入")
            return False

        try:
            # 登入
            logger.info("正在登入富邦證券...")
            self.accounts = self.sdk.login(
                self.account_id, self.password, self.cert_filepath, self.cert_password
            )

            if (
                self.accounts
                and hasattr(self.accounts, "is_success")
                and self.accounts.is_success
            ):
                self.is_logged_in = True
                logger.info("富邦證券登入成功")

                # 設置回調函數
                self._setup_callbacks()

                # 初始化行情元件
                self.sdk.init_realtime()
                self.is_connected = True
                logger.info("行情元件初始化成功")

                return True
            else:
                logger.error(f"登入失敗：{self.accounts}")
                return False

        except Exception as e:
            logger.error(f"登入過程發生錯誤: {e}")
            return False

    def _setup_callbacks(self):
        """設置回調函數"""
        if not self.sdk:
            return

        def on_order(err, content):
            logger.info(f"下單回報 - 錯誤: {err}, 內容: {content}")

        def on_order_changed(err, content):
            logger.info(f"改單回報 - 錯誤: {err}, 內容: {content}")

        def on_filled(err, content):
            logger.info(f"成交回報 - 錯誤: {err}, 內容: {content}")

        def on_event(err, content):
            logger.info(f"事件回報 - 錯誤: {err}, 內容: {content}")

        # 設置回調
        self.sdk.set_on_order(on_order)
        self.sdk.set_on_order_changed(on_order_changed)
        self.sdk.set_on_filled(on_filled)
        self.sdk.set_on_event(on_event)

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        獲取帳戶信息

        Returns:
            Dict: 帳戶信息
        """
        if not self.is_logged_in or not self.accounts:
            logger.warning("未登入，無法獲取帳戶信息")
            return None

        try:
            account = self.accounts.data[0]
            return {
                "account_id": account.account,
                "account_name": account.name,
                "branch_id": account.branch_no,
                "account_type": account.account_type,
            }
        except Exception as e:
            logger.error(f"獲取帳戶信息失敗: {e}")
            return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        獲取持倉信息

        Returns:
            List[Dict]: 持倉列表
        """
        if not self.is_logged_in:
            logger.warning("未登入，無法獲取持倉信息")
            return []

        try:
            result = self.sdk.accounting.inventories(self.accounts.data[0])
            if result.is_success:
                positions = []
                for inv in result.data:
                    positions.append(
                        {
                            "symbol": inv.stock_no,
                            "quantity": inv.today_qty,
                            "tradable_qty": inv.tradable_qty,
                            "lastday_qty": inv.lastday_qty,
                            "buy_qty": inv.buy_qty,
                            "sell_qty": inv.sell_qty,
                            "buy_value": inv.buy_value,
                            "sell_value": inv.sell_value,
                            "order_type": str(inv.order_type),
                        }
                    )
                return positions
            else:
                logger.error(f"獲取持倉失敗: {result.message}")
                return []
        except Exception as e:
            logger.error(f"獲取持倉信息失敗: {e}")
            return []

    def get_orders(self) -> List[Dict[str, Any]]:
        """
        獲取委託單信息

        Returns:
            List[Dict]: 委託單列表
        """
        if not self.is_logged_in:
            logger.warning("未登入，無法獲取委託單信息")
            return []

        try:
            result = self.sdk.stock.get_order_results(self.accounts.data[0])
            if result.is_success:
                orders = []
                for order in result.data:
                    orders.append(
                        {
                            "order_no": order.order_no,
                            "symbol": order.stock_no,
                            "buy_sell": str(order.buy_sell),
                            "quantity": order.quantity,
                            "price": order.price,
                            "status": order.status,
                            "filled_quantity": order.filled_qty,
                            "filled_money": order.filled_money,
                            "price_type": str(order.price_type),
                            "market_type": str(order.market_type),
                            "time_in_force": str(order.time_in_force),
                            "order_type": str(order.order_type),
                            "seq_no": order.seq_no,
                            "date": order.date,
                            "last_time": order.last_time,
                        }
                    )
                return orders
            else:
                logger.error(f"獲取委託單失敗: {result.message}")
                return []
        except Exception as e:
            logger.error(f"獲取委託單信息失敗: {e}")
            return []

    def place_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        side: str = "buy",
        order_type: str = "limit",
    ) -> Optional[Dict[str, Any]]:
        """
        下單

        Args:
            symbol: 股票代碼
            quantity: 數量
            price: 價格（市價單可為 None）
            side: 買賣方向 ('buy' 或 'sell')
            order_type: 訂單類型 ('limit', 'market', 'reference')

        Returns:
            Dict: 下單結果
        """
        # 確保SDK已初始化並登入
        if not self._ensure_sdk_initialized():
            logger.warning("SDK不可用，無法下單")
            return None

        if not self.is_logged_in:
            # 嘗試登入
            if not self._login_and_setup():
                logger.warning("登入失敗，無法下單")
                return None

        try:
            # 轉換參數
            buy_sell = BSAction.Buy if side.lower() == "buy" else BSAction.Sell

            if order_type == "limit":
                price_type = PriceType.Limit
            elif order_type == "market":
                price_type = PriceType.Market
            else:
                price_type = PriceType.Reference

            # 創建訂單
            order = Order(
                buy_sell=buy_sell,
                symbol=symbol,
                price=price,
                quantity=quantity,
                market_type=MarketType.Common,
                price_type=price_type,
                time_in_force=TimeInForce.ROD,
                order_type=OrderType.Stock,
                user_def=None,
            )

            # 下單
            response = self.sdk.stock.place_order(self.accounts.data[0], order)

            if response.is_success:
                logger.info(f"下單成功: {symbol} {side} {quantity} @ {price}")
                return {
                    "success": True,
                    "order_no": response.data.order_no,
                    "message": "下單成功",
                }
            else:
                logger.error(f"下單失敗: {response.message}")
                return {"success": False, "message": response.message}

        except Exception as e:
            logger.error(f"下單過程發生錯誤: {e}")
            return {"success": False, "message": str(e)}

    def cancel_order(self, order_no: str) -> Optional[Dict[str, Any]]:
        """
        取消委託單

        Args:
            order_no: 委託單號

        Returns:
            Dict: 取消結果
        """
        if not self.is_logged_in:
            logger.warning("未登入，無法取消委託單")
            return None

        try:
            # 獲取委託單
            orders = self.sdk.stock.get_order_results(self.accounts.data[0])
            target_order = None

            for order in orders.data:
                if order.order_no == order_no:
                    target_order = order
                    break

            if target_order is None:
                logger.error(f"找不到委託單: {order_no}")
                return {"success": False, "message": f"找不到委託單: {order_no}"}

            # 取消委託單
            response = self.sdk.stock.cancel_order(self.accounts.data[0], target_order)

            if response.is_success:
                logger.info(f"取消委託單成功: {order_no}")
                return {"success": True, "message": "取消委託單成功"}
            else:
                logger.error(f"取消委託單失敗: {response.message}")
                return {"success": False, "message": response.message}

        except Exception as e:
            logger.error(f"取消委託單過程發生錯誤: {e}")
            return {"success": False, "message": str(e)}

    def get_order_status(self, order_no: str) -> Optional[Dict[str, Any]]:
        """
        獲取委託單狀態

        Args:
            order_no: 委託單號

        Returns:
            Dict: 委託單狀態
        """
        if not self.is_logged_in:
            logger.warning("未登入，無法獲取委託單狀態")
            return None

        try:
            orders = self.sdk.stock.get_order_results(self.accounts.data[0])

            for order in orders.data:
                if order.order_no == order_no:
                    return {
                        "order_no": order.order_no,
                        "symbol": order.symbol,
                        "buy_sell": order.buy_sell,
                        "quantity": order.quantity,
                        "price": order.price,
                        "status": order.status,
                        "filled_quantity": order.filled_quantity,
                        "filled_price": order.filled_price,
                        "order_time": order.order_time,
                    }

            logger.warning(f"找不到委託單: {order_no}")
            return None

        except Exception as e:
            logger.error(f"獲取委託單狀態失敗: {e}")
            return None

    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        獲取市場數據

        Args:
            symbol: 股票代碼

        Returns:
            Dict: 市場數據
        """
        if not self.is_connected:
            logger.warning("未連接行情，無法獲取市場數據")
            return None

        try:
            # 使用 REST API 獲取即時報價
            rest_stock = self.sdk.marketdata.rest_client.stock
            result = rest_stock.intraday.quote(symbol=symbol)

            if result and "data" in result:
                data = result["data"]
                return {
                    "symbol": symbol,
                    "price": data.get("price"),
                    "change": data.get("change"),
                    "change_percent": data.get("change_percent"),
                    "volume": data.get("volume"),
                    "high": data.get("high"),
                    "low": data.get("low"),
                    "open": data.get("open"),
                    "prev_close": data.get("prev_close"),
                }
            else:
                logger.warning(f"無法獲取 {symbol} 的市場數據")
                return None

        except Exception as e:
            logger.error(f"獲取市場數據失敗: {e}")
            return None

    def get_historical_data(
        self, symbol: str, from_date: str, to_date: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        獲取歷史數據

        Args:
            symbol: 股票代碼
            from_date: 開始日期 (YYYY-MM-DD)
            to_date: 結束日期 (YYYY-MM-DD)

        Returns:
            List[Dict]: 歷史數據列表
        """
        if not self.is_connected:
            logger.warning("未連接行情，無法獲取歷史數據")
            return None

        try:
            rest_stock = self.sdk.marketdata.rest_client.stock
            result = rest_stock.historical.candles(
                symbol=symbol, from_date=from_date, to_date=to_date
            )

            if result and "data" in result:
                return result["data"]
            else:
                logger.warning(f"無法獲取 {symbol} 的歷史數據")
                return None

        except Exception as e:
            logger.error(f"獲取歷史數據失敗: {e}")
            return None

    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        獲取實時價格

        Args:
            symbol: 股票代碼

        Returns:
            float: 實時價格
        """
        market_data = self.get_market_data(symbol)
        if market_data and "price" in market_data:
            return market_data["price"]
        return None

    def check_trading_conditions(self) -> Dict[str, Any]:
        """
        檢查交易條件

        Returns:
            Dict: 交易條件狀態
        """
        # 檢查是否為交易時間
        now = time.localtime()
        weekday = now.tm_wday
        hour = now.tm_hour
        minute = now.tm_min

        # 週一到週五，9:00-13:30
        is_trading_day = weekday < 5
        is_trading_time = (9 <= hour < 13) or (hour == 13 and minute <= 30)

        return {
            "is_trading_day": is_trading_day,
            "is_trading_time": is_trading_time,
            "is_market_open": is_trading_day and is_trading_time,
            "current_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def is_market_open(self) -> bool:
        """
        檢查市場是否開放

        Returns:
            bool: 市場是否開放
        """
        conditions = self.check_trading_conditions()
        return conditions["is_market_open"]

    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查

        Returns:
            Dict: 健康狀態
        """
        status = {
            "sdk_available": SDK_AVAILABLE,
            "is_connected": self.is_connected,
            "is_logged_in": self.is_logged_in,
            "market_open": self.is_market_open(),
        }

        if self.is_logged_in:
            try:
                account_info = self.get_account_info()
                status["account_info"] = account_info
            except Exception as e:
                status["account_error"] = str(e)

        return status

    def place_pre_market_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        side: str = "buy",
        order_type: str = "limit",
    ) -> Optional[Dict[str, Any]]:
        """
        開盤前下單

        Args:
            symbol: 股票代碼
            quantity: 數量
            price: 價格（市價單可為 None）
            side: 買賣方向 ('buy' 或 'sell')
            order_type: 訂單類型 ('limit', 'market', 'reference')

        Returns:
            Dict: 下單結果
        """
        if not self.is_logged_in:
            logger.warning("未登入，無法下單")
            return None

        try:
            # 檢查是否為開盤前時間
            if not self.is_pre_market_time():
                logger.warning("非開盤前時間，建議使用一般下單")

            # 轉換參數
            buy_sell = BSAction.Buy if side.lower() == "buy" else BSAction.Sell

            if order_type == "limit":
                price_type = PriceType.Limit
            elif order_type == "market":
                price_type = PriceType.Market
            else:
                price_type = PriceType.Reference

            # 創建開盤前訂單
            order = Order(
                buy_sell=buy_sell,
                symbol=symbol,
                price=price,
                quantity=quantity,
                market_type=MarketType.Common,
                price_type=price_type,
                time_in_force=TimeInForce.ROD,  # 當日有效
                order_type=OrderType.Stock,
                user_def=None,
            )

            # 下單 - 開盤前委託
            logger.info(f"開盤前下單: {symbol} {side} {quantity}股 @ {price}")

            if SDK_AVAILABLE and self.accounts and len(self.accounts.data) > 0:
                response = self.sdk.stock.place_order(self.accounts.data[0], order)

                if response.is_success:
                    result = {
                        "success": True,
                        "order_id": response.data.order_no if response.data else None,
                        "message": "開盤前委託成功",
                        "symbol": symbol,
                        "side": side,
                        "quantity": quantity,
                        "price": price,
                        "order_type": order_type,
                        "timestamp": datetime.now().isoformat(),
                    }
                    logger.info(f"開盤前下單成功: {result}")
                    return result
                else:
                    error_msg = response.message if response else "未知錯誤"
                    logger.error(f"開盤前下單失敗: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "symbol": symbol,
                        "side": side,
                        "quantity": quantity,
                        "price": price,
                    }
            else:
                # 模擬模式
                result = {
                    "success": True,
                    "order_id": f"PRE_MARKET_{int(time.time())}",
                    "message": "開盤前委託成功（模擬）",
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "order_type": order_type,
                    "timestamp": datetime.now().isoformat(),
                }
                logger.info(f"開盤前下單成功（模擬）: {result}")
                return result

        except Exception as e:
            logger.error(f"開盤前下單失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
            }

    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        獲取即時股價

        Args:
            symbol: 股票代碼

        Returns:
            float: 當前股價，如果失敗則返回None
        """
        # 嘗試確保SDK已初始化（但不要求登入，因為即時價格可能不需要登入）
        if not self._ensure_sdk_initialized():
            # SDK不可用，使用模擬模式
            import random

            mock_price = 100 + random.uniform(-10, 10)
            logger.debug(f"模擬模式：{symbol} 即時價格 = {mock_price:.2f}")
            return mock_price

        try:
            if SDK_AVAILABLE and self.sdk:
                # 使用 REST API 獲取即時報價
                rest_stock = self.sdk.marketdata.rest_client.stock
                result = rest_stock.intraday.quote(symbol=symbol)

                if result and "data" in result and result["data"]:
                    data = result["data"]
                    # 獲取當前價格（可能是成交價、委買價或委賣價）
                    current_price = (
                        data.get("price") or data.get("close") or data.get("last")
                    )

                    if current_price is not None:
                        logger.debug(f"獲取 {symbol} 即時價格: {current_price}")
                        return float(current_price)
                    else:
                        logger.warning(f"無法從API回應中提取 {symbol} 的價格")
                        return None
                else:
                    logger.warning(f"API返回空數據: {symbol}")
                    return None
            else:
                # 模擬模式
                import random

                mock_price = 100 + random.uniform(-10, 10)
                logger.debug(f"模擬模式：{symbol} 即時價格 = {mock_price:.2f}")
                return mock_price

        except Exception as e:
            logger.error(f"獲取即時價格失敗 {symbol}: {e}")
            return None

    def is_pre_market_time(self) -> bool:
        """
        檢查是否為開盤前時間（可以進行預單）

        Returns:
            bool: 是否為開盤前時間
        """
        taiwan_tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(taiwan_tz)

        # 週一到週五
        weekday = now.weekday()
        if weekday >= 5:  # 週末
            return False

        time_str = now.strftime("%H:%M")
        # 開盤前時間：07:00-08:59（可以進行預單）
        return "07:00" <= time_str <= "08:59"

    def __del__(self):
        """析構函數，清理資源"""
        if self.sdk and self.is_connected:
            try:
                # 斷開 WebSocket 連接
                if hasattr(self.sdk, "marketdata") and hasattr(
                    self.sdk.marketdata, "websocket_client"
                ):
                    stock = self.sdk.marketdata.websocket_client.stock
                    if hasattr(stock, "disconnect"):
                        stock.disconnect()

                # 登出
                if self.is_logged_in:
                    self.sdk.logout()

                logger.info("富邦證券 API 客戶端已清理")
            except Exception as e:
                logger.error(f"清理富邦證券 API 客戶端時發生錯誤: {e}")
