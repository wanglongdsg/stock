# 测试用例说明

## 目录结构

```
tests/
├── __init__.py          # 测试包初始化
├── test_api.py          # API接口测试
├── test_backtest.py     # 回测接口测试
├── test_all.py          # 统一测试入口
└── README.md            # 本文件
```

## 测试文件说明

### 1. test_api.py

测试API接口功能，包括：
- 健康检查接口
- 计算接口（日线、周线、月线）

**运行方式**:
```bash
python tests/test_api.py
```

### 2. test_backtest.py

测试回测接口功能，包括：
- 日线回测
- 周线回测
- 月线回测

**运行方式**:
```bash
python tests/test_backtest.py
```

### 3. test_all.py

统一测试入口，运行所有测试用例。

**运行方式**:
```bash
python tests/test_all.py
```

## 使用说明

### 前置条件

1. **启动服务**: 在运行测试前，需要先启动API服务
   ```bash
   python app.py
   ```

2. **安装依赖**: 确保已安装测试所需的依赖
   ```bash
   pip install -r requirements.txt
   ```

### 运行测试

#### 方式一：运行单个测试文件

```bash
# 测试API接口
python tests/test_api.py

# 测试回测接口
python tests/test_backtest.py
```

#### 方式二：运行所有测试

```bash
python tests/test_all.py
```

#### 方式三：使用Python模块方式

```bash
# 从项目根目录运行
python -m tests.test_api
python -m tests.test_backtest
python -m tests.test_all
```

## 测试配置

### 修改测试服务器地址

如果API服务运行在不同的地址或端口，可以修改测试文件中的 `BASE_URL`:

```python
BASE_URL = "http://localhost:5000"  # 修改为实际地址
```

### 测试参数

可以在测试函数中修改测试参数：

```python
# 修改初始资金
test_backtest('D', 200000)  # 使用20万初始资金

# 测试不同周期
test_calculate('W')  # 测试周线
```

## 测试输出

测试会输出详细的测试结果，包括：
- 请求状态码
- 响应数据
- 统计信息
- 错误信息（如果有）

## 注意事项

1. **服务必须运行**: 所有测试都需要API服务处于运行状态
2. **数据文件**: 确保 `data/300760.xlsx` 文件存在
3. **网络连接**: 确保可以访问测试服务器地址
4. **依赖安装**: 确保已安装 `requests` 库

## 扩展测试

### 添加新的测试用例

1. 在 `tests/` 目录下创建新的测试文件
2. 遵循命名规范：`test_*.py`
3. 在 `test_all.py` 中添加新的测试调用

### 示例

```python
# tests/test_custom.py
def test_custom_feature():
    """测试自定义功能"""
    # 测试代码
    pass
```

然后在 `test_all.py` 中调用：

```python
from tests.test_custom import test_custom_feature

# 在 run_all_tests() 中添加
results['custom'] = test_custom_feature()
```



