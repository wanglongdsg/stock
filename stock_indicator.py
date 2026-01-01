"""
股票技术指标计算 - 基于通达信公式转换
实现趋势线、支撑阻力、买卖信号等技术指标
"""

import pandas as pd
import numpy as np
from typing import Tuple


class StockIndicator:
    """股票技术指标计算类"""
    
    def __init__(self, n: int = 5):
        """
        初始化
        
        Args:
            n: 计算周期，默认5
        """
        self.n = n
    
    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """
        简单移动平均线
        
        Args:
            data: 数据序列
            period: 周期
            
        Returns:
            移动平均线序列
        """
        return data.rolling(window=period, min_periods=1).mean()
    
    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        指数移动平均线
        
        Args:
            data: 数据序列
            period: 周期
            
        Returns:
            指数移动平均线序列
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算支撑位、阻力位和中线
        
        Args:
            df: 包含股票数据的DataFrame，需要包含'close', 'high', 'low'列
            
        Returns:
            添加了支撑、阻力、中线列的DataFrame
        """
        # DYNAINFO(3) 昨收, DYNAINFO(5) 最高, DYNAINFO(6) 最低
        # 使用前一日的数据作为参考
        prev_close = df['close'].shift(1).fillna(df['close'].iloc[0])
        prev_high = df['high'].shift(1).fillna(df['high'].iloc[0])
        prev_low = df['low'].shift(1).fillna(df['low'].iloc[0])
        
        # H1 = MAX(昨收, 最高)
        h1 = np.maximum(prev_close, prev_high)
        
        # L1 = MIN(昨收, 最低)
        l1 = np.minimum(prev_close, prev_low)
        
        # P1 = H1 - L1
        p1 = h1 - l1
        
        # 阻力 = L1 + P1 * 7/8
        df['阻力'] = l1 + p1 * 7 / 8
        
        # 支撑 = L1 + P1 * 0.5/8
        df['支撑'] = l1 + p1 * 0.5 / 8
        
        # 中线 = (支撑 + 阻力) / 2
        df['中线'] = (df['支撑'] + df['阻力']) / 2
        
        return df
    
    def calculate_trend_line(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算趋势线
        
        Args:
            df: 包含股票数据的DataFrame，需要包含'close', 'high', 'low'列
            
        Returns:
            添加了趋势线相关列的DataFrame
        """
        close = df['close']
        high = df['high']
        low = df['low']
        
        # 计算N周期内的最高价和最低价
        hhv = high.rolling(window=self.n, min_periods=1).max()
        llv = low.rolling(window=self.n, min_periods=1).min()
        
        # 避免除零
        denominator = hhv - llv
        denominator = denominator.replace(0, np.nan)
        
        # (C-LLV(L,N))/(HHV(H,N)-LLV(L,N))*100
        ratio = (close - llv) / denominator * 100
        ratio = ratio.fillna(50)  # 如果分母为0，填充50（中间值）
        
        # 第一层SMA: SMA(ratio, 5, 1)
        sma1 = self.sma(ratio, 5)
        
        # 第二层SMA: SMA(SMA(ratio, 5, 1), 3, 1)
        sma2 = self.sma(sma1, 3)
        
        # V11 = 3*SMA1 - 2*SMA2
        v11 = 3 * sma1 - 2 * sma2
        
        # 趋势线 = EMA(V11, 3)
        df['趋势线'] = self.ema(v11, 3)
        
        # V12 = (趋势线 - REF(趋势线,1)) / REF(趋势线,1) * 100
        df['V12'] = (df['趋势线'] - df['趋势线'].shift(1)) / df['趋势线'].shift(1).replace(0, np.nan) * 100
        
        return df
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算买卖信号
        
        Args:
            df: 包含趋势线和价格数据的DataFrame
            
        Returns:
            添加了信号列的DataFrame
        """
        trend_line = df['趋势线']
        close = df['close']
        midline = df['中线']
        
        # 超卖区判断 (趋势线 < 10)
        df['超卖区'] = (trend_line < 10).astype(int)
        
        # 超买区判断 (趋势线 > 90)
        df['超买区'] = (trend_line > 90).astype(int)
        
        # 买入信号: CROSS(趋势线, 10) - 趋势线从下向上穿越10
        df['买'] = ((trend_line > 10) & (trend_line.shift(1) <= 10)).astype(int)
        
        # 卖出信号: CROSS(90, 趋势线) - 趋势线从上向下穿越90
        df['卖'] = ((trend_line < 90) & (trend_line.shift(1) >= 90)).astype(int)
        
        # AA条件: (趋势线<11) AND FILTER((趋势线<=11),15) AND C<中线
        # FILTER函数：过滤连续满足条件的信号，只保留第一次
        trend_below_11 = (trend_line <= 11).astype(int)
        filter_aa = self._filter_signal(trend_below_11, 15)
        df['AA'] = ((trend_line < 11) & filter_aa & (close < midline)).astype(int)
        
        # BB条件: 多个买入条件
        ref_trend = trend_line.shift(1)
        
        # BB1: REF(趋势线,1)<11 AND REF(趋势线,1)>6 AND CROSS(趋势线,11)
        bb1 = ((ref_trend < 11) & (ref_trend > 6) & 
               (trend_line > 11) & (ref_trend <= 11)).astype(int)
        
        # BB2: REF(趋势线,1)<6 AND REF(趋势线,1)>3 AND CROSS(趋势线,6)
        bb2 = ((ref_trend < 6) & (ref_trend > 3) & 
               (trend_line > 6) & (ref_trend <= 6)).astype(int)
        
        # BB3: REF(趋势线,1)<3 AND REF(趋势线,1)>1 AND CROSS(趋势线,3)
        bb3 = ((ref_trend < 3) & (ref_trend > 1) & 
               (trend_line > 3) & (ref_trend <= 3)).astype(int)
        
        # BB4: REF(趋势线,1)<1 AND REF(趋势线,1)>0 AND CROSS(趋势线,1)
        bb4 = ((ref_trend < 1) & (ref_trend > 0) & 
               (trend_line > 1) & (ref_trend <= 1)).astype(int)
        
        # BB5: REF(趋势线,1)<0 AND CROSS(趋势线,0)
        bb5 = ((ref_trend < 0) & (trend_line > 0) & (ref_trend <= 0)).astype(int)
        
        df['BB'] = (bb1 | bb2 | bb3 | bb4 | bb5).astype(int)
        
        # CC条件: (趋势线>89) AND FILTER((趋势线>89),15) AND C>中线
        trend_above_89 = (trend_line > 89).astype(int)
        filter_cc = self._filter_signal(trend_above_89, 15)
        df['CC'] = ((trend_line > 89) & filter_cc & (close > midline)).astype(int)
        
        # DD条件: 多个卖出条件
        # DD1: REF(趋势线,1)>89 AND REF(趋势线,1)<94 AND CROSS(89,趋势线)
        dd1 = ((ref_trend > 89) & (ref_trend < 94) & 
               (trend_line < 89) & (ref_trend >= 89)).astype(int)
        
        # DD2: REF(趋势线,1)>94 AND REF(趋势线,1)<97 AND CROSS(94,趋势线)
        dd2 = ((ref_trend > 94) & (ref_trend < 97) & 
               (trend_line < 94) & (ref_trend >= 94)).astype(int)
        
        # DD3: REF(趋势线,1)>97 AND REF(趋势线,1)>99 AND CROSS(97,趋势线)
        dd3 = ((ref_trend > 97) & (ref_trend > 99) & 
               (trend_line < 97) & (ref_trend >= 97)).astype(int)
        
        # DD4: REF(趋势线,1)>99 AND REF(趋势线,1)<100 AND CROSS(99,趋势线)
        dd4 = ((ref_trend > 99) & (ref_trend < 100) & 
               (trend_line < 99) & (ref_trend >= 99)).astype(int)
        
        # DD5: REF(趋势线,1)>100 AND CROSS(100,趋势线)
        dd5 = ((ref_trend > 100) & (trend_line < 100) & (ref_trend >= 100)).astype(int)
        
        df['DD'] = (dd1 | dd2 | dd3 | dd4 | dd5).astype(int)
        
        # 添加参考线
        df['顶'] = 90
        df['底'] = 10
        df['中'] = 50
        
        return df
    
    def _filter_signal(self, signal: pd.Series, period: int) -> pd.Series:
        """
        FILTER函数实现：过滤连续信号，只保留第一次出现的信号
        
        Args:
            signal: 信号序列（0或1）
            period: 过滤周期
            
        Returns:
            过滤后的信号序列
        """
        result = pd.Series(0, index=signal.index)
        count = 0
        
        for i in range(len(signal)):
            if signal.iloc[i] == 1:
                if count == 0:
                    result.iloc[i] = 1
                count += 1
                if count >= period:
                    count = 0
            else:
                count = 0
        
        return result
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有指标
        
        Args:
            df: 包含股票数据的DataFrame，需要包含'date', 'open', 'high', 'low', 'close', 'volume'列
                如果列名不同，需要先重命名
            
        Returns:
            添加了所有指标列的DataFrame
        """
        # 确保数据按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        # 计算支撑阻力
        df = self.calculate_support_resistance(df)
        
        # 计算趋势线
        df = self.calculate_trend_line(df)
        
        # 计算信号
        df = self.calculate_signals(df)
        
        return df


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


def load_stock_data(file_path: str) -> pd.DataFrame:
    """
    加载股票数据
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        包含股票数据的DataFrame
    """
    # 先读取原始数据，不设置header
    df_raw = pd.read_excel(file_path, header=None)
    
    # 查找列名行（通常包含"时间"、"开盘"等关键词）
    header_row = None
    for i in range(min(10, len(df_raw))):
        row_str = ' '.join([str(x) for x in df_raw.iloc[i].tolist() if pd.notna(x)])
        if '时间' in row_str or '开盘' in row_str or '日期' in row_str:
            header_row = i
            break
    
    if header_row is None:
        # 如果找不到列名行，尝试使用第2行（常见格式）
        header_row = 2
    
    # 读取数据，使用找到的列名行作为header
    df = pd.read_excel(file_path, header=header_row)
    
    # 删除空行
    df = df.dropna(how='all')
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    # 尝试自动识别列名（常见的中文和英文列名）
    column_mapping = {}
    
    # 日期列 - 检查所有列
    date_keywords = ['时间', '日期', 'date', 'Date', 'time', 'Time', '交易日期']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in date_keywords):
            column_mapping[col] = 'date'
            break
    
    # 开盘价
    open_keywords = ['开盘', 'open', 'Open', '开盘价']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in open_keywords):
            column_mapping[col] = 'open'
            break
    
    # 最高价
    high_keywords = ['最高', 'high', 'High', '最高价']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in high_keywords):
            column_mapping[col] = 'high'
            break
    
    # 最低价
    low_keywords = ['最低', 'low', 'Low', '最低价']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in low_keywords):
            column_mapping[col] = 'low'
            break
    
    # 收盘价
    close_keywords = ['收盘', 'close', 'Close', '收盘价', '价格', 'price']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in close_keywords):
            column_mapping[col] = 'close'
            break
    
    # 成交量
    volume_keywords = ['成交量', 'volume', 'Volume', '成交额', 'amount']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in volume_keywords):
            column_mapping[col] = 'volume'
            break
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    # 如果列名映射失败，尝试按位置映射（常见格式：时间、开盘、最高、最低、收盘）
    if 'open' not in df.columns and len(df.columns) >= 5:
        # 假设标准格式：第0列=时间，第1列=开盘，第2列=最高，第3列=最低，第4列=收盘
        df.columns.values[0] = 'date'
        df.columns.values[1] = 'open'
        df.columns.values[2] = 'high'
        df.columns.values[3] = 'low'
        df.columns.values[4] = 'close'
        if len(df.columns) >= 6:
            df.columns.values[5] = 'volume'
    
    # 确保必需的列存在
    required_cols = ['open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # 打印当前列名以便调试
        print(f"当前列名: {df.columns.tolist()[:10]}")
        raise ValueError(f"缺少必需的列: {missing_cols}。请确保数据包含: {required_cols}")
    
    # 转换数据类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            # 尝试转换为数值类型
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 删除包含NaN的行（数据不完整）
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    return df


if __name__ == '__main__':
    # 使用示例
    try:
        # 加载数据
        print("正在加载数据...")
        df = load_stock_data('data/300760.xlsx')
        print(f"数据加载成功，共 {len(df)} 条记录")
        print(f"列名: {df.columns.tolist()}")
        print("\n前5条数据:")
        print(df.head())
        
        # 创建指标计算器
        indicator = StockIndicator(n=5)
        
        # 计算所有指标
        print("\n正在计算指标...")
        result_df = indicator.calculate_all(df.copy())
        
        # 显示结果
        print("\n计算完成！")
        print("\n关键指标列:")
        key_cols = ['date', 'close', '支撑', '阻力', '中线', '趋势线', '买', '卖', 
                   '超卖区', '超买区', '顶', '底', '中']
        available_cols = [col for col in key_cols if col in result_df.columns]
        print(result_df[available_cols].tail(20))
        
        # 统计信号
        buy_signals = result_df['买'].sum()
        sell_signals = result_df['卖'].sum()
        oversold_count = result_df['超卖区'].sum()
        overbought_count = result_df['超买区'].sum()
        
        print(f"\n信号统计:")
        print(f"买入信号: {buy_signals} 次")
        print(f"卖出信号: {sell_signals} 次")
        print(f"超卖区: {oversold_count} 次")
        print(f"超买区: {overbought_count} 次")
        
        # 保存结果
        output_file = 'data/300760_result.xlsx'
        result_df.to_excel(output_file, index=False)
        print(f"\n结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

