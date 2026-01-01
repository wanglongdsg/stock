"""
回测服务
负责计算回测结果
"""

import pandas as pd
from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period
from services.indicator_service import IndicatorService


class BacktestService:
    """回测服务类"""
    
    @classmethod
    def calculate_backtest(cls, period: str, initial_amount: float, file_path: str = 'data/300760.xlsx'):
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
            daily_df = IndicatorService.get_daily_data(file_path)
            
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



