"""
回测服务
负责计算回测结果
"""

import pandas as pd
import numpy as np
import logging
import traceback
from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period
from services.indicator_service import IndicatorService

# 配置日志
logger = logging.getLogger(__name__)


def format_decimal(value, decimals=3):
    """
    格式化数值为指定小数位数
    
    Args:
        value: 要格式化的值（可以是None、NaN或数值）
        decimals: 小数位数，默认3位
        
    Returns:
        格式化后的浮点数，如果输入为None或NaN则返回None
    """
    if value is None or pd.isna(value):
        return None
    try:
        return round(float(value), decimals)
    except (ValueError, TypeError):
        return None


class BacktestService:
    """回测服务类"""
    
    @classmethod
    def calculate_backtest(cls, period: str, initial_amount: float, file_path: str = 'data/159915.xlsx',
                          start_date: str = None, end_date: str = None, stop_loss_percent: float = 5.0,
                          take_profit_percent: float = None, buy_threshold: float = 10.0, below_ma20_days: int = 3):
        """
        计算回测结果
        
        Args:
            period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
            initial_amount: 初始资金金额
            file_path: 数据文件路径
            start_date: 开始日期（格式：'YYYY-MM-DD'），可选
            end_date: 结束日期（格式：'YYYY-MM-DD'），可选
            stop_loss_percent: 止损比例（默认5%）
            take_profit_percent: 止盈比例（可选，None表示不设止盈）
            
        Returns:
            包含回测结果的字典
        """
        try:
            # 周期名称映射
            period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
            period_name = period_names.get(period.upper(), period)
            
            # 获取日线数据（使用表格中的MA.MA3作为20日均线）
            daily_df = IndicatorService.get_daily_data(file_path)
            
            # 确保日线数据按日期排序
            if 'date' in daily_df.columns:
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                daily_df = daily_df.sort_values('date').reset_index(drop=True)
                
                # 按时间范围过滤日线数据
                if start_date:
                    start_dt = pd.to_datetime(start_date)
                    daily_df = daily_df[daily_df['date'] >= start_dt]
                
                if end_date:
                    end_dt = pd.to_datetime(end_date)
                    daily_df = daily_df[daily_df['date'] <= end_dt]
            
            # 使用表格中的MA.MA3作为20日均线（完全使用表格中的值，不计算）
            if 'ma20' not in daily_df.columns:
                return {
                    'success': False,
                    'error': '数据文件中未找到MA.MA3列（20日均线），请确保数据文件包含此列',
                    'error_code': 'MA20_COLUMN_NOT_FOUND'
                }
            
            # 检查ma20列是否有有效值
            if daily_df['ma20'].notna().sum() == 0:
                return {
                    'success': False,
                    'error': '数据文件中的MA.MA3列（20日均线）没有有效值，请检查数据文件',
                    'error_code': 'MA20_NO_VALID_DATA'
                }
            
            # 完全使用表格中的MA.MA3值，不进行任何计算或填充
            # 对于NaN值，保持NaN，在后续使用时会跳过这些行
            
            
            # 创建日期到索引的映射（用于快速查找）
            daily_date_to_idx = {date: idx for idx, date in enumerate(daily_df['date'])}
            
            # 如果选择周线或月线，进行周期转换
            if period.upper() != 'D':
                df = convert_to_period(daily_df, period.upper())
            else:
                df = daily_df.copy()
            
            # 确保date列是datetime类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # 如果过滤后没有数据，返回错误
            if len(df) == 0:
                return {
                    'success': False,
                    'error': '指定时间范围内没有数据',
                    'error_code': 'NO_DATA_IN_RANGE'
                }
            
            # 检查日线数据是否为空
            if len(daily_df) == 0:
                return {
                    'success': False,
                    'error': '日线数据为空，无法计算20日均线',
                    'error_code': 'NO_DAILY_DATA'
                }
            
            # 创建指标计算器
            indicator = StockIndicator(n=5)
            
            # 计算所有指标
            result_df = indicator.calculate_all(df.copy(), buy_threshold=buy_threshold)
            
            # 确保数据按日期排序
            result_df = result_df.sort_values('date').reset_index(drop=True)
            result_df['date'] = pd.to_datetime(result_df['date'])
            
            # 检查数据是否足够
            if len(result_df) < 2:
                return {
                    'success': False,
                    'error': '数据不足，至少需要2条数据才能进行回测',
                    'error_code': 'INSUFFICIENT_DATA'
                }
            
            # 回测逻辑：新的买入卖出规则（优化版本）
            # 使用向量化操作和预计算数据加速
            cash = initial_amount  # 现金
            shares = 0  # 持仓数量
            position = False  # 是否持仓
            buy_trades = []  # 买入交易记录
            sell_trades = []  # 卖出交易记录
            buy_price = 0  # 买入价格（用于止损计算）
            buy_date_idx = -1  # 买入日期在日线数据中的索引
            buy_below_ma20 = False  # 买入时收盘价是否在20均线下方（只有这种情况才触发上穿策略）
            crossed_ma20 = False  # 是否已上穿20日线
            crossed_ma20_date_idx = -1  # 上穿20均线的日期索引（用于后续检查）
            close_below_ma20_days = 0  # 收盘价在20均线下方连续天数
            last_checked_daily_idx = -1  # 上次检查的日线数据索引
            last_ma20_check_idx = -1  # 上次检查20均线下方情况的日线索引
            
            # 将DataFrame转换为numpy数组以提高访问速度
            result_dates = result_df['date'].values
            result_buy_signals = result_df['买'].values
            result_opens = result_df['open'].values
            result_closes = result_df['close'].values
            
            daily_dates = daily_df['date'].values
            daily_ma20 = daily_df['ma20'].values
            daily_closes = daily_df['close'].values
            
            # 遍历数据，模拟交易
            for i in range(len(result_df) - 1):  # 最后一条数据不能买入，因为没有下一条数据
                current_date = result_dates[i]
                next_date = result_dates[i + 1]
                current_buy_signal = result_buy_signals[i]
                next_open = result_opens[i + 1]
                current_close = result_closes[i]
                next_close = result_closes[i + 1]
                
                # 快速获取当前日期对应的日线数据索引
                current_daily_idx = -1
                current_ma20_val = None
                
                if period.upper() == 'D':
                    # 日线：直接使用日期映射
                    current_daily_idx = daily_date_to_idx.get(current_date, -1)
                else:
                    # 周线/月线：从上次位置开始查找
                    start_idx = max(0, last_checked_daily_idx) if last_checked_daily_idx >= 0 else 0
                    # 使用numpy的searchsorted加速查找
                    insert_pos = np.searchsorted(daily_dates[start_idx:], current_date, side='right')
                    if insert_pos > 0:
                        current_daily_idx = start_idx + insert_pos - 1
                    elif start_idx > 0:
                        current_daily_idx = start_idx - 1
                
                if current_daily_idx >= 0 and current_daily_idx < len(daily_df):
                    current_ma20_val = daily_ma20[current_daily_idx]
                    last_checked_daily_idx = current_daily_idx
                
                # 买入信号：CROSS(趋势线,10) - 趋势线从下向上穿越10
                if current_buy_signal == 1 and not position:
                    # 第二天开盘价买入
                    buy_price = next_open
                    buy_amount = cash  # 使用当前现金全仓买入
                    shares = buy_amount / buy_price  # 全仓买入
                    cash = 0
                    position = True
                    
                    # 买入日期索引（用于后续20日均线检查）
                    if period.upper() == 'D':
                        buy_date_idx = daily_date_to_idx.get(next_date, -1)
                    else:
                        # 周线/月线：找到对应的日线索引
                        insert_pos = np.searchsorted(daily_dates, next_date, side='right')
                        buy_date_idx = insert_pos - 1 if insert_pos > 0 else -1
                    
                    # 检查买入时收盘价是否在20均线下方（只有这种情况才触发上穿策略）
                    buy_below_ma20 = False
                    if buy_date_idx >= 0 and buy_date_idx < len(daily_df):
                        buy_day_close = daily_closes[buy_date_idx] if buy_date_idx < len(daily_closes) else None
                        buy_day_ma20 = daily_ma20[buy_date_idx] if buy_date_idx < len(daily_ma20) else None
                        # 如果买入时收盘价在20均线下方，才启用上穿策略
                        if pd.notna(buy_day_close) and pd.notna(buy_day_ma20):
                            buy_below_ma20 = buy_day_close < buy_day_ma20
                    
                    crossed_ma20 = False  # 重置上穿标志（买入后需要等待上穿20均线）
                    crossed_ma20_date_idx = -1  # 重置上穿日期索引
                    close_below_ma20_days = 0  # 重置收盘价在20均线下方天数
                    last_checked_daily_idx = current_daily_idx if current_daily_idx >= 0 else -1
                    last_ma20_check_idx = -1  # 重置20均线检查索引
                    
                    # 注意：只有买入时收盘价在20均线下方，才启用"上穿20均线后回落3天卖出"策略
                    # 如果买入时已在20均线上方，则不启用此策略（只使用止盈和止损）
                    
                    buy_trades.append({
                        'date': pd.Timestamp(next_date).strftime('%Y-%m-%d'),
                        'price': format_decimal(buy_price),
                        'shares': format_decimal(shares),
                        'amount': format_decimal(buy_amount)
                    })
                
                # 卖出逻辑（仅在持仓时执行）
                elif position:
                    should_sell = False
                    sell_reason = ''
                    
                    # 计算当前盈亏比例
                    profit_percent = ((current_close - buy_price) / buy_price * 100) if buy_price > 0 else 0
                    
                    # 卖出条件1：止盈检查（如果设置了止盈比例）
                    if take_profit_percent is not None and profit_percent >= take_profit_percent:
                        should_sell = True
                        sell_reason = f'止盈({profit_percent:.2f}%)'
                    
                    # 卖出条件2：买入后上穿20均线，然后收盘价回落到20均线下方3天，第4天卖出
                    # 严格逻辑：
                    # 1. 只有买入时收盘价在20均线下方，才启用此策略
                    # 2. 必须先上穿20均线，然后才开始检查收盘价是否在20均线下方
                    # 注意：必须使用日线数据进行检查，而不是周期数据
                    elif not should_sell and buy_below_ma20 and buy_date_idx >= 0 and current_daily_idx >= 0:
                        # 第一步：检查是否上穿20均线（从买入日期之后开始检查）
                        if not crossed_ma20:
                            # 遍历从买入日期之后到当前日期的所有日线数据，检查是否有上穿动作
                            # 上穿：前一日收盘价 <= 20均线，当前收盘价 > 20均线
                            check_start_idx = buy_date_idx + 1  # 从买入日期的下一天开始检查
                            check_end_idx = current_daily_idx
                            
                            for check_idx in range(check_start_idx, check_end_idx + 1):
                                if check_idx < 1 or check_idx >= len(daily_df):
                                    continue
                                
                                # 获取当前和前一日的数据
                                prev_idx = check_idx - 1
                                if prev_idx < buy_date_idx:  # 确保前一日在买入日期之后或当天
                                    continue
                                
                                prev_close = daily_closes[prev_idx] if prev_idx < len(daily_closes) else None
                                prev_ma20 = daily_ma20[prev_idx] if prev_idx < len(daily_ma20) else None
                                curr_close = daily_closes[check_idx] if check_idx < len(daily_closes) else None
                                curr_ma20 = daily_ma20[check_idx] if check_idx < len(daily_ma20) else None
                                
                                # 检查是否上穿：前一日收盘价 <= 20均线，当前收盘价 > 20均线
                                # 注意：只使用表格中的MA.MA3值，如果值为NaN则跳过（不进行计算填充）
                                if (pd.notna(prev_ma20) and pd.notna(prev_close) and 
                                    pd.notna(curr_ma20) and pd.notna(curr_close) and
                                    prev_close <= prev_ma20 and curr_close > curr_ma20):
                                    crossed_ma20 = True
                                    crossed_ma20_date_idx = check_idx
                                    close_below_ma20_days = 0
                                    break  # 找到上穿后，停止检查
                        
                        # 第二步：如果已上穿20均线，检查收盘价是否在20均线下方
                        # 注意：需要从上穿日期之后开始，每天（日线）检查一次，累计连续在20均线下方的天数
                        if crossed_ma20 and crossed_ma20_date_idx >= 0:
                            # 从上穿日期的下一天开始，到当前日期，检查所有日线数据
                            # 确保检查的是连续的交易日，而不是周期数据
                            check_start_idx = max(crossed_ma20_date_idx + 1, last_ma20_check_idx + 1)
                            check_end_idx = current_daily_idx
                            
                            # 从上一次检查的位置之后开始，到当前日期，遍历所有日线数据
                            for check_idx in range(check_start_idx, check_end_idx + 1):
                                if check_idx >= len(daily_df):
                                    break
                                
                                daily_close = daily_closes[check_idx] if check_idx < len(daily_closes) else None
                                daily_ma20_val = daily_ma20[check_idx] if check_idx < len(daily_ma20) else None
                                
                                # 注意：只使用表格中的MA.MA3值，如果值为NaN则跳过（不进行计算填充）
                                if pd.notna(daily_ma20_val) and pd.notna(daily_close):
                                    if daily_close < daily_ma20_val:
                                        # 收盘价在20均线下方，累加计数
                                        close_below_ma20_days += 1
                                        
                                        # 如果连续below_ma20_days天在20均线下方，第(below_ma20_days+1)天卖出
                                        # 注意：当close_below_ma20_days == below_ma20_days时，表示已经连续below_ma20_days天在下方，第(below_ma20_days+1)天（当前这天）卖出
                                        if close_below_ma20_days == below_ma20_days:
                                            should_sell = True
                                            sell_reason = f'收盘价在20均线下方{below_ma20_days}天，第{below_ma20_days+1}天卖出'
                                            last_ma20_check_idx = check_idx  # 更新检查索引
                                            break  # 找到卖出条件后，停止检查
                                    else:
                                        # 如果收盘价回到20均线上方，重置计数
                                        close_below_ma20_days = 0
                            
                            # 更新最后检查的索引（即使没有卖出，也要更新）
                            if not should_sell:
                                last_ma20_check_idx = check_end_idx
                    
                    # 卖出条件3：止损检查
                    elif not should_sell and profit_percent <= -stop_loss_percent:
                        should_sell = True
                        sell_reason = f'止损({profit_percent:.2f}%)'
                    
                    # 执行卖出
                    if should_sell:
                        # 第二天开盘价卖出
                        sell_price = next_open
                        cash = shares * sell_price  # 全仓卖出
                        buy_amount = buy_trades[-1]['amount'] if buy_trades else initial_amount
                        profit = cash - buy_amount
                        profit_rate = (profit / buy_amount * 100) if buy_amount > 0 else 0
                        
                        sell_trades.append({
                            'date': pd.Timestamp(next_date).strftime('%Y-%m-%d'),
                            'price': format_decimal(sell_price),
                            'shares': format_decimal(shares),
                            'amount': format_decimal(cash),
                            'profit': format_decimal(profit),
                            'profit_rate': format_decimal(profit_rate),
                            'reason': sell_reason
                        })
                        shares = 0
                        position = False
                        buy_below_ma20 = False
                        crossed_ma20 = False
                        crossed_ma20_date_idx = -1
                        close_below_ma20_days = 0
                        last_checked_daily_idx = -1
                        last_ma20_check_idx = -1
                        buy_date_idx = -1
            
            # 如果最后还有持仓，按最后一天收盘价计算
            if position and len(result_df) > 0 and len(buy_trades) > 0:
                last_price = result_df.iloc[-1]['close']
                cash = shares * last_price
                buy_amount = buy_trades[-1]['amount']
                profit = cash - buy_amount
                profit_rate = (profit / buy_amount) * 100 if buy_amount > 0 else 0
                sell_trades.append({
                    'date': result_df.iloc[-1]['date'].strftime('%Y-%m-%d'),
                    'price': format_decimal(last_price),
                    'shares': format_decimal(shares),
                    'amount': format_decimal(cash),
                    'profit': format_decimal(profit),
                    'profit_rate': format_decimal(profit_rate)
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
                    'buy_price': format_decimal(buy_trade['price']),
                    'sell_date': sell_trade['date'],
                    'sell_price': format_decimal(sell_trade['price']),
                    'shares': format_decimal(buy_trade['shares']),
                    'profit': format_decimal(sell_trade['profit']),
                    'profit_rate': format_decimal(sell_trade['profit_rate']),
                    'reason': sell_trade.get('reason', '-')  # 获取卖出原因，如果没有则使用 '-'
                })
            
            # 按卖出日期倒序排序（最新的交易在前）
            trade_pairs.sort(key=lambda x: x['sell_date'], reverse=True)
            
            return {
                'success': True,
                'period': period.upper(),
                'period_name': period_name,
                'initial_amount': format_decimal(initial_amount),
                'final_amount': format_decimal(final_amount),
                'total_profit': format_decimal(total_profit),
                'total_profit_rate': format_decimal(total_profit_rate),
                'annual_profit_rate': format_decimal(annual_profit_rate),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'trading_days': int(days),
                'total_trades': len(trade_pairs),
                'trades': trade_pairs
            }
            
        except FileNotFoundError as e:
            logger.error(f'数据文件未找到: {file_path}', exc_info=True)
            return {
                'success': False,
                'error': f'数据文件未找到: {file_path}',
                'error_code': 'FILE_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f'回测计算时发生错误: {str(e)}', exc_info=True)
            logger.error(f'错误堆栈:\n{traceback.format_exc()}')
            return {
                'success': False,
                'error': str(e),
                'error_code': 'BACKTEST_ERROR'
            }




