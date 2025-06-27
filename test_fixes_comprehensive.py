#!/usr/bin/env python3
"""
全面测试修复的功能：选座位、ALL_IN逻辑、摊牌功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerAction, PlayerStatus
from poker_engine.bot import Bot, BotLevel
from poker_engine.card import Card, Suit, Rank
import json

def test_seat_selection():
    """测试选座位功能"""
    print("=" * 60)
    print("🪑 测试选座位功能")
    print("=" * 60)
    
    # 创建牌桌
    table = Table("test_table", "测试桌", max_players=6)
    
    # 测试添加玩家到指定位置
    player1 = Player("p1", "Alice", 1000)
    player2 = Player("p2", "Bob", 1000) 
    player3 = Player("p3", "Charlie", 1000)
    
    # 测试在指定位置添加玩家
    result1 = table.add_player_at_position(player1, 1)  # 座位2
    result2 = table.add_player_at_position(player2, 3)  # 座位4  
    result3 = table.add_player_at_position(player3, 1)  # 座位2 (应该失败)
    
    print(f"Alice 坐座位2: {result1} ✅" if result1 else f"Alice 坐座位2: {result1} ❌")
    print(f"Bob 坐座位4: {result2} ✅" if result2 else f"Bob 坐座位4: {result2} ❌")
    print(f"Charlie 坐座位2 (已占用): {result3} ❌" if not result3 else f"Charlie 坐座位2 (应该失败): {result3} ✅")
    
    # 检查座位分配
    print("\n📋 座位分配情况:")
    for i in range(table.max_players):
        player = table.seats.get(i)
        if player:
            print(f"  座位{i+1}: {player.nickname}")
        else:
            print(f"  座位{i+1}: 空")
    
    # 检查玩家位置查询
    alice_pos = table.get_player_position("p1")
    bob_pos = table.get_player_position("p2")
    print(f"\n🔍 位置查询:")
    print(f"Alice 位置: {alice_pos + 1 if alice_pos is not None else '未找到'}")
    print(f"Bob 位置: {bob_pos + 1 if bob_pos is not None else '未找到'}")
    
    return table

def test_all_in_logic():
    """测试ALL_IN逻辑"""
    print("\n" + "=" * 60)
    print("🎰 测试ALL_IN逻辑")
    print("=" * 60)
    
    # 创建牌桌
    table = Table("test_table", "测试桌", small_blind=10, big_blind=20, initial_chips=100)
    
    # 添加玩家 (不同筹码数量)
    player1 = Player("p1", "Alice", 100)   # 正常筹码
    player2 = Player("p2", "Bob", 30)      # 少量筹码，容易全下
    player3 = Player("p3", "Charlie", 100) # 正常筹码
    
    table.add_player(player1)
    table.add_player(player2) 
    table.add_player(player3)
    
    print(f"初始玩家筹码: Alice=${player1.chips}, Bob=${player2.chips}, Charlie=${player3.chips}")
    
    # 开始新手牌
    table.start_new_hand()
    print(f"游戏开始: 阶段={table.game_stage.value}, 当前下注=${table.current_bet}, 底池=${table.pot}")
    
    # 模拟游戏过程
    print("\n🎮 模拟游戏过程:")
    
    # 获取第一个行动玩家
    current_player = table.get_current_player()
    print(f"第一个行动玩家: {current_player.nickname if current_player else '无'}")
    
    # Alice 跟注
    if current_player and current_player.id == "p1":
        result = table.process_player_action("p1", PlayerAction.CALL)
        print(f"Alice 跟注: {result['success']}, {result.get('message', '')}")
        current_player = table.get_current_player()
    
    # Bob 全下 (他只有30筹码)
    if current_player and current_player.id == "p2":
        print(f"Bob 全下前: 筹码=${player2.chips}, 状态={player2.status.value}")
        result = table.process_player_action("p2", PlayerAction.ALL_IN)
        print(f"Bob 全下: {result['success']}, {result.get('message', '')}")
        print(f"Bob 全下后: 筹码=${player2.chips}, 状态={player2.status.value}")
        print(f"当前下注提升到: ${table.current_bet}, 底池=${table.pot}")
    
    # 检查投注回合状态
    is_complete = table.is_betting_round_complete()
    print(f"\n📊 投注回合完成状态: {is_complete}")
    
    # 检查当前行动玩家
    current_player = table.get_current_player()
    if current_player:
        print(f"下一个行动玩家: {current_player.nickname}")
        print(f"需要跟注金额: ${table.current_bet - current_player.current_bet}")
    else:
        print("没有需要行动的玩家")
    
    # Charlie 跟注Bob的全下
    if current_player and current_player.id == "p3":
        result = table.process_player_action("p3", PlayerAction.CALL)
        print(f"Charlie 跟注: {result['success']}, {result.get('message', '')}")
    
    # 再次检查投注回合
    is_complete = table.is_betting_round_complete()
    print(f"所有玩家行动后投注回合完成: {is_complete}")
    
    # 检查游戏阶段
    print(f"当前游戏阶段: {table.game_stage.value}")
    
    # 验证ALL_IN玩家被正确包含在活跃玩家中
    active_players = [p for p in table.players if p.status in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]]
    print(f"活跃玩家状态: {[(p.nickname, p.status.value, p.chips) for p in active_players]}")
    
    if table.game_stage == GameStage.SHOWDOWN:
        print("❌ 错误: 过早进入摊牌阶段")
    else:
        print("✅ 正确: 没有过早进入摊牌阶段")
    
    return table

def test_showdown_logic():
    """测试摊牌逻辑"""
    print("\n" + "=" * 60)
    print("🃏 测试摊牌逻辑")
    print("=" * 60)
    
    # 创建牌桌并直接设置到River阶段进行摊牌测试
    table = Table("test_table", "测试桌", small_blind=10, big_blind=20)
    
    # 添加玩家
    player1 = Player("p1", "Alice", 1000)
    player2 = Player("p2", "Bob", 1000)
    player3 = Bot("p3", "机器人Charlie", 1000, BotLevel.BEGINNER)
    
    table.add_player(player1)
    table.add_player(player2)
    table.add_player(player3)
    
    # 手动设置游戏状态到SHOWDOWN阶段
    table.start_new_hand()
    table.game_stage = GameStage.SHOWDOWN  # 摊牌阶段
    table.pot = 300  # 设置底池
    
    # 手动分配手牌进行测试
    # Alice: 一对A (强牌)
    player1.hole_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.SPADES, Rank.ACE)
    ]
    
    # Bob: 一对K (中等牌)  
    player2.hole_cards = [
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.SPADES, Rank.KING)
    ]
    
    # 机器人: 高牌 (弱牌)
    player3.hole_cards = [
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN)
    ]
    
    # 设置公共牌
    table.community_cards = [
        Card(Suit.DIAMONDS, Rank.TWO),
        Card(Suit.CLUBS, Rank.FIVE),
        Card(Suit.HEARTS, Rank.EIGHT),
        Card(Suit.SPADES, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.QUEEN)
    ]
    
    print("🎴 手牌分配:")
    print(f"Alice: {[f'{c.rank.symbol}{c.suit.value}' for c in player1.hole_cards]} (一对A)")
    print(f"Bob: {[f'{c.rank.symbol}{c.suit.value}' for c in player2.hole_cards]} (一对K)")
    print(f"机器人: {[f'{c.rank.symbol}{c.suit.value}' for c in player3.hole_cards]} (高牌)")
    print(f"公共牌: {[f'{c.rank.symbol}{c.suit.value}' for c in table.community_cards]}")
    
    # 设置玩家状态为可以摊牌
    for player in table.players:
        player.status = PlayerStatus.PLAYING
        player.has_acted = True
    
    # 测试摊牌逻辑
    print("\n🏆 开始摊牌测试:")
    showdown_result = table._determine_winner()
    
    print("摊牌结果:")
    winner = showdown_result.get('winner')
    if winner:
        winner_name = winner.nickname if hasattr(winner, 'nickname') else str(winner)
        print(f"  获胜者: {winner_name}")
    else:
        print(f"  获胜者: 未知")
    
    print(f"  是否摊牌: {showdown_result.get('is_showdown', False)}")
    print(f"  底池金额: ${showdown_result.get('pot', 0)}")
    
    if 'showdown_players' in showdown_result and showdown_result['showdown_players']:
        print("  摊牌玩家详情:")
        for i, player_info in enumerate(showdown_result['showdown_players']):
            print(f"    {i+1}. {player_info.get('nickname', '未知')}: {player_info.get('hand_description', '未知')} - {player_info.get('result', '未知')}")
    
    # 验证获胜者是否正确 (应该是Alice的一对A)
    expected_winner = "Alice"
    actual_winner = winner.nickname if winner and hasattr(winner, 'nickname') else ''
    
    if actual_winner == expected_winner:
        print(f"✅ 摊牌逻辑正确: {expected_winner} 获胜")
    else:
        print(f"❌ 摊牌逻辑错误: 期望 {expected_winner} 获胜，实际 {actual_winner} 获胜")
    
    return showdown_result

def test_mixed_scenario():
    """测试混合场景：选座位 + ALL_IN + 摊牌"""
    print("\n" + "=" * 60)
    print("🎭 测试混合场景：选座位 + ALL_IN + 摊牌")
    print("=" * 60)
    
    # 创建牌桌
    table = Table("test_table", "综合测试桌", small_blind=5, big_blind=10, initial_chips=50)
    
    # 玩家选择特定座位
    player1 = Player("p1", "Alice", 50)
    player2 = Player("p2", "Bob", 25)    # 筹码少，容易全下
    player3 = Player("p3", "Charlie", 50)
    
    # 测试选座位
    seat1_result = table.add_player_at_position(player1, 0)  # 座位1
    seat2_result = table.add_player_at_position(player2, 2)  # 座位3
    seat3_result = table.add_player_at_position(player3, 4)  # 座位5
    
    print(f"选座结果: Alice座位1({seat1_result}), Bob座位3({seat2_result}), Charlie座位5({seat3_result})")
    
    # 开始游戏
    table.start_new_hand()
    print(f"游戏开始: 底池=${table.pot}, 当前下注=${table.current_bet}")
    
    # 模拟完整游戏流程
    action_count = 0
    max_actions = 20  # 防止无限循环
    
    print("\n🎯 完整游戏流程:")
    while not table.is_hand_complete() and action_count < max_actions:
        current_player = table.get_current_player()
        if not current_player:
            # 没有玩家需要行动，推进游戏流程
            flow_result = table.process_game_flow()
            if flow_result['stage_changed']:
                print(f"  阶段变更: {table.game_stage.value}")
            if flow_result['hand_complete']:
                print(f"  手牌结束: {flow_result.get('message', '')}")
                break
            continue
        
        action_count += 1
        print(f"  第{action_count}个动作: {current_player.nickname} 需要行动")
        
        # 简单的行动逻辑
        if current_player.id == "p2" and current_player.chips <= 15:
            # Bob 在筹码不多时全下
            result = table.process_player_action("p2", PlayerAction.ALL_IN)
            print(f"    Bob 全下: {result['success']}")
        elif table.current_bet > current_player.current_bet:
            # 需要跟注
            call_amount = table.current_bet - current_player.current_bet
            if current_player.chips >= call_amount:
                result = table.process_player_action(current_player.id, PlayerAction.CALL)
                print(f"    {current_player.nickname} 跟注: {result['success']}")
            else:
                result = table.process_player_action(current_player.id, PlayerAction.FOLD)
                print(f"    {current_player.nickname} 弃牌: {result['success']}")
        else:
            # 可以过牌
            result = table.process_player_action(current_player.id, PlayerAction.CHECK)
            print(f"    {current_player.nickname} 过牌: {result['success']}")
    
    # 检查最终状态
    print(f"\n📊 最终状态:")
    print(f"  游戏阶段: {table.game_stage.value}")
    print(f"  底池: ${table.pot}")
    active_players = [p for p in table.players if p.status in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]]
    print(f"  活跃玩家: {[(p.nickname, p.status.value, p.chips) for p in active_players]}")
    
    # 如果游戏结束，检查摊牌结果
    if table.is_hand_complete():
        showdown_result = table._determine_winner()
        if showdown_result.get('winner'):
            print(f"  获胜者: {showdown_result['winner']['nickname']}")
            print(f"  获胜金额: ${showdown_result.get('pot', 0)}")
        
        if showdown_result.get('is_showdown'):
            print("  ✅ 正确进行了摊牌")
        else:
            print("  ℹ️ 提前结束 (其他玩家弃牌)")

def main():
    """运行所有测试"""
    print("🧪 开始全面测试修复的功能")
    print("=" * 80)
    
    try:
        # 测试选座位功能
        table1 = test_seat_selection()
        
        # 测试ALL_IN逻辑
        table2 = test_all_in_logic()
        
        # 测试摊牌逻辑
        showdown_result = test_showdown_logic()
        
        # 测试混合场景
        test_mixed_scenario()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试完成!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()