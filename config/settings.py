"""
配置文件
"""

import os

# 数据文件路径
DEFAULT_DATA_FILE = os.getenv('DATA_FILE', 'data/300760.xlsx')

# Flask配置
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# 数据库配置（预留）
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///stock.db')

# 指标计算参数
INDICATOR_N = int(os.getenv('INDICATOR_N', 5))

