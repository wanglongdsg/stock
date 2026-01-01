"""
股票技术指标计算类
基于通达信公式转换
"""

import pandas as pd
import numpy as np


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



