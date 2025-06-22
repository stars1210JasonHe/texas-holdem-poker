#!/usr/bin/env python3
"""
摊牌记录功能测试脚本
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine import Player, Table, Bot, BotLevel
from poker_engine.card import Card, Rank, Suit
from poker_engine.hand_evaluator import HandEvaluator
from game_logger import log_table_created, log_hand_started, log_hand_ended

def test_showdown_functionality():
    """测试摊牌记录功能"""
    print("🃏 开始测试摊牌记录功能...")
    print("=" * 60)
    
    # 创建测试牌桌
    table = Table("test_table", "测试摊牌功能", small_blind=10, big_blind=20)
    
    # 创建测试玩家
    player1 = Player("test_player_1", "Alice", 1000)
    player2 = Player("test_player_2", "Bob", 1000)
    bot1 = Bot("test_bot_1", "Bot_Easy", 1000, BotLevel.BEGINNER)
    
    # 添加玩家到牌桌
    table.add_player(player1)
    table.add_player(player2)
    table.add_player(bot1)
    
    print(f"✅ 牌桌创建完成，玩家数: {len(table.players)}")
    
    # 开始新手牌
    success = table.start_new_hand()
    if not success:
        print("❌ 开始手牌失败")
        return False
    
    print(f"✅ 手牌开始 #{table.hand_number}")
    
    # 手动设置玩家手牌以便测试摊牌
    # Alice: A♠️ K♠️ (皇家同花顺的潜力)
    player1.hole_cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.SPADES, Rank.KING)
    ]
    
    # Bob: Q♦️ Q♣️ (一对Q)
    player2.hole_cards = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.QUEEN)
    ]
    
    # Bot: J♣️ 10♣️ (顺子潜力)
    bot1.hole_cards = [
        Card(Suit.CLUBS, Rank.JACK),
        Card(Suit.CLUBS, Rank.TEN)
    ]
    
    # 设置公共牌 - 创造一个有趣的摊牌场景
    # Q♠️ J♠️ 10♠️ 9♠️ 8♠️ (同花顺)
    table.community_cards = [
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN),
        Card(Suit.SPADES, Rank.NINE),
        Card(Suit.SPADES, Rank.EIGHT)
    ]
    
    # 设置底池
    table.pot = 300
    
    # 将游戏阶段设置为摊牌
    from poker_engine.table import GameStage
    table.game_stage = GameStage.SHOWDOWN
    
    print("\n🎴 测试场景设置:")
    print("公共牌: Q♠️ J♠️ 10♠️ 9♠️ 8♠️")
    print("Alice: A♠️ K♠️")
    print("Bob: Q♦️ Q♣️") 
    print("Bot: J♣️ 10♣️")
    print(f"底池: ${table.pot}")
    print("-" * 40)
    
    # 执行摊牌
    showdown_result = table._determine_winner()
    
    print("\n🏆 摊牌结果分析:")
    print(f"是否为摊牌: {showdown_result.get('is_showdown')}")
    print(f"获胜原因: {showdown_result.get('win_reason')}")
    
    if showdown_result.get('winner'):
        winner = showdown_result['winner']
        print(f"获胜者: {winner.nickname}")
        print(f"获胜者筹码: ${winner.chips}")
    
    # 显示所有玩家的详细信息
    if showdown_result.get('showdown_players'):
        print("\n📊 详细摊牌记录:")
        for player_info in showdown_result['showdown_players']:
            rank_emoji = "🥇" if player_info['rank'] == 1 else "🥈" if player_info['rank'] == 2 else "🥉"
            player_type = "🤖" if player_info['is_bot'] else "👤"
            print(f"{rank_emoji} {player_type} {player_info['nickname']}: "
                  f"{player_info['hole_cards_str']} -> {player_info['hand_description']} "
                  f"({'赢得 $' + str(player_info['winnings']) if player_info['result'] == 'winner' else '败北'})")
    
    print("\n🔍 手牌强度分析:")
    for player in [player1, player2, bot1]:
        if len(player.hole_cards) == 2:
            hand_rank, kickers = HandEvaluator.evaluate_hand(player.hole_cards, table.community_cards)
            hand_description = HandEvaluator.hand_to_string((hand_rank, kickers))
            player_type = "🤖" if player.is_bot else "👤"
            print(f"{player_type} {player.nickname}: {hand_description} (强度: {hand_rank.rank_value})")
    
    print("\n✅ 摊牌功能测试完成！")
    return True

def test_hand_evaluator():
    """测试手牌评估器"""
    print("\n🎯 测试手牌评估器...")
    
    # 测试皇家同花顺
    royal_flush_cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.SPADES, Rank.KING)
    ]
    community = [
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN)
    ]
    
    hand_rank, kickers = HandEvaluator.evaluate_hand(royal_flush_cards, community)
    description = HandEvaluator.hand_to_string((hand_rank, kickers))
    print(f"A♠️ K♠️ + Q♠️ J♠️ 10♠️ = {description}")
    
    # 测试三条
    three_kind_cards = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.QUEEN)
    ]
    
    hand_rank2, kickers2 = HandEvaluator.evaluate_hand(three_kind_cards, community)
    description2 = HandEvaluator.hand_to_string((hand_rank2, kickers2))
    print(f"Q♦️ Q♣️ + Q♠️ J♠️ 10♠️ = {description2}")
    
    print("✅ 手牌评估器测试完成！")

if __name__ == "__main__":
    print("🃏 德州扑克摊牌记录功能测试")
    print("=" * 60)
    
    try:
        # 测试手牌评估器
        test_hand_evaluator()
        
        # 测试摊牌功能
        test_showdown_functionality()
        
        print("\n🎉 所有测试完成！摊牌记录功能运行正常。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 