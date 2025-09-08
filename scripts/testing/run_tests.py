#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試運行腳本
運行所有模組的測試
"""

import sys
import os
import unittest
from pathlib import Path

# 添加src目錄到Python路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def run_all_tests():
    """運行所有測試"""
    print("🚀 開始運行自動化程式交易系統測試...")
    print("=" * 60)

    # 發現並運行測試
    loader = unittest.TestLoader()
    start_dir = src_path / "tests"

    if not start_dir.exists():
        print("❌ 測試目錄不存在")
        return False

    # 發現測試套件
    suite = loader.discover(start_dir, pattern="test_*.py")

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 輸出測試結果摘要
    print("=" * 60)
    print("📊 測試結果摘要:")
    print(f"  運行測試: {result.testsRun}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  錯誤: {len(result.errors)}")
    print(f"  跳過: {len(result.skipped)}")

    if result.failures:
        print("\n❌ 失敗的測試:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n💥 錯誤的測試:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

    # 返回測試是否全部通過
    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️  有 {len(result.failures) + len(result.errors)} 個測試失敗")

    return success


def run_specific_test(test_name):
    """運行特定測試"""
    print(f"🎯 運行特定測試: {test_name}")

    # 構建測試路徑
    test_path = src_path / "tests" / f"test_{test_name}.py"

    if not test_path.exists():
        print(f"❌ 測試文件不存在: {test_path}")
        return False

    # 運行特定測試
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f"test_{test_name}")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return len(result.failures) == 0 and len(result.errors) == 0


def main():
    """主函數"""
    if len(sys.argv) > 1:
        # 運行特定測試
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # 運行所有測試
        success = run_all_tests()

    # 設置退出碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
