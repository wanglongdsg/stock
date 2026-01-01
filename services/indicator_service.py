"""
指标计算服务
负责计算股票技术指标和信号
"""

import pandas as pd
from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period


class IndicatorService:
    """指标计算服务类"""
    
    # 全局缓存，避免重复加载数据（按文件路径缓存）
    _cached_daily_data = {}
    
    @classmethod
    def get_daily_data(cls, file_path: str = 'data/300760.xlsx'):
        """
        获取日线数据（带缓存）
        
        Args:
            file_path: 数据文件路径

        Returns:
            日线数据DataFrame
        """
        # 使用文件路径作为缓存键
        if file_path not in cls._cached_daily_data:
            cls._cached_daily_data[file_path] = load_stock_data(file_path)
        return cls._cached_daily_data[file_path]
    
    @classmethod
    def calculate_signals(cls, period: str, file_path: str = 'data/300760.xlsx', 
                         start_date: str = None, end_date: str = None):
        """
        计算指定周期的买卖信号
        
        Args:
            period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
            file_path: 数据文件路径
            start_date: 开始日期（格式：'YYYY-MM-DD'），可选
            end_date: 结束日期（格式：'YYYY-MM-DD'），可选
            
        Returns:
            包含信号信息的字典
        """
        try:
            # 周期名称映射
            period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
            period_name = period_names.get(period.upper(), period)
            
            # 获取日线数据
            daily_df = cls.get_daily_data(file_path)
            
            # 如果选择周线或月线，进行周期转换
            if period.upper() != 'D':
                df = convert_to_period(daily_df, period.upper())
            else:
                df = daily_df.copy()
            
            # 确保date列是datetime类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
                # 按时间范围过滤数据
                if start_date:
                    start_dt = pd.to_datetime(start_date)
                    df = df[df['date'] >= start_dt]
                
                if end_date:
                    end_dt = pd.to_datetime(end_date)
                    df = df[df['date'] <= end_dt]
            
            # 如果过滤后没有数据，返回错误
            if len(df) == 0:
                return {
                    'success': False,
                    'error': '指定时间范围内没有数据',
                    'error_code': 'NO_DATA_IN_RANGE'
                }
            
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
                    buy_display['date'] = pd.to_datetime(buy_display['date'])
                    # 按日期倒序排序
                    buy_display = buy_display.sort_values('date', ascending=False)
                    buy_display['date'] = buy_display['date'].dt.strftime('%Y-%m-%d')
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
                    sell_display['date'] = pd.to_datetime(sell_display['date'])
                    # 按日期倒序排序
                    sell_display = sell_display.sort_values('date', ascending=False)
                    sell_display['date'] = sell_display['date'].dt.strftime('%Y-%m-%d')
                for _, row in sell_display.iterrows():
                    sell_signals_list.append({
                        'date': str(row['date']),
                        'close': float(row['close']),
                        'trend_line': float(row['趋势线'])
                    })
            
            # 获取最近20条关键指标数据（按日期倒序）
            key_cols = ['date', 'close', '支撑', '阻力', '中线', '趋势线', '买', '卖']
            available_cols = [col for col in key_cols if col in result_df.columns]
            recent_data = result_df[available_cols].tail(20).copy()
            if 'date' in recent_data.columns:
                recent_data['date'] = pd.to_datetime(recent_data['date'])
                # 按日期倒序排序
                recent_data = recent_data.sort_values('date', ascending=False)
                recent_data['date'] = recent_data['date'].dt.strftime('%Y-%m-%d')
            
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




