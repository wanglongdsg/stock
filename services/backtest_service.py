"""
回测服务
负责计算回测结果
"""

import pandas as pd
import numpy as np
from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period
from services.indicator_service import IndicatorService


class BacktestService:
    """回测服务类"""
    
    @classmethod
    def calculate_backtest(cls, period: str, initial_amount: float, file_path: str = 'data/300760.xlsx',
                          start_date: str = None, end_date: str = None, stop_loss_percent: float = 5.0):
        """
        计算回测结果
        
        Args:
            period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
            initial_amount: 初始资金金额
            file_path: 数据文件路径
            start_date: 开始日期（格式：'YYYY-MM-DD'），可选
            end_date: 结束日期（格式：'YYYY-MM-DD'），可选
            stop_loss_percent: 止损比例（默认5%）
            
        Returns:
            包含回测结果的字典
        """
        try:
            # 周期名称映射
            period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
            period_name = period_names.get(period.upper(), period)
            
            # 获取日线数据（用于计算20日均线）
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
            
            # 计算20日均线（使用日线数据）
            daily_df['ma20'] = daily_df['close'].rolling(window=20, min_periods=1).mean()
            
            # 预先计算20日均线的变化（用于快速判断连续下跌）
            daily_df['ma20_change'] = daily_df['ma20'].diff()
            daily_df['ma20_declining'] = (daily_df['ma20_change'] < 0).astype(int)
            
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
            result_df = indicator.calculate_all(df.copy())
            
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
            crossed_ma20 = False  # 是否已上穿20日线
            ma20_decline_days = 0  # 20日均线连续下跌天数
            last_checked_daily_idx = -1  # 上次检查的日线数据索引
            
            # 将DataFrame转换为numpy数组以提高访问速度
            result_dates = result_df['date'].values
            result_buy_signals = result_df['买'].values
            result_opens = result_df['open'].values
            result_closes = result_df['close'].values
            
            daily_dates = daily_df['date'].values
            daily_ma20 = daily_df['ma20'].values
            daily_closes = daily_df['close'].values
            daily_ma20_declining = daily_df['ma20_declining'].values
            
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
                    
                    crossed_ma20 = False  # 重置上穿标志
                    ma20_decline_days = 0  # 重置下跌天数
                    last_checked_daily_idx = current_daily_idx if current_daily_idx >= 0 else -1
                    
                    # 检查买入时是否已在20日均线上方
                    if buy_date_idx >= 0 and buy_date_idx < len(daily_df):
                        if pd.notna(current_ma20_val) and next_close > current_ma20_val:
                            crossed_ma20 = True
                    
                    buy_trades.append({
                        'date': pd.Timestamp(next_date).strftime('%Y-%m-%d'),
                        'price': float(buy_price),
                        'shares': float(shares),
                        'amount': float(buy_amount)
                    })
                
                # 卖出逻辑（仅在持仓时执行）
                elif position:
                    should_sell = False
                    sell_reason = ''
                    
                    # 卖出条件1：止损检查（向量化计算）
                    loss_percent = ((current_close - buy_price) / buy_price * 100) if buy_price > 0 else 0
                    if loss_percent <= -stop_loss_percent:
                        should_sell = True
                        sell_reason = f'止损({loss_percent:.2f}%)'
                    
                    # 卖出条件2：20日均线连续3天下跌（优化版本）
                    # 使用向量化操作和预计算数据
                    if not should_sell and current_daily_idx >= 0 and buy_date_idx >= 0:
                        # 确定检查的日线数据范围
                        check_start_idx = max(buy_date_idx + 1, last_checked_daily_idx + 1) if last_checked_daily_idx >= 0 else (buy_date_idx + 1)
                        check_end_idx = current_daily_idx
                        
                        # 确保索引在有效范围内
                        check_start_idx = max(0, min(check_start_idx, len(daily_df)))
                        check_end_idx = max(0, min(check_end_idx, len(daily_df)))
                        
                        if check_start_idx < check_end_idx:
                            # 使用向量化操作批量检查
                            check_range = daily_ma20_declining[check_start_idx:check_end_idx]
                            check_closes = daily_closes[check_start_idx:check_end_idx]
                            check_ma20s = daily_ma20[check_start_idx:check_end_idx]
                            
                            # 检查是否上穿20日线
                            if not crossed_ma20:
                                # 向量化检查上穿
                                valid_mask = pd.notna(check_ma20s)
                                if np.any(valid_mask):
                                    cross_mask = (check_closes > check_ma20s) & valid_mask
                                    cross_indices = np.where(cross_mask)[0]
                                    if len(cross_indices) > 0:
                                        crossed_ma20 = True
                                        ma20_decline_days = 0
                            
                            if crossed_ma20:
                                # 检查连续下跌（使用预计算的declining标志）
                                # 只检查有效的MA20数据
                                valid_mask = pd.notna(check_ma20s)
                                if np.any(valid_mask):
                                    declining_sequence = check_range[valid_mask]
                                    
                                    # 使用numpy高效计算连续下跌天数
                                    if len(declining_sequence) > 0:
                                        # 找到所有连续下跌的段
                                        # 将数组转换为int类型，避免pandas的bool问题
                                        declining_int = declining_sequence.astype(int)
                                        
                                        # 计算连续为1（下跌）的段
                                        # 使用diff找到变化点
                                        diff = np.diff(np.concatenate(([0], declining_int, [0])))
                                        starts = np.where(diff == 1)[0]
                                        ends = np.where(diff == -1)[0]
                                        
                                        if len(starts) > 0 and len(ends) > 0:
                                            # 计算每段的长度
                                            lengths = ends - starts
                                            if len(lengths) > 0:
                                                max_decline = np.max(lengths)
                                                # 更新连续下跌天数（累加，但不超过当前检查范围的最大值）
                                                ma20_decline_days = max(ma20_decline_days, max_decline)
                                        
                                        # 如果连续3天下跌，卖出
                                        if ma20_decline_days >= 3:
                                            should_sell = True
                                            sell_reason = '20均线连续3天下跌'
                        
                        # 更新最后检查的索引
                        if current_daily_idx >= 0 and current_daily_idx < len(daily_df):
                            last_checked_daily_idx = current_daily_idx
                    
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
                            'price': float(sell_price),
                            'shares': float(shares),
                            'amount': float(cash),
                            'profit': float(profit),
                            'profit_rate': float(profit_rate),
                            'reason': sell_reason
                        })
                        shares = 0
                        position = False
                        crossed_ma20 = False
                        ma20_decline_days = 0
                        last_checked_daily_idx = -1
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
                    'profit_rate': sell_trade['profit_rate'],
                    'reason': sell_trade.get('reason', '-')  # 获取卖出原因，如果没有则使用 '-'
                })
            
            # 按卖出日期倒序排序（最新的交易在前）
            trade_pairs.sort(key=lambda x: x['sell_date'], reverse=True)
            
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




