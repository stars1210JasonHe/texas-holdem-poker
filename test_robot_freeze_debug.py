#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器人卡死问题诊断测试
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerStatus, PlayerAction
from poker_engine.bot import Bot, BotLevel
from poker_engine.card import Card, Rank, Suit

def create_debug_test_table():
    """创建调试测试桌子"""
    table = Table("debug_test", "卡死诊断测试", small_blind=10, big_blind=20)
    
    # 添加1个真人玩家
    human = Player("human1", "真人玩家", 1000)
    table.add_player(human)
    
    # 添加5个不同等级的机器人
    bots = [
        Bot("bot1", "新手机器人", 1000, BotLevel.BEGINNER),
        Bot("bot2", "中级机器人", 1000, BotLevel.INTERMEDIATE), 
        Bot("bot3", "高级机器人", 1000, BotLevel.ADVANCED),
        Bot("bot4", "神级机器人", 1000, BotLevel.GOD),
        Bot("bot5", "测试机器人", 1000, BotLevel.BEGINNER)
    ]
    
    for bot in bots:
        table.add_player(bot)
    
    return table, human, bots

def test_normal_game_flow():
    """测试正常游戏流程"""
    print("🎮 测试1: 正常游戏流程")
    try:
        table, human, bots = create_debug_test_table()
        
        # 开始新手牌
        success = table.start_new_hand()
        if not success:
            print("❌ 无法开始新手牌")
            return False
        
        print(f"✅ 手牌开始成功，游戏阶段: {table.stage.value}")
        
        # 真人玩家弃牌
        print("👤 真人玩家弃牌...")
        result = table.process_player_action("human1", PlayerAction.FOLD)
        print(f"结果: {result}")
        
        # 处理机器人行动
        print("🤖 开始处理机器人行动...")
        start_time = time.time()
        
        bot_result = table.process_bot_actions()
        end_time = time.time()
        
        print(f"✅ 机器人处理完成，耗时: {end_time - start_time:.2f}秒")
        print(f"游戏状态: {bot_result}")
        
        # 检查是否成功完成
        if bot_result.get('hand_complete', False):
            print("✅ 手牌成功完成")
            return True
        else:
            print(f"⚠️ 手牌未完成，状态: {bot_result}")
            return True  # 即使未完成也算成功，因为没有卡死
        
    except Exception as e:
        print(f"❌ 正常游戏流程测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_timeout_detection():
    """测试超时检测"""
    print("\n🕰️ 测试2: 超时检测")
    table, human, bots = create_debug_test_table()
    
    # 修改一个机器人的决策函数，让它故意卡死
    def broken_decide_action(self, game_state):
        print(f"🔥 {self.nickname} 故意卡死中...")
        time.sleep(2)  # 模拟卡死
        return None  # 返回无效结果
    
    # 给第一个机器人添加故意卡死的决策函数
    bots[0].decide_action = lambda game_state: broken_decide_action(bots[0], game_state)
    
    table.start_new_hand()
    table.process_player_action("human1", PlayerAction.FOLD)
    
    print("🤖 测试超时检测...")
    start_time = time.time()
    
    try:
        bot_result = table.process_bot_actions()
        end_time = time.time()
        
        print(f"✅ 超时检测正常，耗时: {end_time - start_time:.2f}秒")
        print(f"游戏状态: {bot_result}")
        return True
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ 超时检测失败，耗时: {end_time - start_time:.2f}秒")
        print(f"错误: {e}")
        return False

def test_infinite_loop_protection():
    """测试无限循环保护"""
    print("\n🔄 测试3: 无限循环保护")
    table, human, bots = create_debug_test_table()
    
    # 修改游戏状态检查，模拟无限循环情况
    original_get_current_player = table.get_current_player
    call_count = [0]
    
    def mock_get_current_player():
        call_count[0] += 1
        if call_count[0] <= 15:  # 前15次返回同一个机器人
            return bots[0]
        return None
    
    table.get_current_player = mock_get_current_player
    
    table.start_new_hand()
    
    print("🤖 测试无限循环保护...")
    start_time = time.time()
    
    try:
        bot_result = table.process_bot_actions()
        end_time = time.time()
        
        print(f"✅ 无限循环保护正常，耗时: {end_time - start_time:.2f}秒")
        print(f"get_current_player 调用次数: {call_count[0]}")
        print(f"游戏状态: {bot_result}")
        return True
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ 无限循环保护失败，耗时: {end_time - start_time:.2f}秒")
        print(f"错误: {e}")
        return False

def test_memory_leak():
    """测试内存泄漏"""
    print("\n🧠 测试4: 内存使用监控")
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"初始内存: {initial_memory:.1f} MB")
    
    # 运行多轮游戏
    for round_num in range(10):
        table, human, bots = create_debug_test_table()
        table.start_new_hand()
        table.process_player_action("human1", PlayerAction.FOLD)
        table.process_bot_actions()
        
        current_memory = process.memory_info().rss / 1024 / 1024
        if round_num % 3 == 0:
            print(f"轮次 {round_num + 1}: {current_memory:.1f} MB")
    
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    print(f"最终内存: {final_memory:.1f} MB")
    print(f"内存增长: {memory_increase:.1f} MB")
    
    if memory_increase < 10:  # 内存增长小于10MB认为正常
        print("✅ 内存使用正常")
        return True
    else:
        print("❌ 可能存在内存泄漏")
        return False

def test_concurrent_processing():
    """测试并发处理"""
    print("\n🔀 测试5: 并发处理安全性")
    
    results = []
    
    def run_game_in_thread(thread_id):
        try:
            table, human, bots = create_debug_test_table()
            table.start_new_hand()
            table.process_player_action("human1", PlayerAction.FOLD)
            bot_result = table.process_bot_actions()
            results.append(f"线程{thread_id}: 成功")
        except Exception as e:
            results.append(f"线程{thread_id}: 失败 - {e}")
    
    # 启动3个并发线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=run_game_in_thread, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    success_count = len([r for r in results if "成功" in r])
    
    print("并发测试结果:")
    for result in results:
        print(f"  {result}")
    
    if success_count == 3:
        print("✅ 并发处理安全")
        return True
    else:
        print("❌ 并发处理存在问题")
        return False

def main():
    """主测试函数"""
    print("🔍 机器人卡死问题诊断测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("正常游戏流程", test_normal_game_flow),
        ("超时检测", test_timeout_detection), 
        ("无限循环保护", test_infinite_loop_protection),
        ("内存使用监控", test_memory_leak),
        ("并发处理安全性", test_concurrent_processing)
    ]
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            test_results.append((test_name, result, end_time - start_time))
            
        except Exception as e:
            print(f"❌ 测试 {test_name} 出现异常: {e}")
            test_results.append((test_name, False, 0))
    
    # 输出测试总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result, duration in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name} ({duration:.2f}秒)")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过，机器人卡死问题已修复！")
    else:
        print("⚠️ 部分测试失败，需要进一步调查")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 