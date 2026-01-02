"""
回测服务
负责计算回测结果
"""

import pandas as pd
import numpy as np
import logging
import traceback
from typing import List
from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period
from services.indicator_service import IndicatorService
from services.sell_strategies import create_strategy, SellStrategy

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
                          start_date: str = None, end_date: str = None, stop_loss_percent: float = None,
                          take_profit_percent: float = None, buy_threshold: float = 10.0, below_ma20_days: int = None,
                          sell_strategies: list = None, trailing_stop_percent: float = None, strategy_relation: str = 'OR',
                          below_ma20_min_profit: float = None):
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
            
            # 数据验证：确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success': False,
                    'error': f'数据文件缺少必需的列: {", ".join(missing_columns)}',
                    'error_code': 'MISSING_COLUMNS'
                }
            
            # 数据验证：确保价格数据有效
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if df[col].isna().all():
                    return {
                        'success': False,
                        'error': f'列 {col} 的数据全部为NaN，无法进行回测',
                        'error_code': 'INVALID_PRICE_DATA'
                    }
            
            # 创建指标计算器
            indicator = StockIndicator(n=5)
            
            # 计算所有指标
            try:
                result_df = indicator.calculate_all(df.copy(), buy_threshold=buy_threshold)
            except ValueError as e:
                # 处理指标计算中的值错误
                logger.error(f'指标计算时发生值错误: {str(e)}', exc_info=True)
                return {
                    'success': False,
                    'error': f'指标计算失败: {str(e)}',
                    'error_code': 'INDICATOR_CALCULATION_ERROR'
                }
            
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
            
            # 初始化卖出策略列表（如果未提供，默认全选）
            if sell_strategies is None:
                active_strategy_names = ['stop_loss', 'take_profit', 'below_ma20']
            else:
                active_strategy_names = sell_strategies
            
            # 创建策略实例
            strategy_instances: List[SellStrategy] = []
            strategy_kwargs = {
                'stop_loss_percent': stop_loss_percent,
                'take_profit_percent': take_profit_percent,
                'below_ma20_days': below_ma20_days,
                'below_ma20_min_profit': below_ma20_min_profit,
                'trailing_stop_percent': trailing_stop_percent
            }
            
            for strategy_name in active_strategy_names:
                strategy = create_strategy(strategy_name, **strategy_kwargs)
                if strategy:
                    strategy_instances.append(strategy)
            
            if len(strategy_instances) == 0:
                return {
                    'success': False,
                    'error': '至少需要选择一种卖出策略',
                    'error_code': 'NO_SELL_STRATEGY'
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
            last_checked_daily_idx = -1  # 上次检查的日线数据索引
            
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
                
                # 买入信号：CROSS(趋势线,buy_threshold) - 趋势线从下向上穿越buy_threshold
                if current_buy_signal == 1 and not position:
                    # 验证下一天的开盘价是否有效
                    if pd.isna(next_open) or next_open <= 0:
                        # 如果下一天开盘价无效，跳过此次买入信号
                        logger.warning(f'日期 {current_date} 的买入信号被跳过：下一天开盘价无效 (next_open={next_open})')
                        continue
                    
                    # 验证现金是否足够（虽然全仓买入，但需要确保有现金）
                    if cash <= 0:
                        logger.warning(f'日期 {current_date} 的买入信号被跳过：现金不足 (cash={cash})')
                        continue
                    
                    # 第二天开盘价买入
                    buy_price = float(next_open)
                    buy_amount = cash  # 使用当前现金全仓买入
                    
                    # 计算买入股数，确保不会因为价格问题导致除零或负数
                    if buy_price > 0:
                        shares = buy_amount / buy_price
                    else:
                        logger.error(f'日期 {current_date} 的买入信号被跳过：买入价格无效 (buy_price={buy_price})')
                        continue
                    
                    # 验证买入股数是否有效
                    if shares <= 0 or pd.isna(shares):
                        logger.error(f'日期 {current_date} 的买入信号被跳过：买入股数无效 (shares={shares})')
                        continue
                    
                    cash = 0
                    position = True
                    
                    # 买入日期索引（用于后续20日均线检查）
                    buy_date_idx = -1
                    if period.upper() == 'D':
                        buy_date_idx = daily_date_to_idx.get(next_date, -1)
                    else:
                        # 周线/月线：找到对应的日线索引
                        # 使用numpy的searchsorted加速查找
                        insert_pos = np.searchsorted(daily_dates, next_date, side='right')
                        if insert_pos > 0:
                            buy_date_idx = insert_pos - 1
                        else:
                            # 如果找不到，尝试查找最接近的日期（向前查找）
                            buy_date_idx = -1
                    
                    # 如果找不到买入日期索引，记录警告但继续执行
                    if buy_date_idx < 0:
                        logger.warning(f'无法找到买入日期 {next_date} 对应的日线索引，20均线策略可能无法正常工作')
                    
                    # 检查买入时收盘价是否在20均线下方（只有这种情况才触发上穿策略）
                    buy_below_ma20 = False
                    if buy_date_idx >= 0 and buy_date_idx < len(daily_df):
                        buy_day_close = daily_closes[buy_date_idx] if buy_date_idx < len(daily_closes) else None
                        buy_day_ma20 = daily_ma20[buy_date_idx] if buy_date_idx < len(daily_ma20) else None
                        # 如果买入时收盘价在20均线下方，才启用上穿策略
                        if pd.notna(buy_day_close) and pd.notna(buy_day_ma20):
                            buy_below_ma20 = buy_day_close < buy_day_ma20
                    
                    last_checked_daily_idx = current_daily_idx if current_daily_idx >= 0 else -1
                    
                    # 重置所有策略状态并设置买入信息
                    for strategy in strategy_instances:
                        try:
                            strategy.reset()
                            # 为需要买入信息的策略设置信息
                            strategy_name = strategy.get_name()
                            if strategy_name == 'below_ma20':
                                strategy.set_buy_info(buy_date_idx, buy_below_ma20)
                            elif strategy_name == 'trailing_stop_loss':
                                strategy.set_buy_info(buy_price, buy_date_idx)
                            elif strategy_name == 'stop_loss':
                                strategy.set_buy_info(buy_date_idx)
                            elif strategy_name == 'take_profit':
                                strategy.set_buy_info(buy_date_idx)
                        except Exception as e:
                            logger.warning(f'设置策略 {strategy_name} 买入信息时发生错误: {str(e)}', exc_info=True)
                            # 继续执行，不中断回测流程
                    
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
                    
                    # 构建策略上下文
                    strategy_context = {
                        'position': position,
                        'current_close': current_close,
                        'buy_price': buy_price,
                        'buy_date_idx': buy_date_idx,
                        'current_daily_idx': current_daily_idx,
                        'daily_df': daily_df,
                        'daily_closes': daily_closes,
                        'daily_ma20': daily_ma20,
                        'result_df': result_df,
                        'period': period
                    }
                    
                    # 根据策略关系（AND/OR）判断是否卖出
                    if strategy_relation.upper() == 'AND':
                        # AND关系：所有策略都必须触发才卖出
                        triggered_strategies = []
                        all_triggered = True
                        
                        for strategy in strategy_instances:
                            try:
                                sell, reason = strategy.should_sell(strategy_context)
                                if sell:
                                    triggered_strategies.append(reason)
                                else:
                                    all_triggered = False
                            except Exception as e:
                                logger.warning(f'策略 {strategy.get_name()} 判断卖出时发生错误: {str(e)}', exc_info=True)
                                # 如果策略出错，在AND模式下视为未触发
                                all_triggered = False
                        
                        if all_triggered and len(triggered_strategies) > 0:
                            should_sell = True
                            sell_reason = ' & '.join(triggered_strategies)  # 组合所有触发的原因
                    else:
                        # OR关系（默认）：任一策略触发即卖出
                        for strategy in strategy_instances:
                            try:
                                sell, reason = strategy.should_sell(strategy_context)
                                if sell:
                                    should_sell = True
                                    sell_reason = reason
                                    break  # 任一策略触发卖出即执行
                            except Exception as e:
                                logger.warning(f'策略 {strategy.get_name()} 判断卖出时发生错误: {str(e)}', exc_info=True)
                                # 如果策略出错，在OR模式下继续检查其他策略
                                continue
                    
                    # 执行卖出
                    if should_sell:
                        # 验证下一天的开盘价是否有效
                        if pd.isna(next_open) or next_open <= 0:
                            logger.warning(f'日期 {current_date} 的卖出信号被跳过：下一天开盘价无效 (next_open={next_open})')
                            continue
                        
                        # 验证持仓数量是否有效
                        if shares <= 0 or pd.isna(shares):
                            logger.warning(f'日期 {current_date} 的卖出信号被跳过：持仓数量无效 (shares={shares})')
                            continue
                        
                        # 第二天开盘价卖出
                        sell_price = float(next_open)
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
                        last_checked_daily_idx = -1
                        buy_date_idx = -1
                        
                        # 重置所有策略状态
                        for strategy in strategy_instances:
                            try:
                                strategy.reset()
                            except Exception as e:
                                logger.warning(f'重置策略 {strategy.get_name()} 状态时发生错误: {str(e)}', exc_info=True)
                                # 继续执行，不中断回测流程
            
            # 如果最后还有持仓，按最后一天收盘价计算
            if position and len(result_df) > 0 and len(buy_trades) > 0:
                last_price = result_df.iloc[-1]['close']
                
                # 验证最后一天收盘价是否有效
                if pd.isna(last_price) or last_price <= 0:
                    logger.warning(f'最后一天收盘价无效 (last_price={last_price})，使用买入价格计算')
                    last_price = buy_price if buy_price > 0 else buy_trades[-1]['price']
                
                # 验证持仓数量是否有效
                if shares > 0 and not pd.isna(shares):
                    cash = shares * float(last_price)
                    buy_amount = buy_trades[-1]['amount']
                    profit = cash - buy_amount
                    profit_rate = (profit / buy_amount) * 100 if buy_amount > 0 else 0
                else:
                    logger.warning(f'最后持仓数量无效 (shares={shares})，跳过最终结算')
                    cash = 0
                    profit = 0
                    profit_rate = 0
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




