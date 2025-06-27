#!/usr/bin/env python3
"""测试全下玩家的胜负判定修复"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table
from poker_engine.player import Player, PlayerStatus, PlayerAction
from poker_engine.card import Card, Rank, Suit

def test_all_in_winner_determination():
    """测试全下玩家是否能正确参与胜负判定"""
    print("🧪 测试：全下玩家胜负判定修复")
    print("=" * 50)
    
    # 创建测试桌子
    table = Table("test_table", "测试桌子", game_mode="ante", initial_chips=1000)
    
    # 添加测试玩家
    player1 = Player("player1", "玩家1", chips=1000, is_bot=False)
    player2 = Player("player2", "玩家2", chips=1000, is_bot=False)
    
    table.add_player(player1)
    table.add_player(player2)
    
    # 开始新手牌
    table.start_new_hand()
    
    print(f"🎮 游戏开始，初始状态：")
    print(f"  玩家1: 筹码={player1.chips}, 状态={player1.status.value}")
    print(f"  玩家2: 筹码={player2.chips}, 状态={player2.status.value}")
    
    # 模拟下注到玩家1全下
    print(f"\n📈 模拟下注过程：")
    
    # 玩家1下注100
    result = table.process_player_action("player1", PlayerAction.BET, 100)
    print(f"  玩家1下注100: {result['description']}")
    
    # 玩家2加注到500
    result = table.process_player_action("player2", PlayerAction.RAISE, 500)
    print(f"  玩家2加注到500: {result['description']}")
    
    # 玩家1全下（剩余900筹码）
    result = table.process_player_action("player1", PlayerAction.ALL_IN, player1.chips)
    print(f"  玩家1全下: {result['description']}")
    print(f"    玩家1状态: {player1.status.value}, 筹码: {player1.chips}")
    
    # 玩家2跟注
    needed = player1.current_bet - player2.current_bet
    result = table.process_player_action("player2", PlayerAction.CALL, needed)
    print(f"  玩家2跟注: {result['description']}")
    
    # 检查活跃玩家判定
    print(f"\n🏆 胜负判定测试：")
    
    # 手动设置公共牌进入摊牌阶段
    table.community_cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS), 
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS)
    ]
    table.game_stage = table.game_stage.SHOWDOWN
    
    # 设置玩家手牌（玩家1获胜）
    player1.hole_cards = [Card(Rank.NINE, Suit.HEARTS), Card(Rank.EIGHT, Suit.HEARTS)]  # 同花顺
    player2.hole_cards = [Card(Rank.TWO, Suit.SPADES), Card(Rank.THREE, Suit.CLUBS)]    # 高牌
    
    # 确定获胜者
    showdown_result = table._determine_winner()
    
    print(f"  活跃玩家数量: {len([p for p in table.players if p.status in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]])}")
    print(f"  获胜者: {showdown_result['winner'].nickname if showdown_result['winner'] else '无'}")
    print(f"  是否摊牌: {showdown_result['is_showdown']}")
    print(f"  底池: ${showdown_result['pot']}")
    
    # 验证结果
    if showdown_result['winner'] and showdown_result['winner'].nickname == "玩家1":
        print(f"✅ 测试通过：全下玩家 {showdown_result['winner'].nickname} 正确获胜！")
        print(f"   获胜玩家筹码: {showdown_result['winner'].chips}")
        return True
    else:
        print(f"❌ 测试失败：全下玩家未能参与胜负判定")
        return False

def test_all_in_status_transition():
    """测试全下状态转换"""
    print("\n🧪 测试：全下状态转换")
    print("=" * 50)
    
    player = Player("test", "测试玩家", chips=100)
    player.status = PlayerStatus.PLAYING
    
    print(f"初始状态: 筹码={player.chips}, 状态={player.status.value}")
    
    # 全下所有筹码
    amount = player.place_bet(100)
    
    print(f"全下后: 筹码={player.chips}, 状态={player.status.value}, 实际下注={amount}")
    
    if player.status == PlayerStatus.ALL_IN and player.chips == 0:
        print("✅ 测试通过：全下状态正确设置为 ALL_IN")
        return True
    else:
        print("❌ 测试失败：全下状态设置错误")
        return False

if __name__ == "__main__":
    print("🚀 开始测试全下玩家胜负判定修复...")
    
    test1_passed = test_all_in_status_transition()
    test2_passed = test_all_in_winner_determination()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！全下玩家胜负判定已修复")
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
    print("=" * 50) 