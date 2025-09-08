# FinMind API Token 設置指南

## 獲取 FinMind API Token

1. 訪問 [FinMind 官網](https://finmindtrade.com/)
2. 註冊帳號並登入
3. 在個人中心找到 API Token
4. 複製您的 API Token

## 設置方法

### 方法1: 環境變量（推薦）

在虛擬機上設置環境變量：

```bash
export FINMIND_TOKEN="your_actual_token_here"
```

然後運行：
```bash
docker-compose -f docker-compose-simple.yml --profile migrate up data_migrate
```

### 方法2: 直接修改配置文件

編輯 `config.yaml` 文件，將第25行：
```yaml
token: ${FINMIND_TOKEN:-your_finmind_token_here}
```

改為：
```yaml
token: your_actual_token_here
```

### 方法3: 使用 .env 文件

創建 `.env` 文件：
```bash
echo "FINMIND_TOKEN=your_actual_token_here" > .env
```

## 測試連接

設置完成後，可以測試連接：

```bash
# 使用環境變量
export FINMIND_TOKEN="your_actual_token_here"
docker-compose -f docker-compose-simple.yml --profile migrate up data_migrate

# 或者直接修改配置文件後運行
docker-compose -f docker-compose-simple.yml --profile migrate up data_migrate
```

## 注意事項

- 請確保 API Token 有效且未過期
- 不要將真實的 API Token 提交到 Git 倉庫
- 建議使用環境變量的方式來保護敏感信息
