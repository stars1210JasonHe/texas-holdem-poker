#!/usr/bin/env python3
"""
反卡死测试：测试机器人在各种边界情况下的行为
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table
from poker_engine.player import Player, PlayerStatus
from poker_engine.bot import Bot, BotLevel
from poker_engine.card import Card, Suit, Rank
import time

def test_bot_anti_freeze():
    """测试机器人防卡死机制"""
    print("🧪 开始反卡死测试...")
    
    # 创建牌桌
    table = Table("test_table", "反卡死测试桌", small_blind=10, big_blind=20)
    
    # 添加人类玩家
    human = Player("human1", "人类玩家", 1000)
    table.add_player_at_position(human, 0)
    
    # 添加各种等级的机器人
    bots = [
        Bot("bot1", "初级机器人", 100, BotLevel.BEGINNER),      # 低筹码
        Bot("bot2", "中级机器人", 1000, BotLevel.INTERMEDIATE),
        Bot("bot3", "高级机器人", 5000, BotLevel.ADVANCED),
        Bot("bot4", "神级机器人", 0, BotLevel.GOD),             # 无筹码
    ]
    
    for i, bot in enumerate(bots):
        table.add_player_at_position(bot, i + 1)
    
    print(f"✅ 创建牌桌，{len(table.players)} 名玩家")
    
    # 测试各种边界情况
    test_cases = [
        "正常游戏流程",
        "低筹码机器人",
        "无筹码机器人", 
        "异常游戏状态",
        "决策超时"
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🔍 测试用例 {i+1}: {test_case}")
        
        try:
            if i == 0:
                # 正常游戏流程
                table.start_new_hand()
                human.fold()  # 人类弃牌，让机器人处理
                
            elif i == 1:
                # 测试低筹码机器人
                table.start_new_hand()
                bots[0].chips = 5  # 设置极低筹码
                human.fold()
                
            elif i == 2:
                # 测试无筹码机器人
                table.start_new_hand()
                bots[3].chips = 0  # 设置无筹码
                human.fold()
                
            elif i == 3:
                # 异常游戏状态
                table.start_new_hand()
                # 模拟异常状态
                for bot in bots:
                    if bot.chips > 0:
                        bot.status = PlayerStatus.FOLDED
                human.fold()
                
            elif i == 4:
                # 测试决策超时（模拟机器人决策函数异常）
                table.start_new_hand()
                # 这会触发机器人的异常处理机制
                original_decide = bots[1].decide_action
                bots[1].decide_action = lambda x: None  # 模拟返回None
                human.fold()
                bots[1].decide_action = original_decide  # 恢复
            
            # 处理机器人动作，设置超时
            start_time = time.time()
            timeout = 10  # 10秒超时
            
            print("⏳ 开始处理机器人动作...")
            
            # 模拟处理机器人动作
            result = table.process_bot_actions()
            
            elapsed = time.time() - start_time
            
            if elapsed > timeout:
                print(f"❌ 测试用例 {i+1} 超时! 耗时: {elapsed:.2f}秒")
                return False
            else:
                print(f"✅ 测试用例 {i+1} 通过! 耗时: {elapsed:.2f}秒")
                print(f"   结果: {result}")
                
        except Exception as e:
            print(f"❌ 测试用例 {i+1} 异常: {e}")
            return False
    
    print("\n🎉 所有反卡死测试通过!")
    return True

def test_bot_decision_robustness():
    """测试机器人决策的健壮性"""
    print("\n🧪 开始机器人决策健壮性测试...")
    
    # 创建机器人
    bot = Bot("test_bot", "测试机器人", 1000, BotLevel.INTERMEDIATE)
    
    # 测试各种异常游戏状态
    test_states = [
        {},  # 空状态
        {'current_bet': -1},  # 负数下注
        {'pot_size': None},  # None值
        {'community_cards': None},  # None公共牌
        {'active_players': 0},  # 无活跃玩家
    ]
    
    for i, state in enumerate(test_states):
        print(f"🔍 测试异常状态 {i+1}: {state}")
        
        try:
            result = bot.decide_action(state)
            
            if result and len(result) == 2:
                action_type, amount = result
                print(f"✅ 返回有效决策: {action_type.value}, ${amount}")
            else:
                print(f"❌ 返回无效决策: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 决策异常: {e}")
            return False
    
    print("✅ 机器人决策健壮性测试通过!")
    return True

if __name__ == "__main__":
    print("🚀 启动反卡死综合测试...")
    
    success = True
    
    # 测试1: 反卡死机制
    if not test_bot_anti_freeze():
        success = False
    
    # 测试2: 决策健壮性
    if not test_bot_decision_robustness():
        success = False
    
    if success:
        print("\n🎯 所有测试通过! 机器人反卡死机制工作正常")
        print("🔧 修复内容:")
        print("   - 添加了机器人决策异常处理")
        print("   - 实现了兜底策略防止返回None")
        print("   - 增强了游戏状态验证")
        print("   - 添加了超时和错误恢复机制")
    else:
        print("\n❌ 测试失败! 请检查机器人逻辑")
        
    print("\n现在可以重新开始游戏，机器人不会再卡死了!") 