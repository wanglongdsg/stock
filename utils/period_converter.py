"""
周期转换工具
负责将日线数据转换为周线或月线数据
"""

import pandas as pd


def convert_to_period(df: pd.DataFrame, period: str = 'D') -> pd.DataFrame:
    """
    将日线数据转换为周线或月线数据
    
    Args:
        df: 日线数据DataFrame，必须包含'date', 'open', 'high', 'low', 'close', 'volume'列
        period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线
        
    Returns:
        转换后的DataFrame
    """
    if period == 'D':
        return df.copy()
    
    # 确保date列是datetime类型
    if 'date' not in df.columns:
        raise ValueError("数据必须包含'date'列")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # 设置date为索引以便进行resample
    df_indexed = df.set_index('date')
    
    if period == 'W':
        # 周线：按照自然周（周一到周日）计算
        # 开盘：自然周内第一个交易日的开盘价
        # 收盘：自然周内最后一个交易日的收盘价
        # 最高：自然周内最高价
        # 最低：自然周内最低价
        # 成交量：自然周内成交量之和
        # 使用 'W-SUN' 表示周一到周日（周日作为周结束标签）
        weekly = pd.DataFrame()
        weekly['open'] = df_indexed['open'].resample('W-SUN', label='right', closed='right').first()
        weekly['close'] = df_indexed['close'].resample('W-SUN', label='right', closed='right').last()
        weekly['high'] = df_indexed['high'].resample('W-SUN', label='right', closed='right').max()
        weekly['low'] = df_indexed['low'].resample('W-SUN', label='right', closed='right').min()
        if 'volume' in df_indexed.columns:
            weekly['volume'] = df_indexed['volume'].resample('W-SUN', label='right', closed='right').sum()
        # 日期使用自然周的结束日期（周日）
        weekly['date'] = weekly.index
        weekly = weekly.reset_index(drop=True)
        result = weekly
        
    elif period == 'M':
        # 月线：按照自然月（1号到月末）计算
        # 开盘：自然月内第一个交易日的开盘价
        # 收盘：自然月内最后一个交易日的收盘价
        # 最高：自然月内最高价
        # 最低：自然月内最低价
        # 成交量：自然月内成交量之和
        # 使用 'ME' 表示自然月末（月末最后一天作为标签）
        monthly = pd.DataFrame()
        monthly['open'] = df_indexed['open'].resample('ME', label='right', closed='right').first()
        monthly['close'] = df_indexed['close'].resample('ME', label='right', closed='right').last()
        monthly['high'] = df_indexed['high'].resample('ME', label='right', closed='right').max()
        monthly['low'] = df_indexed['low'].resample('ME', label='right', closed='right').min()
        if 'volume' in df_indexed.columns:
            monthly['volume'] = df_indexed['volume'].resample('ME', label='right', closed='right').sum()
        # 日期使用自然月的结束日期（月末最后一天）
        monthly['date'] = monthly.index
        monthly = monthly.reset_index(drop=True)
        result = monthly
    else:
        raise ValueError(f"不支持的周期类型: {period}，支持的类型: 'D'(日线), 'W'(周线), 'M'(月线)")
    
    return result








