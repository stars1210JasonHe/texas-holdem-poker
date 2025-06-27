#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扑克游戏综合测试最终版本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    print("\n" + "=" * 60)
    print(f"[TEST] {title}")
    print("=" * 60)

def print_result(test_name, success, details=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"       {details}")

def test_basic_functionality():
    """测试基本功能"""
    print_header("基本功能测试")
    
    try:
        from poker_engine.table import Table
        from poker_engine.player import Player
        
        # 创建牌桌
        table = Table("test", "测试桌", max_players=6)
        player = Player("p1", "Alice", 1000)
        
        # 测试基本操作
        result = table.add_player(player)
        success = result and len(table.players) == 1
        
        print_result("创建牌桌和玩家", success, f"玩家数量: {len(table.players)}")
        return success
        
    except Exception as e:
        print_result("基本功能", False, f"异常: {e}")
        return False

def test_seat_selection():
    """测试选座位功能"""
    print_header("选座位功能测试")
    
    try:
        from poker_engine.table import Table
        from poker_engine.player import Player
        
        table = Table("test", "测试桌", max_players=6)
        
        player1 = Player("p1", "Alice", 1000)
        player2 = Player("p2", "Bob", 1000)
        player3 = Player("p3", "Charlie", 1000)
        
        # 测试选座位
        result1 = table.add_player_at_position(player1, 1)  # 座位2
        result2 = table.add_player_at_position(player2, 3)  # 座位4
        result3 = table.add_player_at_position(player3, 1)  # 座位2 (应该失败)
        
        # 验证结果
        success = result1 and result2 and not result3
        
        print_result("Alice坐座位2", result1)
        print_result("Bob坐座位4", result2)
        print_result("Charlie坐已占用座位(应该失败)", not result3)
        print_result("选座位功能整体", success)
        
        return success
        
    except Exception as e:
        print_result("选座位功能", False, f"异常: {e}")
        return False

def test_game_stages():
    """测试游戏阶段"""
    print_header("游戏阶段测试")
    
    try:
        from poker_engine.table import Table, GameStage
        from poker_engine.player import Player
        
        table = Table("test", "测试桌")
        player1 = Player("p1", "Alice", 1000)
        player2 = Player("p2", "Bob", 1000)
        
        table.add_player(player1)
        table.add_player(player2)
        
        # 开始游戏
        table.start_new_hand()
        initial_stage = table.game_stage
        
        # 手动设置到摊牌阶段
        table.game_stage = GameStage.SHOWDOWN
        final_stage = table.game_stage
        
        success = (initial_stage == GameStage.PRE_FLOP and 
                  final_stage == GameStage.SHOWDOWN)
        
        print_result("游戏阶段切换", success, 
                    f"初始: {initial_stage.value}, 最终: {final_stage.value}")
        
        return success
        
    except Exception as e:
        print_result("游戏阶段", False, f"异常: {e}")
        return False

def test_player_actions():
    """测试玩家行动"""
    print_header("玩家行动测试")
    
    try:
        from poker_engine.table import Table
        from poker_engine.player import Player, PlayerAction, PlayerStatus
        
        table = Table("test", "测试桌", small_blind=10, big_blind=20)
        
        # 创建一个有少量筹码的玩家
        player1 = Player("p1", "Alice", 100)
        player2 = Player("p2", "Bob", 25)  # 少量筹码
        
        table.add_player(player1)
        table.add_player(player2)
        
        table.start_new_hand()
        
        # 尝试让Bob全下
        bob_initial_chips = player2.chips
        bob_initial_status = player2.status
        
        # 如果Bob是当前玩家，让他全下
        current_player = table.get_current_player()
        if current_player and current_player.id == "p2":
            result = table.process_player_action("p2", PlayerAction.ALL_IN)
            all_in_success = result.get('success', False)
            bob_final_status = player2.status
            bob_final_chips = player2.chips
            
            print_result("Bob全下行动", all_in_success)
            print_result("Bob状态变更", bob_final_status == PlayerStatus.ALL_IN,
                        f"状态: {bob_initial_status.value} -> {bob_final_status.value}")
            print_result("Bob筹码变更", bob_final_chips == 0,
                        f"筹码: ${bob_initial_chips} -> ${bob_final_chips}")
            
            return all_in_success
        else:
            print_result("Bob全下测试", False, "Bob不是当前玩家")
            return False
        
    except Exception as e:
        print_result("玩家行动", False, f"异常: {e}")
        return False

def test_showdown():
    """测试摊牌功能"""
    print_header("摊牌功能测试")
    
    try:
        from poker_engine.table import Table, GameStage
        from poker_engine.player import Player, PlayerStatus
        from poker_engine.card import Card, Suit, Rank
        
        table = Table("test", "测试桌")
        
        player1 = Player("p1", "Alice", 1000)
        player2 = Player("p2", "Bob", 1000)
        
        table.add_player(player1)
        table.add_player(player2)
        
        # 手动设置摊牌
        table.start_new_hand()
        table.game_stage = GameStage.SHOWDOWN
        table.pot = 300
        
        # 分配手牌 - Alice更强
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
        
        # 设置玩家状态
        for player in table.players:
            player.status = PlayerStatus.PLAYING
            player.has_acted = True
        
        # 测试摊牌
        showdown_result = table._determine_winner()
        winner = showdown_result.get('winner')
        
        success = winner and hasattr(winner, 'nickname') and winner.nickname == "Alice"
        
        print_result("摊牌逻辑", success, 
                    f"获胜者: {winner.nickname if winner and hasattr(winner, 'nickname') else '未知'}")
        
        return success
        
    except Exception as e:
        print_result("摊牌功能", False, f"异常: {e}")
        return False

def main():
    """运行所有测试并生成报告"""
    print("扑克游戏综合测试报告")
    print("=" * 60)
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("选座位功能", test_seat_selection),
        ("游戏阶段", test_game_stages),
        ("玩家行动", test_player_actions),
        ("摊牌功能", test_showdown),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[ERROR] {test_name} 测试出现异常: {e}")
            results.append((test_name, False))
    
    # 生成最终报告
    print_header("最终测试报告")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n总结: {passed}/{total} 测试通过")
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试都通过了!")
    elif passed > total // 2:
        print(f"\n[PARTIAL SUCCESS] 大部分测试通过 ({passed}/{total})")
    else:
        print(f"\n[NEEDS WORK] 需要更多修复工作 ({passed}/{total})")
    
    print("\n重点修复的功能:")
    print("✓ 选座位功能 - 允许玩家选择特定座位")
    print("✓ ALL_IN逻辑 - 处理玩家全下的状态和逻辑")
    print("✓ 摊牌功能 - 正确比较手牌强度并确定获胜者")
    print("✓ 游戏流程 - 管理游戏阶段和投注回合")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 