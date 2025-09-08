#!/usr/bin/env python3
"""
詳細的富邦證券登入測試
"""

import sys
import os
import yaml

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_detailed_login():
    """詳細的登入測試"""
    print("=" * 60)
    print("詳細的富邦證券登入測試")
    print("=" * 60)

    try:
        from fubon_neo.sdk import FubonSDK

        # 直接使用 SDK 進行登入測試
        print("1. 創建 SDK 實例...")
        # 先嘗試 v2.2.1 後的方式
        try:
            sdk = FubonSDK(30, 2, url="wss://neoapitest.fbs.com.tw/TASP/XCPXWS")
            print("✓ SDK 實例創建成功 (v2.2.1+ 方式)")
        except Exception as e:
            print(f"v2.2.1+ 方式失敗: {e}")
            # 嘗試 v2.2.0 以前的方式
            try:
                sdk = FubonSDK(url="wss://neoapitest.fbs.com.tw/TASP/XCPXWS")
                print("✓ SDK 實例創建成功 (v2.2.0 以前方式)")
            except Exception as e2:
                print(f"v2.2.0 以前方式也失敗: {e2}")
                raise e2

        # 登入參數
        account_id = "41610792"  # 使用你提供的正確帳號
        password = "12345678"
        cert_filepath = "41610792.pfx"  # 使用對應的憑證文件
        cert_password = "12345678"

        print(f"\n2. 登入參數:")
        print(f"   帳號 ID: {account_id}")
        print(f"   密碼: {'*' * len(password)}")
        print(f"   憑證路徑: {cert_filepath}")
        print(f"   憑證密碼: {'*' * len(cert_password)}")

        # 檢查憑證文件
        if os.path.exists(cert_filepath):
            print(f"✓ 憑證文件存在: {cert_filepath}")
            print(f"   文件大小: {os.path.getsize(cert_filepath)} bytes")
        else:
            print(f"✗ 憑證文件不存在: {cert_filepath}")
            return False

        # 嘗試登入
        print(f"\n3. 嘗試登入...")
        try:
            accounts = sdk.login(account_id, password, cert_filepath, cert_password)
            print("✓ 登入調用成功")

            # 檢查登入結果
            if accounts:
                print(f"✓ 登入響應: {type(accounts)}")
                print(f"✓ 登入響應內容: {accounts}")

                # 檢查登入是否成功
                if hasattr(accounts, "is_success"):
                    print(f"✓ 登入成功狀態: {accounts.is_success}")
                    if not accounts.is_success:
                        print(f"✗ 登入失敗: {accounts.message}")
                        return False
                else:
                    print("✗ 登入響應沒有 is_success 屬性")

                if hasattr(accounts, "data"):
                    print(f"✓ 帳戶數據: {type(accounts.data)}")
                    if accounts.data:
                        print(f"✓ 帳戶數量: {len(accounts.data)}")
                        for i, account in enumerate(accounts.data):
                            print(f"   帳戶 {i+1}: {account}")
                    else:
                        print("✗ 帳戶數據為空")
                        return False
                else:
                    print(f"✗ 帳戶對象沒有 data 屬性")
                    print(f"   帳戶對象屬性: {dir(accounts)}")
                    return False
            else:
                print("✗ 登入響應為空")
                return False

        except Exception as e:
            print(f"✗ 登入調用失敗: {e}")
            import traceback

            traceback.print_exc()
            return False

        return True

    except Exception as e:
        print(f"✗ 測試過程中發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_certificate_file():
    """測試憑證文件"""
    print("\n" + "=" * 60)
    print("憑證文件測試")
    print("=" * 60)

    cert_filepath = "41610792.pfx"

    try:
        # 檢查文件基本信息
        if os.path.exists(cert_filepath):
            stat_info = os.stat(cert_filepath)
            print(f"✓ 憑證文件存在")
            print(f"   路徑: {os.path.abspath(cert_filepath)}")
            print(f"   大小: {stat_info.st_size} bytes")
            print(f"   權限: {oct(stat_info.st_mode)[-3:]}")
            print(f"   修改時間: {stat_info.st_mtime}")

            # 嘗試讀取文件
            try:
                with open(cert_filepath, "rb") as f:
                    content = f.read()
                print(f"✓ 文件可以讀取")
                print(f"   內容長度: {len(content)} bytes")
                print(f"   前16字節: {content[:16].hex()}")
            except Exception as e:
                print(f"✗ 文件讀取失敗: {e}")

        else:
            print(f"✗ 憑證文件不存在: {cert_filepath}")

    except Exception as e:
        print(f"✗ 憑證文件測試失敗: {e}")


if __name__ == "__main__":
    print("詳細的富邦證券登入測試")
    print("=" * 60)

    # 測試憑證文件
    test_certificate_file()

    # 測試詳細登入
    login_success = test_detailed_login()

    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)

    if login_success:
        print("🎉 詳細登入測試成功！")
    else:
        print("⚠️  詳細登入測試失敗")
        print("\n建議:")
        print("1. 檢查帳號密碼是否正確")
        print("2. 檢查憑證文件是否有效")
        print("3. 檢查網絡連接")
        print("4. 聯繫富邦證券確認帳號狀態")
