"""
API路由定义
"""

from flask import Blueprint, request, jsonify
from services.indicator_service import IndicatorService
from services.backtest_service import BacktestService

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


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
        
        # 可选：获取文件路径参数
        file_path = data.get('file_path', 'data/300760.xlsx')
        
        # 计算信号
        result = IndicatorService.calculate_signals(period, file_path)
        
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
        
        # 可选：获取文件路径参数
        file_path = data.get('file_path', 'data/300760.xlsx')
        
        # 计算回测结果
        result = BacktestService.calculate_backtest(period, initial_amount, file_path)
        
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




