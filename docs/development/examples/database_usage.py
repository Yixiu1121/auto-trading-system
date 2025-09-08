#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫模型使用示例
展示如何使用數據庫模型進行 CRUD 操作
"""

import os
import sys
import yaml
import psycopg2
from datetime import datetime
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.modules.database.models import (
    Stock,
    PriceData,
    TechnicalIndicator,
    TradingSignal,
    Trade,
    Position,
    RiskRecord,
    SystemLog,
    PeriodType,
    TradeSide,
    SignalType,
)


def load_config():
    """加載配置文件"""
    config_path = "../config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"配置文件 {config_path} 不存在")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def connect_database(db_config):
    """連接到數據庫"""
    try:
        conn = psycopg2.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            database=db_config.get("database", "trading_system"),
            user=db_config.get("user", "trading_user"),
            password=db_config.get("password", "trading_password"),
        )
        return conn
    except Exception as e:
        logger.error(f"數據庫連接失敗: {e}")
        return None


def example_stock_operations(conn):
    """股票操作示例"""
    print("\n=== 股票操作示例 ===")

    cursor = conn.cursor()

    # 創建股票模型
    stock = Stock(
        symbol="2330",
        name="台積電",
        sector="半導體",
        market_cap=5000000000000,  # 5兆台幣
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 插入股票
    cursor.execute(Stock.get_insert_sql(), stock.to_tuple())
    print(f"✅ 插入股票: {stock.symbol} - {stock.name}")

    # 查詢股票
    cursor.execute("SELECT * FROM stocks WHERE symbol = %s", (stock.symbol,))
    result = cursor.fetchone()
    if result:
        print(f"✅ 查詢到股票: {result[0]} - {result[1]}")

    conn.commit()
    cursor.close()


def example_price_data_operations(conn):
    """價格數據操作示例"""
    print("\n=== 價格數據操作示例 ===")

    cursor = conn.cursor()

    # 創建價格數據模型
    price_data = PriceData(
        symbol="2330",
        timestamp=datetime(2025, 8, 31, 9, 0, 0),
        open_price=580.0,
        high=585.0,
        low=575.0,
        close=582.0,
        volume=1000000,
        period=PeriodType.HOUR_4_5.value,
        created_at=datetime.now(),
    )

    # 插入價格數據
    cursor.execute(PriceData.get_insert_sql(), price_data.to_tuple())
    print(f"✅ 插入價格數據: {price_data.symbol} - {price_data.timestamp}")

    # 查詢價格數據
    cursor.execute(
        "SELECT * FROM price_data WHERE symbol = %s ORDER BY timestamp DESC LIMIT 1",
        (price_data.symbol,),
    )
    result = cursor.fetchone()
    if result:
        print(f"✅ 查詢到價格數據: {result[1]} - {result[2]} - 收盤: {result[6]}")

    conn.commit()
    cursor.close()


def example_technical_indicator_operations(conn):
    """技術指標操作示例"""
    print("\n=== 技術指標操作示例 ===")

    cursor = conn.cursor()

    # 創建技術指標模型
    indicator = TechnicalIndicator(
        symbol="2330",
        timestamp=datetime(2025, 8, 31, 9, 0, 0),
        period=PeriodType.HOUR_4_5.value,
        ma_blue=580.5,
        ma_green=575.2,
        ma_orange=570.8,
        ma_blue_slope=0.02,
        ma_green_slope=0.015,
        ma_orange_slope=0.01,
        blue_deviation=0.002,
        green_deviation=0.012,
        orange_deviation=0.02,
        volume_ratio=1.5,
        created_at=datetime.now(),
    )

    # 插入技術指標
    cursor.execute(TechnicalIndicator.get_insert_sql(), indicator.to_tuple())
    print(f"✅ 插入技術指標: {indicator.symbol} - 藍線: {indicator.ma_blue}")

    # 查詢技術指標
    cursor.execute(
        "SELECT symbol, ma_blue, ma_green, ma_orange FROM technical_indicators WHERE symbol = %s",
        (indicator.symbol,),
    )
    result = cursor.fetchone()
    if result:
        print(
            f"✅ 查詢到技術指標: {result[0]} - 藍:{result[1]} 綠:{result[2]} 橘:{result[3]}"
        )

    conn.commit()
    cursor.close()


def example_trading_signal_operations(conn):
    """交易信號操作示例"""
    print("\n=== 交易信號操作示例 ===")

    cursor = conn.cursor()

    # 創建交易信號模型
    signal = TradingSignal(
        symbol="2330",
        timestamp=datetime.now(),
        signal_type=SignalType.LONG_ENTRY.value,
        price=582.0,
        volume=1000,
        confidence=0.85,
        strategy_name="Blue Long Strategy",
        parameters={"ma_period": 120, "deviation_threshold": 0.05},
        created_at=datetime.now(),
    )

    # 插入交易信號
    cursor.execute(TradingSignal.get_insert_sql(), signal.to_tuple())
    print(
        f"✅ 插入交易信號: {signal.symbol} - {signal.signal_type} - 信心度: {signal.confidence}"
    )

    # 查詢交易信號
    cursor.execute(
        "SELECT symbol, signal_type, price, confidence FROM trading_signals WHERE symbol = %s",
        (signal.symbol,),
    )
    result = cursor.fetchone()
    if result:
        print(
            f"✅ 查詢到交易信號: {result[0]} - {result[1]} - 價格: {result[2]} - 信心度: {result[3]}"
        )

    conn.commit()
    cursor.close()


def example_trade_operations(conn):
    """交易記錄操作示例"""
    print("\n=== 交易記錄操作示例 ===")

    cursor = conn.cursor()

    # 創建交易記錄模型
    trade = Trade(
        symbol="2330",
        timestamp=datetime.now(),
        side=TradeSide.BUY.value,
        price=582.0,
        volume=1000,
        amount=582000.0,
        commission=582.0,
        strategy_name="Blue Long Strategy",
        signal_id=1,
        created_at=datetime.now(),
    )

    # 插入交易記錄
    cursor.execute(Trade.get_insert_sql(), trade.to_tuple())
    print(f"✅ 插入交易記錄: {trade.symbol} - {trade.side} - 數量: {trade.volume}")

    # 查詢交易記錄
    cursor.execute(
        "SELECT symbol, side, price, volume FROM trades WHERE symbol = %s",
        (trade.symbol,),
    )
    result = cursor.fetchone()
    if result:
        print(
            f"✅ 查詢到交易記錄: {result[0]} - {result[1]} - 價格: {result[2]} - 數量: {result[3]}"
        )

    conn.commit()
    cursor.close()


def example_position_operations(conn):
    """持倉操作示例"""
    print("\n=== 持倉操作示例 ===")

    cursor = conn.cursor()

    # 創建持倉模型
    position = Position(
        symbol="2330",
        volume=1000,
        avg_price=580.0,
        market_value=582000.0,
        unrealized_pnl=2000.0,
        realized_pnl=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 插入持倉
    cursor.execute(Position.get_insert_sql(), position.to_tuple())
    print(
        f"✅ 插入持倉: {position.symbol} - 數量: {position.volume} - 未實現損益: {position.unrealized_pnl}"
    )

    # 查詢持倉
    cursor.execute(
        "SELECT symbol, volume, avg_price, unrealized_pnl FROM positions WHERE symbol = %s",
        (position.symbol,),
    )
    result = cursor.fetchone()
    if result:
        print(
            f"✅ 查詢到持倉: {result[0]} - 數量: {result[1]} - 成本: {result[2]} - 未實現損益: {result[3]}"
        )

    conn.commit()
    cursor.close()


def example_risk_record_operations(conn):
    """風險記錄操作示例"""
    print("\n=== 風險記錄操作示例 ===")

    cursor = conn.cursor()

    # 創建風險記錄模型
    risk_record = RiskRecord(
        symbol="2330",
        timestamp=datetime.now(),
        risk_type="價格波動",
        risk_level="中等",
        description="股價波動超過5%",
        action_taken="調整持倉比例",
        created_at=datetime.now(),
    )

    # 插入風險記錄
    cursor.execute(RiskRecord.get_insert_sql(), risk_record.to_tuple())
    print(
        f"✅ 插入風險記錄: {risk_record.symbol} - {risk_record.risk_type} - 等級: {risk_record.risk_level}"
    )

    # 查詢風險記錄
    cursor.execute(
        "SELECT symbol, risk_type, risk_level, description FROM risk_records WHERE symbol = %s",
        (risk_record.symbol,),
    )
    result = cursor.fetchone()
    if result:
        print(
            f"✅ 查詢到風險記錄: {result[0]} - {result[1]} - 等級: {result[2]} - 描述: {result[3]}"
        )

    conn.commit()
    cursor.close()


def example_system_log_operations(conn):
    """系統日誌操作示例"""
    print("\n=== 系統日誌操作示例 ===")

    cursor = conn.cursor()

    # 創建系統日誌模型
    system_log = SystemLog(
        timestamp=datetime.now(),
        level="INFO",
        module="data_fetcher",
        message="成功獲取股票數據",
        details={"stock_id": "2330", "data_count": 1},
        created_at=datetime.now(),
    )

    # 插入系統日誌
    cursor.execute(SystemLog.get_insert_sql(), system_log.to_tuple())
    print(
        f"✅ 插入系統日誌: {system_log.level} - {system_log.module} - {system_log.message}"
    )

    # 查詢系統日誌
    cursor.execute(
        "SELECT level, module, message FROM system_logs WHERE module = %s ORDER BY timestamp DESC LIMIT 1",
        (system_log.module,),
    )
    result = cursor.fetchone()
    if result:
        print(f"✅ 查詢到系統日誌: {result[0]} - {result[1]} - {result[2]}")

    conn.commit()
    cursor.close()


def main():
    """主函數"""
    print("=== 數據庫模型使用示例 ===")

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    # 連接到數據庫
    db_config = config.get("database", {})
    conn = connect_database(db_config)
    if not conn:
        print("❌ 無法連接到數據庫")
        return

    try:
        # 執行各種操作示例
        example_stock_operations(conn)
        example_price_data_operations(conn)
        example_technical_indicator_operations(conn)
        example_trading_signal_operations(conn)
        example_trade_operations(conn)
        example_position_operations(conn)
        example_risk_record_operations(conn)
        example_system_log_operations(conn)

        print("\n✅ 所有數據庫模型操作示例完成")

    except Exception as e:
        logger.error(f"執行示例時發生錯誤: {e}")
        print(f"❌ 執行示例失敗: {e}")
    finally:
        conn.close()
        print("\n=== 數據庫模型使用示例完成 ===")


if __name__ == "__main__":
    main()
