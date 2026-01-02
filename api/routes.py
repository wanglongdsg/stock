"""
API路由定义
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import os
from services.indicator_service import IndicatorService
from services.backtest_service import BacktestService
from config import DATA_DIR

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


# API登录验证装饰器
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


@api_bp.route('/health', methods=['GET'])
def health():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常'
    }), 200


@api_bp.route('/calculate', methods=['POST'])
@api_login_required
def calculate():
    """
    计算股票技术指标信号
    """
    try:
        # 检查请求内容类型
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': '请求内容类型必须是 application/json',
                'error_code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        # 获取JSON数据
        data = request.get_json()
        
        if data is None:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'error_code': 'EMPTY_BODY'
            }), 400
        
        # 获取周期参数
        period = data.get('period', 'D').upper()
        
        # 验证周期参数
        if period not in ['D', 'W', 'M']:
            return jsonify({
                'success': False,
                'error': f'无效的周期参数: {period}，支持的值: D(日线), W(周线), M(月线)',
                'error_code': 'INVALID_PERIOD'
            }), 400
        
        # 获取股票代码
        stock_code = data.get('stock_code', '159915').strip()
        if not stock_code:
            stock_code = '159915'
        
        # 构建文件路径
        file_path = data.get('file_path')
        if not file_path:
            file_path = os.path.join(DATA_DIR, f'{stock_code}.xlsx')
        
        # 获取时间范围参数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 获取买入信号阈值（可选，默认10）
        buy_threshold = data.get('buy_threshold')
        if buy_threshold is not None and buy_threshold != '':
            try:
                buy_threshold = float(buy_threshold)
                if buy_threshold < 0 or buy_threshold > 100:
                    return jsonify({
                        'success': False,
                        'error': 'buy_threshold 必须在0-100之间',
                        'error_code': 'INVALID_BUY_THRESHOLD'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'buy_threshold 必须是有效的数字',
                    'error_code': 'INVALID_BUY_THRESHOLD'
                }), 400
        else:
            buy_threshold = 10.0  # 默认值
        
        # 计算信号
        result = IndicatorService.calculate_signals(period, file_path, start_date, end_date, buy_threshold)
        
        # 如果计算失败，返回错误
        if not result.get('success', False):
            return jsonify(result), 500
        
        # 返回成功结果
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'SERVER_ERROR'
        }), 500


@api_bp.route('/backtest', methods=['POST'])
@api_login_required
def backtest():
    """
    回测接口：按照买卖信号进行全仓回测
    """
    try:
        # 检查请求内容类型
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': '请求内容类型必须是 application/json',
                'error_code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        # 获取JSON数据
        data = request.get_json()
        
        if data is None:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'error_code': 'EMPTY_BODY'
            }), 400
        
        # 获取周期参数
        period = data.get('period', 'D').upper()
        
        # 验证周期参数
        if period not in ['D', 'W', 'M']:
            return jsonify({
                'success': False,
                'error': f'无效的周期参数: {period}，支持的值: D(日线), W(周线), M(月线)',
                'error_code': 'INVALID_PERIOD'
            }), 400
        
        # 获取初始资金
        initial_amount = data.get('initial_amount')
        if initial_amount is None:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: initial_amount',
                'error_code': 'MISSING_PARAMETER'
            }), 400
        
        try:
            initial_amount = float(initial_amount)
            if initial_amount <= 0:
                return jsonify({
                    'success': False,
                    'error': 'initial_amount 必须大于0',
                    'error_code': 'INVALID_AMOUNT'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'initial_amount 必须是有效的数字',
                'error_code': 'INVALID_AMOUNT'
            }), 400
        
        # 获取卖出策略列表（可选，默认全选）
        sell_strategies = data.get('sell_strategies', ['stop_loss', 'take_profit', 'below_ma20'])
        if not isinstance(sell_strategies, list):
            sell_strategies = ['stop_loss', 'take_profit', 'below_ma20']  # 默认全选
        
        # 验证策略名称
        valid_strategies = ['stop_loss', 'take_profit', 'below_ma20']
        sell_strategies = [s for s in sell_strategies if s in valid_strategies]
        
        if len(sell_strategies) == 0:
            return jsonify({
                'success': False,
                'error': '至少需要选择一种卖出策略',
                'error_code': 'NO_SELL_STRATEGY'
            }), 400
        
        # 根据选中的策略获取参数
        stop_loss_percent = None
        take_profit_percent = None
        below_ma20_days = None
        
        # 获取止损比例（如果选中了止损策略）
        if 'stop_loss' in sell_strategies:
            stop_loss_percent = data.get('stop_loss_percent', 5.0)
            try:
                stop_loss_percent = float(stop_loss_percent)
                if stop_loss_percent < 0 or stop_loss_percent > 50:
                    return jsonify({
                        'success': False,
                        'error': 'stop_loss_percent 必须在0-50之间',
                        'error_code': 'INVALID_STOP_LOSS'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'stop_loss_percent 必须是有效的数字',
                    'error_code': 'INVALID_STOP_LOSS'
                }), 400
        
        # 获取止盈比例（如果选中了止盈策略）
        if 'take_profit' in sell_strategies:
            take_profit_percent = data.get('take_profit_percent')
            if take_profit_percent is not None and take_profit_percent != '':
                try:
                    take_profit_percent = float(take_profit_percent)
                    if take_profit_percent < 0 or take_profit_percent > 200:
                        return jsonify({
                            'success': False,
                            'error': 'take_profit_percent 必须在0-200之间',
                            'error_code': 'INVALID_TAKE_PROFIT'
                        }), 400
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': 'take_profit_percent 必须是有效的数字',
                        'error_code': 'INVALID_TAKE_PROFIT'
                    }), 400
            else:
                take_profit_percent = None
        
        # 获取收盘价在20均线下方天数（如果选中了20均线策略）
        if 'below_ma20' in sell_strategies:
            below_ma20_days = data.get('below_ma20_days', 3)
            try:
                below_ma20_days = int(below_ma20_days)
                if below_ma20_days < 1 or below_ma20_days > 30:
                    return jsonify({
                        'success': False,
                        'error': 'below_ma20_days 必须在1-30之间',
                        'error_code': 'INVALID_BELOW_MA20_DAYS'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'below_ma20_days 必须是有效的整数',
                    'error_code': 'INVALID_BELOW_MA20_DAYS'
                }), 400
        
        # 获取买入信号阈值（可选，默认10）
        buy_threshold = data.get('buy_threshold')
        if buy_threshold is not None and buy_threshold != '':
            try:
                buy_threshold = float(buy_threshold)
                if buy_threshold < 0 or buy_threshold > 100:
                    return jsonify({
                        'success': False,
                        'error': 'buy_threshold 必须在0-100之间',
                        'error_code': 'INVALID_BUY_THRESHOLD'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'buy_threshold 必须是有效的数字',
                    'error_code': 'INVALID_BUY_THRESHOLD'
                }), 400
        else:
            buy_threshold = 10.0  # 默认值
        
        # 获取股票代码
        stock_code = data.get('stock_code', '159915').strip()
        if not stock_code:
            stock_code = '159915'
        
        # 构建文件路径
        file_path = data.get('file_path')
        if not file_path:
            file_path = os.path.join(DATA_DIR, f'{stock_code}.xlsx')
        
        # 获取时间范围参数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 计算回测结果
        result = BacktestService.calculate_backtest(
            period, initial_amount, file_path, start_date, end_date, 
            stop_loss_percent, take_profit_percent, buy_threshold, 
            below_ma20_days, sell_strategies
        )
        
        # 如果计算失败，返回错误
        if not result.get('success', False):
            return jsonify(result), 500
        
        # 返回成功结果
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'SERVER_ERROR'
        }), 500


def register_routes(app):
    """
    注册所有路由到Flask应用
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(api_bp)




