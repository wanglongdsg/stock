"""
卖出策略模块
使用策略模式实现不同的卖出策略
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple


class SellStrategy(ABC):
    """卖出策略基类"""
    
    @abstractmethod
    def should_sell(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断是否应该卖出
        
        Args:
            context: 包含当前状态的上下文字典，包括：
                - position: 是否持仓
                - current_close: 当前收盘价
                - buy_price: 买入价格
                - buy_date_idx: 买入日期在日线数据中的索引
                - current_daily_idx: 当前日期在日线数据中的索引
                - daily_df: 日线数据DataFrame
                - daily_closes: 日线收盘价数组
                - daily_ma20: 日线20均线数组
                - result_df: 周期数据DataFrame
                - period: 周期类型
                - 其他策略特定参数
        
        Returns:
            (是否卖出, 卖出原因)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取策略名称"""
        pass
    
    @abstractmethod
    def reset(self):
        """重置策略状态（买入时调用）"""
        pass


class StopLossStrategy(SellStrategy):
    """止损策略：当亏损达到指定比例时卖出
    注意：使用日线数据进行检查，确保不会错过止损点"""
    
    def __init__(self, stop_loss_percent: float):
        """
        初始化止损策略
        
        Args:
            stop_loss_percent: 止损比例（如5.0表示5%）
        """
        if stop_loss_percent <= 0:
            raise ValueError(f"止损比例必须大于0，当前值: {stop_loss_percent}")
        
        self.stop_loss_percent = stop_loss_percent
        self.buy_date_idx = -1  # 买入日期索引
        self.last_check_idx = -1  # 上次检查的日线索引
    
    def should_sell(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        if not context.get('position', False):
            return False, ''
        
        buy_price = context.get('buy_price', 0)
        # 优先使用 context 中的 buy_date_idx，如果没有则使用实例变量
        buy_date_idx = context.get('buy_date_idx', self.buy_date_idx)
        current_daily_idx = context.get('current_daily_idx', -1)
        
        if buy_price <= 0 or buy_date_idx < 0 or current_daily_idx < 0:
            return False, ''
        
        daily_df = context.get('daily_df')
        daily_closes = context.get('daily_closes')
        
        if daily_df is None or daily_closes is None:
            return False, ''
        
        # 使用日线数据进行检查，从买入日期的下一天开始，到当前日期
        # 这样可以确保不会错过任何止损点
        # 确保 last_check_idx 有效，如果为 -1 则从买入日期下一天开始
        check_start_idx = max(buy_date_idx + 1, self.last_check_idx + 1 if self.last_check_idx >= 0 else buy_date_idx + 1)
        check_end_idx = current_daily_idx
        
        # 确保检查范围有效
        if check_start_idx > check_end_idx:
            return False, ''
        
        # 预先获取数组长度，避免重复计算
        daily_df_len = len(daily_df)
        daily_closes_len = len(daily_closes)
        
        # 遍历从上次检查位置到当前日期的所有日线数据
        for check_idx in range(check_start_idx, check_end_idx + 1):
            if check_idx >= daily_df_len:
                break
            
            daily_close = daily_closes[check_idx] if check_idx < daily_closes_len else None
            
            if pd.notna(daily_close) and daily_close > 0:
                # 计算该日的盈亏比例
                profit_percent = ((daily_close - buy_price) / buy_price * 100)
                
                # 如果亏损达到止损比例，立即卖出
                if profit_percent <= -self.stop_loss_percent:
                    self.last_check_idx = check_idx
                    return True, f'止损({profit_percent:.2f}%)'
        
        # 更新最后检查的索引（即使没有触发止损，也要更新以避免重复检查）
        if check_end_idx >= 0:
            self.last_check_idx = check_end_idx
        
        return False, ''
    
    def get_name(self) -> str:
        return 'stop_loss'
    
    def reset(self):
        """重置策略状态"""
        self.buy_date_idx = -1
        self.last_check_idx = -1
    
    def set_buy_info(self, buy_date_idx: int):
        """
        设置买入信息
        
        Args:
            buy_date_idx: 买入日期索引
        """
        self.buy_date_idx = buy_date_idx
        self.last_check_idx = buy_date_idx


class TakeProfitStrategy(SellStrategy):
    """止盈策略：当盈利达到指定比例时卖出
    注意：使用日线数据进行检查，确保不会错过止盈点"""
    
    def __init__(self, take_profit_percent: Optional[float]):
        """
        初始化止盈策略
        
        Args:
            take_profit_percent: 止盈比例（如10.0表示10%），None表示不设止盈
        """
        self.take_profit_percent = take_profit_percent
        self.buy_date_idx = -1  # 买入日期索引
        self.last_check_idx = -1  # 上次检查的日线索引
    
    def should_sell(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        if not context.get('position', False):
            return False, ''
        
        if self.take_profit_percent is None:
            return False, ''
        
        buy_price = context.get('buy_price', 0)
        # 优先使用 context 中的 buy_date_idx，如果没有则使用实例变量
        buy_date_idx = context.get('buy_date_idx', self.buy_date_idx)
        current_daily_idx = context.get('current_daily_idx', -1)
        
        if buy_price <= 0 or buy_date_idx < 0 or current_daily_idx < 0:
            return False, ''
        
        daily_df = context.get('daily_df')
        daily_closes = context.get('daily_closes')
        
        if daily_df is None or daily_closes is None:
            # 如果没有日线数据，使用周期数据检查（兼容性处理）
            current_close = context.get('current_close', 0)
            if current_close > 0:
                profit_percent = ((current_close - buy_price) / buy_price * 100)
                if profit_percent >= self.take_profit_percent:
                    return True, f'止盈({profit_percent:.2f}%)'
            return False, ''
        
        # 使用日线数据进行检查，从买入日期的下一天开始，到当前日期
        # 这样可以确保不会错过任何止盈点
        # 确保 last_check_idx 有效，如果为 -1 则从买入日期下一天开始
        check_start_idx = max(buy_date_idx + 1, self.last_check_idx + 1 if self.last_check_idx >= 0 else buy_date_idx + 1)
        check_end_idx = current_daily_idx
        
        # 确保检查范围有效
        if check_start_idx > check_end_idx:
            return False, ''
        
        # 预先获取数组长度，避免重复计算
        daily_df_len = len(daily_df)
        daily_closes_len = len(daily_closes)
        
        # 遍历从上次检查位置到当前日期的所有日线数据
        for check_idx in range(check_start_idx, check_end_idx + 1):
            if check_idx >= daily_df_len:
                break
            
            daily_close = daily_closes[check_idx] if check_idx < daily_closes_len else None
            
            if pd.notna(daily_close) and daily_close > 0:
                # 计算该日的盈亏比例
                profit_percent = ((daily_close - buy_price) / buy_price * 100)
                
                # 如果盈利达到止盈比例，立即卖出
                if profit_percent >= self.take_profit_percent:
                    self.last_check_idx = check_idx
                    return True, f'止盈({profit_percent:.2f}%)'
        
        # 更新最后检查的索引
        if check_end_idx >= 0:
            self.last_check_idx = check_end_idx
        
        return False, ''
    
    def get_name(self) -> str:
        return 'take_profit'
    
    def reset(self):
        """重置策略状态"""
        self.buy_date_idx = -1
        self.last_check_idx = -1
    
    def set_buy_info(self, buy_date_idx: int):
        """
        设置买入信息
        
        Args:
            buy_date_idx: 买入日期索引
        """
        self.buy_date_idx = buy_date_idx
        self.last_check_idx = buy_date_idx


class BelowMa20Strategy(SellStrategy):
    """20均线下方策略：买入后上穿20均线，然后收盘价回落到20均线下方N天，第(N+1)天卖出
    新增：只有在收益达到指定阈值（如10%）以上时才触发此策略"""
    
    def __init__(self, below_ma20_days: int, min_profit_percent: Optional[float] = None):
        """
        初始化20均线下方策略
        
        Args:
            below_ma20_days: 收盘价在20均线下方连续天数
            min_profit_percent: 最小收益阈值（%），只有收益达到此值以上才触发策略，None表示不设限制
        """
        if below_ma20_days <= 0:
            raise ValueError(f"below_ma20_days必须大于0，当前值: {below_ma20_days}")
        
        if min_profit_percent is not None and min_profit_percent <= 0:
            raise ValueError(f"min_profit_percent必须大于0（如果提供），当前值: {min_profit_percent}")
        
        self.below_ma20_days = below_ma20_days
        self.min_profit_percent = min_profit_percent  # 最小收益阈值
        self.buy_below_ma20 = False  # 买入时收盘价是否在20均线下方
        self.crossed_ma20 = False  # 是否已上穿20日线
        self.crossed_ma20_date_idx = -1  # 上穿20均线的日期索引
        self.close_below_ma20_days = 0  # 收盘价在20均线下方连续天数
        self.last_ma20_check_idx = -1  # 上次检查20均线下方情况的日线索引
        self.buy_date_idx = -1  # 买入日期索引
        self.profit_threshold_reached = False  # 是否已经达到过收益阈值（用于min_profit_percent检查）
    
    def should_sell(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        if not context.get('position', False):
            return False, ''
        
        # 只有买入时收盘价在20均线下方，才启用此策略
        if not self.buy_below_ma20:
            return False, ''
        
        # 优先使用 context 中的 buy_date_idx，如果没有则使用实例变量
        buy_date_idx = context.get('buy_date_idx', self.buy_date_idx)
        current_daily_idx = context.get('current_daily_idx', -1)
        
        if buy_date_idx < 0 or current_daily_idx < 0:
            return False, ''
        
        daily_df = context.get('daily_df')
        daily_closes = context.get('daily_closes')
        daily_ma20 = context.get('daily_ma20')
        
        if daily_df is None or daily_closes is None or daily_ma20 is None:
            return False, ''
        
        # 第一步：检查是否上穿20均线（从买入日期之后开始检查）
        if not self.crossed_ma20:
            # 遍历从买入日期的下一天到当前日期的所有日线数据，检查是否有上穿动作
            # 上穿：前一日收盘价 <= 20均线，当前收盘价 > 20均线
            # 注意：需要从买入日期的下一天开始，因为买入当天已经在20均线下方
            check_start_idx = buy_date_idx + 1  # 从买入日期的下一天开始检查
            check_end_idx = current_daily_idx
            
            # 预先获取数组长度，避免重复计算
            daily_df_len = len(daily_df)
            daily_closes_len = len(daily_closes)
            daily_ma20_len = len(daily_ma20)
            
            for check_idx in range(check_start_idx, check_end_idx + 1):
                if check_idx < 1 or check_idx >= daily_df_len:
                    continue
                
                # 获取当前和前一日的数据
                prev_idx = check_idx - 1
                # 前一日必须至少是买入日期当天（因为买入时已经在20均线下方）
                if prev_idx < buy_date_idx:
                    continue
                
                prev_close = daily_closes[prev_idx] if prev_idx < daily_closes_len else None
                prev_ma20 = daily_ma20[prev_idx] if prev_idx < daily_ma20_len else None
                curr_close = daily_closes[check_idx] if check_idx < daily_closes_len else None
                curr_ma20 = daily_ma20[check_idx] if check_idx < daily_ma20_len else None
                
                # 检查是否上穿：前一日收盘价 <= 20均线，当前收盘价 > 20均线
                if (pd.notna(prev_ma20) and pd.notna(prev_close) and 
                    pd.notna(curr_ma20) and pd.notna(curr_close) and
                    prev_close <= prev_ma20 and curr_close > curr_ma20):
                    self.crossed_ma20 = True
                    self.crossed_ma20_date_idx = check_idx
                    self.close_below_ma20_days = 0
                    self.last_ma20_check_idx = check_idx  # 初始化检查索引
                    break  # 找到上穿后，停止检查
        
        # 第二步：如果已上穿20均线，检查收盘价是否在20均线下方
        if self.crossed_ma20 and self.crossed_ma20_date_idx >= 0:
            buy_price = context.get('buy_price', 0)
            
            # 从上穿日期的下一天开始，到当前日期，检查所有日线数据
            # 使用last_ma20_check_idx来避免重复检查，从上一次检查的位置之后开始
            check_start_idx = max(self.crossed_ma20_date_idx + 1, self.last_ma20_check_idx + 1)
            check_end_idx = current_daily_idx
            
            # 确保检查范围有效
            if check_start_idx > check_end_idx:
                return False, ''
            
            # 预先获取数组长度，避免重复计算
            daily_df_len = len(daily_df)
            daily_closes_len = len(daily_closes)
            daily_ma20_len = len(daily_ma20)
            
            # 从上一次检查的位置之后开始，到当前日期，遍历所有日线数据
            for check_idx in range(check_start_idx, check_end_idx + 1):
                if check_idx >= daily_df_len:
                    break
                
                daily_close = daily_closes[check_idx] if check_idx < daily_closes_len else None
                daily_ma20_val = daily_ma20[check_idx] if check_idx < daily_ma20_len else None
                
                # 注意：只使用表格中的MA.MA3值，如果值为NaN则跳过
                if pd.notna(daily_ma20_val) and pd.notna(daily_close):
                    # 如果设置了最小收益阈值，需要先检查收益是否达到阈值
                    if self.min_profit_percent is not None and buy_price > 0:
                        daily_profit_percent = ((daily_close - buy_price) / buy_price * 100)
                        
                        # 如果收益达到阈值，标记为已达到（后续即使暂时低于阈值也继续检查）
                        if daily_profit_percent >= self.min_profit_percent:
                            self.profit_threshold_reached = True
                        
                        # 只有在收益达到阈值后，才开始检查收盘价是否在20均线下方
                        if not self.profit_threshold_reached:
                            continue  # 收益未达到阈值，跳过检查
                    
                    # 检查收盘价是否在20均线下方
                    if daily_close < daily_ma20_val:
                        # 收盘价在20均线下方，累加计数
                        self.close_below_ma20_days += 1
                        
                        # 如果连续below_ma20_days天在20均线下方，第(below_ma20_days+1)天卖出
                        if self.close_below_ma20_days >= self.below_ma20_days:
                            self.last_ma20_check_idx = check_idx  # 更新检查索引
                            # 计算最终收益用于显示
                            final_profit_percent = ((daily_close - buy_price) / buy_price * 100) if buy_price > 0 else 0
                            profit_info = f'（收益{final_profit_percent:.2f}%）' if self.min_profit_percent is not None else ''
                            return True, f'收盘价在20均线下方{self.below_ma20_days}天{profit_info}，第{self.below_ma20_days+1}天卖出'
                    else:
                        # 如果收盘价回到20均线上方，重置计数
                        self.close_below_ma20_days = 0
            
            # 更新最后检查的索引（即使没有卖出，也要更新，避免重复检查）
            if check_end_idx >= 0:
                self.last_ma20_check_idx = check_end_idx
        
        return False, ''
    
    def get_name(self) -> str:
        return 'below_ma20'
    
    def reset(self):
        """重置策略状态"""
        self.crossed_ma20 = False
        self.crossed_ma20_date_idx = -1
        self.close_below_ma20_days = 0
        self.last_ma20_check_idx = -1
        self.profit_threshold_reached = False
    
    def set_buy_info(self, buy_date_idx: int, buy_below_ma20: bool):
        """
        设置买入信息
        
        Args:
            buy_date_idx: 买入日期索引
            buy_below_ma20: 买入时收盘价是否在20均线下方
        """
        self.buy_date_idx = buy_date_idx
        self.buy_below_ma20 = buy_below_ma20
        self.reset()


class TrailingStopLossStrategy(SellStrategy):
    """追踪止损策略：初始止损点设置为买入价格下方一定幅度（如15-20%），
    随着股价上升，止损点也随之上移，始终保持在最新高点下方相同幅度
    注意：使用日线数据进行检查，确保不会错过止损点"""
    
    def __init__(self, trailing_stop_percent: float):
        """
        初始化追踪止损策略
        
        Args:
            trailing_stop_percent: 追踪止损比例（如15.0表示15%）
        """
        if trailing_stop_percent <= 0:
            raise ValueError(f"追踪止损比例必须大于0，当前值: {trailing_stop_percent}")
        
        self.trailing_stop_percent = trailing_stop_percent
        self.highest_price = 0.0  # 买入后的最高价
        self.stop_loss_price = 0.0  # 当前止损价
        self.buy_date_idx = -1  # 买入日期索引
        self.last_check_idx = -1  # 上次检查的日线索引
    
    def should_sell(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        if not context.get('position', False):
            return False, ''
        
        buy_price = context.get('buy_price', 0)
        # 优先使用 context 中的 buy_date_idx，如果没有则使用实例变量
        buy_date_idx = context.get('buy_date_idx', self.buy_date_idx)
        current_daily_idx = context.get('current_daily_idx', -1)
        
        if buy_price <= 0 or buy_date_idx < 0 or current_daily_idx < 0:
            return False, ''
        
        daily_df = context.get('daily_df')
        daily_closes = context.get('daily_closes')
        
        if daily_df is None or daily_closes is None:
            return False, ''
        
        # 使用日线数据进行检查，从买入日期的下一天开始，到当前日期
        # 确保 last_check_idx 有效，如果为 -1 则从买入日期下一天开始
        check_start_idx = max(buy_date_idx + 1, self.last_check_idx + 1 if self.last_check_idx >= 0 else buy_date_idx + 1)
        check_end_idx = current_daily_idx
        
        # 确保检查范围有效
        if check_start_idx > check_end_idx:
            return False, ''
        
        # 预先获取数组长度，避免重复计算
        daily_df_len = len(daily_df)
        daily_closes_len = len(daily_closes)
        
        # 遍历从上次检查位置到当前日期的所有日线数据
        for check_idx in range(check_start_idx, check_end_idx + 1):
            if check_idx >= daily_df_len:
                break
            
            daily_close = daily_closes[check_idx] if check_idx < daily_closes_len else None
            
            if pd.notna(daily_close) and daily_close > 0:
                # 更新最高价
                if daily_close > self.highest_price:
                    self.highest_price = daily_close
                    # 计算新的止损价：最高价下方trailing_stop_percent%
                    self.stop_loss_price = self.highest_price * (1 - self.trailing_stop_percent / 100)
                
                # 如果当前收盘价跌破止损价，则卖出
                if daily_close < self.stop_loss_price:
                    profit_percent = ((daily_close - buy_price) / buy_price * 100)
                    self.last_check_idx = check_idx
                    return True, f'追踪止损({profit_percent:.2f}%)'
        
        # 更新最后检查的索引（即使没有触发止损，也要更新以避免重复检查）
        if check_end_idx >= 0:
            self.last_check_idx = check_end_idx
        
        return False, ''
    
    def get_name(self) -> str:
        return 'trailing_stop_loss'
    
    def reset(self):
        """重置策略状态"""
        self.highest_price = 0.0
        self.stop_loss_price = 0.0
        self.buy_date_idx = -1
        self.last_check_idx = -1
    
    def set_buy_info(self, buy_price: float, buy_date_idx: int = -1):
        """
        设置买入信息
        
        Args:
            buy_price: 买入价格
            buy_date_idx: 买入日期索引（可选，用于日线数据检查）
        """
        if buy_price <= 0:
            raise ValueError(f"买入价格必须大于0，当前值: {buy_price}")
        
        self.highest_price = buy_price
        self.buy_date_idx = buy_date_idx
        self.last_check_idx = buy_date_idx if buy_date_idx >= 0 else -1
        # 初始止损价：买入价下方trailing_stop_percent%
        self.stop_loss_price = buy_price * (1 - self.trailing_stop_percent / 100)


def create_strategy(strategy_name: str, **kwargs) -> Optional[SellStrategy]:
    """
    工厂方法：创建卖出策略实例
    
    Args:
        strategy_name: 策略名称
        **kwargs: 策略参数
    
    Returns:
        策略实例，如果策略名称无效则返回None
    """
    strategies = {
        'stop_loss': lambda: StopLossStrategy(kwargs.get('stop_loss_percent', 5.0)),
        'take_profit': lambda: TakeProfitStrategy(kwargs.get('take_profit_percent')),
        'below_ma20': lambda: BelowMa20Strategy(kwargs.get('below_ma20_days', 3), kwargs.get('below_ma20_min_profit', None)),
        'trailing_stop_loss': lambda: TrailingStopLossStrategy(kwargs.get('trailing_stop_percent', 15.0))
    }
    
    strategy_factory = strategies.get(strategy_name)
    if strategy_factory:
        return strategy_factory()
    return None

