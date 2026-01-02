"""
股票技术指标计算 Web API
Flask应用入口
"""

from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
import logging
from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG, DEFAULT_DATA_FILE,
    FLASK_SECRET_KEY, LOGIN_USERNAME, LOGIN_PASSWORD,
    COLOR_RISE, COLOR_FALL
)
from api.routes import register_routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('app.log', encoding='utf-8')  # 输出到文件
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = FLASK_SECRET_KEY
CORS(app)  # 允许跨域请求

# 注册API路由
register_routes(app)

# 登录验证装饰器（用于页面路由）
def login_required(f):
    """登录验证装饰器（用于页面路由）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# API登录验证装饰器（用于API路由，返回JSON）
def api_login_required(f):
    """API登录验证装饰器（返回JSON错误）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return jsonify({
                'success': False,
                'error': '未登录或登录已过期，请先登录',
                'error_code': 'UNAUTHORIZED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面和处理"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # 验证账号密码
        if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return jsonify({
                'success': True,
                'redirect': url_for('index')
            })
        else:
            return jsonify({
                'success': False,
                'error': '账号或密码错误'
            }), 401
    
    # GET请求，显示登录页面
    # 如果已登录，重定向到首页
    if session.get('logged_in'):
        return redirect(url_for('index'))
    
    return render_template('login.html')


# 退出登录路由
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))


# 首页路由（重定向到计算指标页面）
@app.route('/index')
@app.route('/')
@login_required
def index():
    """首页 - 重定向到计算指标页面"""
    return redirect(url_for('calculate'))

# 计算指标页面路由
@app.route('/calculate')
@login_required
def calculate():
    """计算指标页面"""
    return render_template('calculate.html', 
                     username=session.get('username', '用户'),
                     color_rise=COLOR_RISE,
                     color_fall=COLOR_FALL)

# 回测分析页面路由
@app.route('/backtest')
@login_required
def backtest():
    """回测分析页面"""
    return render_template('backtest.html', 
                     username=session.get('username', '用户'),
                     color_rise=COLOR_RISE,
                     color_fall=COLOR_FALL)


@app.route('/api', methods=['GET'])
def api_info():
    """
    API信息接口
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
                    'file_path': '可选，数据文件路径，默认为 data/159915.xlsx'
                }
            },
            '/api/backtest': {
                'method': 'POST',
                'description': '回测接口：按照买卖信号进行全仓回测',
                'content_type': 'application/json',
                'request_body': {
                    'period': 'D|W|M (D=日线, W=周线, M=月线)',
                    'initial_amount': '初始资金金额（必填）',
                    'file_path': '可选，数据文件路径，默认为 data/159915.xlsx'
                }
            }
        }
    }), 200


if __name__ == '__main__':
    # 检查数据文件是否存在
    if not os.path.exists(DEFAULT_DATA_FILE):
        print(f"警告: 数据文件 {DEFAULT_DATA_FILE} 不存在，请确保文件存在后再启动服务")
    
    # 打印登录信息
    print("\n" + "="*60)
    print("股票技术指标分析系统")
    print("="*60)
    print(f"登录账号: {LOGIN_USERNAME}")
    print(f"登录密码: {LOGIN_PASSWORD}")
    print("="*60)
    print(f"服务地址: http://{FLASK_HOST}:{FLASK_PORT}")
    print("="*60 + "\n")
    
    # 启动Flask应用
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

