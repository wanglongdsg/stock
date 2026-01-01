"""
统一测试入口
运行所有测试用例
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .test_api import test_health, test_calculate
from .test_backtest import test_backtest


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("股票技术指标计算 API - 完整测试套件")
    print("=" * 60 + "\n")
    
    results = {
        'health': False,
        'calculate_d': False,
        'calculate_w': False,
        'calculate_m': False,
        'backtest_d': False,
        'backtest_w': False,
        'backtest_m': False
    }
    
    # 1. 健康检查
    print("\n[1/7] 健康检查测试")
    results['health'] = test_health()
    
    if not results['health']:
        print("\n❌ 健康检查失败，请确保服务已启动")
        print("启动服务: python app.py")
        return results
    
    # 2. 计算接口测试
    print("\n[2/7] 日线计算测试")
    results['calculate_d'] = test_calculate('D')
    
    print("\n[3/7] 周线计算测试")
    results['calculate_w'] = test_calculate('W')
    
    print("\n[4/7] 月线计算测试")
    results['calculate_m'] = test_calculate('M')
    
    # 3. 回测接口测试
    print("\n[5/7] 日线回测测试")
    results['backtest_d'] = test_backtest('D', 100000)
    
    print("\n[6/7] 周线回测测试")
    results['backtest_w'] = test_backtest('W', 100000)
    
    print("\n[7/7] 月线回测测试")
    results['backtest_m'] = test_backtest('M', 100000)
    
    # 测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed > 0:
        print("\n失败的测试:")
        for test_name, result in results.items():
            if not result:
                print(f"  ❌ {test_name}")
    else:
        print("\n✅ 所有测试通过！")
    
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    run_all_tests()

