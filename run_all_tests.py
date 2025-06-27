#!/usr/bin/env python3
"""
扑克游戏全面测试脚本
"""

import os
import sys
import subprocess
import time

def print_header(title):
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)

def run_python_test(test_file, description):
    """运行Python测试"""
    print(f"\n🐍 运行 {description}")
    print(f"   文件: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
        
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} - 通过")
            return True
        else:
            print(f"❌ {description} - 失败")
            if result.stderr:
                print(f"   错误: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False
    except Exception as e:
        print(f"💥 {description} - 异常: {e}")
        return False

def main():
    print("🎮 扑克游戏全面测试")
    
    # Python测试列表
    python_tests = [
        ('test_fixes_comprehensive.py', '综合功能修复测试'),
        ('test_all_in_fix.py', 'ALL IN 逻辑修复测试'),
        ('test_ante_manual.py', '前注模式测试'),
        ('test_showdown_api.py', '摊牌API测试'),
        ('test_showdown.py', '摊牌逻辑测试'),
        ('test_two_humans.py', '双人游戏测试'),
        ('test_two_humans_one_bot.py', '人机混合游戏测试'),
    ]
    
    print_header("Python 后端测试")
    
    passed = 0
    total = len(python_tests)
    
    for test_file, description in python_tests:
        if run_python_test(test_file, description):
            passed += 1
    
    print(f"\n📊 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")

if __name__ == '__main__':
    main() 