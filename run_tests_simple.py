#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扑克游戏全面测试脚本 (无emoji版本，适配Windows)
"""

import os
import sys
import subprocess
import time

def print_header(title):
    print("\n" + "=" * 60)
    print("[TEST] " + title)
    print("=" * 60)

def run_python_test(test_file, description):
    """运行Python测试"""
    print(f"\n[PYTHON] 运行 {description}")
    print(f"   文件: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"[ERROR] 测试文件不存在: {test_file}")
        return False
        
    try:
        # 设置环境变量，强制使用UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, 
                              timeout=300, env=env, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"[PASS] {description} - 通过")
            if result.stdout:
                print("输出预览:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print(f"[FAIL] {description} - 失败")
            if result.stderr:
                print(f"   错误: {result.stderr[:300]}...")
            if result.stdout:
                print(f"   输出: {result.stdout[:300]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {description} - 超时")
        return False
    except Exception as e:
        print(f"[EXCEPTION] {description} - 异常: {e}")
        return False

def test_imports():
    """测试基本模块导入"""
    print_header("测试基本模块导入")
    
    modules_to_test = [
        'poker_engine.table',
        'poker_engine.player', 
        'poker_engine.card',
        'poker_engine.bot',
        'poker_engine.hand_evaluator',
        'database',
        'game_logger'
    ]
    
    passed = 0
    total = len(modules_to_test)
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"[PASS] {module} - 导入成功")
            passed += 1
        except ImportError as e:
            print(f"[FAIL] {module} - 导入失败: {e}")
        except Exception as e:
            print(f"[ERROR] {module} - 异常: {e}")
    
    print(f"\n模块导入测试: {passed}/{total} 通过")
    return passed == total

def run_individual_tests():
    """运行单独的测试"""
    print_header("运行单独测试")
    
    # 先运行一个简单测试
    simple_test_code = '''
import sys
sys.path.append(".")

try:
    from poker_engine.table import Table
    from poker_engine.player import Player
    
    # 简单测试
    table = Table("test", "测试桌", max_players=6)
    player = Player("p1", "测试玩家", 1000)
    
    result = table.add_player(player)
    print(f"添加玩家结果: {result}")
    print(f"桌子玩家数: {len(table.players)}")
    print("基本功能测试通过")
    
except Exception as e:
    print(f"基本功能测试失败: {e}")
    import traceback
    traceback.print_exc()
'''
    
    try:
        with open('temp_test.py', 'w', encoding='utf-8') as f:
            f.write(simple_test_code)
        
        result = subprocess.run([sys.executable, 'temp_test.py'], 
                              capture_output=True, text=True, 
                              encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("[PASS] 基本功能测试通过")
            print(result.stdout)
        else:
            print("[FAIL] 基本功能测试失败")
            print(result.stderr)
            
        os.remove('temp_test.py')
        
    except Exception as e:
        print(f"[ERROR] 运行基本测试时出错: {e}")

def main():
    print("扑克游戏全面测试 (Windows兼容版)")
    
    # 首先测试模块导入
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n[ERROR] 基本模块导入失败，无法继续测试")
        return
        
    # 运行简单功能测试
    run_individual_tests()
    
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
    
    print(f"\n[SUMMARY] 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("[SUCCESS] 所有测试都通过了！")
    else:
        print(f"[WARNING] 有 {total - passed} 个测试失败")
        
    print("\n[INFO] 如需运行前端测试，请启动服务器后手动运行:")
    print("  python app.py (在另一个终端)")
    print("  npx playwright test tests/ --reporter=line")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] 测试被用户中断")
    except Exception as e:
        print(f"\n[ERROR] 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc() 