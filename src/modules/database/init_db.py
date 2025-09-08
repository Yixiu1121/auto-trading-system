#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫初始化腳本
用於創建所有必要的數據庫表和索引
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from loguru import logger
from typing import Dict, List

from .models import get_all_create_table_sqls, ALL_MODELS


class DatabaseInitializer:
    """數據庫初始化器"""

    def __init__(self, db_config: Dict):
        """
        初始化數據庫初始化器

        Args:
            db_config: 數據庫配置字典
        """
        self.db_config = db_config
        self.connection = None

    def connect(self) -> bool:
        """連接到數據庫"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 5432),
                database=self.db_config.get("database", "trading_system"),
                user=self.db_config.get("user", "trading_user"),
                password=self.db_config.get("password", "trading_password"),
            )
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("數據庫連接成功")
            return True
        except Exception as e:
            logger.error(f"數據庫連接失敗: {e}")
            return False

    def close(self):
        """關閉數據庫連接"""
        if self.connection:
            self.connection.close()
            logger.info("數據庫連接已關閉")

    def create_database(self, db_name: str) -> bool:
        """
        創建數據庫（如果不存在）

        Args:
            db_name: 數據庫名稱

        Returns:
            bool: 創建是否成功
        """
        try:
            # 連接到默認數據庫
            conn = psycopg2.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 5432),
                database="postgres",  # 連接到默認數據庫
                user=self.db_config.get("user", "trading_user"),
                password=self.db_config.get("password", "trading_password"),
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            cursor = conn.cursor()

            # 檢查數據庫是否存在
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()

            if not exists:
                # 創建數據庫
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"數據庫 {db_name} 創建成功")
            else:
                logger.info(f"數據庫 {db_name} 已存在")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"創建數據庫失敗: {e}")
            return False

    def create_tables(self) -> bool:
        """
        創建所有數據庫表

        Returns:
            bool: 創建是否成功
        """
        if not self.connection:
            logger.error("數據庫未連接")
            return False

        try:
            cursor = self.connection.cursor()

            # 獲取所有表的創建 SQL
            create_sqls = get_all_create_table_sqls()

            for i, sql in enumerate(create_sqls):
                try:
                    cursor.execute(sql)
                    table_name = ALL_MODELS[i].get_table_name()
                    logger.info(f"表 {table_name} 創建成功")
                except Exception as e:
                    table_name = ALL_MODELS[i].get_table_name()
                    logger.error(f"創建表 {table_name} 失敗: {e}")
                    return False

            cursor.close()
            logger.info("所有數據庫表創建完成")
            return True

        except Exception as e:
            logger.error(f"創建數據庫表時發生錯誤: {e}")
            return False

    def create_indexes(self) -> bool:
        """
        創建數據庫索引

        Returns:
            bool: 創建是否成功
        """
        if not self.connection:
            logger.error("數據庫未連接")
            return False

        try:
            cursor = self.connection.cursor()

            # 定義索引
            indexes = [
                # price_data 表索引
                "CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timestamp ON price_data (symbol, timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_price_data_period ON price_data (period);",
                "CREATE INDEX IF NOT EXISTS idx_price_data_timestamp ON price_data (timestamp);",
                # technical_indicators 表索引
                "CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_timestamp ON technical_indicators (symbol, timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_technical_indicators_period ON technical_indicators (period);",
                # trading_signals 表索引
                "CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_timestamp ON trading_signals (symbol, timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_trading_signals_signal_type ON trading_signals (signal_type);",
                "CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy_name ON trading_signals (strategy_name);",
                # trades 表索引
                "CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades (symbol, timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_trades_side ON trades (side);",
                "CREATE INDEX IF NOT EXISTS idx_trades_strategy_name ON trades (strategy_name);",
                # positions 表索引
                "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions (symbol);",
                # risk_records 表索引
                "CREATE INDEX IF NOT EXISTS idx_risk_records_symbol_timestamp ON risk_records (symbol, timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_risk_records_risk_type ON risk_records (risk_type);",
                "CREATE INDEX IF NOT EXISTS idx_risk_records_risk_level ON risk_records (risk_level);",
                # system_logs 表索引
                "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs (timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs (level);",
                "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs (module);",
            ]

            for sql in indexes:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"創建索引失敗: {e}")

            cursor.close()
            logger.info("數據庫索引創建完成")
            return True

        except Exception as e:
            logger.error(f"創建數據庫索引時發生錯誤: {e}")
            return False

    def create_triggers(self) -> bool:
        """
        創建數據庫觸發器

        Returns:
            bool: 創建是否成功
        """
        if not self.connection:
            logger.error("數據庫未連接")
            return False

        try:
            cursor = self.connection.cursor()

            # 創建更新時間觸發器函數
            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """
            )

            # 為 stocks 表創建觸發器
            cursor.execute(
                """
                DROP TRIGGER IF EXISTS update_stocks_updated_at ON stocks;
                CREATE TRIGGER update_stocks_updated_at
                    BEFORE UPDATE ON stocks
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """
            )

            # 為 positions 表創建觸發器
            cursor.execute(
                """
                DROP TRIGGER IF EXISTS update_positions_updated_at ON positions;
                CREATE TRIGGER update_positions_updated_at
                    BEFORE UPDATE ON positions
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """
            )

            cursor.close()
            logger.info("數據庫觸發器創建完成")
            return True

        except Exception as e:
            logger.error(f"創建數據庫觸發器時發生錯誤: {e}")
            return False

    def initialize(self) -> bool:
        """
        完整初始化數據庫

        Returns:
            bool: 初始化是否成功
        """
        logger.info("開始初始化數據庫...")

        # 創建數據庫
        db_name = self.db_config.get("database", "trading_system")
        if not self.create_database(db_name):
            return False

        # 連接到目標數據庫
        if not self.connect():
            return False

        try:
            # 創建表
            if not self.create_tables():
                return False

            # 創建索引
            if not self.create_indexes():
                return False

            # 創建觸發器
            if not self.create_triggers():
                return False

            logger.info("數據庫初始化完成")
            return True

        finally:
            self.close()

    def verify_tables(self) -> bool:
        """
        驗證所有表是否正確創建

        Returns:
            bool: 驗證是否成功
        """
        if not self.connect():
            return False

        try:
            cursor = self.connection.cursor()

            # 檢查所有表是否存在
            for model in ALL_MODELS:
                table_name = model.get_table_name()
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """,
                    (table_name,),
                )

                exists = cursor.fetchone()[0]
                if exists:
                    logger.info(f"✅ 表 {table_name} 存在")
                else:
                    logger.error(f"❌ 表 {table_name} 不存在")
                    return False

            cursor.close()
            logger.info("所有表驗證完成")
            return True

        except Exception as e:
            logger.error(f"驗證表時發生錯誤: {e}")
            return False
        finally:
            self.close()


def initialize_database(config: Dict) -> bool:
    """
    初始化數據庫的便捷函數

    Args:
        config: 配置字典

    Returns:
        bool: 初始化是否成功
    """
    db_config = config.get("database", {})
    initializer = DatabaseInitializer(db_config)
    return initializer.initialize()


def verify_database(config: Dict) -> bool:
    """
    驗證數據庫的便捷函數

    Args:
        config: 配置字典

    Returns:
        bool: 驗證是否成功
    """
    db_config = config.get("database", {})
    initializer = DatabaseInitializer(db_config)
    return initializer.verify_tables()


