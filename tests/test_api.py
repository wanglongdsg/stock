"""
API测试脚本
用于测试股票技术指标计算API
"""

import requests
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5000"


def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试健康检查接口")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}\n")
        return False


def test_calculate(period: str):
    """测试计算接口"""
    print("=" * 60)
    print(f"测试计算接口 - {period}")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/calculate"
    headers = {"Content-Type": "application/json"}
    data = {"period": period}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"周期: {result.get('period_name')}")
            print(f"总记录数: {result.get('total_records')}")
            print(f"\n统计信息:")
            stats = result.get('statistics', {})
            print(f"  买入信号: {stats.get('buy_signals_count')} 次")
            print(f"  卖出信号: {stats.get('sell_signals_count')} 次")
            print(f"  超卖区: {stats.get('oversold_count')} 次")
            print(f"  超买区: {stats.get('overbought_count')} 次")
            
            buy_signals = result.get('buy_signals', [])
            if buy_signals:
                print(f"\n买入信号位置 (前5个):")
                for signal in buy_signals[:5]:
                    print(f"  日期: {signal['date']}, 收盘价: {signal['close']:.2f}, 趋势线: {signal['trend_line']:.2f}")
            
            sell_signals = result.get('sell_signals', [])
            if sell_signals:
                print(f"\n卖出信号位置 (前5个):")
                for signal in sell_signals[:5]:
                    print(f"  日期: {signal['date']}, 收盘价: {signal['close']:.2f}, 趋势线: {signal['trend_line']:.2f}")
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
    print("股票技术指标计算 API 测试")
    print("=" * 60 + "\n")
    
    # 测试健康检查
    health_ok = test_health()
    
    if not health_ok:
        print("警告: 健康检查失败，请确保服务已启动")
        print("启动服务: python app.py")
        return
    
    # 测试日线
    test_calculate('D')
    
    # 测试周线
    test_calculate('W')
    
    # 测试月线
    test_calculate('M')
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()



