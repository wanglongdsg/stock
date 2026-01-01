"""
回测接口测试脚本
"""

import requests
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5000"


def test_backtest(period: str, initial_amount: float):
    """测试回测接口"""
    print("=" * 60)
    print(f"测试回测接口 - {period}, 初始资金: {initial_amount:,.2f}")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/backtest"
    headers = {"Content-Type": "application/json"}
    data = {
        "period": period,
        "initial_amount": initial_amount
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"\n周期: {result.get('period_name')}")
            print(f"初始资金: {result.get('initial_amount'):,.2f}")
            print(f"最终资金: {result.get('final_amount'):,.2f}")
            print(f"总收益: {result.get('total_profit'):,.2f}")
            print(f"总收益率: {result.get('total_profit_rate'):.2f}%")
            print(f"年收益率: {result.get('annual_profit_rate'):.2f}%")
            print(f"开始日期: {result.get('start_date')}")
            print(f"结束日期: {result.get('end_date')}")
            print(f"交易天数: {result.get('trading_days')} 天")
            print(f"交易次数: {result.get('total_trades')} 次")
            
            trades = result.get('trades', [])
            if trades:
                print(f"\n交易记录 (前5笔):")
                for i, trade in enumerate(trades[:5], 1):
                    print(f"\n  交易 {i}:")
                    print(f"    买入日期: {trade['buy_date']}, 买入价: {trade['buy_price']:.2f}")
                    print(f"    卖出日期: {trade['sell_date']}, 卖出价: {trade['sell_price']:.2f}")
                    print(f"    收益: {trade['profit']:,.2f}, 收益率: {trade['profit_rate']:.2f}%")
        else:
            print(f"错误: {result.get('error')}")
            print(f"错误代码: {result.get('error_code')}")
        
        print()
        return result.get('success', False)
        
    except Exception as e:
        print(f"错误: {e}\n")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("回测接口测试")
    print("=" * 60 + "\n")
    
    # 测试日线回测
    test_backtest('D', 100000)
    
    # 测试周线回测
    test_backtest('W', 100000)
    
    # 测试月线回测
    test_backtest('M', 100000)
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()


