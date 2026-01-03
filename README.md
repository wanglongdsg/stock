# 股票技术指标计算与回测系统

基于Flask的股票技术分析系统，提供技术指标计算、买卖信号识别、多策略回测和Web可视化界面。

## 项目结构

```
stock/
├── app.py                    # Flask应用入口
├── main.py                   # 命令行工具
├── config/                   # 配置目录
│   ├── __init__.py
│   └── settings.py          # 配置文件
├── utils/                    # 工具类包
│   ├── data_loader.py       # 数据加载工具
│   └── period_converter.py  # 周期转换工具
├── services/                 # 服务层
│   ├── indicator_service.py # 指标计算服务
│   ├── backtest_service.py  # 回测服务
│   └── sell_strategies.py   # 卖出策略模块
├── models/                   # 数据模型
│   ├── indicator.py         # 指标计算类
│   └── stock_data.py        # 股票数据模型（预留）
├── api/                      # API路由
│   └── routes.py            # 路由定义
├── templates/                # HTML模板
│   ├── login.html           # 登录页面
│   ├── index.html           # 首页
│   ├── calculate.html       # 指标计算页面
│   └── backtest.html        # 回测分析页面
├── static/                   # 静态资源
│   ├── css/                 # 样式文件
│   │   └── style.css
│   └── js/                  # JavaScript文件
│       ├── app.js           # 主应用逻辑
│       ├── calculate.js     # 指标计算页面逻辑
│       └── backtest.js      # 回测页面逻辑
├── data/                     # 数据目录
│   ├── 159915.xlsx          # 股票数据文件示例
│   ├── 300760.xlsx
│   └── 588000.xlsx
├── doc/                      # 文档目录
│   ├── API_DOCUMENTATION.md # API文档
│   ├── API_DOCS.md          # API快速参考
│   └── WEB_UI_GUIDE.md      # Web界面使用指南
└── tests/                    # 测试用例
    ├── test_api.py          # API接口测试
    └── test_backtest.py     # 回测功能测试
```

## 功能特性

### 核心功能

- ✅ **技术指标计算**：支撑位、阻力位、趋势线（基于SMA和EMA）
- ✅ **买卖信号识别**：自动识别买入和卖出信号
  - 买入信号：趋势线从下向上穿越买入阈值（默认10）
  - 卖出信号：趋势线从上向下穿越90
- ✅ **多周期支持**：日线（D）、周线（W）、月线（M）
- ✅ **回测功能**：全仓回测，计算收益、年化收益率等指标

### 卖出策略

系统支持多种卖出策略，可单独使用或组合使用（AND/OR关系）：

1. **止损策略**（stop_loss）
   - 当亏损达到指定比例时自动卖出
   - 默认止损比例：5%
   - 使用日线数据检查，确保不会错过止损点

2. **止盈策略**（take_profit）
   - 当盈利达到指定比例时自动卖出
   - 可选，留空表示不设止盈限制
   - 使用日线数据检查，确保不会错过止盈点

3. **20均线下方策略**（below_ma20）
   - 买入后上穿20均线，然后收盘价回落到20均线下方N天，第(N+1)天卖出
   - 默认连续天数：3天
   - 可选最小收益阈值（如10%），只有收益达到阈值后才触发此策略

4. **追踪止损策略**（trailing_stop_loss）
   - 初始止损点设置为买入价格下方一定幅度（默认5%）
   - 随着股价上升，止损点也随之上移，始终保持在最新高点下方相同幅度
   - 使用日线数据检查，确保不会错过止损点

### Web界面

- ✅ **登录系统**：安全的用户认证机制
- ✅ **指标计算页面**：可视化展示技术指标和买卖信号
- ✅ **回测分析页面**：配置回测参数，查看回测结果和交易记录
- ✅ **响应式设计**：支持不同屏幕尺寸
- ✅ **颜色方案**：支持红涨绿跌（中国习惯）和绿涨红跌（美国习惯）

### API接口

- ✅ RESTful API设计
- ✅ JSON格式数据交互
- ✅ 完整的错误处理和错误码
- ✅ 健康检查接口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**依赖包**：
- `pandas>=2.0.0` - 数据处理
- `numpy>=1.24.0` - 数值计算
- `openpyxl>=3.0.0` - Excel文件读取
- `flask>=2.3.0` - Web框架
- `flask-cors>=4.0.0` - 跨域支持

### 2. 启动Web服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

**启动信息**：
- 系统启动时会在控制台打印登录账号和密码
- 默认账号：`admin`（可通过环境变量修改）
- 默认密码：随机生成（启动时在控制台显示）

### 3. 访问Web界面

启动服务后，在浏览器中访问：
- **登录页面**: `http://localhost:5000/login`
- **指标计算页面**: `http://localhost:5000/calculate`
- **回测分析页面**: `http://localhost:5000/backtest`
- **API信息**: `http://localhost:5000/api`

### 4. 使用命令行工具

```bash
# 日线
python main.py D

# 周线
python main.py W

# 月线
python main.py M
```

## API 文档

详细的API文档请查看：
- [API_DOCUMENTATION.md](doc/API_DOCUMENTATION.md) - 完整API文档
- [API_DOCS.md](doc/API_DOCS.md) - API快速参考

### 快速示例

```bash
# 健康检查（无需登录）
curl http://localhost:5000/api/health

# 计算日线信号（需要登录）
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "period": "D",
    "stock_code": "159915",
    "buy_threshold": 10.0
  }'

# 回测（需要登录）
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "period": "D",
    "initial_amount": 100000,
    "stock_code": "159915",
    "sell_strategies": ["stop_loss", "take_profit"],
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
  }'
```

## 配置说明

配置文件位于 `config/settings.py`，支持环境变量：

### 基础配置

- `DATA_DIR`: 数据文件目录（默认：`data`）
- `DEFAULT_DATA_FILE`: 默认数据文件路径（默认：`data/159915.xlsx`）
- `FLASK_HOST`: Flask主机地址（默认：`0.0.0.0`）
- `FLASK_PORT`: Flask端口（默认：`5000`）
- `FLASK_DEBUG`: 调试模式（默认：`True`）
- `FLASK_SECRET_KEY`: Session密钥（默认：随机生成）

### 登录配置

- `LOGIN_USERNAME`: 登录账号（默认：`admin`）
- `LOGIN_PASSWORD`: 登录密码（默认：随机生成，启动时在控制台显示）

**登录说明**：
- 系统启动时会在控制台打印登录账号和密码
- 可以通过环境变量 `LOGIN_USERNAME` 和 `LOGIN_PASSWORD` 自定义账号密码
- 所有页面和API接口都需要登录后才能访问

### 显示配置

- `STOCK_COLOR_SCHEME`: 股票涨跌颜色方案（默认：`CN`）
  - `CN`: 红涨绿跌（中国习惯）
  - `US`: 绿涨红跌（美国习惯）

**颜色配置说明**：
- 默认使用红涨绿跌（中国习惯）
- 可通过环境变量 `STOCK_COLOR_SCHEME` 设置为 `US` 使用绿涨红跌（美国习惯）
- 颜色配置会应用到所有收益、收益率等数值显示

### 指标配置

- `INDICATOR_N`: 指标计算周期（默认：`5`）

### 数据库配置（预留）

- `DATABASE_URL`: 数据库URL（预留，暂未使用）

## 技术指标说明

### 支撑位和阻力位

- **支撑位** = L1 + P1 * 0.5/8
- **阻力位** = L1 + P1 * 7/8
- **中线** = (支撑 + 阻力) / 2

其中：
- L1：最低价
- P1：价格区间（最高价 - 最低价）

### 趋势线

基于SMA（简单移动平均）和EMA（指数移动平均）计算，用于识别买卖信号。

### 买卖信号

- **买入信号**：趋势线从下向上穿越买入阈值（默认10）
- **卖出信号**：趋势线从上向下穿越90

### 20日均线

系统使用数据文件中的 `MA.MA3` 列作为20日均线，不进行额外计算。

## 数据格式

Excel文件应包含以下列：

### 必需列

- **日期/时间**：日期列，格式为 `YYYY-MM-DD` 或 Excel日期格式
- **开盘**（open）：开盘价
- **最高**（high）：最高价
- **最低**（low）：最低价
- **收盘**（close）：收盘价

### 可选列

- **成交量**（volume）：成交量（可选）
- **MA.MA3**：20日均线值（用于20均线策略，如果不存在则20均线策略无法使用）

### 数据文件位置

将Excel数据文件放在 `data/` 目录下，文件名格式为：`{股票代码}.xlsx`

例如：
- `data/159915.xlsx`
- `data/300760.xlsx`
- `data/588000.xlsx`

## 回测功能说明

### 回测参数

- **周期**：日线（D）、周线（W）、月线（M）
- **初始资金**：回测起始资金金额
- **股票代码**：要回测的股票代码（对应data目录下的Excel文件）
- **时间范围**：可选，指定回测的开始日期和结束日期
- **买入信号阈值**：趋势线穿越此值触发买入（默认10）

### 卖出策略配置

- **策略选择**：可选择多个卖出策略，支持AND/OR关系
  - AND：所有策略都触发才卖出
  - OR：任一策略触发即卖出（默认）
- **策略参数**：
  - 止损比例：默认5%
  - 止盈比例：可选，留空表示不设止盈
  - 20均线下方天数：默认3天
  - 20均线策略最小收益阈值：可选，如10%
  - 追踪止损比例：默认5%

### 回测结果

回测结果包含：
- 初始资金、最终资金
- 总收益、总收益率
- 年化收益率
- 交易天数
- 总交易次数
- 详细交易记录（买入日期、卖出日期、价格、收益等）

## 测试

### 运行测试

测试用例统一放在 `tests/` 目录中。

#### 运行所有测试

```bash
python tests/test_all.py
```

#### 运行单个测试

```bash
# API接口测试
python tests/test_api.py

# 回测接口测试
python tests/test_backtest.py
```

**注意**: 运行测试前需要先启动API服务：
```bash
python app.py
```

详细测试说明请查看 [tests/README.md](tests/README.md)

## 开发说明

### 项目架构

- **工具层 (utils/)**: 通用工具函数（数据加载、周期转换）
- **模型层 (models/)**: 数据模型和核心计算类（指标计算）
- **服务层 (services/)**: 业务逻辑服务（指标服务、回测服务、卖出策略）
- **API层 (api/)**: HTTP接口路由
- **视图层 (templates/)**: HTML模板
- **静态资源 (static/)**: CSS样式和JavaScript脚本
- **测试层 (tests/)**: 测试用例

### 扩展开发

1. **添加新的卖出策略**：
   - 在 `services/sell_strategies.py` 中创建新的策略类
   - 继承 `SellStrategy` 基类
   - 实现 `should_sell`、`get_name`、`reset` 方法
   - 在 `create_strategy` 函数中注册新策略

2. **添加新的API接口**：
   - 在 `api/routes.py` 中添加路由
   - 使用 `@api_login_required` 装饰器保护接口

3. **添加新的服务**：
   - 在 `services/` 中创建服务类
   - 遵循单一职责原则

4. **添加数据库支持**：
   - 在 `models/stock_data.py` 中定义模型
   - 配置 `DATABASE_URL` 环境变量

5. **添加测试用例**：
   - 在 `tests/` 中创建测试文件
   - 使用统一的测试框架

### 代码规范

- 遵循PEP 8 Python代码规范
- 使用类型提示（Type Hints）
- 添加详细的文档字符串
- 异常处理和日志记录

## 常见问题

### Q: 如何修改默认数据文件？

A: 通过环境变量 `DEFAULT_DATA_FILE` 设置，或在API请求中指定 `file_path` 参数。

### Q: 如何自定义登录账号密码？

A: 设置环境变量 `LOGIN_USERNAME` 和 `LOGIN_PASSWORD`。

### Q: 20均线策略为什么没有触发？

A: 检查数据文件中是否包含 `MA.MA3` 列（20日均线），且买入时收盘价必须在20均线下方。

### Q: 回测结果中的年化收益率如何计算？

A: 年化收益率 = ((最终资金 / 初始资金) ^ (1 / 年数) - 1) * 100

### Q: 如何切换颜色方案？

A: 设置环境变量 `STOCK_COLOR_SCHEME=US` 使用绿涨红跌，或保持默认的 `CN`（红涨绿跌）。

## 许可证

本项目仅供学习和研究使用。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持技术指标计算和买卖信号识别
- 支持多周期（日线、周线、月线）
- 支持多种卖出策略（止损、止盈、20均线、追踪止损）
- 支持Web界面和API接口
- 支持回测功能
