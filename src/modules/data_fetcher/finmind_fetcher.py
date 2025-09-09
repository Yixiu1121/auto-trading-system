#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FinMind 數據獲取器
負責從 FinMind API 獲取股票數據並存儲到數據庫
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# 導入數據庫模型
from ..database.models import Stock, PriceData, PeriodType


class FinMindFetcher:
    """FinMind 數據獲取器"""

    def __init__(self, config: Dict):
        """
        初始化 FinMind 數據獲取器

        Args:
            config: 配置字典，包含 API 和數據庫配置
        """
        self.config = config

        # FinMind API 配置
        self.api_base_url = "https://api.finmindtrade.com"
        finmind_config = config.get("finmind", {})
        self.api_token = os.getenv("FINMIND_TOKEN", finmind_config.get("token", ""))

        # 數據庫配置 - 處理環境變量
        db_config = config.get("database", {})
        self.db_config = {
            "host": os.getenv("DB_HOST", db_config.get("host", "localhost")),
            "port": int(os.getenv("DB_PORT", db_config.get("port", 5432))),
            "database": os.getenv(
                "DB_NAME", db_config.get("database", "trading_system")
            ),
            "user": os.getenv("DB_USER", db_config.get("user", "trading_user")),
            "password": os.getenv(
                "DB_PASSWORD", db_config.get("password", "trading_password")
            ),
        }

        # 請求頭
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
            "Origin": "https://finmindtrade.com",
            "Referer": "https://finmindtrade.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        # 數據庫連接
        self.db_conn = None

        logger.info("FinMind 數據獲取器初始化完成")

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

    def get_stock_list(self) -> List[Dict]:
        """獲取股票列表"""
        try:
            url = f"{self.api_base_url}/api/v4/data"
            params = {"dataset": "TaiwanStockInfo", "device": "web"}

            response = requests.get(
                url, params=params, headers=self.headers, timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # 處理新的 API 響應格式
            if isinstance(data, dict) and data.get("status") == 200:
                data_list = data.get("data", [])
            elif isinstance(data, list):
                data_list = data
            else:
                data_list = []

            if len(data_list) > 0:
                logger.info(f"成功獲取 {len(data_list)} 支股票信息")
                return data_list
            else:
                logger.error(f"獲取股票列表失敗: 返回數據格式不正確")
                return []

        except Exception as e:
            logger.error(f"獲取股票列表時發生錯誤: {e}")
            return []

    def get_stock_data(
        self, stock_id: str, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        獲取單支股票的歷史數據

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            DataFrame 包含 OHLCV 數據，如果失敗則返回 None
        """
        try:
            url = f"{self.api_base_url}/api/v4/data"
            params = {
                "dataset": "TaiwanStockPrice",
                "data_id": stock_id,
                "start_date": start_date,
                "end_date": end_date,
                "device": "web",
            }

            response = requests.get(
                url, params=params, headers=self.headers, timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # 處理新的 API 響應格式
            if isinstance(data, dict) and data.get("status") == 200:
                data_list = data.get("data", [])
            elif isinstance(data, list):
                data_list = data
            else:
                data_list = []

            if len(data_list) > 0:
                df = pd.DataFrame(data_list)
                if not df.empty:
                    # 標準化列名
                    df.columns = [col.lower() for col in df.columns]

                    # 映射列名到標準格式
                    column_mapping = {
                        "max": "high",
                        "min": "low",
                        "trading_volume": "volume",
                    }

                    for old_col, new_col in column_mapping.items():
                        if old_col in df.columns and new_col not in df.columns:
                            df[new_col] = df[old_col]

                    # 確保必要的列存在
                    required_columns = [
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ]
                    if all(col in df.columns for col in required_columns):
                        # 轉換數據類型
                        df["date"] = pd.to_datetime(df["date"])
                        numeric_columns = ["open", "high", "low", "close", "volume"]
                        for col in numeric_columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                        # 按日期排序
                        df = df.sort_values("date").reset_index(drop=True)

                        logger.info(f"成功獲取 {stock_id} 的 {len(df)} 筆數據")
                        return df
                    else:
                        logger.error(f"數據格式不正確，缺少必要列: {required_columns}")
                        return None
                else:
                    logger.warning(f"股票 {stock_id} 在指定日期範圍內沒有數據")
                    return None
            else:
                logger.error(f"獲取股票 {stock_id} 數據失敗: 返回數據格式不正確")
                return None

        except Exception as e:
            logger.error(f"獲取股票 {stock_id} 數據時發生錯誤: {e}")
            return None

    def store_stock_data(self, stock_id: str, df: pd.DataFrame) -> bool:
        """
        將股票數據存儲到數據庫

        Args:
            stock_id: 股票代碼
            df: 包含 OHLCV 數據的 DataFrame

        Returns:
            存儲成功返回 True，失敗返回 False
        """
        if not self.db_conn:
            logger.error("數據庫未連接")
            return False

        try:
            cursor = self.db_conn.cursor()

            # 檢查股票是否已存在於 stocks 表
            cursor.execute("SELECT symbol FROM stocks WHERE symbol = %s", (stock_id,))
            stock_record = cursor.fetchone()

            if not stock_record:
                # 創建股票模型並插入
                stock = Stock(
                    symbol=stock_id,
                    name=f"Stock_{stock_id}",
                    sector="Unknown",
                    market_cap=0,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                cursor.execute(Stock.get_insert_sql(), stock.to_tuple())
                logger.info(f"新增股票記錄: {stock_id}")
            else:
                logger.info(f"股票 {stock_id} 已存在於數據庫中")

            # 準備插入數據
            data_to_insert = []
            for _, row in df.iterrows():
                # 創建價格數據模型
                price_data = PriceData(
                    symbol=stock_id,
                    timestamp=row["date"],
                    open_price=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    period=PeriodType.HOUR_4_5.value,
                    created_at=datetime.now(),
                )
                data_to_insert.append(price_data.to_tuple())

            # 使用 UPSERT 語句，避免重複數據
            cursor.executemany(PriceData.get_insert_sql(), data_to_insert)

            self.db_conn.commit()
            logger.info(f"成功存儲 {stock_id} 的 {len(data_to_insert)} 筆數據到數據庫")
            return True

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"存儲股票 {stock_id} 數據時發生錯誤: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def initialize_database(
        self, stock_ids: Optional[List[str]] = None, days_back: int = 30
    ):
        """
        初始化數據庫，獲取指定股票的歷史數據

        Args:
            stock_ids: 股票代碼列表，如果為 None 則獲取所有股票
            days_back: 獲取多少天前的數據
        """
        if not self.connect_database():
            logger.error("無法連接到數據庫，初始化失敗")
            return False

        try:
            # 如果沒有指定股票，獲取股票列表
            if stock_ids is None:
                stocks = self.get_stock_list()
                stock_ids = [
                    stock["stock_id"] for stock in stocks[:50]
                ]  # 限制為前50支股票
                logger.info(f"將初始化 {len(stock_ids)} 支股票的數據")

            # 計算日期範圍
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days_back)).strftime(
                "%Y-%m-%d"
            )

            success_count = 0
            total_count = len(stock_ids)

            for i, stock_id in enumerate(stock_ids, 1):
                logger.info(f"正在處理股票 {stock_id} ({i}/{total_count})")

                # 獲取股票數據
                df = self.get_stock_data(stock_id, start_date, end_date)
                if df is not None and not df.empty:
                    # 存儲到數據庫
                    if self.store_stock_data(stock_id, df):
                        success_count += 1

                # 避免 API 請求過於頻繁
                time.sleep(0.5)

            logger.info(
                f"數據庫初始化完成，成功處理 {success_count}/{total_count} 支股票"
            )
            return True

        except Exception as e:
            logger.error(f"初始化數據庫時發生錯誤: {e}")
            return False
        finally:
            self.close_database()

    def update_daily_data(self, stock_ids: Optional[List[str]] = None):
        """
        更新每日最新數據

        Args:
            stock_ids: 股票代碼列表，如果為 None 則更新所有股票
        """
        if not self.connect_database():
            logger.error("無法連接到數據庫，更新失敗")
            return False

        try:
            # 如果沒有指定股票，從數據庫獲取股票列表
            if stock_ids is None:
                cursor = self.db_conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM stocks")
                stock_records = cursor.fetchall()
                stock_ids = [record[0] for record in stock_records]
                cursor.close()

            # 獲取今天的數據
            today = datetime.now().strftime("%Y-%m-%d")

            success_count = 0
            total_count = len(stock_ids)

            for i, stock_id in enumerate(stock_ids, 1):
                logger.info(f"正在更新股票 {stock_id} 的每日數據 ({i}/{total_count})")

                # 獲取今天的數據
                df = self.get_stock_data(stock_id, today, today)
                if df is not None and not df.empty:
                    # 存儲到數據庫
                    if self.store_stock_data(stock_id, df):
                        success_count += 1

                # 避免 API 請求過於頻繁
                time.sleep(0.5)

            logger.info(
                f"每日數據更新完成，成功更新 {success_count}/{total_count} 支股票"
            )
            return True

        except Exception as e:
            logger.error(f"更新每日數據時發生錯誤: {e}")
            return False
        finally:
            self.close_database()

    def health_check(self) -> Dict:
        """健康檢查"""
        try:
            # 檢查 API 連接
            api_status = "healthy"
            try:
                params = {"dataset": "TaiwanStockInfo", "device": "web"}
                response = requests.get(
                    f"{self.api_base_url}/api/v4/data",
                    params=params,
                    headers=self.headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    api_status = "unhealthy"
            except:
                api_status = "unhealthy"

            # 檢查數據庫連接
            db_status = "healthy"
            if not self.connect_database():
                db_status = "unhealthy"
            else:
                self.close_database()

            return {
                "api_status": api_status,
                "database_status": db_status,
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "api_status": "error",
                "database_status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
