#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫模型定義
定義所有數據庫表的結構和約束
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PeriodType(Enum):
    """K線週期類型"""

    DAILY = "1d"
    HOUR_4_5 = "4.5h"
    HOURLY = "1h"
    MINUTE_30 = "30m"
    MINUTE_15 = "15m"
    MINUTE_5 = "5m"
    MINUTE_1 = "1m"


class TradeSide(Enum):
    """交易方向"""

    BUY = "buy"
    SELL = "sell"


class SignalType(Enum):
    """信號類型"""

    LONG_ENTRY = "long_entry"
    LONG_EXIT = "long_exit"
    SHORT_ENTRY = "short_entry"
    SHORT_EXIT = "short_exit"


@dataclass
class Stock:
    """股票基本信息模型"""

    symbol: str  # 股票代碼 (主鍵)
    name: str  # 股票名稱
    sector: Optional[str] = None  # 行業分類
    market_cap: Optional[float] = None  # 市值
    created_at: Optional[datetime] = None  # 創建時間
    updated_at: Optional[datetime] = None  # 更新時間

    @classmethod
    def get_table_name(cls) -> str:
        return "stocks"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS stocks (
            symbol VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            sector VARCHAR(50),
            market_cap NUMERIC(20,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO stocks (symbol, name, sector, market_cap, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol) 
        DO UPDATE SET
            name = EXCLUDED.name,
            sector = EXCLUDED.sector,
            market_cap = EXCLUDED.market_cap,
            updated_at = EXCLUDED.updated_at
        """

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.name,
            self.sector,
            self.market_cap,
            self.created_at or datetime.now(),
            self.updated_at or datetime.now(),
        )


@dataclass
class PriceData:
    """價格數據模型"""

    id: Optional[int] = None  # 自增主鍵
    symbol: str = ""  # 股票代碼 (外鍵)
    timestamp: Optional[datetime] = None  # 時間戳
    open_price: float = 0.0  # 開盤價
    high: float = 0.0  # 最高價
    low: float = 0.0  # 最低價
    close: float = 0.0  # 收盤價
    volume: int = 0  # 成交量
    period: str = PeriodType.HOUR_4_5.value  # K線週期
    created_at: Optional[datetime] = None  # 創建時間

    @classmethod
    def get_table_name(cls) -> str:
        return "price_data"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS price_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open_price NUMERIC(10,4) NOT NULL,
            high NUMERIC(10,4) NOT NULL,
            low NUMERIC(10,4) NOT NULL,
            close NUMERIC(10,4) NOT NULL,
            volume BIGINT NOT NULL,
            period VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE,
            UNIQUE(symbol, timestamp, period)
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO price_data (symbol, timestamp, open_price, high, low, close, volume, period, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, timestamp, period) 
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            created_at = EXCLUDED.created_at
        """

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.timestamp,
            self.open_price,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.period,
            self.created_at or datetime.now(),
        )


@dataclass
class TechnicalIndicator:
    """技術指標模型"""

    id: Optional[int] = None  # 自增主鍵
    symbol: str = ""  # 股票代碼 (外鍵)
    timestamp: Optional[datetime] = None  # 時間戳
    blue_line: Optional[float] = None  # 藍線 (短期均線)
    green_line: Optional[float] = None  # 綠線 (中期均線)
    orange_line: Optional[float] = None  # 橘線 (長期均線)
    rsi: Optional[float] = None  # RSI 指標
    macd: Optional[float] = None  # MACD 指標
    macd_signal: Optional[float] = None  # MACD 信號線
    macd_histogram: Optional[float] = None  # MACD 柱狀圖
    created_at: Optional[datetime] = None  # 創建時間

    @classmethod
    def get_table_name(cls) -> str:
        return "technical_indicators"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            blue_line NUMERIC(10,4),
            green_line NUMERIC(10,4),
            orange_line NUMERIC(10,4),
            rsi NUMERIC(5,2),
            macd NUMERIC(10,4),
            macd_signal NUMERIC(10,4),
            macd_histogram NUMERIC(10,4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE,
            UNIQUE(symbol, timestamp)
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO technical_indicators (
            symbol, timestamp, blue_line, green_line, orange_line,
            rsi, macd, macd_signal, macd_histogram, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, timestamp) 
        DO UPDATE SET
            blue_line = EXCLUDED.blue_line,
            green_line = EXCLUDED.green_line,
            orange_line = EXCLUDED.orange_line,
            rsi = EXCLUDED.rsi,
            macd = EXCLUDED.macd,
            macd_signal = EXCLUDED.macd_signal,
            macd_histogram = EXCLUDED.macd_histogram,
            created_at = EXCLUDED.created_at
        """

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.timestamp,
            self.blue_line,
            self.green_line,
            self.orange_line,
            self.rsi,
            self.macd,
            self.macd_signal,
            self.macd_histogram,
            self.created_at or datetime.now(),
        )


@dataclass
class TradingSignal:
    """交易信號模型"""

    id: Optional[int] = None  # 自增主鍵
    symbol: str = ""  # 股票代碼 (外鍵)
    timestamp: Optional[datetime] = None  # 時間戳
    signal_type: str = ""  # 信號類型
    price: float = 0.0  # 信號價格
    volume: int = 0  # 建議成交量
    confidence: float = 0.0  # 信號強度 (0-1)
    strategy_name: str = ""  # 策略名稱
    parameters: Optional[Dict[str, Any]] = None  # 策略參數
    created_at: Optional[datetime] = None  # 創建時間

    @classmethod
    def get_table_name(cls) -> str:
        return "trading_signals"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS trading_signals (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            signal_type VARCHAR(20) NOT NULL,
            price NUMERIC(10,4) NOT NULL,
            volume INTEGER NOT NULL,
            confidence NUMERIC(3,2) NOT NULL,
            strategy_name VARCHAR(50) NOT NULL,
            parameters JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO trading_signals (
            symbol, timestamp, signal_type, price, volume, 
            confidence, strategy_name, parameters, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

    def to_tuple(self) -> tuple:
        import json

        return (
            self.symbol,
            self.timestamp,
            self.signal_type,
            self.price,
            self.volume,
            self.confidence,
            self.strategy_name,
            json.dumps(self.parameters) if self.parameters else None,
            self.created_at or datetime.now(),
        )


@dataclass
class Trade:
    """交易記錄模型"""

    id: Optional[int] = None  # 自增主鍵
    symbol: str = ""  # 股票代碼 (外鍵)
    timestamp: Optional[datetime] = None  # 交易時間
    side: str = ""  # 交易方向 (buy/sell)
    price: float = 0.0  # 交易價格
    volume: int = 0  # 交易數量
    amount: float = 0.0  # 交易金額
    commission: float = 0.0  # 手續費
    strategy_name: str = ""  # 策略名稱
    signal_id: Optional[int] = None  # 關聯的信號ID
    created_at: Optional[datetime] = None  # 創建時間

    @classmethod
    def get_table_name(cls) -> str:
        return "trades"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            side VARCHAR(4) NOT NULL,
            price NUMERIC(10,4) NOT NULL,
            volume INTEGER NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            commission NUMERIC(10,2) NOT NULL,
            strategy_name VARCHAR(50) NOT NULL,
            signal_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE,
            FOREIGN KEY (signal_id) REFERENCES trading_signals(id) ON DELETE SET NULL
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO trades (
            symbol, timestamp, side, price, volume, amount, 
            commission, strategy_name, signal_id, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.timestamp,
            self.side,
            self.price,
            self.volume,
            self.amount,
            self.commission,
            self.strategy_name,
            self.signal_id,
            self.created_at or datetime.now(),
        )


@dataclass
class Position:
    """持倉模型"""

    id: Optional[int] = None  # 自增主鍵
    symbol: str = ""  # 股票代碼 (外鍵)
    volume: int = 0  # 持倉數量
    avg_price: float = 0.0  # 平均成本
    market_value: float = 0.0  # 市值
    unrealized_pnl: float = 0.0  # 未實現損益
    realized_pnl: float = 0.0  # 已實現損益
    created_at: Optional[datetime] = None  # 創建時間
    updated_at: Optional[datetime] = None  # 更新時間

    @classmethod
    def get_table_name(cls) -> str:
        return "positions"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            volume INTEGER NOT NULL,
            avg_price NUMERIC(10,4) NOT NULL,
            market_value NUMERIC(15,2) NOT NULL,
            unrealized_pnl NUMERIC(15,2) NOT NULL,
            realized_pnl NUMERIC(15,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE,
            UNIQUE(symbol)
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO positions (
            symbol, volume, avg_price, market_value, 
            unrealized_pnl, realized_pnl, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol) 
        DO UPDATE SET
            volume = EXCLUDED.volume,
            avg_price = EXCLUDED.avg_price,
            market_value = EXCLUDED.market_value,
            unrealized_pnl = EXCLUDED.unrealized_pnl,
            realized_pnl = EXCLUDED.realized_pnl,
            updated_at = EXCLUDED.updated_at
        """

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.volume,
            self.avg_price,
            self.market_value,
            self.unrealized_pnl,
            self.realized_pnl,
            self.created_at or datetime.now(),
            self.updated_at or datetime.now(),
        )


@dataclass
class RiskRecord:
    """風險記錄模型"""

    id: Optional[int] = None  # 自增主鍵
    symbol: str = ""  # 股票代碼 (外鍵)
    timestamp: Optional[datetime] = None  # 時間戳
    risk_type: str = ""  # 風險類型
    risk_level: str = ""  # 風險等級
    description: str = ""  # 風險描述
    action_taken: str = ""  # 採取的行動
    created_at: Optional[datetime] = None  # 創建時間

    @classmethod
    def get_table_name(cls) -> str:
        return "risk_records"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS risk_records (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            risk_type VARCHAR(50) NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            description TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO risk_records (
            symbol, timestamp, risk_type, risk_level, 
            description, action_taken, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.timestamp,
            self.risk_type,
            self.risk_level,
            self.description,
            self.action_taken,
            self.created_at or datetime.now(),
        )


@dataclass
class SystemLog:
    """系統日誌模型"""

    id: Optional[int] = None  # 自增主鍵
    timestamp: Optional[datetime] = None  # 時間戳
    level: str = ""  # 日誌級別
    module: str = ""  # 模組名稱
    message: str = ""  # 日誌消息
    details: Optional[Dict[str, Any]] = None  # 詳細信息
    created_at: Optional[datetime] = None  # 創建時間

    @classmethod
    def get_table_name(cls) -> str:
        return "system_logs"

    @classmethod
    def get_create_table_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            level VARCHAR(20) NOT NULL,
            module VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @classmethod
    def get_insert_sql(cls) -> str:
        return """
        INSERT INTO system_logs (
            timestamp, level, module, message, details, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

    def to_tuple(self) -> tuple:
        import json

        return (
            self.timestamp,
            self.level,
            self.module,
            self.message,
            json.dumps(self.details) if self.details else None,
            self.created_at or datetime.now(),
        )


# 所有模型的列表
ALL_MODELS = [
    Stock,
    PriceData,
    TechnicalIndicator,
    TradingSignal,
    Trade,
    Position,
    RiskRecord,
    SystemLog,
]


def get_all_create_table_sqls() -> List[str]:
    """獲取所有表的創建 SQL"""
    return [model.get_create_table_sql() for model in ALL_MODELS]


def get_model_by_table_name(table_name: str):
    """根據表名獲取對應的模型類"""
    for model in ALL_MODELS:
        if model.get_table_name() == table_name:
            return model
    return None
