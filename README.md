# 股票技术指标计算系统

股票技术分析系统，提供技术指标计算、买卖信号识别和回测功能。

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
│   └── backtest_service.py  # 回测服务
├── models/                   # 数据模型
│   ├── indicator.py         # 指标计算类
│   └── stock_data.py        # 股票数据模型（预留）
├── api/                      # API路由
│   └── routes.py            # 路由定义
└── data/                     # 数据目录
    └── 300760.xlsx          # 股票数据文件
```

## 功能特性

- ✅ 技术指标计算（支撑位、阻力位、趋势线）
- 买卖信号识别（买入/卖出信号）
- 多周期支持（日线、周线、月线）
- 回测功能（全仓回测，计算收益）
- RESTful API 接口
- 命令行工具

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动Web服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

### 3. 访问Web界面

启动服务后，在浏览器中访问：
- **Web界面**: `http://localhost:5000/` 或 `http://localhost:5000/index`
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

详细的API文档请查看 [API_DOCUMENTATION.md](doc/API_DOCUMENTATION.md)

### 快速示例

```bash
# 健康检查
curl http://localhost:5000/api/health

# 计算日线信号
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"period": "D"}'

# 回测
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"period": "D", "initial_amount": 100000}'
```

## 配置说明

配置文件位于 `config/settings.py`，支持环境变量：

- `DATA_FILE`: 数据文件路径（默认：`data/300760.xlsx`）
- `FLASK_HOST`: Flask主机地址（默认：`0.0.0.0`）
- `FLASK_PORT`: Flask端口（默认：`5000`）
- `FLASK_DEBUG`: 调试模式（默认：`True`）
- `DATABASE_URL`: 数据库URL（预留）
- `INDICATOR_N`: 指标计算周期（默认：`5`）
- `LOGIN_USERNAME`: 登录账号（默认：`admin`，每次启动会生成随机密码）
- `LOGIN_PASSWORD`: 登录密码（默认：随机生成，启动时在控制台显示）
- `FLASK_SECRET_KEY`: Session密钥（默认：随机生成）
- `STOCK_COLOR_SCHEME`: 股票涨跌颜色方案（默认：`CN`）
  - `CN`: 红涨绿跌（中国习惯）
  - `US`: 绿涨红跌（美国习惯）

**登录说明**：
- 系统启动时会在控制台打印登录账号和密码
- 可以通过环境变量 `LOGIN_USERNAME` 和 `LOGIN_PASSWORD` 自定义账号密码
- 所有页面和API接口都需要登录后才能访问

**颜色配置说明**：
- 默认使用红涨绿跌（中国习惯）
- 可通过环境变量 `STOCK_COLOR_SCHEME` 设置为 `US` 使用绿涨红跌（美国习惯）
- 颜色配置会应用到所有收益、收益率等数值显示

## 技术指标说明

### 支撑位和阻力位

- **支撑位** = L1 + P1 * 0.5/8
- **阻力位** = L1 + P1 * 7/8
- **中线** = (支撑 + 阻力) / 2

### 趋势线

基于SMA和EMA计算，用于识别买卖信号。

### 买卖信号

- **买入信号**：趋势线从下向上穿越10
- **卖出信号**：趋势线从上向下穿越90

## 数据格式

Excel文件应包含以下列：

- 日期/时间
- 开盘
- 最高
- 最低
- 收盘
- 成交量（可选）

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

- **工具层 (utils/)**: 通用工具函数
- **模型层 (models/)**: 数据模型和核心计算类
- **服务层 (services/)**: 业务逻辑服务
- **API层 (api/)**: HTTP接口路由
- **测试层 (tests/)**: 测试用例

### 扩展开发

1. **添加新的API接口**：在 `api/routes.py` 中添加路由
2. **添加新的服务**：在 `services/` 中创建服务类
3. **添加数据库支持**：在 `models/stock_data.py` 中定义模型
4. **添加测试用例**：在 `tests/` 中创建测试文件

## 许可证

本项目仅供学习和研究使用。
