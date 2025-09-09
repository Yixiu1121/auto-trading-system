#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略執行器
負責從數據庫獲取數據並執行交易策略
"""

import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

from .strategy_base import BaseStrategy
from .blue_long import BlueLongStrategy
from .blue_short import BlueShortStrategy
from .green_long import GreenLongStrategy
from .green_short import GreenShortStrategy
from .orange_long import OrangeLongStrategy
from .orange_short import OrangeShortStrategy


class StrategyExecutor:
    """策略執行器"""

    def __init__(self, config: Dict):
        """
        初始化策略執行器

        Args:
            config: 配置字典或數據庫配置字典
        """
        self.config = config
        # 如果 config 包含 database 鍵且該鍵的值是字典類型，則提取數據庫配置；否則假設整個 config 就是數據庫配置
        if "database" in config and isinstance(config.get("database"), dict):
            self.db_config = config.get("database", {})
        else:
            self.db_config = config
        self.db_conn = None
        self.strategies = {
            "blue_long": BlueLongStrategy,
            "blue_short": BlueShortStrategy,
            "green_long": GreenLongStrategy,
            "green_short": GreenShortStrategy,
            "orange_long": OrangeLongStrategy,
            "orange_short": OrangeShortStrategy,
        }

    def connect_database(self) -> bool:
        """連接到 PostgreSQL 數據庫"""
        try:
            self.db_conn = psycopg2.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 5432),
                database=self.db_config.get("database", "trading_system"),
                user=self.db_config.get("user", "trading_user"),
                password=self.db_config.get("password", "trading_password"),
            )
            logger.info("數據庫連接成功")
            return True
        except Exception as e:
            logger.error(f"數據庫連接失敗: {e}")
            return False

    def close_database(self):
        """關閉數據庫連接"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("數據庫連接已關閉")

    def get_combined_data(
        self, stock_id: str, start_date: str = None, end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        獲取結合價格和技術指標的數據

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            結合價格和技術指標的 DataFrame，如果失敗則返回 None
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return None

        try:
            cursor = self.db_conn.cursor()

            # 構建查詢語句，結合價格數據和技術指標
            query = """
            SELECT 
                p.symbol,
                p.timestamp as date,
                p.open_price as open,
                p.high,
                p.low,
                p.close,
                p.volume,
                t.blue_line,
                t.green_line,
                t.orange_line,
                t.rsi,
                t.macd,
                t.macd_signal,
                t.macd_histogram
            FROM price_data p
            LEFT JOIN technical_indicators t ON p.symbol = t.symbol AND p.timestamp = t.timestamp
            WHERE p.symbol = %s
            """
            params = [stock_id]

            if start_date:
                query += " AND p.timestamp >= %s"
                params.append(start_date)

            if end_date:
                query += " AND p.timestamp <= %s"
                params.append(end_date)

            query += " ORDER BY p.timestamp ASC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            if results:
                # 創建 DataFrame
                columns = [
                    "symbol",
                    "date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "blue_line",
                    "green_line",
                    "orange_line",
                    "rsi",
                    "macd",
                    "macd_signal",
                    "macd_histogram",
                ]
                df = pd.DataFrame(results, columns=columns)

                # 轉換數據類型
                df["date"] = pd.to_datetime(df["date"])
                numeric_columns = [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "blue_line",
                    "green_line",
                    "orange_line",
                    "rsi",
                    "macd",
                    "macd_signal",
                    "macd_histogram",
                ]
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                logger.info(f"成功獲取 {stock_id} 的 {len(df)} 筆結合數據")
                return df
            else:
                logger.warning(f"股票 {stock_id} 沒有找到數據")
                return None

        except Exception as e:
            logger.error(f"獲取結合數據時發生錯誤: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def calculate_additional_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算策略需要的額外技術指標

        Args:
            df: 包含基本價格和技術指標的 DataFrame

        Returns:
            添加了額外技術指標的 DataFrame
        """
        try:
            df = df.copy()

            # 計算斜率 (如果沒有技術指標數據，使用簡單的差分)
            if "blue_line" in df.columns:
                df["blue_slope"] = df["blue_line"].diff(5) / 5
                df["green_slope"] = df["green_line"].diff(5) / 5
                df["orange_slope"] = df["orange_line"].diff(5) / 5

                # 計算乖離率
                df["blue_deviation"] = (df["close"] - df["blue_line"]) / df["blue_line"]
                df["green_deviation"] = (df["close"] - df["green_line"]) / df[
                    "green_line"
                ]
                df["orange_deviation"] = (df["close"] - df["orange_line"]) / df[
                    "orange_line"
                ]

                # 計算成交量比率
                df["volume_ma"] = df["volume"].rolling(window=20).mean()
                df["volume_ratio"] = df["volume"] / df["volume_ma"]

                # 計算趨勢強度
                df["trend_strength"] = 0.0
                for i in range(len(df)):
                    blue_slope = df.loc[df.index[i], "blue_slope"]
                    green_slope = df.loc[df.index[i], "green_slope"]
                    orange_slope = df.loc[df.index[i], "orange_slope"]

                    if (
                        pd.notna(blue_slope)
                        and pd.notna(green_slope)
                        and pd.notna(orange_slope)
                    ):
                        if blue_slope > 0 and green_slope > 0 and orange_slope > 0:
                            df.loc[df.index[i], "trend_strength"] = 1.0
                        elif blue_slope < 0 and green_slope < 0 and orange_slope < 0:
                            df.loc[df.index[i], "trend_strength"] = -1.0
                        else:
                            df.loc[df.index[i], "trend_strength"] = 0.0

            logger.info("成功計算額外技術指標")
            return df

        except Exception as e:
            logger.error(f"計算額外技術指標時發生錯誤: {e}")
            return df

    def execute_strategy(
        self,
        strategy_name: str,
        stock_id: str,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        """
        執行指定策略

        Args:
            strategy_name: 策略名稱
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            策略執行結果字典
        """
        try:
            logger.info(f"開始執行策略: {strategy_name} 對股票: {stock_id}")

            # 檢查策略是否存在
            if strategy_name not in self.strategies:
                logger.error(f"策略 {strategy_name} 不存在")
                return {"success": False, "error": f"策略 {strategy_name} 不存在"}

            # 連接數據庫
            if not self.connect_database():
                return {"success": False, "error": "無法連接到數據庫"}

            # 獲取數據
            df = self.get_combined_data(stock_id, start_date, end_date)
            if df is None or df.empty:
                return {"success": False, "error": "無法獲取數據"}

            # 計算額外技術指標
            df = self.calculate_additional_indicators(df)

            # 創建策略實例
            strategy_class = self.strategies[strategy_name]
            strategy = strategy_class({})  # 使用空配置，策略會使用默認參數

            # 執行策略 - 使用 generate_signals 方法
            strategy_signals = strategy.generate_signals(df)

            # 轉換信號格式
            signals = []

            # 檢查返回的信號格式
            if isinstance(strategy_signals, list):
                # 如果是列表格式 (Blue Long 策略)
                for signal in strategy_signals:
                    signal_date = signal.get("timestamp")
                    if signal_date:
                        matching_row = df[df["date"] == signal_date]
                        if not matching_row.empty:
                            row = matching_row.iloc[0]
                            signals.append(
                                {
                                    "date": signal_date,
                                    "signal": {
                                        "action": signal.get("action", "unknown"),
                                        "strength": signal.get("strength", 0),
                                        "reason": signal.get("reason", ""),
                                    },
                                    "price": row["close"],
                                    "ma_blue": row.get("blue_line"),
                                    "ma_green": row.get("green_line"),
                                    "ma_orange": row.get("orange_line"),
                                }
                            )
            elif isinstance(strategy_signals, pd.DataFrame):
                # 如果是 DataFrame 格式 (Blue Short 策略)
                for idx, row in strategy_signals.iterrows():
                    if row.get("short_signal", 0) != 0:  # 有信號
                        matching_data_row = df.iloc[idx]
                        signals.append(
                            {
                                "date": matching_data_row["date"],
                                "signal": {
                                    "action": (
                                        "sell"
                                        if row.get("short_signal", 0) < 0
                                        else "buy"
                                    ),
                                    "strength": row.get("short_strength", 0),
                                    "reason": f"Entry: {row.get('entry_price', 'N/A')}, Exit: {row.get('exit_price', 'N/A')}",
                                },
                                "price": matching_data_row["close"],
                                "ma_blue": matching_data_row.get("blue_line"),
                                "ma_green": matching_data_row.get("green_line"),
                                "ma_orange": matching_data_row.get("orange_line"),
                            }
                        )

            # 計算策略統計
            total_signals = len(signals)
            buy_signals = len([s for s in signals if s["signal"]["action"] == "buy"])
            sell_signals = len([s for s in signals if s["signal"]["action"] == "sell"])

            result = {
                "success": True,
                "strategy_name": strategy_name,
                "stock_id": stock_id,
                "data_period": f"{df['date'].min()} 到 {df['date'].max()}",
                "total_data_points": len(df),
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "signals": signals[-10:] if signals else [],  # 返回最近10個信號
                "latest_data": {
                    "date": df.iloc[-1]["date"],
                    "close": df.iloc[-1]["close"],
                    "ma_blue": df.iloc[-1].get("blue_line"),
                    "ma_green": df.iloc[-1].get("green_line"),
                    "ma_orange": df.iloc[-1].get("orange_line"),
                    "trend_strength": df.iloc[-1].get("trend_strength"),
                },
            }

            logger.info(f"策略 {strategy_name} 執行完成，產生 {total_signals} 個信號")
            return result

        except Exception as e:
            logger.error(f"執行策略時發生錯誤: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.close_database()

    def execute_all_strategies(
        self, stock_id: str, start_date: str = None, end_date: str = None
    ) -> Dict:
        """
        執行所有策略

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            所有策略的執行結果
        """
        results = {}

        for strategy_name in self.strategies.keys():
            logger.info(f"執行策略: {strategy_name}")
            result = self.execute_strategy(
                strategy_name, stock_id, start_date, end_date
            )
            results[strategy_name] = result

        return results

    def execute_strategies(self, symbols: List[str] = None) -> List[Dict]:
        """
        執行策略並返回信號列表

        Args:
            symbols: 股票代碼列表，如果為 None 則使用配置中的股票池

        Returns:
            List[Dict]: 信號列表
        """
        if symbols is None:
            # 使用默認股票池
            symbols = ["2330", "0050", "1101"]

        all_signals = []

        try:
            for symbol in symbols:
                logger.info(f"執行策略分析: {symbol}")

                # 執行所有策略
                results = self.execute_all_strategies(symbol)

                # 提取信號
                for strategy_name, result in results.items():
                    if result.get("success") and result.get("signals"):
                        for signal in result["signals"]:
                            # 轉換信號格式
                            formatted_signal = {
                                "symbol": symbol,
                                "strategy": strategy_name,
                                "action": signal["signal"]["action"],
                                "signal_strength": signal["signal"]["strength"],
                                "target_price": signal["price"],
                                "quantity": 1000,  # 預設數量
                                "date": signal["date"],
                                "reason": signal["signal"]["reason"],
                                "ma_blue": signal.get("ma_blue"),
                                "ma_green": signal.get("ma_green"),
                                "ma_orange": signal.get("ma_orange"),
                            }
                            all_signals.append(formatted_signal)

                logger.info(
                    f"{symbol} 策略分析完成，產生 {len([s for s in all_signals if s['symbol'] == symbol])} 個信號"
                )

            # 按信號強度排序
            all_signals.sort(key=lambda x: abs(x["signal_strength"]), reverse=True)

            logger.info(f"總共產生 {len(all_signals)} 個信號")
            return all_signals

        except Exception as e:
            logger.error(f"執行策略時發生錯誤: {e}")
            return []
