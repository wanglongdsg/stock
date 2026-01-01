"""
股票技术指标计算 Web API
提供RESTful API接口，支持日线、周线、月线信号查询
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from stock_indicator import StockIndicator, load_stock_data, convert_to_period
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量，缓存数据以提高性能
_cached_daily_data = None


def get_daily_data(file_path: str = 'data/300760.xlsx'):
    """
    获取日线数据（带缓存）
    
    Args:
        file_path: 数据文件路径
        
    Returns:
        日线数据DataFrame
    """
    global _cached_daily_data
    if _cached_daily_data is None:
        _cached_daily_data = load_stock_data(file_path)
    return _cached_daily_data


def calculate_signals(period: str, file_path: str = 'data/300760.xlsx'):
    """
    计算指定周期的买卖信号
    
    Args:
        period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
        file_path: 数据文件路径
        
    Returns:
        包含信号信息的字典
    """
    try:
        # 周期名称映射
        period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
        period_name = period_names.get(period.upper(), period)
        
        # 获取日线数据
        daily_df = get_daily_data(file_path)
        
        # 如果选择周线或月线，进行周期转换
        if period.upper() != 'D':
            df = convert_to_period(daily_df, period.upper())
        else:
            df = daily_df.copy()
        
        # 创建指标计算器
        indicator = StockIndicator(n=5)
        
        # 计算所有指标
        result_df = indicator.calculate_all(df.copy())
        
        # 统计信号
        buy_signals_count = int(result_df['买'].sum())
        sell_signals_count = int(result_df['卖'].sum())
        oversold_count = int(result_df['超卖区'].sum())
        overbought_count = int(result_df['超买区'].sum())
        
        # 获取买入信号位置
        buy_positions = result_df[result_df['买'] == 1]
        buy_signals_list = []
        if len(buy_positions) > 0:
            buy_display = buy_positions[['date', 'close', '趋势线']].copy()
            if 'date' in buy_display.columns:
                buy_display['date'] = pd.to_datetime(buy_display['date']).dt.strftime('%Y-%m-%d')
            for _, row in buy_display.iterrows():
                buy_signals_list.append({
                    'date': str(row['date']),
                    'close': float(row['close']),
                    'trend_line': float(row['趋势线'])
                })
        
        # 获取卖出信号位置
        sell_positions = result_df[result_df['卖'] == 1]
        sell_signals_list = []
        if len(sell_positions) > 0:
            sell_display = sell_positions[['date', 'close', '趋势线']].copy()
            if 'date' in sell_display.columns:
                sell_display['date'] = pd.to_datetime(sell_display['date']).dt.strftime('%Y-%m-%d')
            for _, row in sell_display.iterrows():
                sell_signals_list.append({
                    'date': str(row['date']),
                    'close': float(row['close']),
                    'trend_line': float(row['趋势线'])
                })
        
        # 获取最近20条关键指标数据
        key_cols = ['date', 'close', '支撑', '阻力', '中线', '趋势线', '买', '卖']
        available_cols = [col for col in key_cols if col in result_df.columns]
        recent_data = result_df[available_cols].tail(20).copy()
        if 'date' in recent_data.columns:
            recent_data['date'] = pd.to_datetime(recent_data['date']).dt.strftime('%Y-%m-%d')
        
        recent_data_list = []
        for _, row in recent_data.iterrows():
            data_item = {}
            for col in available_cols:
                value = row[col]
                if pd.notna(value):
                    if isinstance(value, (int, float)):
                        data_item[col] = float(value)
                    else:
                        data_item[col] = str(value)
                else:
                    data_item[col] = None
            recent_data_list.append(data_item)
        
        return {
            'success': True,
            'period': period.upper(),
            'period_name': period_name,
            'total_records': len(result_df),
            'statistics': {
                'buy_signals_count': buy_signals_count,
                'sell_signals_count': sell_signals_count,
                'oversold_count': oversold_count,
                'overbought_count': overbought_count
            },
            'buy_signals': buy_signals_list,
            'sell_signals': sell_signals_list,
            'recent_data': recent_data_list
        }
        
    except FileNotFoundError as e:
        return {
            'success': False,
            'error': f'数据文件未找到: {file_path}',
            'error_code': 'FILE_NOT_FOUND'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_code': 'CALCULATION_ERROR'
        }


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """
    计算股票技术指标信号
    
    请求体JSON格式:
    {
        "period": "D"  // D=日线, W=周线, M=月线
    }
    
    返回JSON格式:
    {
        "success": true,
        "period": "D",
        "period_name": "日线",
        "total_records": 1260,
        "statistics": {
            "buy_signals_count": 40,
            "sell_signals_count": 21,
            "oversold_count": 98,
            "overbought_count": 44
        },
        "buy_signals": [
            {
                "date": "2020-11-17",
                "close": 312.67,
                "trend_line": 14.16
            }
        ],
        "sell_signals": [...],
        "recent_data": [...]
    }
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
        result = calculate_signals(period, file_path)
        
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


@app.route('/api/health', methods=['GET'])
def health():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常'
    }), 200


def calculate_backtest(period: str, initial_amount: float, file_path: str = 'data/300760.xlsx'):
    """
    计算回测结果
    
    Args:
        period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
        initial_amount: 初始资金金额
        file_path: 数据文件路径
        
    Returns:
        包含回测结果的字典
    """
    try:
        # 周期名称映射
        period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
        period_name = period_names.get(period.upper(), period)
        
        # 获取日线数据
        daily_df = get_daily_data(file_path)
        
        # 如果选择周线或月线，进行周期转换
        if period.upper() != 'D':
            df = convert_to_period(daily_df, period.upper())
        else:
            df = daily_df.copy()
        
        # 创建指标计算器
        indicator = StockIndicator(n=5)
        
        # 计算所有指标
        result_df = indicator.calculate_all(df.copy())
        
        # 确保数据按日期排序
        result_df = result_df.sort_values('date').reset_index(drop=True)
        result_df['date'] = pd.to_datetime(result_df['date'])
        
        # 回测逻辑：出现买信号的第二天开盘购买，出现卖信号的第二天开盘出售
        # 由于是周期数据，第二天就是下一条数据
        cash = initial_amount  # 现金
        shares = 0  # 持仓数量
        position = False  # 是否持仓
        buy_trades = []  # 买入交易记录
        sell_trades = []  # 卖出交易记录
        
        # 遍历数据，模拟交易
        for i in range(len(result_df) - 1):  # 最后一条数据不能买入，因为没有下一条数据
            current_row = result_df.iloc[i]
            next_row = result_df.iloc[i + 1]
            
            # 买入信号：出现买信号的第二天开盘购买（全仓）
            if current_row['买'] == 1 and not position:
                # 第二天开盘价买入
                buy_price = next_row['open']
                buy_amount = cash  # 使用当前现金全仓买入
                shares = buy_amount / buy_price  # 全仓买入
                cash = 0
                position = True
                buy_trades.append({
                    'date': next_row['date'].strftime('%Y-%m-%d'),
                    'price': float(buy_price),
                    'shares': float(shares),
                    'amount': float(buy_amount)
                })
            
            # 卖出信号：出现卖信号的第二天开盘出售（全仓）
            elif current_row['卖'] == 1 and position:
                # 第二天开盘价卖出
                sell_price = next_row['open']
                cash = shares * sell_price  # 全仓卖出
                buy_amount = buy_trades[-1]['amount'] if buy_trades else initial_amount
                profit = cash - buy_amount
                profit_rate = (profit / buy_amount) * 100 if buy_amount > 0 else 0
                
                sell_trades.append({
                    'date': next_row['date'].strftime('%Y-%m-%d'),
                    'price': float(sell_price),
                    'shares': float(shares),
                    'amount': float(cash),
                    'profit': float(profit),
                    'profit_rate': float(profit_rate)
                })
                shares = 0
                position = False
                # 更新现金为卖出后的金额，用于下次买入
        
        # 如果最后还有持仓，按最后一天收盘价计算
        if position and len(result_df) > 0 and len(buy_trades) > 0:
            last_price = result_df.iloc[-1]['close']
            cash = shares * last_price
            buy_amount = buy_trades[-1]['amount']
            profit = cash - buy_amount
            profit_rate = (profit / buy_amount) * 100 if buy_amount > 0 else 0
            sell_trades.append({
                'date': result_df.iloc[-1]['date'].strftime('%Y-%m-%d'),
                'price': float(last_price),
                'shares': float(shares),
                'amount': float(cash),
                'profit': float(profit),
                'profit_rate': float(profit_rate)
            })
        
        # 计算总收益
        final_amount = cash
        total_profit = final_amount - initial_amount
        total_profit_rate = (total_profit / initial_amount) * 100 if initial_amount > 0 else 0
        
        # 计算年收益率
        start_date = result_df.iloc[0]['date']
        end_date = result_df.iloc[-1]['date']
        days = (end_date - start_date).days
        years = days / 365.25  # 考虑闰年
        annual_profit_rate = ((final_amount / initial_amount) ** (1 / years) - 1) * 100 if years > 0 and initial_amount > 0 else 0
        
        # 配对买卖交易
        trade_pairs = []
        for i in range(min(len(buy_trades), len(sell_trades))):
            buy_trade = buy_trades[i]
            sell_trade = sell_trades[i]
            trade_pairs.append({
                'buy_date': buy_trade['date'],
                'buy_price': buy_trade['price'],
                'sell_date': sell_trade['date'],
                'sell_price': sell_trade['price'],
                'shares': buy_trade['shares'],
                'profit': sell_trade['profit'],
                'profit_rate': sell_trade['profit_rate']
            })
        
        return {
            'success': True,
            'period': period.upper(),
            'period_name': period_name,
            'initial_amount': initial_amount,
            'final_amount': float(final_amount),
            'total_profit': float(total_profit),
            'total_profit_rate': float(total_profit_rate),
            'annual_profit_rate': float(annual_profit_rate),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'trading_days': int(days),
            'total_trades': len(trade_pairs),
            'trades': trade_pairs
        }
        
    except FileNotFoundError as e:
        return {
            'success': False,
            'error': f'数据文件未找到: {file_path}',
            'error_code': 'FILE_NOT_FOUND'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_code': 'BACKTEST_ERROR'
        }


@app.route('/api/backtest', methods=['POST'])
def backtest():
    """
    回测接口：按照买卖信号进行全仓回测
    
    请求体JSON格式:
    {
        "period": "D",  // D=日线, W=周线, M=月线
        "initial_amount": 100000  // 初始资金金额
    }
    
    返回JSON格式:
    {
        "success": true,
        "period": "D",
        "period_name": "日线",
        "initial_amount": 100000,
        "final_amount": 150000,
        "total_profit": 50000,
        "total_profit_rate": 50.0,
        "annual_profit_rate": 12.5,
        "start_date": "2020-10-26",
        "end_date": "2025-12-30",
        "trading_days": 1891,
        "total_trades": 20,
        "trades": [
            {
                "buy_date": "2020-11-18",
                "buy_price": 312.67,
                "sell_date": "2020-10-28",
                "sell_price": 336.08,
                "shares": 319.5,
                "profit": 7485.5,
                "profit_rate": 7.48
            }
        ]
    }
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
        result = calculate_backtest(period, initial_amount, file_path)
        
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
                },
                'response': {
                    'success': 'boolean',
                    'period': '周期类型',
                    'statistics': '统计信息',
                    'buy_signals': '买入信号列表',
                    'sell_signals': '卖出信号列表',
                    'recent_data': '最近20条数据'
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
                },
                'response': {
                    'success': 'boolean',
                    'total_profit': '总收益',
                    'total_profit_rate': '总收益率(%)',
                    'annual_profit_rate': '年收益率(%)',
                    'trades': '交易记录列表（包含买入日期、卖出日期等）'
                }
            }
        }
    }), 200


if __name__ == '__main__':
    # 检查数据文件是否存在
    data_file = 'data/300760.xlsx'
    if not os.path.exists(data_file):
        print(f"警告: 数据文件 {data_file} 不存在，请确保文件存在后再启动服务")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True)

