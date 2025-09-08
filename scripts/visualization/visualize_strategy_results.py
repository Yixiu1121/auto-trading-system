#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略分析圖表
展示台積電的價格走勢、技術指標和交易信號
"""

import os
import sys
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from loguru import logger

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.modules.strategies.executor import StrategyExecutor

# 設置中文字體
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_config():
    """加載配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"配置文件 {config_path} 不存在")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def setup_logging():
    """設置日誌"""
    # 創建日誌目錄
    os.makedirs("logs", exist_ok=True)

    # 配置日誌
    logger.add(
        "logs/visualize_strategy_results.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def create_strategy_analysis_chart(
    executor: StrategyExecutor, stock_id: str, start_date: str, end_date: str
):
    """
    創建策略分析圖表

    Args:
        executor: 策略執行器
        stock_id: 股票代碼
        start_date: 開始日期
        end_date: 結束日期
    """
    try:
        # 獲取數據
        if not executor.connect_database():
            logger.error("無法連接到數據庫")
            return False

        df = executor.get_combined_data(stock_id, start_date, end_date)
        if df is None or df.empty:
            logger.error("無法獲取數據")
            return False

        # 計算額外技術指標
        df = executor.calculate_additional_indicators(df)

        # 執行策略獲取信號
        results = executor.execute_all_strategies(stock_id, start_date, end_date)

        # 創建圖表
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        fig.suptitle(
            f"台積電 ({stock_id}) 策略分析圖表\n{start_date} 到 {end_date}",
            fontsize=16,
            fontweight="bold",
        )

        # 1. 價格和均線圖
        ax1 = axes[0]

        # 繪製價格線
        ax1.plot(df["date"], df["close"], label="收盤價", linewidth=2, color="black")

        # 繪製均線
        if "blue_line" in df.columns:
            ax1.plot(
                df["date"],
                df["blue_line"],
                label="藍線 (20期)",
                linewidth=1.5,
                color="blue",
                alpha=0.8,
            )
        if "green_line" in df.columns:
            ax1.plot(
                df["date"],
                df["green_line"],
                label="綠線 (60期)",
                linewidth=1.5,
                color="green",
                alpha=0.8,
            )
        if "orange_line" in df.columns:
            ax1.plot(
                df["date"],
                df["orange_line"],
                label="橘線 (120期)",
                linewidth=1.5,
                color="orange",
                alpha=0.8,
            )

        # 標記交易信號
        for strategy_name, result in results.items():
            if result.get("success", False) and result.get("signals"):
                for signal in result["signals"]:
                    signal_date = signal["date"]
                    signal_price = signal["price"]
                    action = signal["signal"]["action"]

                    if action == "buy":
                        ax1.scatter(
                            signal_date,
                            signal_price,
                            color="red",
                            marker="^",
                            s=100,
                            label=(
                                f"{strategy_name} 買入"
                                if signal == result["signals"][0]
                                else ""
                            ),
                            zorder=5,
                        )
                    elif action == "sell":
                        ax1.scatter(
                            signal_date,
                            signal_price,
                            color="blue",
                            marker="v",
                            s=100,
                            label=(
                                f"{strategy_name} 賣出"
                                if signal == result["signals"][0]
                                else ""
                            ),
                            zorder=5,
                        )

        ax1.set_title("價格走勢與均線", fontsize=14, fontweight="bold")
        ax1.set_ylabel("價格 (元)", fontsize=12)
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)

        # 2. 成交量圖
        ax2 = axes[1]

        # 繪製成交量
        ax2.bar(df["date"], df["volume"], alpha=0.6, color="gray", width=1)

        # 繪製成交量移動平均
        if "volume_ma" in df.columns:
            ax2.plot(
                df["date"],
                df["volume_ma"],
                label="成交量均線",
                color="red",
                linewidth=1.5,
            )

        ax2.set_title("成交量", fontsize=14, fontweight="bold")
        ax2.set_ylabel("成交量", fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. 技術指標圖
        ax3 = axes[2]

        # 繪製乖離率
        if "blue_deviation" in df.columns:
            ax3.plot(
                df["date"],
                df["blue_deviation"] * 100,
                label="藍線乖離率 (%)",
                linewidth=1.5,
                color="blue",
            )
        if "green_deviation" in df.columns:
            ax3.plot(
                df["date"],
                df["green_deviation"] * 100,
                label="綠線乖離率 (%)",
                linewidth=1.5,
                color="green",
            )
        if "orange_deviation" in df.columns:
            ax3.plot(
                df["date"],
                df["orange_deviation"] * 100,
                label="橘線乖離率 (%)",
                linewidth=1.5,
                color="orange",
            )

        # 添加零線
        ax3.axhline(y=0, color="black", linestyle="--", alpha=0.5)

        ax3.set_title("乖離率", fontsize=14, fontweight="bold")
        ax3.set_ylabel("乖離率 (%)", fontsize=12)
        ax3.set_xlabel("日期", fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 設置日期格式
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # 調整布局
        plt.tight_layout()

        # 保存圖表
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        chart_path = os.path.join(
            output_dir, f"strategy_analysis_{stock_id}_{start_date}_{end_date}.png"
        )
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        logger.info(f"策略分析圖表已保存: {chart_path}")

        # 顯示圖表
        plt.show()

        return True

    except Exception as e:
        logger.error(f"創建策略分析圖表時發生錯誤: {e}")
        return False
    finally:
        executor.close_database()


def create_signal_summary_table(results: dict):
    """
    創建信號摘要表格

    Args:
        results: 策略執行結果
    """
    try:
        # 準備數據
        summary_data = []

        for strategy_name, result in results.items():
            if result.get("success", False):
                summary_data.append(
                    {
                        "策略名稱": strategy_name.replace("_", " ").title(),
                        "總信號數": result.get("total_signals", 0),
                        "買入信號": result.get("buy_signals", 0),
                        "賣出信號": result.get("sell_signals", 0),
                        "數據點數": result.get("total_data_points", 0),
                        "執行狀態": "成功" if result.get("success", False) else "失敗",
                    }
                )

        if not summary_data:
            logger.warning("沒有成功的策略結果來創建摘要表格")
            return False

        # 創建表格圖
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.axis("tight")
        ax.axis("off")

        # 創建表格
        df_summary = pd.DataFrame(summary_data)
        table = ax.table(
            cellText=df_summary.values,
            colLabels=df_summary.columns,
            cellLoc="center",
            loc="center",
            bbox=[0, 0, 1, 1],
        )

        # 設置表格樣式
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 2)

        # 設置標題行樣式
        for i in range(len(df_summary.columns)):
            table[(0, i)].set_facecolor("#4CAF50")
            table[(0, i)].set_text_props(weight="bold", color="white")

        # 設置數據行樣式
        for i in range(1, len(df_summary) + 1):
            for j in range(len(df_summary.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor("#f0f0f0")
                else:
                    table[(i, j)].set_facecolor("white")

        plt.title("策略執行摘要", fontsize=16, fontweight="bold", pad=20)

        # 保存表格
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        table_path = os.path.join(output_dir, "strategy_summary_table.png")
        plt.savefig(table_path, dpi=300, bbox_inches="tight")
        logger.info(f"策略摘要表格已保存: {table_path}")

        # 顯示表格
        plt.show()

        return True

    except Exception as e:
        logger.error(f"創建信號摘要表格時發生錯誤: {e}")
        return False


def main():
    """主函數"""
    print("=== 策略分析圖表生成工具 ===")

    # 設置日誌
    setup_logging()

    # 加載配置
    config = load_config()
    if not config:
        print("❌ 無法加載配置文件")
        return

    print("✅ 配置文件加載成功")

    try:
        # 創建策略執行器
        db_config = config.get("database", {})
        executor = StrategyExecutor(db_config)
        print("✅ 策略執行器創建成功")

        # 執行策略的股票和時間範圍
        stock_id = "2330"  # 台積電
        end_date = "2025-08-29"  # 結束日期
        start_date = "2024-01-01"  # 開始日期 (最近一年)

        print(f"\n--- 生成圖表參數 ---")
        print(f"股票代碼: {stock_id}")
        print(f"時間範圍: {start_date} 到 {end_date}")

        # 執行策略獲取結果
        print(f"\n--- 執行策略獲取信號 ---")
        results = executor.execute_all_strategies(stock_id, start_date, end_date)

        # 顯示策略執行結果摘要
        print(f"\n--- 策略執行結果摘要 ---")
        for strategy_name, result in results.items():
            if result.get("success", False):
                print(f"{strategy_name}: {result.get('total_signals', 0)} 個信號")
            else:
                print(f"{strategy_name}: 執行失敗 - {result.get('error', '未知錯誤')}")

        # 創建策略分析圖表
        print(f"\n--- 生成策略分析圖表 ---")
        chart_success = create_strategy_analysis_chart(
            executor, stock_id, start_date, end_date
        )

        if chart_success:
            print("✅ 策略分析圖表生成成功")
        else:
            print("❌ 策略分析圖表生成失敗")

        # 創建信號摘要表格
        print(f"\n--- 生成信號摘要表格 ---")
        table_success = create_signal_summary_table(results)

        if table_success:
            print("✅ 信號摘要表格生成成功")
        else:
            print("❌ 信號摘要表格生成失敗")

        print(f"\n=== 圖表生成完成 ===")
        print(f"圖表文件保存在 output/ 目錄中")

    except Exception as e:
        logger.error(f"圖表生成過程中發生錯誤: {e}")
        print(f"❌ 圖表生成失敗: {e}")

    print(f"\n=== 策略分析圖表生成完成 ===")


if __name__ == "__main__":
    main()
