-- 自動化程式交易系統數據庫初始化腳本
-- 創建所有必要的表結構

-- 啟用UUID擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 股票基本信息表
CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    market_cap DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 股價數據表
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10,4) NOT NULL,
    high DECIMAL(10,4) NOT NULL,
    low DECIMAL(10,4) NOT NULL,
    close DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    period VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE,
    UNIQUE(symbol, timestamp, period)
);

-- 技術指標表
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    blue_line DECIMAL(10,4),  -- 小藍線（月線）
    green_line DECIMAL(10,4),  -- 小綠線（季線）
    orange_line DECIMAL(10,4), -- 小橘線（年線）
    rsi DECIMAL(5,2),          -- RSI指標
    macd DECIMAL(10,4),        -- MACD線
    macd_signal DECIMAL(10,4), -- MACD信號線
    macd_histogram DECIMAL(10,4), -- MACD柱狀圖
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE,
    UNIQUE(symbol, timestamp)
);

-- 交易信號表
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'buy', 'sell'
    strategy VARCHAR(50) NOT NULL,    -- 'blue_bull', 'blue_bear', 'green_bull', 'green_bear', 'orange_bull', 'orange_bear'
    strength DECIMAL(3,2) NOT NULL,   -- 信號強度 0.0-1.0
    price DECIMAL(10,4) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'executed', 'cancelled', 'expired'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

-- 交易記錄表
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER,
    symbol VARCHAR(10) NOT NULL,
    trade_type VARCHAR(20) NOT NULL, -- 'buy', 'sell'
    quantity INTEGER NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'filled', 'cancelled', 'rejected'
    order_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE,
    FOREIGN KEY (signal_id) REFERENCES trading_signals (id) ON DELETE SET NULL
);

-- 持倉表
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(10,4) NOT NULL,
    current_price DECIMAL(10,4),
    unrealized_pnl DECIMAL(12,2) DEFAULT 0,
    realized_pnl DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'closed'
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

-- 風險控制記錄表
CREATE TABLE IF NOT EXISTS risk_records (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    risk_type VARCHAR(50) NOT NULL, -- 'stop_loss', 'take_profit', 'position_limit'
    trigger_price DECIMAL(10,4) NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'close_position', 'reduce_position', 'alert'
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'ignored'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

-- 系統日誌表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    module VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引以提高查詢性能
CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timestamp ON price_data (symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_price_data_period ON price_data (period);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_timestamp ON technical_indicators (symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_timestamp ON trading_signals (symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_trading_signals_status ON trading_signals (status);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades (symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades (status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions (symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions (status);
CREATE INDEX IF NOT EXISTS idx_risk_records_symbol ON risk_records (symbol);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs (level);

-- 創建視圖：當前持倉摘要
CREATE OR REPLACE VIEW current_positions_summary AS
SELECT 
    symbol,
    SUM(quantity) as total_quantity,
    AVG(avg_price) as weighted_avg_price,
    SUM(quantity * avg_price) as total_cost,
    SUM(unrealized_pnl) as total_unrealized_pnl,
    SUM(realized_pnl) as total_realized_pnl
FROM positions 
WHERE status = 'active' 
GROUP BY symbol;

-- 創建視圖：交易信號統計
CREATE OR REPLACE VIEW trading_signals_summary AS
SELECT 
    strategy,
    signal_type,
    COUNT(*) as signal_count,
    AVG(strength) as avg_strength,
    COUNT(CASE WHEN status = 'executed' THEN 1 END) as executed_count,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
FROM trading_signals 
GROUP BY strategy, signal_type;

-- 插入一些示例股票數據
INSERT INTO stocks (symbol, name, sector) VALUES 
    ('2330', '台積電', '半導體'),
    ('2317', '鴻海', '電子零組件'),
    ('2454', '聯發科', '半導體'),
    ('2412', '中華電', '電信服務'),
    ('1301', '台塑', '塑膠')
ON CONFLICT (symbol) DO NOTHING;

-- 創建更新時間戳的觸發器函數
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 為stocks表創建觸發器
CREATE TRIGGER update_stocks_updated_at 
    BEFORE UPDATE ON stocks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 創建分區表（用於大量歷史數據）
-- 按月分區的股價數據表
CREATE TABLE IF NOT EXISTS price_data_partitioned (
    id SERIAL,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10,4) NOT NULL,
    high DECIMAL(10,4) NOT NULL,
    low DECIMAL(10,4) NOT NULL,
    close DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    period VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- 創建當前月份的分區
CREATE TABLE IF NOT EXISTS price_data_2024_01 PARTITION OF price_data_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS price_data_2024_02 PARTITION OF price_data_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 為分區表創建索引
CREATE INDEX IF NOT EXISTS idx_price_data_partitioned_symbol_timestamp ON price_data_partitioned (symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_price_data_partitioned_period ON price_data_partitioned (period);

-- 創建性能優化的物化視圖
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_price_summary AS
SELECT 
    symbol,
    DATE(timestamp) as trade_date,
    MIN(low) as daily_low,
    MAX(high) as daily_high,
    FIRST(open_price, timestamp) as daily_open,
    LAST(close, timestamp) as daily_close,
    SUM(volume) as daily_volume
FROM price_data 
GROUP BY symbol, DATE(timestamp)
ORDER BY symbol, trade_date;

-- 創建唯一索引以支持並發刷新
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_price_summary_symbol_date ON daily_price_summary (symbol, trade_date);

-- 插入初始系統日誌
INSERT INTO system_logs (level, message, module) VALUES 
    ('INFO', '數據庫初始化完成', 'database'),
    ('INFO', '表結構創建完成', 'database'),
    ('INFO', '索引創建完成', 'database');
