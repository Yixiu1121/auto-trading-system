#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試PostgreSQL數據庫連接和表結構
"""

import psycopg2
from psycopg2 import Error
import sys

# 數據庫連接配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "trading_system",
    "user": "trading_user",
    "password": "trading_password123",
}


def test_connection():
    """測試數據庫連接"""
    try:
        print("🔌 測試數據庫連接...")
        connection = psycopg2.connect(**DB_CONFIG)

        if connection:
            print("✅ 數據庫連接成功！")
            return connection
        else:
            print("❌ 數據庫連接失敗")
            return None

    except Error as e:
        print(f"❌ 數據庫連接錯誤: {e}")
        return None


def check_tables(connection):
    """檢查數據庫表"""
    try:
        cursor = connection.cursor()

        # 查詢所有表
        cursor.execute(
            """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )

        tables = cursor.fetchall()

        print(f"\n📊 數據庫表結構 ({len(tables)} 個表):")
        print("-" * 50)

        for table_name, table_type in tables:
            print(f"  {table_name:<25} ({table_type})")

        return tables

    except Error as e:
        print(f"❌ 查詢表結構錯誤: {e}")
        return []


def check_sample_data(connection):
    """檢查示例數據"""
    try:
        cursor = connection.cursor()

        print(f"\n📈 檢查示例數據:")
        print("-" * 50)

        # 檢查股票數據
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        print(f"  股票數量: {stock_count}")

        if stock_count > 0:
            cursor.execute("SELECT symbol, name, sector FROM stocks LIMIT 5")
            stocks = cursor.fetchall()
            print("  示例股票:")
            for symbol, name, sector in stocks:
                print(f"    {symbol} - {name} ({sector})")

        # 檢查系統日誌
        cursor.execute("SELECT COUNT(*) FROM system_logs")
        log_count = cursor.fetchone()[0]
        print(f"  系統日誌數量: {log_count}")

        if log_count > 0:
            cursor.execute(
                "SELECT level, message, timestamp FROM system_logs ORDER BY timestamp DESC LIMIT 3"
            )
            logs = cursor.fetchall()
            print("  最新日誌:")
            for level, message, timestamp in logs:
                print(f"    [{level}] {message} - {timestamp}")

        return True

    except Error as e:
        print(f"❌ 檢查示例數據錯誤: {e}")
        return False


def check_views(connection):
    """檢查視圖"""
    try:
        cursor = connection.cursor()

        print(f"\n👁️  檢查視圖:")
        print("-" * 50)

        # 查詢視圖
        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )

        views = cursor.fetchall()

        if views:
            print(f"  視圖數量: {len(views)}")
            for (view_name,) in views:
                print(f"    {view_name}")
        else:
            print("  沒有找到視圖")

        return True

    except Error as e:
        print(f"❌ 檢查視圖錯誤: {e}")
        return False


def main():
    """主函數"""
    print("🚀 開始測試PostgreSQL數據庫...")

    # 測試連接
    connection = test_connection()
    if not connection:
        print("❌ 無法連接到數據庫，請檢查服務是否運行")
        sys.exit(1)

    try:
        # 檢查表結構
        tables = check_tables(connection)

        # 檢查示例數據
        check_sample_data(connection)

        # 檢查視圖
        check_views(connection)

        print(f"\n🎉 數據庫測試完成！")
        print(f"📊 總共找到 {len(tables)} 個表")
        print(
            f"🔌 連接信息: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )

    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

    finally:
        if connection:
            connection.close()
            print("🔌 數據庫連接已關閉")


if __name__ == "__main__":
    main()
