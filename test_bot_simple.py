#!/usr/bin/env python3
"""
简单的机器人测试
"""

from poker_engine.bot import Bot, BotLevel
from poker_engine.card import Card, Rank, Suit, Deck
from poker_engine.hand_evaluator import HandEvaluator

def test_bot_decision():
    """测试机器人决策"""
    print("🧪 测试机器人决策...")
    
    # 创建机器人
    bot = Bot("test_bot", "测试机器人", 1000, BotLevel.BEGINNER)
    
    # 发牌
    deck = Deck()
    deck.shuffle()
    hole_cards = deck.deal_cards(2)
    bot.deal_hole_cards(hole_cards)
    
    print(f"机器人手牌: {hole_cards[0].rank.symbol}{hole_cards[0].suit.value} {hole_cards[1].rank.symbol}{hole_cards[1].suit.value}")
    
    # 测试翻前评估
    print("测试翻前手牌评估...")
    try:
        preflop_strength = bot._evaluate_preflop_hand()
        print(f"翻前强度: {preflop_strength}")
    except Exception as e:
        print(f"翻前评估错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试翻后评估
    print("测试翻后手牌评估...")
    community_cards = deck.deal_cards(3)
    print(f"公共牌: {[f'{c.rank.symbol}{c.suit.value}' for c in community_cards]}")
    
    try:
        hand_rank, best_hand = HandEvaluator.evaluate_hand(hole_cards, community_cards)
        print(f"手牌等级: {hand_rank.name}")
    except Exception as e:
        print(f"翻后评估错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试机器人决策
    print("测试机器人决策...")
    game_state = {
        'community_cards': community_cards,
        'current_bet': 20,
        'big_blind': 20,
        'pot_size': 50,
        'active_players': 3,
        'position': 'middle',
        'min_raise': 40
    }
    
    try:
        action, amount = bot.decide_action(game_state)
        print(f"机器人决策: {action.value} ${amount}")
    except Exception as e:
        print(f"决策错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bot_decision() 