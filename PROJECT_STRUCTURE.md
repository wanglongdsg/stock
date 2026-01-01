# 项目结构说明

## 目录结构

```
stock/
├── app.py                 # Flask应用入口
├── config.py              # 配置文件
├── main.py                # 命令行工具入口
├── stock_indicator.py     # 旧版指标计算（保留兼容）
├── requirements.txt       # 依赖包列表
├── README.md              # 项目说明
├── API_DOCS.md            # API文档
├── PROJECT_STRUCTURE.md   # 项目结构说明（本文件）
│
├── data/                  # 数据目录
│   └── 300760.xlsx        # 股票数据文件
│
├── utils/                 # 工具类包
│   ├── __init__.py
│   ├── data_loader.py     # 数据加载工具
│   └── period_converter.py # 周期转换工具
│
├── services/              # 服务层
│   ├── __init__.py
│   ├── indicator_service.py  # 指标计算服务
│   └── backtest_service.py  # 回测服务
│
├── models/                # 数据模型（预留数据库）
│   ├── __init__.py
│   ├── indicator.py       # 指标计算类
│   └── stock_data.py      # 股票数据模型（预留）
│
├── api/                   # API路由
│   ├── __init__.py
│   └── routes.py          # 路由定义
│
└── tests/                 # 测试文件
    ├── test_api.py
    └── test_backtest.py
```

## 模块说明

### 1. utils/ - 工具类包
包含通用的工具函数，不包含业务逻辑。

- **data_loader.py**: 负责从Excel文件加载股票数据
- **period_converter.py**: 负责将日线数据转换为周线或月线数据

### 2. models/ - 数据模型
包含数据模型和核心计算类。

- **indicator.py**: 股票技术指标计算类（StockIndicator）
- **stock_data.py**: 股票数据模型（预留数据库使用）

### 3. services/ - 服务层
包含业务逻辑服务，处理具体的业务需求。

- **indicator_service.py**: 指标计算服务，封装指标计算逻辑
- **backtest_service.py**: 回测服务，封装回测计算逻辑

### 4. api/ - API路由
包含所有API路由定义。

- **routes.py**: 定义所有API端点，处理HTTP请求和响应

### 5. config.py - 配置文件
集中管理配置项，支持环境变量。

### 6. app.py - 应用入口
Flask应用的主入口文件，负责初始化应用和注册路由。

## 设计原则

1. **分层架构**: 工具层 -> 模型层 -> 服务层 -> API层
2. **单一职责**: 每个模块只负责一个功能
3. **依赖注入**: 服务层依赖模型层，API层依赖服务层
4. **可扩展性**: 预留数据库模型，便于后续扩展

## 使用方式

### 启动Web服务
```bash
python app.py
```

### 使用命令行工具
```bash
python main.py D  # 日线
python main.py W  # 周线
python main.py M  # 月线
```

## 扩展说明

### 添加数据库支持
1. 在 `models/stock_data.py` 中定义数据模型
2. 在 `services/` 中添加数据库操作服务
3. 在 `config.py` 中配置数据库连接

### 添加新的API接口
1. 在 `api/routes.py` 中添加新的路由函数
2. 在对应的服务层添加业务逻辑
3. 更新 `API_DOCS.md` 文档

### 添加新的工具函数
1. 在 `utils/` 包中创建新的工具模块
2. 在 `utils/__init__.py` 中导出



