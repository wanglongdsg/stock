# API 快速参考

## 基础信息

- **Base URL**: `http://localhost:5000`
- **认证**: Session认证（需要先登录）
- **Content-Type**: `application/json`

## 接口列表

### 1. 健康检查

```
GET /api/health
```

无需登录

**响应**:
```json
{
    "status": "ok",
    "message": "服务运行正常"
}
```

---

### 2. API信息

```
GET /api
```

无需登录

**响应**: API接口信息

---

### 3. 计算技术指标信号

```
POST /api/calculate
```

需要登录

**请求体**:
```json
{
    "period": "D",              // 必填: D|W|M
    "stock_code": "159915",     // 可选: 股票代码
    "file_path": "...",         // 可选: 数据文件路径
    "start_date": "2020-01-01", // 可选: 开始日期
    "end_date": "2025-12-31",   // 可选: 结束日期
    "buy_threshold": 10.0       // 可选: 买入阈值(0-100)
}
```

**响应字段**:
- `success`: boolean
- `period`: string
- `period_name`: string
- `total_records`: integer
- `statistics`: object
  - `buy_signals_count`: integer
  - `sell_signals_count`: integer
  - `oversold_count`: integer
  - `overbought_count`: integer
- `buy_signals`: array
- `sell_signals`: array
- `recent_data`: array

---

### 4. 回测接口

```
POST /api/backtest
```

需要登录

**请求体**:
```json
{
    // 基础参数
    "period": "D",                    // 必填: D|W|M
    "initial_amount": 100000,         // 必填: 初始资金(>0)
    "stock_code": "159915",           // 可选: 股票代码
    "file_path": "...",               // 可选: 数据文件路径
    "start_date": "2020-01-01",       // 可选: 开始日期
    "end_date": "2025-12-31",         // 可选: 结束日期
    "buy_threshold": 10.0,            // 可选: 买入阈值(0-100)
    
    // 卖出策略
    "sell_strategies": [              // 可选: 策略列表
        "stop_loss",                   // 止损策略
        "take_profit",                 // 止盈策略
        "below_ma20",                  // 20均线下方策略
        "trailing_stop_loss"           // 追踪止损策略
    ],
    "strategy_relation": "OR",        // 可选: AND|OR
    
    // 策略参数（根据选中的策略填写）
    "stop_loss_percent": 5.0,         // 止损比例(0-50)
    "take_profit_percent": 10.0,      // 止盈比例(0-200)，可选
    "below_ma20_days": 3,             // 20均线下方天数(1-30)
    "below_ma20_min_profit": 10.0,    // 20均线策略最小收益(0-200)，可选
    "trailing_stop_percent": 5.0       // 追踪止损比例(0-50)
}
```

**响应字段**:
- `success`: boolean
- `period`: string
- `period_name`: string
- `initial_amount`: float
- `final_amount`: float
- `total_profit`: float
- `total_profit_rate`: float
- `annual_profit_rate`: float
- `start_date`: string
- `end_date`: string
- `trading_days`: integer
- `total_trades`: integer
- `trades`: array
  - `buy_date`: string
  - `buy_price`: float
  - `sell_date`: string
  - `sell_price`: float
  - `shares`: float
  - `profit`: float
  - `profit_rate`: float
  - `reason`: string

---

## 卖出策略说明

### 止损策略 (stop_loss)
- **参数**: `stop_loss_percent` (默认: 5.0)
- **说明**: 当亏损达到指定比例时自动卖出

### 止盈策略 (take_profit)
- **参数**: `take_profit_percent` (可选，留空表示不设止盈)
- **说明**: 当盈利达到指定比例时自动卖出

### 20均线下方策略 (below_ma20)
- **参数**: 
  - `below_ma20_days` (默认: 3)
  - `below_ma20_min_profit` (可选)
- **说明**: 买入后上穿20均线，然后收盘价回落到20均线下方N天卖出

### 追踪止损策略 (trailing_stop_loss)
- **参数**: `trailing_stop_percent` (默认: 5.0)
- **说明**: 初始止损点设置在买入价下方，随股价上升止损点也上移

---

## 错误代码

| 错误代码 | 说明 |
|----------|------|
| UNAUTHORIZED | 未登录或登录已过期 |
| INVALID_PERIOD | 无效的周期参数 |
| MISSING_PARAMETER | 缺少必需参数 |
| INVALID_AMOUNT | 无效的金额参数 |
| NO_SELL_STRATEGY | 未选择卖出策略 |
| INVALID_STOP_LOSS | 无效的止损比例 |
| INVALID_TAKE_PROFIT | 无效的止盈比例 |
| FILE_NOT_FOUND | 数据文件未找到 |

---

## 快速示例

### cURL

```bash
# 健康检查
curl http://localhost:5000/api/health

# 计算日线信号
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"period": "D"}'

# 回测
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "period": "D",
    "initial_amount": 100000,
    "sell_strategies": ["stop_loss", "take_profit"],
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
  }'
```

### Python

```python
import requests

session = requests.Session()
# 先登录
session.post("http://localhost:5000/login", data={
    "username": "admin",
    "password": "your_password"
})

# 计算信号
response = session.post("http://localhost:5000/api/calculate", json={
    "period": "D"
})
print(response.json())

# 回测
response = session.post("http://localhost:5000/api/backtest", json={
    "period": "D",
    "initial_amount": 100000,
    "sell_strategies": ["stop_loss", "take_profit"],
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
})
print(response.json())
```

---

详细文档请查看 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
