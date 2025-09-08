-- 配置pgAdmin服務器連接
-- 這個腳本需要在pgAdmin的數據庫中執行

-- 注意：這個腳本需要在pgAdmin的數據庫中執行，不是trading_system數據庫
-- 您需要手動在pgAdmin中添加服務器連接

-- 手動配置步驟：
-- 1. 訪問 http://localhost:8080
-- 2. 使用以下憑證登錄：
--    郵箱: admin@trading.com
--    密碼: admin123
-- 3. 右鍵點擊 "Servers" -> "Register" -> "Server..."
-- 4. 在 "General" 標籤頁：
--    Name: Trading System DB
-- 5. 在 "Connection" 標籤頁：
--    Host name/address: trading_system_db
--    Port: 5432
--    Maintenance database: trading_system
--    Username: trading_user
--    Password: trading_password123
--    Save password: 勾選
-- 6. 點擊 "Save"

-- 或者，您可以使用以下連接信息直接連接：
-- 主機: localhost (如果從主機連接) 或 trading_system_db (如果從Docker容器連接)
-- 端口: 5432
-- 數據庫: trading_system
-- 用戶名: trading_user
-- 密碼: trading_password123
