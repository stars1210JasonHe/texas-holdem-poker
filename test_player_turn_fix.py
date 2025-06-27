#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真人弃牌后机器人卡死问题的专项修复
"""

import sys
import time
from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerStatus, PlayerAction
from poker_engine.bot import Bot, BotLevel

def test_human_fold_bot_freeze():
    """测试真人弃牌后机器人是否会卡死"""
    print("🎮 开始测试: 真人弃牌后机器人卡死问题")
    
    # 创建测试桌子
    table = Table("test_table", "弃牌卡死测试", small_blind=10, big_blind=20)
    
    # 添加1个真人和3个机器人
    human = Player("human1", "真人玩家", 1000)
    table.add_player(human)
    
    bots = [
        Bot("bot1", "新手机器人", 1000, BotLevel.BEGINNER),
        Bot("bot2", "中级机器人", 1000, BotLevel.INTERMEDIATE), 
        Bot("bot3", "高级机器人", 1000, BotLevel.ADVANCED)
    ]
    
    for bot in bots:
        table.add_player(bot)
    
    print(f"✅ 桌子创建完成，共{len(table.players)}个玩家")
    
    # 开始新手牌
    if not table.start_new_hand():
        print("❌ 无法开始新手牌")
        return False
    
    print(f"✅ 手牌开始，当前阶段: {table.game_stage.value}")
    print(f"当前下注: ${table.current_bet}")
    
    # 查看当前轮到谁
    current_player = table.get_current_player()
    print(f"轮到: {current_player.nickname} ({current_player.id})")
    
    # 真人玩家立即弃牌
    print("\n👤 真人玩家执行弃牌操作...")
    
    # 检查是否轮到真人
    if current_player.id != human.id:
        print(f"❌ 当前不是真人回合，而是 {current_player.nickname}")
        return False
    
    # 执行弃牌
    fold_result = table.process_player_action(human.id, PlayerAction.FOLD)
    print(f"弃牌结果: {fold_result}")
    
    if not fold_result['success']:
        print(f"❌ 弃牌失败: {fold_result['message']}")
        return False
    
    print(f"✅ 真人弃牌成功")
    print(f"真人状态: {human.status.value}")
    print(f"has_acted: {human.has_acted}")
    
    # 打印当前所有玩家状态
    print("\n📊 弃牌后玩家状态:")
    for player in table.players:
        print(f"  {player.nickname}: 状态={player.status.value}, 投注=${player.current_bet}, has_acted={player.has_acted}")
    
    # 检查游戏是否能正常继续
    print("\n🤖 开始处理机器人行动...")
    start_time = time.time()
    
    try:
        # 设置超时时间为10秒
        bot_result = table.process_bot_actions()
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"✅ 机器人处理完成，耗时: {processing_time:.2f}秒")
        print(f"处理结果: {bot_result}")
        
        # 检查是否卡死（超时）
        if processing_time > 5.0:  # 如果超过5秒就认为有问题
            print(f"⚠️ 处理时间过长: {processing_time:.2f}秒，可能存在卡死问题")
            return False
        
        # 检查最终状态
        print("\n📊 最终状态:")
        print(f"游戏阶段: {table.game_stage.value}")
        print(f"底池: ${table.pot}")
        
        for player in table.players:
            print(f"  {player.nickname}: 状态={player.status.value}, 筹码=${player.chips}")
        
        return True
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ 机器人处理出错: {e}")
        print(f"错误发生时间: {end_time - start_time:.2f}秒")
        return False

def test_multiple_scenarios():
    """测试多种弃牌场景"""
    print("\n🧪 运行多种弃牌场景测试...")
    
    scenarios = [
        {"human_pos": 0, "name": "真人第一个行动时弃牌"},
        {"human_pos": 1, "name": "真人第二个行动时弃牌"},
        {"human_pos": 2, "name": "真人第三个行动时弃牌"},
    ]
    
    success_count = 0
    
    for i, scenario in enumerate(scenarios):
        print(f"\n--- 场景 {i+1}: {scenario['name']} ---")
        
        # 创建新桌子
        table = Table(f"test_table_{i}", scenario['name'], small_blind=10, big_blind=20)
        
        # 根据场景添加玩家
        players = []
        for j in range(4):
            if j == scenario['human_pos']:
                player = Player(f"human_{j}", f"真人_{j}", 1000)
            else:
                player = Bot(f"bot_{j}", f"机器人_{j}", 1000, BotLevel.BEGINNER)
            players.append(player)
            table.add_player(player)
        
        # 开始手牌
        if not table.start_new_hand():
            print(f"❌ 场景{i+1}: 无法开始手牌")
            continue
        
        # 等轮到真人时弃牌
        human = players[scenario['human_pos']]
        max_actions = 10
        action_count = 0
        human_folded = False
        
        try:
            while action_count < max_actions and not human_folded:
                current_player = table.get_current_player()
                if not current_player:
                    break
                
                action_count += 1
                
                if current_player.id == human.id:
                    # 真人弃牌
                    print(f"  👤 {human.nickname} 弃牌")
                    result = table.process_player_action(human.id, PlayerAction.FOLD)
                    if result['success']:
                        human_folded = True
                        
                        # 继续处理机器人
                        start_time = time.time()
                        bot_result = table.process_bot_actions()
                        end_time = time.time()
                        
                        if end_time - start_time < 5.0:
                            print(f"  ✅ 场景{i+1}成功，处理时间: {end_time - start_time:.2f}秒")
                            success_count += 1
                        else:
                            print(f"  ❌ 场景{i+1}超时: {end_time - start_time:.2f}秒")
                        break
                    else:
                        print(f"  ❌ 场景{i+1}弃牌失败: {result['message']}")
                        break
                else:
                    # 机器人简单过牌或跟注
                    if table.current_bet > current_player.current_bet:
                        # 需要跟注，简单弃牌
                        table.process_player_action(current_player.id, PlayerAction.FOLD)
                    else:
                        # 可以过牌
                        table.process_player_action(current_player.id, PlayerAction.CHECK)
        
        except Exception as e:
            print(f"  ❌ 场景{i+1}出错: {e}")
    
    print(f"\n📊 多场景测试结果: {success_count}/{len(scenarios)} 成功")
    return success_count == len(scenarios)

if __name__ == "__main__":
    print("=" * 60)
    print("真人弃牌后机器人卡死问题专项测试")
    print("=" * 60)
    
    # 测试1: 基本弃牌场景
    test1_success = test_human_fold_bot_freeze()
    
    # 测试2: 多种弃牌场景
    test2_success = test_multiple_scenarios()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  基本弃牌测试: {'✅ 通过' if test1_success else '❌ 失败'}")
    print(f"  多场景测试: {'✅ 通过' if test2_success else '❌ 失败'}")
    
    if test1_success and test2_success:
        print("🎉 所有测试通过！机器人卡死问题已修复")
        sys.exit(0)
    else:
        print("❌ 发现问题，需要进一步修复")
        sys.exit(1) 