"""
股票技术指标计算主程序
"""

from models.indicator import StockIndicator
from utils.data_loader import load_stock_data
from utils.period_converter import convert_to_period
import pandas as pd
import sys


def main(period: str = 'D'):
    """
    主函数
    
    Args:
        period: 周期类型，'D'=日线, 'W'=周线, 'M'=月线，默认为'D'
    """
    try:
        # 周期名称映射
        period_names = {'D': '日线', 'W': '周线', 'M': '月线'}
        period_name = period_names.get(period, period)
        
        # 加载数据
        print("=" * 60)
        print(f"股票技术指标计算程序 - {period_name}")
        print("=" * 60)
        print("\n正在加载数据...")
        df = load_stock_data('data/300760.xlsx')
        print(f"[OK] 原始日线数据加载成功，共 {len(df)} 条记录")
        
        # 如果选择周线或月线，进行周期转换
        if period != 'D':
            print(f"\n正在转换为{period_name}数据...")
            df = convert_to_period(df, period)
            print(f"[OK] {period_name}数据转换完成，共 {len(df)} 条记录")
        
        print(f"[OK] 数据列: {df.columns.tolist()}")
        
        # 显示原始数据前几条
        print(f"\n{period_name}数据预览（前5条）:")
        print(df.head())
        
        # 创建指标计算器
        indicator = StockIndicator(n=5)
        
        # 计算所有指标
        print(f"\n正在计算{period_name}技术指标...")
        result_df = indicator.calculate_all(df.copy())
        print("[OK] 指标计算完成")
        
        # 显示关键指标
        print("\n" + "=" * 60)
        print(f"{period_name}关键指标结果（最近20条）:")
        print("=" * 60)
        key_cols = ['date', 'close', '支撑', '阻力', '中线', '趋势线', '买', '卖']
        available_cols = [col for col in key_cols if col in result_df.columns]
        
        # 格式化显示
        display_df = result_df[available_cols].tail(20).copy()
        if 'date' in display_df.columns:
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
        
        # 设置显示选项
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        
        print(display_df.to_string(index=False))
        
        # 统计信号
        print("\n" + "=" * 60)
        print(f"{period_name}信号统计:")
        print("=" * 60)
        buy_signals = result_df['买'].sum()
        sell_signals = result_df['卖'].sum()
        oversold_count = result_df['超卖区'].sum()
        overbought_count = result_df['超买区'].sum()
        
        print(f"买入信号 (买): {buy_signals} 次")
        print(f"卖出信号 (卖): {sell_signals} 次")
        print(f"超卖区 (趋势线<10): {oversold_count} 次")
        print(f"超买区 (趋势线>90): {overbought_count} 次")
        
        # 显示买入卖出信号的具体位置
        buy_positions = result_df[result_df['买'] == 1]
        sell_positions = result_df[result_df['卖'] == 1]
        
        if len(buy_positions) > 0:
            print(f"\n{period_name}买入信号位置 (共{len(buy_positions)}次):")
            buy_display = buy_positions[['date', 'close', '趋势线']].copy() if 'date' in buy_positions.columns else buy_positions[['close', '趋势线']].copy()
            if 'date' in buy_display.columns:
                buy_display['date'] = pd.to_datetime(buy_display['date']).dt.strftime('%Y-%m-%d')
            print(buy_display.to_string(index=False))
        
        if len(sell_positions) > 0:
            print(f"\n{period_name}卖出信号位置 (共{len(sell_positions)}次):")
            sell_display = sell_positions[['date', 'close', '趋势线']].copy() if 'date' in sell_positions.columns else sell_positions[['close', '趋势线']].copy()
            if 'date' in sell_display.columns:
                sell_display['date'] = pd.to_datetime(sell_display['date']).dt.strftime('%Y-%m-%d')
            print(sell_display.to_string(index=False))
        
        # 保存结果
        # output_file = 'data/300760_result.xlsx'
        # result_df.to_excel(output_file, index=False)
        # print(f"\n[OK] 完整结果已保存到: {output_file}")
        print("=" * 60)
        
    except FileNotFoundError:
        print("错误: 找不到数据文件 'data/300760.xlsx'")
        print("请确保数据文件存在于指定路径")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 从命令行参数获取周期类型，默认为日线
    period = 'D'  # 默认日线
    
    if len(sys.argv) > 1:
        period_arg = sys.argv[1].upper()
        if period_arg in ['D', 'W', 'M']:
            period = period_arg
        else:
            print(f"警告: 无效的周期参数 '{sys.argv[1]}'，使用默认值: 日线(D)")
            print("支持的周期: D=日线, W=周线, M=月线")
            print("使用方法: python main.py [D|W|M]")
    
    # 如果没有提供参数，显示使用说明
    if len(sys.argv) == 1:
        print("=" * 60)
        print("股票技术指标计算程序")
        print("=" * 60)
        print("\n使用方法:")
        print("  python main.py D   # 计算日线信号（默认）")
        print("  python main.py W   # 计算周线信号")
        print("  python main.py M   # 计算月线信号")
        print("\n" + "=" * 60)
        print("正在使用默认周期: 日线(D)")
        print("=" * 60 + "\n")
    
    main(period)
