"""
手牌评估器
Hand evaluator for Texas Hold'em poker
"""

from typing import List, Tuple, Dict
from enum import Enum
from .card import Card, Rank, Suit
from collections import Counter
import itertools


class HandRank(Enum):
    """手牌等级枚举"""
    HIGH_CARD = (1, "高牌")
    PAIR = (2, "一对")
    TWO_PAIR = (3, "两对")
    THREE_OF_A_KIND = (4, "三条")
    STRAIGHT = (5, "顺子")
    FLUSH = (6, "同花")
    FULL_HOUSE = (7, "葫芦")
    FOUR_OF_A_KIND = (8, "四条")
    STRAIGHT_FLUSH = (9, "同花顺")
    ROYAL_FLUSH = (10, "皇家同花顺")

    def __init__(self, rank_value, rank_name):
        self.rank_value = rank_value
        self.rank_name = rank_name


class HandEvaluator:
    """手牌评估器"""
    
    @staticmethod
    def evaluate_hand(hole_cards: List[Card], community_cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """
        评估最佳五张牌组合
        
        Args:
            hole_cards: 底牌（2张）
            community_cards: 公共牌（最多5张）
            
        Returns:
            Tuple[HandRank, List[int]]: (牌型等级, 决定胜负的关键牌值列表)
        """
        all_cards = hole_cards + community_cards
        
        if len(all_cards) < 5:
            # 如果总牌数少于5张，按现有牌评估
            return HandEvaluator._evaluate_cards(all_cards)
        
        # 从7张牌中选择最好的5张牌组合
        best_rank = HandRank.HIGH_CARD
        best_kickers = []
        
        for five_cards in itertools.combinations(all_cards, 5):
            rank, kickers = HandEvaluator._evaluate_cards(list(five_cards))
            if (rank.rank_value > best_rank.rank_value or
                (rank.rank_value == best_rank.rank_value and kickers > best_kickers)):
                best_rank = rank
                best_kickers = kickers
                
        return best_rank, best_kickers
    
    @staticmethod
    def _evaluate_cards(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """
        评估具体的牌组合
        
        Args:
            cards: 要评估的牌列表
            
        Returns:
            Tuple[HandRank, List[int]]: (牌型等级, 决定胜负的关键牌值列表)
        """
        if len(cards) == 0:
            return HandRank.HIGH_CARD, []
            
        # 按点数分组
        ranks = [card.rank.numeric_value for card in cards]
        suits = [card.suit for card in cards]
        
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        # 排序点数（从大到小）
        sorted_ranks = sorted(ranks, reverse=True)
        unique_ranks = sorted(set(ranks), reverse=True)
        
        # 检查是否为同花
        is_flush = len(suit_counts) == 1 and len(cards) == 5
        
        # 检查是否为顺子
        is_straight, straight_high = HandEvaluator._is_straight(unique_ranks)
        
        # 按出现次数分组
        pairs = []
        three_of_kinds = []
        four_of_kinds = []
        
        for rank, count in rank_counts.items():
            if count == 2:
                pairs.append(rank)
            elif count == 3:
                three_of_kinds.append(rank)
            elif count == 4:
                four_of_kinds.append(rank)
        
        # 排序
        pairs.sort(reverse=True)
        three_of_kinds.sort(reverse=True)
        four_of_kinds.sort(reverse=True)
        
        # 判断牌型
        if is_straight and is_flush:
            if straight_high == 14:  # A高顺子
                return HandRank.ROYAL_FLUSH, [14]
            else:
                return HandRank.STRAIGHT_FLUSH, [straight_high]
        
        if four_of_kinds:
            kicker = [r for r in unique_ranks if r not in four_of_kinds][0] if len(unique_ranks) > 1 else 0
            return HandRank.FOUR_OF_A_KIND, [four_of_kinds[0], kicker]
        
        if three_of_kinds and pairs:
            return HandRank.FULL_HOUSE, [three_of_kinds[0], pairs[0]]
        
        if is_flush:
            return HandRank.FLUSH, sorted_ranks[:5]
        
        if is_straight:
            return HandRank.STRAIGHT, [straight_high]
        
        if three_of_kinds:
            kickers = [r for r in unique_ranks if r not in three_of_kinds][:2]
            return HandRank.THREE_OF_A_KIND, [three_of_kinds[0]] + sorted(kickers, reverse=True)
        
        if len(pairs) >= 2:
            kickers = [r for r in unique_ranks if r not in pairs][:1]
            return HandRank.TWO_PAIR, sorted(pairs, reverse=True)[:2] + sorted(kickers, reverse=True)
        
        if len(pairs) == 1:
            kickers = [r for r in unique_ranks if r not in pairs][:3]
            return HandRank.PAIR, [pairs[0]] + sorted(kickers, reverse=True)
        
        # 高牌
        return HandRank.HIGH_CARD, sorted_ranks[:5]
    
    @staticmethod
    def _is_straight(ranks: List[int]) -> Tuple[bool, int]:
        """
        检查是否为顺子
        
        Args:
            ranks: 排序后的点数列表
            
        Returns:
            Tuple[bool, int]: (是否为顺子, 最高牌)
        """
        if len(ranks) < 5:
            return False, 0
            
        ranks = sorted(set(ranks), reverse=True)
        
        # 检查正常顺子
        for i in range(len(ranks) - 4):
            if ranks[i] - ranks[i + 4] == 4:
                return True, ranks[i]
        
        # 检查A-2-3-4-5顺子
        if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
            return True, 5
        
        return False, 0
    
    @staticmethod
    def compare_hands(hand1: Tuple[HandRank, List[int]], 
                     hand2: Tuple[HandRank, List[int]]) -> int:
        """
        比较两手牌的大小
        
        Args:
            hand1: 第一手牌 (牌型, 关键牌值)
            hand2: 第二手牌 (牌型, 关键牌值)
            
        Returns:
            int: 1表示hand1获胜, -1表示hand2获胜, 0表示平局
        """
        rank1, kickers1 = hand1
        rank2, kickers2 = hand2
        
        # 首先比较牌型等级
        if rank1.rank_value > rank2.rank_value:
            return 1
        elif rank1.rank_value < rank2.rank_value:
            return -1
        
        # 牌型相同，比较关键牌
        for k1, k2 in zip(kickers1, kickers2):
            if k1 > k2:
                return 1
            elif k1 < k2:
                return -1
        
        # 完全相同
        return 0
    
    @staticmethod
    def hand_to_string(hand: Tuple[HandRank, List[int]]) -> str:
        """
        将手牌转换为字符串描述
        
        Args:
            hand: 手牌 (牌型, 关键牌值)
            
        Returns:
            str: 手牌描述字符串
        """
        rank, kickers = hand
        
        if rank == HandRank.ROYAL_FLUSH:
            return "皇家同花顺"
        elif rank == HandRank.STRAIGHT_FLUSH:
            return f"{HandEvaluator._rank_to_string(kickers[0])}高同花顺"
        elif rank == HandRank.FOUR_OF_A_KIND:
            return f"四条{HandEvaluator._rank_to_string(kickers[0])}"
        elif rank == HandRank.FULL_HOUSE:
            return f"{HandEvaluator._rank_to_string(kickers[0])}满{HandEvaluator._rank_to_string(kickers[1])}"
        elif rank == HandRank.FLUSH:
            return f"{HandEvaluator._rank_to_string(kickers[0])}高同花"
        elif rank == HandRank.STRAIGHT:
            return f"{HandEvaluator._rank_to_string(kickers[0])}高顺子"
        elif rank == HandRank.THREE_OF_A_KIND:
            return f"三条{HandEvaluator._rank_to_string(kickers[0])}"
        elif rank == HandRank.TWO_PAIR:
            return f"{HandEvaluator._rank_to_string(kickers[0])}和{HandEvaluator._rank_to_string(kickers[1])}两对"
        elif rank == HandRank.PAIR:
            return f"一对{HandEvaluator._rank_to_string(kickers[0])}"
        else:
            return f"{HandEvaluator._rank_to_string(kickers[0])}高牌"
    
    @staticmethod
    def _rank_to_string(rank_value: int) -> str:
        """将点数值转换为字符串"""
        rank_names = {
            2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
            10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"
        }
        return rank_names.get(rank_value, str(rank_value))
    
    @staticmethod
    def calculate_outs(hole_cards: List[Card], community_cards: List[Card], 
                      target_hands: List[HandRank] = None) -> Dict[str, int]:
        """
        计算剩余的outs（改善手牌的牌）
        
        Args:
            hole_cards: 底牌
            community_cards: 公共牌
            target_hands: 目标牌型列表（如果为None则计算所有可能的改善）
            
        Returns:
            Dict[str, int]: 各种改善的outs数量
        """
        # 简化版本的outs计算
        all_cards = hole_cards + community_cards
        seen_cards = set((card.suit, card.rank) for card in all_cards)
        
        # 创建剩余牌组
        remaining_cards = []
        for suit in Suit:
            for rank in Rank:
                if (suit, rank) not in seen_cards:
                    remaining_cards.append(Card(suit, rank))
        
        current_hand = HandEvaluator.evaluate_hand(hole_cards, community_cards)
        
        outs = {
            "pair": 0,
            "two_pair": 0,
            "three_of_a_kind": 0,
            "straight": 0,
            "flush": 0,
            "full_house": 0,
            "four_of_a_kind": 0,
            "straight_flush": 0
        }
        
        # 检查每张剩余的牌
        for card in remaining_cards:
            new_community = community_cards + [card]
            new_hand = HandEvaluator.evaluate_hand(hole_cards, new_community)
            
            if new_hand[0].rank_value > current_hand[0].rank_value:
                # 手牌得到改善
                if new_hand[0] == HandRank.PAIR:
                    outs["pair"] += 1
                elif new_hand[0] == HandRank.TWO_PAIR:
                    outs["two_pair"] += 1
                elif new_hand[0] == HandRank.THREE_OF_A_KIND:
                    outs["three_of_a_kind"] += 1
                elif new_hand[0] == HandRank.STRAIGHT:
                    outs["straight"] += 1
                elif new_hand[0] == HandRank.FLUSH:
                    outs["flush"] += 1
                elif new_hand[0] == HandRank.FULL_HOUSE:
                    outs["full_house"] += 1
                elif new_hand[0] == HandRank.FOUR_OF_A_KIND:
                    outs["four_of_a_kind"] += 1
                elif new_hand[0] == HandRank.STRAIGHT_FLUSH:
                    outs["straight_flush"] += 1
        
        return outs 