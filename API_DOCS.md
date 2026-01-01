# 股票技术指标计算 API 文档

## 项目简介

这是一个基于Flask的Web API服务，提供股票技术指标计算功能。支持日线、周线、月线三种周期的买卖信号分析。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行项目

### 方式一：直接运行

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

### 方式二：使用Flask命令运行

```bash
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```

### 方式三：使用gunicorn（生产环境推荐）

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API 接口说明

### 1. 健康检查接口

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

### 2. 计算技术指标信号

**接口地址**: `POST /api/calculate`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
    "period": "D"
}
```

**参数说明**:
- `period` (必填): 周期类型
  - `D`: 日线
  - `W`: 周线
  - `M`: 月线
- `file_path` (可选): 数据文件路径，默认为 `data/300760.xlsx`

**请求示例**:

使用curl:
```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "D"}'
```

使用Python requests:
```python
import requests

url = "http://localhost:5000/api/calculate"
headers = {"Content-Type": "application/json"}
data = {"period": "D"}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result)
```

使用JavaScript (fetch):
```javascript
fetch('http://localhost:5000/api/calculate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    period: 'D'
  })
})
.then(response => response.json())
.then(data => console.log(data));
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
        },
        {
            "date": "2020-12-18",
            "close": 351.43,
            "trend_line": 89.504564
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
- `success`: 是否成功
- `period`: 周期类型 (D/W/M)
- `period_name`: 周期名称 (日线/周线/月线)
- `total_records`: 总记录数
- `statistics`: 统计信息
  - `buy_signals_count`: 买入信号次数
  - `sell_signals_count`: 卖出信号次数
  - `oversold_count`: 超卖区次数
  - `overbought_count`: 超买区次数
- `buy_signals`: 买入信号列表
  - `date`: 日期
  - `close`: 收盘价
  - `trend_line`: 趋势线值
- `sell_signals`: 卖出信号列表（格式同买入信号）
- `recent_data`: 最近20条关键指标数据

**错误响应示例**:
```json
{
    "success": false,
    "error": "无效的周期参数: X，支持的值: D(日线), W(周线), M(月线)",
    "error_code": "INVALID_PERIOD"
}
```

**HTTP状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

### 3. 回测接口

**接口地址**: `POST /api/backtest`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
    "period": "D",
    "initial_amount": 100000
}
```

**参数说明**:
- `period` (必填): 周期类型
  - `D`: 日线
  - `W`: 周线
  - `M`: 月线
- `initial_amount` (必填): 初始资金金额，必须大于0
- `file_path` (可选): 数据文件路径，默认为 `data/300760.xlsx`

**请求示例**:

使用curl:
```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "D", "initial_amount": 100000}'
```

使用Python requests:
```python
import requests

url = "http://localhost:5000/api/backtest"
headers = {"Content-Type": "application/json"}
data = {
    "period": "D",
    "initial_amount": 100000
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result)
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
- `success`: 是否成功
- `period`: 周期类型 (D/W/M)
- `period_name`: 周期名称 (日线/周线/月线)
- `initial_amount`: 初始资金金额
- `final_amount`: 最终资金金额
- `total_profit`: 总收益
- `total_profit_rate`: 总收益率（百分比）
- `annual_profit_rate`: 年收益率（百分比）
- `start_date`: 回测开始日期
- `end_date`: 回测结束日期
- `trading_days`: 交易天数
- `total_trades`: 交易次数
- `trades`: 交易记录列表
  - `buy_date`: 买入日期
  - `buy_price`: 买入价格
  - `sell_date`: 卖出日期
  - `sell_price`: 卖出价格
  - `shares`: 持仓数量
  - `profit`: 单笔收益
  - `profit_rate`: 单笔收益率（百分比）

**回测规则**:
- 出现买入信号的第二天开盘价全仓买入
- 出现卖出信号的第二天开盘价全仓卖出
- 全仓操作，不保留现金
- 如果最后还有持仓，按最后一天收盘价计算

**错误响应示例**:
```json
{
    "success": false,
    "error": "缺少必需参数: initial_amount",
    "error_code": "MISSING_PARAMETER"
}
```

**HTTP状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

## 使用示例

### 查询日线信号

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "D"}'
```

### 查询周线信号

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "W"}'
```

### 查询月线信号

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "M"}'
```

### 使用自定义数据文件

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "D", "file_path": "data/your_stock.xlsx"}'
```

### 日线回测

```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "D", "initial_amount": 100000}'
```

### 周线回测

```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "W", "initial_amount": 100000}'
```

### 月线回测

```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "M", "initial_amount": 100000}'
```

## Python客户端示例

```python
import requests
import json

# API地址
base_url = "http://localhost:5000"

# 查询日线信号
def get_daily_signals():
    url = f"{base_url}/api/calculate"
    headers = {"Content-Type": "application/json"}
    data = {"period": "D"}
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if result.get('success'):
        print(f"周期: {result['period_name']}")
        print(f"买入信号: {result['statistics']['buy_signals_count']} 次")
        print(f"卖出信号: {result['statistics']['sell_signals_count']} 次")
        
        print("\n买入信号位置:")
        for signal in result['buy_signals']:
            print(f"  日期: {signal['date']}, 收盘价: {signal['close']}, 趋势线: {signal['trend_line']:.2f}")
        
        print("\n卖出信号位置:")
        for signal in result['sell_signals']:
            print(f"  日期: {signal['date']}, 收盘价: {signal['close']}, 趋势线: {signal['trend_line']:.2f}")
    else:
        print(f"错误: {result.get('error')}")

# 查询周线信号
def get_weekly_signals():
    url = f"{base_url}/api/calculate"
    headers = {"Content-Type": "application/json"}
    data = {"period": "W"}
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# 查询月线信号
def get_monthly_signals():
    url = f"{base_url}/api/calculate"
    headers = {"Content-Type": "application/json"}
    data = {"period": "M"}
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def backtest_daily(initial_amount: float = 100000):
    """日线回测"""
    url = f"{base_url}/api/backtest"
    headers = {"Content-Type": "application/json"}
    data = {
        "period": "D",
        "initial_amount": initial_amount
    }
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if result.get('success'):
        print(f"初始资金: {result['initial_amount']:,.2f}")
        print(f"最终资金: {result['final_amount']:,.2f}")
        print(f"总收益: {result['total_profit']:,.2f}")
        print(f"总收益率: {result['total_profit_rate']:.2f}%")
        print(f"年收益率: {result['annual_profit_rate']:.2f}%")
        print(f"交易次数: {result['total_trades']}")
        
        print("\n交易记录:")
        for i, trade in enumerate(result['trades'][:5], 1):  # 只显示前5笔
            print(f"  交易{i}: {trade['buy_date']} 买入 {trade['buy_price']:.2f} -> "
                  f"{trade['sell_date']} 卖出 {trade['sell_price']:.2f}, "
                  f"收益: {trade['profit']:,.2f} ({trade['profit_rate']:.2f}%)")
    else:
        print(f"错误: {result.get('error')}")

if __name__ == '__main__':
    # 查询日线信号
    get_daily_signals()
    
    # 日线回测
    print("\n" + "=" * 60)
    print("日线回测")
    print("=" * 60)
    backtest_daily(100000)
```

## 注意事项

1. **数据文件**: 确保 `data/300760.xlsx` 文件存在，或通过 `file_path` 参数指定其他文件路径
2. **数据格式**: Excel文件应包含日期、开盘、最高、最低、收盘等列
3. **性能优化**: 日线数据会被缓存，提高后续请求的响应速度
4. **跨域支持**: 已启用CORS，支持跨域请求
5. **错误处理**: 所有错误都会返回JSON格式的错误信息

## 部署建议

### 开发环境
直接使用 `python app.py` 运行

### 生产环境
推荐使用 `gunicorn` 或 `uwsgi` 部署：

```bash
# 使用gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 使用uwsgi
uwsgi --http 0.0.0.0:5000 --wsgi-file app.py --callable app --processes 4
```

### Docker部署（可选）

创建 `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

构建和运行:
```bash
docker build -t stock-indicator-api .
docker run -p 5000:5000 stock-indicator-api
```

## 技术支持

如有问题，请检查：
1. 数据文件是否存在且格式正确
2. 依赖包是否已正确安装
3. 端口5000是否被占用
4. 查看服务器日志获取详细错误信息

