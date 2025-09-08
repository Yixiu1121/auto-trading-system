#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技術指標存儲器
負責將計算好的技術指標存儲到數據庫
"""

import pandas as pd
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from ..database.models import TechnicalIndicator, PeriodType


class TechnicalIndicatorStorage:
    """技術指標存儲器"""

    def __init__(self, db_config: Dict):
        """
        初始化技術指標存儲器

        Args:
            db_config: 數據庫配置字典
        """
        self.db_config = db_config
        self.db_conn = None

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

    def store_technical_indicators(self, stock_id: str, df: pd.DataFrame) -> bool:
        """
        將技術指標存儲到數據庫

        Args:
            stock_id: 股票代碼
            df: 包含技術指標的 DataFrame

        Returns:
            存儲成功返回 True，失敗返回 False
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return False

        try:
            cursor = self.db_conn.cursor()

            # 準備插入數據
            data_to_insert = []
            for _, row in df.iterrows():
                # 創建技術指標模型
                indicator = TechnicalIndicator(
                    symbol=stock_id,
                    timestamp=row["date"],
                    blue_line=row.get("ma_blue"),  # 映射到 blue_line
                    green_line=row.get("ma_green"),  # 映射到 green_line
                    orange_line=row.get("ma_orange"),  # 映射到 orange_line
                    rsi=None,  # 暫時設為 None，後續可以添加 RSI 計算
                    macd=None,  # 暫時設為 None，後續可以添加 MACD 計算
                    macd_signal=None,  # 暫時設為 None
                    macd_histogram=None,  # 暫時設為 None
                    created_at=datetime.now(),
                )
                data_to_insert.append(indicator.to_tuple())

            # 使用 UPSERT 語句，避免重複數據
            cursor.executemany(TechnicalIndicator.get_insert_sql(), data_to_insert)

            self.db_conn.commit()
            logger.info(
                f"成功存儲 {stock_id} 的 {len(data_to_insert)} 筆技術指標到數據庫"
            )
            return True

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"存儲技術指標時發生錯誤: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_technical_indicators(
        self, stock_id: str, start_date: str = None, end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        從數據庫獲取技術指標

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            包含技術指標的 DataFrame，如果失敗則返回 None
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return None

        try:
            cursor = self.db_conn.cursor()

            # 構建查詢語句
            query = """
            SELECT symbol, timestamp, blue_line, green_line, orange_line,
                   rsi, macd, macd_signal, macd_histogram, created_at
            FROM technical_indicators
            WHERE symbol = %s
            """
            params = [stock_id]

            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            query += " ORDER BY timestamp ASC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            if results:
                # 創建 DataFrame
                columns = [
                    "symbol",
                    "timestamp",
                    "blue_line",
                    "green_line",
                    "orange_line",
                    "rsi",
                    "macd",
                    "macd_signal",
                    "macd_histogram",
                    "created_at",
                ]
                df = pd.DataFrame(results, columns=columns)

                # 轉換數據類型
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                numeric_columns = [
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

                logger.info(f"成功獲取 {stock_id} 的 {len(df)} 筆技術指標")
                return df
            else:
                logger.warning(f"股票 {stock_id} 沒有找到技術指標數據")
                return None

        except Exception as e:
            logger.error(f"獲取技術指標時發生錯誤: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def delete_technical_indicators(
        self, stock_id: str, start_date: str = None, end_date: str = None
    ) -> bool:
        """
        刪除技術指標數據

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            刪除成功返回 True，失敗返回 False
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return False

        try:
            cursor = self.db_conn.cursor()

            # 構建刪除語句
            query = "DELETE FROM technical_indicators WHERE symbol = %s"
            params = [stock_id]

            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            cursor.execute(query, params)
            deleted_count = cursor.rowcount

            self.db_conn.commit()
            logger.info(f"成功刪除 {stock_id} 的 {deleted_count} 筆技術指標")
            return True

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"刪除技術指標時發生錯誤: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_latest_indicators(self, stock_id: str) -> Optional[Dict]:
        """
        獲取最新的技術指標

        Args:
            stock_id: 股票代碼

        Returns:
            最新技術指標字典，如果失敗則返回 None
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return None

        try:
            cursor = self.db_conn.cursor()

            query = """
            SELECT symbol, timestamp, blue_line, green_line, orange_line,
                   rsi, macd, macd_signal, macd_histogram, created_at
            FROM technical_indicators
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            cursor.execute(query, (stock_id,))
            result = cursor.fetchone()

            if result:
                columns = [
                    "symbol",
                    "timestamp",
                    "blue_line",
                    "green_line",
                    "orange_line",
                    "rsi",
                    "macd",
                    "macd_signal",
                    "macd_histogram",
                    "created_at",
                ]

                latest_indicator = dict(zip(columns, result))
                logger.info(f"成功獲取 {stock_id} 的最新技術指標")
                return latest_indicator
            else:
                logger.warning(f"股票 {stock_id} 沒有找到技術指標數據")
                return None

        except Exception as e:
            logger.error(f"獲取最新技術指標時發生錯誤: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def get_indicator_statistics(self, stock_id: str) -> Optional[Dict]:
        """
        獲取技術指標統計信息

        Args:
            stock_id: 股票代碼

        Returns:
            技術指標統計字典，如果失敗則返回 None
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return None

        try:
            cursor = self.db_conn.cursor()

            query = """
            SELECT 
                COUNT(*) as total_records,
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date,
                AVG(blue_line) as avg_blue_line,
                AVG(green_line) as avg_green_line,
                AVG(orange_line) as avg_orange_line,
                AVG(rsi) as avg_rsi
            FROM technical_indicators
            WHERE symbol = %s
            """

            cursor.execute(query, (stock_id,))
            result = cursor.fetchone()

            if result:
                columns = [
                    "total_records",
                    "earliest_date",
                    "latest_date",
                    "avg_blue_line",
                    "avg_green_line",
                    "avg_orange_line",
                    "avg_rsi",
                ]

                stats = dict(zip(columns, result))
                logger.info(f"成功獲取 {stock_id} 的技術指標統計信息")
                return stats
            else:
                logger.warning(f"股票 {stock_id} 沒有找到技術指標數據")
                return None

        except Exception as e:
            logger.error(f"獲取技術指標統計信息時發生錯誤: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
