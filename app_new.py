"""
股票技术指标计算 Web API
Flask应用入口
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, DEFAULT_DATA_FILE
from api.routes import register_routes

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 注册API路由
register_routes(app)


@app.route('/', methods=['GET'])
def index():
    """
    根路径，返回API文档
    """
    return jsonify({
        'name': '股票技术指标计算 API',
        'version': '1.0.0',
        'description': '提供股票技术指标计算服务，支持日线、周线、月线信号查询和回测',
        'endpoints': {
            '/api/health': {
                'method': 'GET',
                'description': '健康检查接口'
            },
            '/api/calculate': {
                'method': 'POST',
                'description': '计算股票技术指标信号',
                'content_type': 'application/json',
                'request_body': {
                    'period': 'D|W|M (D=日线, W=周线, M=月线)',
                    'file_path': '可选，数据文件路径，默认为 data/300760.xlsx'
                }
            },
            '/api/backtest': {
                'method': 'POST',
                'description': '回测接口：按照买卖信号进行全仓回测',
                'content_type': 'application/json',
                'request_body': {
                    'period': 'D|W|M (D=日线, W=周线, M=月线)',
                    'initial_amount': '初始资金金额（必填）',
                    'file_path': '可选，数据文件路径，默认为 data/300760.xlsx'
                }
            }
        }
    }), 200


if __name__ == '__main__':
    # 检查数据文件是否存在
    if not os.path.exists(DEFAULT_DATA_FILE):
        print(f"警告: 数据文件 {DEFAULT_DATA_FILE} 不存在，请确保文件存在后再启动服务")
    
    # 启动Flask应用
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)



