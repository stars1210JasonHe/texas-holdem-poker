#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试和修复ALL_IN逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerAction, PlayerStatus
from poker_engine.card import Card, Suit, Rank

def test_all_in_detailed():
    """详细测试ALL_IN逻辑"""
    print("=== 详细ALL_IN逻辑测试 ===")
    
    try:
        # 创建牌桌
        table = Table("test_table", "测试桌", small_blind=10, big_blind=20, initial_chips=100)
        
        # 添加玩家
        player1 = Player("p1", "Alice", 100)
        player2 = Player("p2", "Bob", 30)  # 少量筹码，容易全下
        player3 = Player("p3", "Charlie", 100)
        
        table.add_player(player1)
        table.add_player(player2) 
        table.add_player(player3)
        
        print(f"初始筹码: Alice=${player1.chips}, Bob=${player2.chips}, Charlie=${player3.chips}")
        
        # 开始新手牌
        table.start_new_hand()
        print(f"游戏开始: 阶段={table.game_stage.value}, 当前下注=${table.current_bet}")
        
        # 检查初始状态
        print("\n=== 初始状态 ===")
        for i, player in enumerate(table.players):
            print(f"{player.nickname}: 筹码=${player.chips}, 投注=${player.current_bet}, 状态={player.status.value}")
        
        # 模拟行动序列
        action_count = 0
        max_actions = 10
        
        print("\n=== 行动序列 ===")
        while action_count < max_actions:
            current_player = table.get_current_player()
            if not current_player:
                print("没有当前玩家，检查投注回合状态")
                if table.is_betting_round_complete():
                    print("投注回合完成，推进游戏")
                    break
                else:
                    print("投注回合未完成但没有当前玩家，异常情况")
                    break
            
            action_count += 1
            print(f"\n--- 行动 {action_count} ---")
            print(f"当前玩家: {current_player.nickname}")
            print(f"当前下注: ${table.current_bet}")
            print(f"玩家当前投注: ${current_player.current_bet}")
            print(f"玩家筹码: ${current_player.chips}")
            
            # 决定行动
            if current_player.id == "p2":  # Bob - 尝试全下
                print(f"Bob尝试全下...")
                print(f"Bob全下前状态: 筹码=${current_player.chips}, 状态={current_player.status.value}")
                result = table.process_player_action("p2", PlayerAction.ALL_IN)
                print(f"Bob全下结果: {result.get('success', False)} - {result.get('message', '')}")
                print(f"Bob全下后状态: 筹码=${current_player.chips}, 状态={current_player.status.value}")
                
                # 验证Bob的状态
                if current_player.status == PlayerStatus.ALL_IN:
                    print("[SUCCESS] Bob成功全下")
                    return True
                else:
                    print(f"[FAIL] Bob全下失败，状态仍为: {current_player.status.value}")
                    
            elif table.current_bet > current_player.current_bet:
                # 需要跟注
                call_amount = table.current_bet - current_player.current_bet
                print(f"需要跟注: ${call_amount}")
                result = table.process_player_action(current_player.id, PlayerAction.CALL)
                print(f"跟注结果: {result.get('success', False)}")
            else:
                # 可以过牌
                print("过牌")
                result = table.process_player_action(current_player.id, PlayerAction.CHECK)
                print(f"过牌结果: {result.get('success', False)}")
        
        print(f"\n=== 最终状态 ===")
        for player in table.players:
            print(f"{player.nickname}: 筹码=${player.chips}, 状态={player.status.value}")
        
        # 检查Bob是否成功全下
        bob = None
        for player in table.players:
            if player.id == "p2":
                bob = player
                break
        
        if bob and bob.status == PlayerStatus.ALL_IN:
            print("[PASS] ALL_IN逻辑测试通过")
            return True
        else:
            print(f"[FAIL] ALL_IN逻辑测试失败 - Bob状态: {bob.status.value if bob else 'None'}")
            return False
            
    except Exception as e:
        print(f"[ERROR] ALL_IN测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_all_in():
    """简单ALL_IN测试"""
    print("\n=== 简单ALL_IN测试 ===")
    
    try:
        # 创建一个只有Bob的简单场景
        table = Table("test", "测试", small_blind=5, big_blind=10)
        
        # Bob筹码很少
        bob = Player("bob", "Bob", 15)
        alice = Player("alice", "Alice", 100)
        
        table.add_player(bob)
        table.add_player(alice)
        
        table.start_new_hand()
        
        print(f"Bob初始状态: 筹码=${bob.chips}, 状态={bob.status.value}")
        
        # 直接让Bob全下
        if table.get_current_player() and table.get_current_player().id == "bob":
            print("Bob是当前玩家，尝试全下...")
            result = table.process_player_action("bob", PlayerAction.ALL_IN)
            print(f"全下结果: {result}")
            print(f"Bob全下后状态: 筹码=${bob.chips}, 状态={bob.status.value}")
            
            if bob.status == PlayerStatus.ALL_IN and bob.chips == 0:
                print("[PASS] 简单ALL_IN测试通过")
                return True
            else:
                print("[FAIL] 简单ALL_IN测试失败")
                return False
        else:
            print("Bob不是当前玩家，跳过测试")
            return False
            
    except Exception as e:
        print(f"[ERROR] 简单ALL_IN测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行ALL_IN测试"""
    print("=== ALL_IN逻辑修复测试 ===")
    
    # 运行简单测试
    simple_result = test_simple_all_in()
    
    # 运行详细测试
    detailed_result = test_all_in_detailed()
    
    print(f"\n=== 结果总结 ===")
    print(f"简单ALL_IN测试: {'PASS' if simple_result else 'FAIL'}")
    print(f"详细ALL_IN测试: {'PASS' if detailed_result else 'FAIL'}")
    
    if simple_result or detailed_result:
        print("[SUCCESS] 至少一个ALL_IN测试通过")
        return True
    else:
        print("[FAIL] 所有ALL_IN测试都失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 