# 股票技术指标计算 API 文档

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [API 接口](#api-接口)
  - [健康检查](#1-健康检查)
  - [计算技术指标信号](#2-计算技术指标信号)
  - [回测接口](#3-回测接口)
- [数据格式](#数据格式)
- [错误处理](#错误处理)
- [示例代码](#示例代码)

---

## 概述

股票技术指标计算 API 提供基于通达信公式的股票技术分析服务，支持：

- **技术指标计算**：支撑位、阻力位、趋势线等
- **买卖信号识别**：自动识别买入和卖出信号
- **多周期支持**：日线、周线、月线
- **回测功能**：基于历史数据的策略回测

### 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **请求方法**: `POST` (除健康检查外)

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

### 3. 测试连接

```bash
curl http://localhost:5000/api/health
```

---

## API 接口

### 1. 健康检查

检查服务运行状态。

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

### 2. 计算技术指标信号

计算指定周期的技术指标和买卖信号。

**接口地址**: `POST /api/calculate`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
    "period": "D",
    "file_path": "data/300760.xlsx"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period | string | 是 | 周期类型：`D`(日线)、`W`(周线)、`M`(月线) |
| file_path | string | 否 | 数据文件路径，默认为 `data/300760.xlsx` |

**请求示例**:

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "period": "D"
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
        },
        {
            "date": "2021-03-01",
            "close": 396.06,
            "trend_line": 17.514042
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

### 3. 回测接口

按照买卖信号进行全仓回测，计算收益情况。

**接口地址**: `POST /api/backtest`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
    "period": "D",
    "initial_amount": 100000,
    "file_path": "data/300760.xlsx"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period | string | 是 | 周期类型：`D`(日线)、`W`(周线)、`M`(月线) |
| initial_amount | float | 是 | 初始资金金额，必须大于0 |
| file_path | string | 否 | 数据文件路径，默认为 `data/300760.xlsx` |

**回测规则**:
- 出现买入信号的第二天开盘价全仓买入
- 出现卖出信号的第二天开盘价全仓卖出
- 全仓操作，不保留现金
- 如果最后还有持仓，按最后一天收盘价计算

**请求示例**:

```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "period": "D",
    "initial_amount": 100000
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
            "sell_date": "2020-10-28",
            "sell_price": 336.08,
            "shares": 319.5,
            "profit": 7485.5,
            "profit_rate": 7.48
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
| annual_profit_rate | float | 年收益率（百分比） |
| start_date | string | 回测开始日期 |
| end_date | string | 回测结束日期 |
| trading_days | integer | 交易天数 |
| total_trades | integer | 交易次数 |
| trades | array | 交易记录列表 |
| trades[].buy_date | string | 买入日期 |
| trades[].buy_price | float | 买入价格 |
| trades[].sell_date | string | 卖出日期 |
| trades[].sell_price | float | 卖出价格 |
| trades[].shares | float | 持仓数量 |
| trades[].profit | float | 单笔收益 |
| trades[].profit_rate | float | 单笔收益率（百分比） |

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

- **日期/时间**：交易日期
- **开盘**：开盘价
- **最高**：最高价
- **最低**：最低价
- **收盘**：收盘价
- **成交量**：成交量（可选）

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

### 错误代码

| 错误代码 | 说明 |
|----------|------|
| INVALID_CONTENT_TYPE | 请求内容类型错误 |
| EMPTY_BODY | 请求体为空 |
| INVALID_PERIOD | 无效的周期参数 |
| MISSING_PARAMETER | 缺少必需参数 |
| INVALID_AMOUNT | 无效的金额参数 |
| FILE_NOT_FOUND | 数据文件未找到 |
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

# 1. 健康检查
response = requests.get(f"{BASE_URL}/api/health")
print(response.json())

# 2. 计算日线信号
response = requests.post(
    f"{BASE_URL}/api/calculate",
    json={"period": "D"},
    headers={"Content-Type": "application/json"}
)
result = response.json()
if result.get('success'):
    print(f"买入信号: {result['statistics']['buy_signals_count']} 次")
    print(f"卖出信号: {result['statistics']['sell_signals_count']} 次")

# 3. 回测
response = requests.post(
    f"{BASE_URL}/api/backtest",
    json={
        "period": "D",
        "initial_amount": 100000
    },
    headers={"Content-Type": "application/json"}
)
result = response.json()
if result.get('success'):
    print(f"总收益: {result['total_profit']:,.2f}")
    print(f"总收益率: {result['total_profit_rate']:.2f}%")
    print(f"年收益率: {result['annual_profit_rate']:.2f}%")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:5000';

// 1. 健康检查
fetch(`${BASE_URL}/api/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// 2. 计算日线信号
fetch(`${BASE_URL}/api/calculate`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    period: 'D'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`买入信号: ${data.statistics.buy_signals_count} 次`);
    console.log(`卖出信号: ${data.statistics.sell_signals_count} 次`);
  }
});

// 3. 回测
fetch(`${BASE_URL}/api/backtest`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    period: 'D',
    initial_amount: 100000
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`总收益: ${data.total_profit.toLocaleString()}`);
    console.log(`总收益率: ${data.total_profit_rate.toFixed(2)}%`);
    console.log(`年收益率: ${data.annual_profit_rate.toFixed(2)}%`);
  }
});
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:5000/api/health

# 计算日线信号
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "D"}'

# 计算周线信号
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "W"}'

# 计算月线信号
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "M"}'

# 日线回测
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "D", "initial_amount": 100000}'

# 周线回测
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "W", "initial_amount": 100000}'

# 月线回测
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "M", "initial_amount": 100000}'
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

- **买入信号**：趋势线从下向上穿越10
- **卖出信号**：趋势线从上向下穿越90
- **超卖区**：趋势线 < 10
- **超买区**：趋势线 > 90

---

## 注意事项

1. **数据文件**：确保数据文件存在且格式正确
2. **周期转换**：周线和月线按照自然周和自然月计算
3. **回测规则**：全仓操作，不保留现金
4. **性能优化**：日线数据会被缓存，提高响应速度
5. **跨域支持**：已启用CORS，支持跨域请求

---

## 版本信息

- **API版本**: 1.0.0
- **最后更新**: 2025年

---

## 支持与反馈

如有问题或建议，请查看项目文档或提交Issue。

