"""
指标计算服务
负责计算股票技术指标和信号
"""

import pandas as pd
import logging
import traceback
from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period

# 配置日志
logger = logging.getLogger(__name__)


class IndicatorService:
    """指标计算服务类"""
    
    # 全局缓存，避免重复加载数据（按文件路径缓存）
    _cached_daily_data = {}
    
    @classmethod
    def get_daily_data(cls, file_path: str = 'data/159915.xlsx'):
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
    def calculate_signals(cls, period: str, file_path: str = 'data/159915.xlsx', 
                         start_date: str = None, end_date: str = None, buy_threshold: float = 10.0):
        """
        计算指定周期的买卖信号
        
        Args:
            period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
            file_path: 数据文件路径
            start_date: 开始日期（格式：'YYYY-MM-DD'），可选
            end_date: 结束日期（格式：'YYYY-MM-DD'），可选
            buy_threshold: 买入信号阈值，趋势线从下向上穿越此值进行买入（默认10.0）
            
        Returns:
            包含信号信息的字典
        """
        try:
            # 周期名称映射
            period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
            period_name = period_names.get(period.upper(), period)
            
            # 获取日线数据
            daily_df = cls.get_daily_data(file_path)
            
            # 计算20日均线（使用日线数据）
            if 'date' in daily_df.columns:
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                daily_df = daily_df.sort_values('date').reset_index(drop=True)
            
            # 按时间范围过滤日线数据（使用表格中的MA.MA3作为20日均线）
            if start_date:
                start_dt = pd.to_datetime(start_date)
                daily_df_filtered = daily_df[daily_df['date'] >= start_dt].copy()
            else:
                daily_df_filtered = daily_df.copy()
            
            if end_date:
                end_dt = pd.to_datetime(end_date)
                daily_df_filtered = daily_df_filtered[daily_df_filtered['date'] <= end_dt]
            
            # 使用表格中的MA.MA3作为20日均线（完全使用表格中的值，不计算）
            if 'ma20' not in daily_df_filtered.columns:
                return {
                    'success': False,
                    'error': '数据文件中未找到MA.MA3列（20日均线），请确保数据文件包含此列',
                    'error_code': 'MA20_COLUMN_NOT_FOUND'
                }
            
            # 完全使用表格中的MA.MA3值，不进行任何计算或填充
            # 对于NaN值，保持NaN，在后续使用时会跳过这些行
            
            # 创建日期到20日均线的映射（用于快速查找）
            daily_ma20_map = {}
            for idx, row in daily_df_filtered.iterrows():
                if pd.notna(row['ma20']):
                    daily_ma20_map[row['date']] = row['ma20']
            
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
            result_df = indicator.calculate_all(df.copy(), buy_threshold=buy_threshold)
            
            # 统计信号
            buy_signals_count = int(result_df['买'].sum())
            sell_signals_count = int(result_df['卖'].sum())
            oversold_count = int(result_df['超卖区'].sum())
            overbought_count = int(result_df['超买区'].sum())
            
            # 获取买入信号位置
            buy_positions = result_df[result_df['买'] == 1]
            buy_signals_list = []
            if len(buy_positions) > 0:
                # 包含买入原因列
                buy_cols = ['date', 'close', '趋势线', '买入原因']
                available_buy_cols = [col for col in buy_cols if col in buy_positions.columns]
                buy_display = buy_positions[available_buy_cols].copy()
                if 'date' in buy_display.columns:
                    buy_display['date'] = pd.to_datetime(buy_display['date'])
                    # 按日期倒序排序
                    buy_display = buy_display.sort_values('date', ascending=False)
                    buy_display['date'] = buy_display['date'].dt.strftime('%Y-%m-%d')
                for _, row in buy_display.iterrows():
                    signal_date = pd.to_datetime(row['date'])
                    # 获取该日期对应的日线20日均线
                    ma20_value = None
                    # 查找最接近的日线数据
                    for check_date in pd.date_range(end=signal_date, periods=10, freq='D'):
                        if check_date in daily_ma20_map:
                            ma20_value = daily_ma20_map[check_date]
                            break
                    
                    signal_item = {
                        'date': str(row['date']),
                        'close': float(row['close']),
                        'trend_line': float(row['趋势线']),
                        'ma20': float(ma20_value) if ma20_value is not None and pd.notna(ma20_value) else None
                    }
                    # 添加买入原因（如果有）
                    if '买入原因' in row:
                        signal_item['reason'] = str(row['买入原因']) if pd.notna(row['买入原因']) else '趋势线从下向上穿越10'
                    else:
                        signal_item['reason'] = '趋势线从下向上穿越10'
                    buy_signals_list.append(signal_item)
            
            # 获取卖出信号位置
            sell_positions = result_df[result_df['卖'] == 1]
            sell_signals_list = []
            if len(sell_positions) > 0:
                # 包含卖出原因列
                sell_cols = ['date', 'close', '趋势线', '卖出原因']
                available_sell_cols = [col for col in sell_cols if col in sell_positions.columns]
                sell_display = sell_positions[available_sell_cols].copy()
                if 'date' in sell_display.columns:
                    sell_display['date'] = pd.to_datetime(sell_display['date'])
                    # 按日期倒序排序
                    sell_display = sell_display.sort_values('date', ascending=False)
                    sell_display['date'] = sell_display['date'].dt.strftime('%Y-%m-%d')
                for _, row in sell_display.iterrows():
                    signal_date = pd.to_datetime(row['date'])
                    # 获取该日期对应的日线20日均线
                    ma20_value = None
                    # 查找最接近的日线数据
                    for check_date in pd.date_range(end=signal_date, periods=10, freq='D'):
                        if check_date in daily_ma20_map:
                            ma20_value = daily_ma20_map[check_date]
                            break
                    
                    signal_item = {
                        'date': str(row['date']),
                        'close': float(row['close']),
                        'trend_line': float(row['趋势线']),
                        'ma20': float(ma20_value) if ma20_value is not None and pd.notna(ma20_value) else None
                    }
                    # 添加卖出原因（如果有）
                    if '卖出原因' in row:
                        signal_item['reason'] = str(row['卖出原因']) if pd.notna(row['卖出原因']) else '-'
                    else:
                        signal_item['reason'] = '-'
                    sell_signals_list.append(signal_item)
            
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
            logger.error(f'数据文件未找到: {file_path}', exc_info=True)
            return {
                'success': False,
                'error': f'数据文件未找到: {file_path}',
                'error_code': 'FILE_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f'计算指标时发生错误: {str(e)}', exc_info=True)
            logger.error(f'错误堆栈:\n{traceback.format_exc()}')
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CALCULATION_ERROR'
            }




