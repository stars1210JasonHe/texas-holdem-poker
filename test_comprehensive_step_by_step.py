#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerAction, PlayerStatus
from poker_engine.card import Card, Suit, Rank

def test_seat_selection():
    """测试选座位功能"""
    print("\n=== 测试选座位功能 ===")
    
    try:
        # 创建牌桌
        table = Table("test_table", "测试桌", max_players=6)
        
        # 创建玩家
        player1 = Player("p1", "Alice", 1000)
        player2 = Player("p2", "Bob", 1000) 
        player3 = Player("p3", "Charlie", 1000)
        
        # 测试在指定位置添加玩家
        result1 = table.add_player_at_position(player1, 1)  # 座位2
        result2 = table.add_player_at_position(player2, 3)  # 座位4  
        result3 = table.add_player_at_position(player3, 1)  # 座位2 (应该失败)
        
        print(f"Alice 坐座位2: {result1} {'[PASS]' if result1 else '[FAIL]'}")
        print(f"Bob 坐座位4: {result2} {'[PASS]' if result2 else '[FAIL]'}")
        print(f"Charlie 坐座位2 (已占用): {result3} {'[FAIL Expected]' if not result3 else '[SHOULD FAIL]'}")
        
        # 检查座位分配
        print("\n座位分配情况:")
        seat_count = 0
        for i in range(table.max_players):
            player = table.seats.get(i)
            if player:
                print(f"  座位{i+1}: {player.nickname}")
                seat_count += 1
            else:
                print(f"  座位{i+1}: 空")
        
        # 验证结果
        if result1 and result2 and not result3 and seat_count == 2:
            print("[PASS] 选座位功能测试通过")
            return True
        else:
            print("[FAIL] 选座位功能测试失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 选座位测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_in_logic():
    """测试ALL_IN逻辑"""
    print("\n=== 测试ALL_IN逻辑 ===")
    
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
        
        # 模拟全下过程
        current_player = table.get_current_player()
        print(f"第一个行动玩家: {current_player.nickname if current_player else '无'}")
        
        # 找到Bob并让他全下
        for i, player in enumerate(table.players):
            if player.id == "p2":  # Bob
                print(f"Bob 全下前: 筹码=${player.chips}, 状态={player.status.value}")
                if current_player and current_player.id == "p2":
                    result = table.process_player_action("p2", PlayerAction.ALL_IN)
                    print(f"Bob 全下: {result.get('success', False)}")
                    print(f"Bob 全下后: 筹码=${player.chips}, 状态={player.status.value}")
                    break
        
        # 验证ALL_IN状态
        bob = None
        for player in table.players:
            if player.id == "p2":
                bob = player
                break
        
        if bob and bob.status == PlayerStatus.ALL_IN and bob.chips == 0:
            print("[PASS] ALL_IN逻辑测试通过")
            return True
        else:
            print(f"[FAIL] ALL_IN逻辑测试失败 - Bob状态: {bob.status.value if bob else 'None'}, 筹码: {bob.chips if bob else 'None'}")
            return False
            
    except Exception as e:
        print(f"[ERROR] ALL_IN测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_showdown_logic():
    """测试摊牌逻辑"""
    print("\n=== 测试摊牌逻辑 ===")
    
    try:
        # 创建牌桌
        table = Table("test_table", "测试桌")
        
        # 添加玩家
        player1 = Player("p1", "Alice", 1000)
        player2 = Player("p2", "Bob", 1000)
        
        table.add_player(player1)
        table.add_player(player2)
        
        # 手动设置到摊牌阶段
        table.start_new_hand()
        table.game_stage = GameStage.SHOWDOWN
        table.pot = 300
        
        # 分配手牌 - Alice 更强
        player1.hole_cards = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.SPADES, Rank.ACE)
        ]
        
        player2.hole_cards = [
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.SPADES, Rank.KING)
        ]
        
        # 设置公共牌
        table.community_cards = [
            Card(Suit.DIAMONDS, Rank.TWO),
            Card(Suit.CLUBS, Rank.FIVE),
            Card(Suit.HEARTS, Rank.EIGHT),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.DIAMONDS, Rank.QUEEN)
        ]
        
        print("手牌分配:")
        print(f"Alice: AA (一对A)")
        print(f"Bob: KK (一对K)")
        
        # 设置玩家状态
        for player in table.players:
            player.status = PlayerStatus.PLAYING
            player.has_acted = True
        
        # 测试摊牌
        print("\n开始摊牌...")
        showdown_result = table._determine_winner()
        
        winner = showdown_result.get('winner')
        if winner:
            winner_name = winner.nickname if hasattr(winner, 'nickname') else str(winner)
            print(f"获胜者: {winner_name}")
            
            if winner_name == "Alice":
                print("[PASS] 摊牌逻辑测试通过 - Alice正确获胜")
                return True
            else:
                print(f"[FAIL] 摊牌逻辑测试失败 - 应该Alice获胜，实际{winner_name}获胜")
                return False
        else:
            print("[FAIL] 摊牌逻辑测试失败 - 没有获胜者")
            return False
            
    except Exception as e:
        print(f"[ERROR] 摊牌测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_game_flow():
    """测试简单游戏流程"""
    print("\n=== 测试简单游戏流程 ===")
    
    try:
        # 创建牌桌
        table = Table("test_table", "测试桌", small_blind=5, big_blind=10)
        
        # 添加玩家
        player1 = Player("p1", "Alice", 100)
        player2 = Player("p2", "Bob", 100)
        
        table.add_player(player1)
        table.add_player(player2)
        
        print(f"玩家数: {len(table.players)}")
        
        # 开始游戏
        table.start_new_hand()
        print(f"游戏开始: 阶段={table.game_stage.value}")
        
        # 模拟几个简单动作
        action_count = 0
        max_actions = 5
        
        while action_count < max_actions:
            current_player = table.get_current_player()
            if not current_player:
                print("没有当前玩家，游戏可能结束")
                break
                
            action_count += 1
            print(f"动作{action_count}: {current_player.nickname} 行动")
            
            # 简单策略：过牌或跟注
            if table.current_bet > current_player.current_bet:
                result = table.process_player_action(current_player.id, PlayerAction.CALL)
                print(f"  跟注: {result.get('success', False)}")
            else:
                result = table.process_player_action(current_player.id, PlayerAction.CHECK)
                print(f"  过牌: {result.get('success', False)}")
        
        print(f"执行了{action_count}个动作")
        print(f"最终阶段: {table.game_stage.value}")
        
        if action_count > 0 and action_count < max_actions:
            print("[PASS] 简单游戏流程测试通过")
            return True
        else:
            print("[FAIL] 简单游戏流程测试失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 游戏流程测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("=== 扑克游戏综合功能测试 ===")
    
    tests = [
        ("选座位功能", test_seat_selection),
        ("ALL_IN逻辑", test_all_in_logic),
        ("摊牌逻辑", test_showdown_logic),
        ("简单游戏流程", test_simple_game_flow),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        try:
            if test_func():
                print(f"[PASS] {test_name}")
                passed += 1
            else:
                print(f"[FAIL] {test_name}")
        except Exception as e:
            print(f"[ERROR] {test_name} 测试异常: {e}")
    
    print(f"\n=== 测试总结 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] 所有测试都通过了!")
    else:
        print(f"[WARNING] 有 {total - passed} 个测试失败")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 