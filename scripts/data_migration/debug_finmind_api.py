#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試 FinMind API 響應格式
"""

import requests
import json

# FinMind API 配置
api_base_url = "https://api.finmindtrade.com"
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wOC0zMCAxNjowODoxOSIsInVzZXJfaWQiOiJTaHJlZXkxMTIxIiwiaXAiOiIxODAuMTc2Ljg2LjkxIn0.mjybEoOaMhLXP1dr1rixxkQUZjfw41Gex6cshaknGaE"


def test_stock_info():
    """測試股票信息 API"""
    print("=== 測試股票信息 API ===")

    url = f"{api_base_url}/api/v4/data"
    params = {"dataset": "TaiwanStockInfo", "token": api_token}

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"狀態碼: {response.status_code}")
        print(f"響應頭: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"數據類型: {type(data)}")
            print(f"數據長度: {len(data) if isinstance(data, list) else 'N/A'}")

            if isinstance(data, list) and len(data) > 0:
                print(
                    f"第一筆數據: {json.dumps(data[0], indent=2, ensure_ascii=False)}"
                )
            else:
                print(f"完整響應: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"錯誤響應: {response.text}")

    except Exception as e:
        print(f"請求失敗: {e}")


def test_stock_price():
    """測試股票價格 API"""
    print("\n=== 測試股票價格 API ===")

    url = f"{api_base_url}/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": "0050",
        "start_date": "2025-08-29",
        "end_date": "2025-08-29",
        "token": api_token,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"狀態碼: {response.status_code}")
        print(f"響應頭: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"數據類型: {type(data)}")
            print(f"數據長度: {len(data) if isinstance(data, list) else 'N/A'}")

            if isinstance(data, list) and len(data) > 0:
                print(
                    f"第一筆數據: {json.dumps(data[0], indent=2, ensure_ascii=False)}"
                )
            else:
                print(f"完整響應: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"錯誤響應: {response.text}")

    except Exception as e:
        print(f"請求失敗: {e}")


def test_stock_price_range():
    """測試股票價格範圍 API"""
    print("\n=== 測試股票價格範圍 API ===")

    url = f"{api_base_url}/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": "0050",
        "start_date": "2025-08-25",
        "end_date": "2025-08-29",
        "token": api_token,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"狀態碼: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"數據類型: {type(data)}")
            print(f"數據長度: {len(data) if isinstance(data, list) else 'N/A'}")

            if isinstance(data, list) and len(data) > 0:
                print(f"數據筆數: {len(data)}")
                print(
                    f"第一筆數據: {json.dumps(data[0], indent=2, ensure_ascii=False)}"
                )
                if len(data) > 1:
                    print(
                        f"最後一筆數據: {json.dumps(data[-1], indent=2, ensure_ascii=False)}"
                    )
            else:
                print(f"完整響應: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"錯誤響應: {response.text}")

    except Exception as e:
        print(f"請求失敗: {e}")


if __name__ == "__main__":
    test_stock_info()
    test_stock_price()
    test_stock_price_range()
