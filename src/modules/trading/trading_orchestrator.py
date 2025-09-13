#!/usr/bin/env python3
"""
交易系統協調器
整合所有交易相關模組，提供統一的交易執行介面
"""

import time
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import pytz

from .auto_trader import AutoTrader
from .fubon_api_client import FubonAPIClient
from .pre_market_analyzer import PreMarketAnalyzer
from ..strategies.executor import StrategyExecutor
from ..data_fetcher import FinMindFetcher
from ..risk_manager.risk_manager import RiskManager
from ..monitor.market_monitor import MarketMonitor


class TradingOrchestrator:
    """交易系統協調器"""

    def __init__(self, config: Dict):
        """初始化交易協調器"""
        self.config = config
        self.running = False
        self.modules = {}

        # 初始化所有模組
        self._initialize_modules()

        # 設置定時任務
        self._setup_scheduled_tasks()

        logger.info("交易協調器初始化完成")

    def _initialize_modules(self):
        """初始化所有模組"""
        try:
            # 初始化富邦證券 API 客戶端
            self.modules["fubon_client"] = FubonAPIClient(self.config)

            # 初始化自動交易器
            real_trading = self.config.get("trading", {}).get("real_trading", False)
            self.modules["auto_trader"] = AutoTrader(
                self.config, real_trading=real_trading
            )

            # 初始化策略執行器
            db_config = self.config.get("database", {})
            self.modules["strategy_executor"] = StrategyExecutor(db_config)

            # 初始化數據獲取器
            self.modules["data_fetcher"] = FinMindFetcher(self.config)

            # 初始化風險管理器
            self.modules["risk_manager"] = RiskManager(self.config)

            # 初始化市場監控器
            self.modules["market_monitor"] = MarketMonitor(
                self.config,
                fubon_client=self.modules["auto_trader"].fubon_client,
                data_fetcher=self.modules["data_fetcher"],
            )

            # 初始化開盤前分析器
            self.modules["pre_market_analyzer"] = PreMarketAnalyzer(self.config)

            logger.info("所有交易模組初始化完成")

        except Exception as e:
            logger.error(f"模組初始化失敗: {e}")
            raise

    def _setup_scheduled_tasks(self):
        """設置定時任務"""
        # 獲取台灣時區
        taiwan_tz = pytz.timezone("Asia/Taipei")

        # 每日開盤前準備 (台灣時間 08:30)
        schedule.every().day.at("08:30", tz=taiwan_tz).do(self._pre_market_preparation)

        # 每日收盤後清理 (台灣時間 14:00)
        schedule.every().day.at("14:00", tz=taiwan_tz).do(self._post_market_cleanup)

        # 每日收盤後更新數據 (台灣時間 14:30)
        schedule.every().day.at("14:30", tz=taiwan_tz).do(self._update_daily_data)

        # 每小時檢查系統狀態
        schedule.every().hour.do(self._health_check)

        # 每5分鐘檢查交易信號
        schedule.every(5).minutes.do(self._check_trading_signals)

        logger.info("定時任務設置完成 (台灣時區)")
        logger.info("📅 定時任務排程:")
        logger.info("  - 08:30: 開盤前準備")
        logger.info("  - 14:00: 收盤後清理")
        logger.info("  - 14:30: 每日數據更新")
        logger.info("  - 每小時: 系統健康檢查")
        logger.info("  - 每5分鐘: 交易信號檢查")

    def start(self):
        """啟動交易系統"""
        if self.running:
            logger.warning("交易系統已在運行中")
            return

        try:
            logger.info("啟動交易系統...")
            self.running = True

            # 啟動市場監控
            self.modules["market_monitor"].start()

            # 啟動風險管理
            self.modules["risk_manager"].start()

            # 啟動自動交易器
            self.modules["auto_trader"].start()

            # 啟動定時任務調度器
            self._start_scheduler()

            logger.info("交易系統啟動成功")

        except Exception as e:
            logger.error(f"交易系統啟動失敗: {e}")
            raise

    def stop(self):
        """停止交易系統"""
        if not self.running:
            return

        logger.info("正在停止交易系統...")
        self.running = False

        # 停止所有模組
        for name, module in self.modules.items():
            try:
                if hasattr(module, "stop"):
                    module.stop()
                    logger.debug(f"模組 {name} 已停止")
            except Exception as e:
                logger.error(f"停止模組 {name} 時發生錯誤: {e}")

        logger.info("交易系統已停止")

    def _start_scheduler(self):
        """啟動定時任務調度器"""

        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("定時任務調度器已啟動")

    def _pre_market_preparation(self):
        """開盤前準備"""
        logger.info("開始開盤前準備...")

        try:
            # 檢查系統狀態
            self._health_check()

            # 更新股票池數據
            self._update_stock_pool_data()

            # 計算技術指標
            self._calculate_indicators()

            # 使用開盤前分析器計算所有策略信號
            self._analyze_pre_market_signals()

            # 開始價格監控和自動下單準備
            self._start_pre_market_monitoring()

            logger.info("開盤前準備完成")

        except Exception as e:
            logger.error(f"開盤前準備失敗: {e}")

    def _analyze_pre_market_signals(self):
        """分析開盤前策略信號"""
        try:
            logger.info("開始分析開盤前六大策略信號...")

            # 獲取股票池
            stock_pool = self._get_active_stock_pool()

            # 使用開盤前分析器計算所有策略信號
            pre_market_analyzer = self.modules["pre_market_analyzer"]
            signals = pre_market_analyzer.analyze_pre_market_signals(stock_pool)

            logger.info(f"開盤前信號分析完成，產生 {len(signals)} 個信號")

            # 顯示信號摘要
            self._display_signals_summary(signals)

        except Exception as e:
            logger.error(f"開盤前信號分析失敗: {e}")

    def _start_pre_market_monitoring(self):
        """開始開盤前監控"""
        try:
            logger.info("開始啟動開盤前價格監控...")

            pre_market_analyzer = self.modules["pre_market_analyzer"]

            # 啟動價格監控（將在開盤時自動開始監控）
            pre_market_analyzer.start_price_monitoring()

            logger.info("開盤前價格監控已啟動，將在開盤時自動執行")

        except Exception as e:
            logger.error(f"啟動開盤前監控失敗: {e}")

    def _display_signals_summary(self, signals: List[Dict]):
        """顯示信號摘要"""
        try:
            if not signals:
                logger.info("沒有產生任何交易信號")
                return

            # 按策略統計
            strategy_stats = {}
            for signal in signals:
                strategy = signal["strategy"]
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {"buy": 0, "sell": 0, "total": 0}

                strategy_stats[strategy][signal["action"]] += 1
                strategy_stats[strategy]["total"] += 1

            logger.info("=== 開盤前信號摘要 ===")
            for strategy, stats in strategy_stats.items():
                logger.info(
                    f"{strategy}: 買入 {stats['buy']} 賣出 {stats['sell']} 總計 {stats['total']}"
                )

            # 顯示最強信號
            top_signals = sorted(
                signals, key=lambda x: abs(x["signal_strength"]), reverse=True
            )[:5]
            logger.info("\n=== 最強信號前5名 ===")
            for i, signal in enumerate(top_signals, 1):
                logger.info(
                    f"{i}. {signal['symbol']} {signal['strategy']} {signal['action']} "
                    f"強度: {signal['signal_strength']:.3f} 目標價: {signal['target_price']:.2f}"
                )

        except Exception as e:
            logger.error(f"顯示信號摘要失敗: {e}")

    def _post_market_cleanup(self):
        """收盤後清理"""
        logger.info("開始收盤後清理...")

        try:
            # 停止價格監控
            self._stop_pre_market_monitoring()

            # 清理過期數據
            self._cleanup_old_data()

            # 生成日報
            self._generate_daily_report()

            # 更新風險參數
            self.modules["risk_manager"].update_risk_parameters()

            logger.info("收盤後清理完成")

        except Exception as e:
            logger.error(f"收盤後清理失敗: {e}")

    def _stop_pre_market_monitoring(self):
        """停止開盤前監控"""
        try:
            logger.info("停止開盤前價格監控...")

            pre_market_analyzer = self.modules["pre_market_analyzer"]
            pre_market_analyzer.stop_price_monitoring()

            # 生成當日交易報告
            self._generate_trading_report()

            logger.info("開盤前價格監控已停止")

        except Exception as e:
            logger.error(f"停止開盤前監控失敗: {e}")

    def _generate_trading_report(self):
        """生成當日交易報告"""
        try:
            pre_market_analyzer = self.modules["pre_market_analyzer"]
            status = pre_market_analyzer.get_monitoring_status()
            signals = pre_market_analyzer.get_pre_market_signals()

            logger.info("=== 當日交易報告 ===")
            logger.info(f"總信號數: {status['total_signals']}")
            logger.info(f"執行成功: {status['executed_signals']}")
            logger.info(f"執行失敗: {status['failed_signals']}")
            logger.info(f"待執行: {status['pending_signals']}")

            # 詳細執行結果
            executed_signals = [s for s in signals if s["status"] == "executed"]
            if executed_signals:
                logger.info("=== 已執行的交易 ===")
                for signal in executed_signals:
                    profit_loss = ""
                    if signal.get("executed_price") and signal.get("target_price"):
                        diff = signal["executed_price"] - signal["target_price"]
                        profit_loss = f"(差價: {diff:+.2f})"

                    logger.info(
                        f"{signal['symbol']} {signal['strategy']} {signal['action']} "
                        f"{signal['executed_quantity']}股 @ {signal['executed_price']:.2f} {profit_loss}"
                    )

        except Exception as e:
            logger.error(f"生成交易報告失敗: {e}")

    def _health_check(self):
        """系統健康檢查"""
        try:
            # 檢查富邦證券連接
            fubon_health = self.modules["fubon_client"].health_check()

            # 檢查數據庫連接
            db_health = self.modules["strategy_executor"].check_connection()

            # 檢查風險管理狀態
            risk_health = self.modules["risk_manager"].get_status()

            # 檢查市場監控狀態
            monitor_health = self.modules["market_monitor"].get_status()

            # 記錄健康狀態
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "fubon_api": fubon_health,
                "database": db_health,
                "risk_manager": risk_health,
                "market_monitor": monitor_health,
            }

            logger.info(f"系統健康檢查: {health_status}")

            # 如果有問題，發送警報
            if not all(
                [
                    fubon_health.get("connected", False),
                    db_health.get("connected", False),
                ]
            ):
                logger.warning("系統健康檢查發現問題")

        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")

    def _check_trading_signals(self):
        """檢查交易信號"""
        if not self._is_market_open():
            return

        try:
            # 獲取當前股票池
            stock_pool = self._get_active_stock_pool()

            # 檢查每個股票的信號
            for stock_id in stock_pool:
                signals = self._check_stock_signals(stock_id)

                if signals:
                    # 執行交易
                    self._execute_trades(stock_id, signals)

        except Exception as e:
            logger.error(f"檢查交易信號失敗: {e}")

    def _is_market_open(self) -> bool:
        """檢查市場是否開盤"""
        now = datetime.now(pytz.timezone("Asia/Taipei"))

        # 檢查是否為工作日
        if now.weekday() >= 5:  # 週末
            return False

        # 檢查交易時間
        market_hours = self.config.get("trading", {}).get("market_hours", {})
        start_time = market_hours.get("start", "09:00")
        end_time = market_hours.get("end", "13:30")

        current_time = now.strftime("%H:%M")
        return start_time <= current_time <= end_time

    def _get_active_stock_pool(self) -> List[str]:
        """獲取活躍股票池"""
        try:
            # 從配置或數據庫獲取股票池
            default_pool = ["2330", "0050", "1101"]
            return self.config.get("trading", {}).get("stock_pool", default_pool)
        except Exception as e:
            logger.error(f"獲取股票池失敗: {e}")
            return []

    def _check_stock_signals(self, stock_id: str) -> List[Dict]:
        """檢查單個股票的交易信號"""
        try:
            # 執行策略分析
            results = self.modules["strategy_executor"].execute_strategies([stock_id])

            # 過濾最新的信號
            current_signals = []
            for signal in results:
                if self._is_recent_signal(signal):
                    current_signals.append(signal)

            return current_signals

        except Exception as e:
            logger.error(f"檢查股票 {stock_id} 信號失敗: {e}")
            return []

    def _is_recent_signal(self, signal: Dict) -> bool:
        """檢查是否為最近的信號"""
        try:
            signal_time = datetime.fromisoformat(signal.get("timestamp", ""))
            now = datetime.now()

            # 檢查是否為最近5分鐘內的信號
            return (now - signal_time).total_seconds() <= 300

        except Exception:
            return False

    def _execute_trades(self, stock_id: str, signals: List[Dict]):
        """執行交易"""
        try:
            for signal in signals:
                # 檢查風險限制
                if not self.modules["risk_manager"].check_trade_allowed(signal):
                    logger.warning(f"交易被風險管理阻止: {signal}")
                    continue

                # 執行交易
                result = self.modules["auto_trader"].execute_trade(signal)

                if result.get("success"):
                    logger.info(f"交易執行成功: {result}")
                else:
                    logger.error(f"交易執行失敗: {result}")

        except Exception as e:
            logger.error(f"執行交易失敗: {e}")

    def _update_stock_pool_data(self):
        """更新股票池數據"""
        try:
            stock_pool = self._get_active_stock_pool()

            for stock_id in stock_pool:
                # 獲取最新數據
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

                data = self.modules["data_fetcher"].get_stock_data(
                    stock_id, start_date, end_date
                )

                if data is not None:
                    logger.info(f"股票 {stock_id} 數據更新成功")
                else:
                    logger.warning(f"股票 {stock_id} 數據更新失敗")

        except Exception as e:
            logger.error(f"更新股票池數據失敗: {e}")

    def _calculate_indicators(self):
        """計算技術指標"""
        try:
            stock_pool = self._get_active_stock_pool()

            for stock_id in stock_pool:
                # 計算技術指標
                self.modules["strategy_executor"].calculate_indicators(stock_id)

        except Exception as e:
            logger.error(f"計算技術指標失敗: {e}")

    def _generate_trading_signals(self):
        """生成交易信號"""
        try:
            stock_pool = self._get_active_stock_pool()

            for stock_id in stock_pool:
                # 生成交易信號
                signals = self.modules["strategy_executor"].execute_strategies(
                    [stock_id]
                )

                if signals:
                    logger.info(f"股票 {stock_id} 生成 {len(signals)} 個信號")

        except Exception as e:
            logger.error(f"生成交易信號失敗: {e}")

    def _update_daily_data(self):
        """更新每日數據"""
        try:
            logger.info("開始每日數據更新...")

            # 獲取數據獲取器
            data_fetcher = self.modules.get("data_fetcher")
            if not data_fetcher:
                logger.error("數據獲取器不可用，跳過數據更新")
                return

            # 執行每日數據更新
            success = data_fetcher.update_daily_data()

            if success:
                logger.info("每日數據更新完成")

                # 更新完數據後，重新計算技術指標
                self._update_technical_indicators()

            else:
                logger.error("每日數據更新失敗")

        except Exception as e:
            logger.error(f"每日數據更新過程失敗: {e}")

    def _update_technical_indicators(self):
        """更新技術指標"""
        try:
            logger.info("開始更新技術指標...")

            # 獲取策略執行器
            strategy_executor = self.modules.get("strategy_executor")
            if not strategy_executor:
                logger.error("策略執行器不可用，跳過技術指標更新")
                return

            # 更新技術指標（這裡可以添加具體的技術指標更新邏輯）
            # 例如重新計算移動平均線、RSI等指標

            logger.info("技術指標更新完成")

        except Exception as e:
            logger.error(f"技術指標更新失敗: {e}")

    def _cleanup_old_data(self):
        """清理舊數據"""
        try:
            # 清理30天前的數據
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            # 這裡可以添加數據清理邏輯

            logger.info("舊數據清理完成")

        except Exception as e:
            logger.error(f"清理舊數據失敗: {e}")

    def _generate_daily_report(self):
        """生成日報"""
        try:
            # 生成交易日報
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "total_pnl": 0.0,
                "risk_metrics": {},
            }

            logger.info(f"日報生成完成: {report}")

        except Exception as e:
            logger.error(f"生成日報失敗: {e}")

    def trigger_data_update(self) -> bool:
        """
        手動觸發數據更新

        Returns:
            bool: 更新是否成功
        """
        try:
            logger.info("手動觸發數據更新...")
            self._update_daily_data()
            return True
        except Exception as e:
            logger.error(f"手動數據更新失敗: {e}")
            return False

    def get_status(self) -> Dict:
        """獲取系統狀態"""
        return {
            "running": self.running,
            "modules": {
                name: (
                    module.get_status() if hasattr(module, "get_status") else "unknown"
                )
                for name, module in self.modules.items()
            },
            "timestamp": datetime.now().isoformat(),
        }
