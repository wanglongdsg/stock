# 股票技术指标计算 API 完整文档

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [认证说明](#认证说明)
- [API 接口](#api-接口)
  - [1. 健康检查](#1-健康检查)
  - [2. API信息](#2-api信息)
  - [3. 计算技术指标信号](#3-计算技术指标信号)
  - [4. 回测接口](#4-回测接口)
- [数据格式](#数据格式)
- [错误处理](#错误处理)
- [示例代码](#示例代码)
- [技术指标说明](#技术指标说明)

---

## 概述

股票技术指标计算 API 提供基于通达信公式的股票技术分析服务，支持：

- **技术指标计算**：支撑位、阻力位、趋势线等
- **买卖信号识别**：自动识别买入和卖出信号
- **多周期支持**：日线、周线、月线
- **回测功能**：基于历史数据的策略回测，支持多种卖出策略

### 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **请求方法**: `POST` (除健康检查和API信息外)
- **认证方式**: Session认证（需要先登录）

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

**重要提示**：启动时会在控制台显示登录账号和密码，请妥善保存。

### 3. 登录获取Session

所有API接口（除健康检查外）都需要登录后才能访问。可以通过Web界面登录，或使用以下方式：

```bash
# 使用curl登录（需要先访问登录页面获取CSRF token）
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password" \
  -c cookies.txt
```

### 4. 测试连接

```bash
# 健康检查（无需登录）
curl http://localhost:5000/api/health
```

---

## 认证说明

### 登录方式

1. **Web界面登录**：
   - 访问 `http://localhost:5000/login`
   - 输入账号和密码（启动时在控制台显示）
   - 登录成功后会自动设置Session

2. **API登录**：
   - 使用POST请求到 `/login` 接口
   - 成功后返回Session Cookie

### 默认账号

- **账号**：`admin`（可通过环境变量 `LOGIN_USERNAME` 修改）
- **密码**：启动时随机生成（可通过环境变量 `LOGIN_PASSWORD` 设置）

### Session使用

登录成功后，后续API请求需要携带Session Cookie：

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"period": "D"}'
```

---

## API 接口

### 1. 健康检查

检查服务运行状态，无需登录。

**接口地址**: `GET /api/health`

**请求示例**:
```bash
curl http://localhost:5000/api/health
```

**响应示例**:
```json
{
    "status": "ok",
    "message": "服务运行正常"
}
```

---

### 2. API信息

获取API接口信息，无需登录。

**接口地址**: `GET /api`

**请求示例**:
```bash
curl http://localhost:5000/api
```

**响应示例**:
```json
{
    "name": "股票技术指标计算 API",
    "version": "1.0.0",
    "description": "提供股票技术指标计算服务，支持日线、周线、月线信号查询和回测",
    "endpoints": {
        "/api/health": {
            "method": "GET",
            "description": "健康检查接口"
        },
        "/api/calculate": {
            "method": "POST",
            "description": "计算股票技术指标信号"
        },
        "/api/backtest": {
            "method": "POST",
            "description": "回测接口：按照买卖信号进行全仓回测"
        }
    }
}
```

---

### 3. 计算技术指标信号

计算指定周期的技术指标和买卖信号。

**接口地址**: `POST /api/calculate`

**认证**: 需要登录

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
    "period": "D",
    "stock_code": "159915",
    "file_path": "data/159915.xlsx",
    "start_date": "2020-01-01",
    "end_date": "2025-12-31",
    "buy_threshold": 10.0
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period | string | 是 | 周期类型：`D`(日线)、`W`(周线)、`M`(月线) |
| stock_code | string | 否 | 股票代码，默认为 `159915` |
| file_path | string | 否 | 数据文件路径，默认为 `data/{stock_code}.xlsx` |
| start_date | string | 否 | 开始日期（格式：`YYYY-MM-DD`），可选 |
| end_date | string | 否 | 结束日期（格式：`YYYY-MM-DD`），可选 |
| buy_threshold | float | 否 | 买入信号阈值，默认 `10.0`（0-100之间） |

**请求示例**:

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "period": "D",
    "stock_code": "159915",
    "buy_threshold": 10.0
  }'
```

**响应示例** (成功):
```json
{
    "success": true,
    "period": "D",
    "period_name": "日线",
    "total_records": 1260,
    "statistics": {
        "buy_signals_count": 40,
        "sell_signals_count": 21,
        "oversold_count": 98,
        "overbought_count": 44
    },
    "buy_signals": [
        {
            "date": "2020-11-17",
            "close": 312.67,
            "trend_line": 14.163019
        }
    ],
    "sell_signals": [
        {
            "date": "2020-10-27",
            "close": 336.08,
            "trend_line": 89.053592
        }
    ],
    "recent_data": [
        {
            "date": "2025-12-03",
            "close": 199.5,
            "支撑": 200.3275,
            "阻力": 201.985,
            "中线": 201.15625,
            "趋势线": 84.243741,
            "买": 0,
            "卖": 0
        }
    ]
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| period | string | 周期类型 |
| period_name | string | 周期名称 |
| total_records | integer | 总记录数 |
| statistics | object | 统计信息 |
| statistics.buy_signals_count | integer | 买入信号次数 |
| statistics.sell_signals_count | integer | 卖出信号次数 |
| statistics.oversold_count | integer | 超卖区次数 |
| statistics.overbought_count | integer | 超买区次数 |
| buy_signals | array | 买入信号列表 |
| buy_signals[].date | string | 买入信号日期 |
| buy_signals[].close | float | 收盘价 |
| buy_signals[].trend_line | float | 趋势线值 |
| sell_signals | array | 卖出信号列表（格式同买入信号） |
| recent_data | array | 最近20条关键指标数据 |

**错误响应**:
```json
{
    "success": false,
    "error": "无效的周期参数: X，支持的值: D(日线), W(周线), M(月线)",
    "error_code": "INVALID_PERIOD"
}
```

---

### 4. 回测接口

按照买卖信号进行全仓回测，支持多种卖出策略组合。

**接口地址**: `POST /api/backtest`

**认证**: 需要登录

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
    "period": "D",
    "initial_amount": 100000,
    "stock_code": "159915",
    "file_path": "data/159915.xlsx",
    "start_date": "2020-01-01",
    "end_date": "2025-12-31",
    "buy_threshold": 10.0,
    "sell_strategies": ["stop_loss", "take_profit", "below_ma20"],
    "strategy_relation": "OR",
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0,
    "below_ma20_days": 3,
    "below_ma20_min_profit": 10.0,
    "trailing_stop_percent": 5.0
}
```

**参数说明**:

#### 基础参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period | string | 是 | 周期类型：`D`(日线)、`W`(周线)、`M`(月线) |
| initial_amount | float | 是 | 初始资金金额，必须大于0 |
| stock_code | string | 否 | 股票代码，默认为 `159915` |
| file_path | string | 否 | 数据文件路径，默认为 `data/{stock_code}.xlsx` |
| start_date | string | 否 | 开始日期（格式：`YYYY-MM-DD`），可选 |
| end_date | string | 否 | 结束日期（格式：`YYYY-MM-DD`），可选 |
| buy_threshold | float | 否 | 买入信号阈值，默认 `10.0`（0-100之间） |

#### 卖出策略参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sell_strategies | array | 否 | 卖出策略列表，默认 `["stop_loss", "take_profit", "below_ma20"]`<br>可选值：`stop_loss`、`take_profit`、`below_ma20`、`trailing_stop_loss` |
| strategy_relation | string | 否 | 策略关系，默认 `OR`<br>`OR`：任一策略触发即卖出<br>`AND`：所有策略都触发才卖出 |
| stop_loss_percent | float | 条件必填 | 止损比例（%），当选中 `stop_loss` 策略时必填，默认 `5.0`（0-50之间） |
| take_profit_percent | float | 条件必填 | 止盈比例（%），当选中 `take_profit` 策略时可选，留空表示不设止盈（0-200之间） |
| below_ma20_days | integer | 条件必填 | 20均线下方连续天数，当选中 `below_ma20` 策略时必填，默认 `3`（1-30之间） |
| below_ma20_min_profit | float | 条件必填 | 20均线策略最小收益阈值（%），当选中 `below_ma20` 策略时可选（0-200之间） |
| trailing_stop_percent | float | 条件必填 | 追踪止损比例（%），当选中 `trailing_stop_loss` 策略时必填，默认 `5.0`（0-50之间） |

**卖出策略说明**：

1. **止损策略** (`stop_loss`)
   - 当亏损达到指定比例时自动卖出
   - 使用日线数据检查，确保不会错过止损点

2. **止盈策略** (`take_profit`)
   - 当盈利达到指定比例时自动卖出
   - 可选，留空表示不设止盈限制
   - 使用日线数据检查，确保不会错过止盈点

3. **20均线下方策略** (`below_ma20`)
   - 买入后上穿20均线，然后收盘价回落到20均线下方N天，第(N+1)天卖出
   - 可选最小收益阈值，只有收益达到阈值后才触发此策略

4. **追踪止损策略** (`trailing_stop_loss`)
   - 初始止损点设置为买入价格下方一定幅度
   - 随着股价上升，止损点也随之上移，始终保持在最新高点下方相同幅度

**回测规则**:
- 出现买入信号的第二天开盘价全仓买入
- 根据选中的卖出策略判断卖出时机
- 出现卖出信号的第二天开盘价全仓卖出
- 全仓操作，不保留现金
- 如果最后还有持仓，按最后一天收盘价计算

**请求示例**:

```bash
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

**响应示例** (成功):
```json
{
    "success": true,
    "period": "D",
    "period_name": "日线",
    "initial_amount": 100000.0,
    "final_amount": 150000.0,
    "total_profit": 50000.0,
    "total_profit_rate": 50.0,
    "annual_profit_rate": 12.5,
    "start_date": "2020-10-26",
    "end_date": "2025-12-30",
    "trading_days": 1891,
    "total_trades": 20,
    "trades": [
        {
            "buy_date": "2020-11-18",
            "buy_price": 312.67,
            "sell_date": "2020-12-28",
            "sell_price": 336.08,
            "shares": 319.5,
            "profit": 7485.5,
            "profit_rate": 7.48,
            "reason": "止盈(10.00%)"
        }
    ]
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| period | string | 周期类型 |
| period_name | string | 周期名称 |
| initial_amount | float | 初始资金金额 |
| final_amount | float | 最终资金金额 |
| total_profit | float | 总收益 |
| total_profit_rate | float | 总收益率（百分比） |
| annual_profit_rate | float | 年化收益率（百分比） |
| start_date | string | 回测开始日期 |
| end_date | string | 回测结束日期 |
| trading_days | integer | 交易天数 |
| total_trades | integer | 交易次数 |
| trades | array | 交易记录列表（按卖出日期倒序） |
| trades[].buy_date | string | 买入日期 |
| trades[].buy_price | float | 买入价格 |
| trades[].sell_date | string | 卖出日期 |
| trades[].sell_price | float | 卖出价格 |
| trades[].shares | float | 持仓数量 |
| trades[].profit | float | 单笔收益 |
| trades[].profit_rate | float | 单笔收益率（百分比） |
| trades[].reason | string | 卖出原因（如：止损、止盈、20均线下方等） |

**错误响应**:
```json
{
    "success": false,
    "error": "缺少必需参数: initial_amount",
    "error_code": "MISSING_PARAMETER"
}
```

---

## 数据格式

### 周期类型

| 值 | 说明 |
|----|------|
| D | 日线 |
| W | 周线（自然周：周一到周日） |
| M | 月线（自然月：1号到月末） |

### 数据文件格式

Excel文件应包含以下列（列名可以是中文或英文）：

#### 必需列

- **日期/时间**：交易日期，格式为 `YYYY-MM-DD` 或 Excel日期格式
- **开盘**（open）：开盘价
- **最高**（high）：最高价
- **最低**（low）：最低价
- **收盘**（close）：收盘价

#### 可选列

- **成交量**（volume）：成交量（可选）
- **MA.MA3**：20日均线值（用于20均线策略，如果不存在则20均线策略无法使用）

### 数据文件位置

将Excel数据文件放在 `data/` 目录下，文件名格式为：`{股票代码}.xlsx`

例如：
- `data/159915.xlsx`
- `data/300760.xlsx`
- `data/588000.xlsx`

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（未登录或登录已过期） |
| 500 | 服务器内部错误 |

### 错误代码

| 错误代码 | 说明 |
|----------|------|
| UNAUTHORIZED | 未登录或登录已过期 |
| INVALID_CONTENT_TYPE | 请求内容类型错误 |
| EMPTY_BODY | 请求体为空 |
| INVALID_PERIOD | 无效的周期参数 |
| MISSING_PARAMETER | 缺少必需参数 |
| INVALID_AMOUNT | 无效的金额参数 |
| INVALID_BUY_THRESHOLD | 无效的买入阈值 |
| NO_SELL_STRATEGY | 未选择卖出策略 |
| INVALID_STOP_LOSS | 无效的止损比例 |
| INVALID_TAKE_PROFIT | 无效的止盈比例 |
| INVALID_BELOW_MA20_DAYS | 无效的20均线下方天数 |
| INVALID_BELOW_MA20_MIN_PROFIT | 无效的20均线策略最小收益阈值 |
| INVALID_TRAILING_STOP_LOSS | 无效的追踪止损比例 |
| FILE_NOT_FOUND | 数据文件未找到 |
| NO_DATA_IN_RANGE | 指定时间范围内没有数据 |
| NO_DAILY_DATA | 日线数据为空 |
| MISSING_COLUMNS | 数据文件缺少必需的列 |
| INVALID_PRICE_DATA | 价格数据无效 |
| INDICATOR_CALCULATION_ERROR | 指标计算错误 |
| INSUFFICIENT_DATA | 数据不足 |
| MA20_COLUMN_NOT_FOUND | 未找到MA.MA3列（20日均线） |
| MA20_NO_VALID_DATA | MA.MA3列没有有效值 |
| CALCULATION_ERROR | 计算错误 |
| BACKTEST_ERROR | 回测错误 |
| SERVER_ERROR | 服务器错误 |

### 错误响应格式

```json
{
    "success": false,
    "error": "错误描述",
    "error_code": "ERROR_CODE"
}
```

---

## 示例代码

### Python 示例

```python
import requests

BASE_URL = "http://localhost:5000"
session = requests.Session()

# 1. 登录（需要先通过Web界面获取账号密码）
login_data = {
    "username": "admin",
    "password": "your_password"
}
response = session.post(f"{BASE_URL}/login", data=login_data)
print("登录状态:", response.status_code)

# 2. 健康检查（无需登录）
response = requests.get(f"{BASE_URL}/api/health")
print(response.json())

# 3. 计算日线信号
response = session.post(
    f"{BASE_URL}/api/calculate",
    json={
        "period": "D",
        "stock_code": "159915",
        "buy_threshold": 10.0
    }
)
result = response.json()
if result.get('success'):
    print(f"买入信号: {result['statistics']['buy_signals_count']} 次")
    print(f"卖出信号: {result['statistics']['sell_signals_count']} 次")

# 4. 回测
response = session.post(
    f"{BASE_URL}/api/backtest",
    json={
        "period": "D",
        "initial_amount": 100000,
        "sell_strategies": ["stop_loss", "take_profit"],
        "stop_loss_percent": 5.0,
        "take_profit_percent": 10.0,
        "strategy_relation": "OR"
    }
)
result = response.json()
if result.get('success'):
    print(f"总收益: {result['total_profit']:,.2f}")
    print(f"总收益率: {result['total_profit_rate']:.2f}%")
    print(f"年化收益率: {result['annual_profit_rate']:.2f}%")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:5000';

// 1. 健康检查（无需登录）
fetch(`${BASE_URL}/api/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// 2. 计算日线信号（需要登录，需要携带Cookie）
fetch(`${BASE_URL}/api/calculate`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // 携带Cookie
  body: JSON.stringify({
    period: 'D',
    stock_code: '159915',
    buy_threshold: 10.0
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`买入信号: ${data.statistics.buy_signals_count} 次`);
    console.log(`卖出信号: ${data.statistics.sell_signals_count} 次`);
  }
});

// 3. 回测（需要登录，需要携带Cookie）
fetch(`${BASE_URL}/api/backtest`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // 携带Cookie
  body: JSON.stringify({
    period: 'D',
    initial_amount: 100000,
    sell_strategies: ['stop_loss', 'take_profit'],
    stop_loss_percent: 5.0,
    take_profit_percent: 10.0,
    strategy_relation: 'OR'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`总收益: ${data.total_profit.toLocaleString()}`);
    console.log(`总收益率: ${data.total_profit_rate.toFixed(2)}%`);
    console.log(`年化收益率: ${data.annual_profit_rate.toFixed(2)}%`);
  }
});
```

### cURL 示例

```bash
# 健康检查（无需登录）
curl http://localhost:5000/api/health

# 计算日线信号（需要先登录获取Cookie）
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "period": "D",
    "stock_code": "159915",
    "buy_threshold": 10.0
  }'

# 回测（需要先登录获取Cookie）
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "period": "D",
    "initial_amount": 100000,
    "sell_strategies": ["stop_loss", "take_profit"],
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0,
    "strategy_relation": "OR"
  }'
```

---

## 技术指标说明

### 支撑位和阻力位

- **支撑位** = L1 + P1 * 0.5/8
- **阻力位** = L1 + P1 * 7/8
- **中线** = (支撑 + 阻力) / 2

其中：
- L1 = MIN(昨收, 最低)
- P1 = MAX(昨收, 最高) - MIN(昨收, 最低)

### 趋势线

基于SMA（简单移动平均）和EMA（指数移动平均）计算：

1. 计算N周期内的最高价(HHV)和最低价(LLV)
2. 计算比率: (收盘价 - LLV) / (HHV - LLV) * 100
3. 第一层SMA: SMA(比率, 5)
4. 第二层SMA: SMA(SMA1, 3)
5. V11 = 3*SMA1 - 2*SMA2
6. 趋势线 = EMA(V11, 3)

### 买卖信号

- **买入信号**：趋势线从下向上穿越买入阈值（默认10）
- **卖出信号**：趋势线从上向下穿越90
- **超卖区**：趋势线 < 10
- **超买区**：趋势线 > 90

### 20日均线

系统使用数据文件中的 `MA.MA3` 列作为20日均线，不进行额外计算。如果数据文件中没有此列，20均线策略将无法使用。

---

## 注意事项

1. **认证要求**：除健康检查和API信息接口外，所有接口都需要登录后才能访问
2. **数据文件**：确保数据文件存在且格式正确
3. **周期转换**：周线和月线按照自然周和自然月计算
4. **回测规则**：全仓操作，不保留现金
5. **卖出策略**：至少需要选择一个卖出策略
6. **策略关系**：AND关系要求所有策略都触发才卖出，OR关系任一策略触发即卖出
7. **性能优化**：日线数据会被缓存，提高响应速度
8. **跨域支持**：已启用CORS，支持跨域请求

---

## 版本信息

- **API版本**: 1.0.0
- **最后更新**: 2025年

---

## 支持与反馈

如有问题或建议，请查看项目文档或提交Issue。
