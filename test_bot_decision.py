#!/usr/bin/env python3

"""
简单的机器人决策测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine import Bot, BotLevel, Table
from poker_engine.card import Card, Suit, Rank

def test_bot_decision():
    print("🧪 测试机器人决策逻辑")
    
    # 创建一个机器人
    bot = Bot("bot1", "测试机器人", 1000, BotLevel.BEGINNER)
    
    # 给机器人发牌
    card1 = Card(Suit.HEARTS, Rank.ACE)
    card2 = Card(Suit.SPADES, Rank.KING)
    bot.deal_hole_cards([card1, card2])
    
    # 重要：设置机器人状态为PLAYING
    from poker_engine.player import PlayerStatus
    bot.status = PlayerStatus.PLAYING
    
    print(f"🤖 机器人: {bot.nickname}")
    print(f"🃏 手牌: {card1} {card2}")
    print(f"📊 状态: {bot.status.value}")
    print(f"💰 筹码: {bot.chips}")
    
    # 构造游戏状态
    game_state = {
        'community_cards': [],
        'current_bet': 20,
        'big_blind': 20,
        'pot_size': 30,
        'active_players': 3,
        'position': 'middle',
        'min_raise': 40
    }
    
    print(f"🎮 游戏状态: {game_state}")
    
    # 测试决策
    try:
        action, amount = bot.decide_action(game_state)
        print(f"✅ 决策结果: {action.value}, 金额: {amount}")
    except Exception as e:
        print(f"❌ 决策失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bot_decision()