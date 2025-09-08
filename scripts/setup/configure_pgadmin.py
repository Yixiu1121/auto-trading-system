#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動配置pgAdmin數據庫連接腳本
"""

import requests
import json
import time
from urllib.parse import urljoin

# pgAdmin配置
PGADMIN_URL = "http://localhost:8080"
PGADMIN_EMAIL = "admin@trading.com"
PGADMIN_PASSWORD = "admin123"

# 數據庫連接配置
DB_CONFIG = {
    "name": "Trading System DB",
    "host": "trading_system_db",  # Docker容器名稱
    "port": 5432,
    "username": "trading_user",
    "password": "trading_password123",
    "database": "trading_system",
    "sslmode": "prefer",
}


def wait_for_pgadmin():
    """等待pgAdmin啟動"""
    print("等待pgAdmin啟動...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{PGADMIN_URL}/browser/", timeout=5)
            if response.status_code == 200:
                print("✅ pgAdmin已啟動")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"嘗試 {attempt + 1}/{max_attempts}...")
        time.sleep(2)

    print("❌ pgAdmin啟動超時")
    return False


def get_master_password():
    """獲取主密碼"""
    try:
        response = requests.post(
            f"{PGADMIN_URL}/browser/master_password/",
            data={"password": PGADMIN_PASSWORD},
            timeout=10,
        )
        if response.status_code == 200:
            return response.cookies.get("pgadmin_csrf_token")
    except Exception as e:
        print(f"獲取主密碼失敗: {e}")
    return None


def login_to_pgadmin():
    """登錄pgAdmin"""
    try:
        # 獲取CSRF token
        response = requests.get(f"{PGADMIN_URL}/browser/", timeout=10)
        if response.status_code != 200:
            print("❌ 無法訪問pgAdmin主頁")
            return None

        # 登錄
        login_data = {"email": PGADMIN_EMAIL, "password": PGADMIN_PASSWORD}

        session = requests.Session()
        response = session.post(f"{PGADMIN_URL}/login", data=login_data, timeout=10)

        if response.status_code == 200:
            print("✅ pgAdmin登錄成功")
            return session
        else:
            print(f"❌ pgAdmin登錄失敗: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ pgAdmin登錄異常: {e}")
        return None


def create_server_connection(session):
    """創建服務器連接"""
    try:
        # 創建服務器組
        server_group_data = {"name": "Trading System Group"}

        response = session.post(
            f"{PGADMIN_URL}/browser/server_group/", data=server_group_data, timeout=10
        )

        if response.status_code == 200:
            group_id = response.json().get("id")
            print(f"✅ 創建服務器組成功: {group_id}")
        else:
            print(f"❌ 創建服務器組失敗: {response.status_code}")
            return None

        # 創建服務器連接
        server_data = {
            "name": DB_CONFIG["name"],
            "group_id": group_id,
            "host": DB_CONFIG["host"],
            "port": DB_CONFIG["port"],
            "username": DB_CONFIG["username"],
            "password": DB_CONFIG["password"],
            "database": DB_CONFIG["database"],
            "sslmode": DB_CONFIG["sslmode"],
            "save_password": True,
        }

        response = session.post(
            f"{PGADMIN_URL}/browser/server/", data=server_data, timeout=10
        )

        if response.status_code == 200:
            server_id = response.json().get("id")
            print(f"✅ 創建服務器連接成功: {server_id}")
            return server_id
        else:
            print(f"❌ 創建服務器連接失敗: {response.status_code}")
            print(f"響應內容: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 創建服務器連接異常: {e}")
        return None


def test_connection(session, server_id):
    """測試數據庫連接"""
    try:
        response = session.get(f"{PGADMIN_URL}/browser/server/{server_id}/", timeout=10)

        if response.status_code == 200:
            print("✅ 數據庫連接測試成功")
            return True
        else:
            print(f"❌ 數據庫連接測試失敗: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 數據庫連接測試異常: {e}")
        return False


def main():
    """主函數"""
    print("🚀 開始自動配置pgAdmin...")

    # 等待pgAdmin啟動
    if not wait_for_pgadmin():
        return

    # 等待一段時間讓pgAdmin完全初始化
    print("等待pgAdmin完全初始化...")
    time.sleep(10)

    # 登錄pgAdmin
    session = login_to_pgadmin()
    if not session:
        return

    # 創建服務器連接
    server_id = create_server_connection(session)
    if not server_id:
        return

    # 測試連接
    if test_connection(session, server_id):
        print("\n🎉 pgAdmin配置完成！")
        print(f"📊 訪問地址: {PGADMIN_URL}")
        print(f"📧 登錄郵箱: {PGADMIN_EMAIL}")
        print(f"🔑 登錄密碼: {PGADMIN_PASSWORD}")
        print(f"🗄️  數據庫: {DB_CONFIG['database']}")
        print(f"🔌 主機: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    else:
        print("\n❌ pgAdmin配置失敗")


if __name__ == "__main__":
    main()
