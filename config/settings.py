"""
配置文件
"""

import os
import secrets

# 数据目录配置
DATA_DIR = os.getenv('DATA_DIR', 'data')

# 数据文件路径（默认）
DEFAULT_DATA_FILE = os.getenv('DATA_FILE', os.path.join(DATA_DIR, '300760.xlsx'))

# Flask配置
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Flask Session配置
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# 数据库配置（预留）
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///stock.db')

# 指标计算参数
INDICATOR_N = int(os.getenv('INDICATOR_N', 5))

# 登录配置
# 默认账号密码（可通过环境变量覆盖）
LOGIN_USERNAME = os.getenv('LOGIN_USERNAME', 'admin')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD', 'wl20272026')

# 股票涨跌颜色配置
# 支持 'CN' (红涨绿跌，中国习惯) 或 'US' (绿涨红跌，美国习惯)
STOCK_COLOR_SCHEME = os.getenv('STOCK_COLOR_SCHEME', 'CN').upper()

# 根据颜色方案设置涨跌颜色
if STOCK_COLOR_SCHEME == 'CN':
    # 中国习惯：红涨绿跌
    COLOR_RISE = '#ef4444'  # 红色
    COLOR_FALL = '#10b981'  # 绿色
else:
    # 美国习惯：绿涨红跌
    COLOR_RISE = '#10b981'  # 绿色
    COLOR_FALL = '#ef4444'  # 红色


