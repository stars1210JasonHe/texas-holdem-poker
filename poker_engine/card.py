"""
扑克牌和牌堆类
Card and Deck classes for poker game
"""

import random
from typing import List, Optional
from enum import Enum


class Suit(Enum):
    """花色枚举"""
    HEARTS = "♥"    # 红桃
    DIAMONDS = "♦"  # 方块
    CLUBS = "♣"     # 梅花
    SPADES = "♠"    # 黑桃


class Rank(Enum):
    """点数枚举"""
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "10")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")

    def __init__(self, numeric_value, symbol):
        self.numeric_value = numeric_value
        self.symbol = symbol


class Card:
    """扑克牌类"""
    
    def __init__(self, suit: Suit, rank: Rank):
        """
        初始化扑克牌
        
        Args:
            suit: 花色
            rank: 点数
        """
        self.suit = suit
        self.rank = rank
    
    def __str__(self) -> str:
        """返回牌的字符串表示"""
        return f"{self.rank.symbol}{self.suit.value}"
    
    def __repr__(self) -> str:
        """返回牌的详细表示"""
        return f"Card({self.suit.name}, {self.rank.name})"
    
    def __eq__(self, other) -> bool:
        """比较两张牌是否相等"""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self) -> int:
        """计算牌的哈希值"""
        return hash((self.suit, self.rank))
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'suit': self.suit.value,
            'rank': self.rank.symbol,
            'value': self.rank.numeric_value
        }


class Deck:
    """牌堆类"""
    
    def __init__(self):
        """初始化一副完整的扑克牌（52张）"""
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """重置牌堆，生成完整的52张牌"""
        self.cards = []
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))
    
    def shuffle(self):
        """使用Fisher-Yates算法洗牌"""
        for i in range(len(self.cards) - 1, 0, -1):
            j = random.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]
    
    def deal_card(self) -> Optional[Card]:
        """
        发一张牌
        
        Returns:
            Card: 发出的牌，如果牌堆为空则返回None
        """
        if not self.cards:
            return None
        return self.cards.pop()
    
    def deal_cards(self, count: int) -> List[Card]:
        """
        发多张牌
        
        Args:
            count: 要发的牌数
            
        Returns:
            List[Card]: 发出的牌列表
        """
        cards = []
        for _ in range(count):
            card = self.deal_card()
            if card is None:
                break
            cards.append(card)
        return cards
    
    def remaining_count(self) -> int:
        """返回剩余牌数"""
        return len(self.cards)
    
    def peek_top(self, count: int = 1) -> List[Card]:
        """
        查看顶部几张牌而不发出
        
        Args:
            count: 要查看的牌数
            
        Returns:
            List[Card]: 顶部的牌列表
        """
        return self.cards[-count:] if count <= len(self.cards) else self.cards[:]
    
    def __len__(self) -> int:
        """返回牌堆中的牌数"""
        return len(self.cards)
    
    def __bool__(self) -> bool:
        """检查牌堆是否为空"""
        return len(self.cards) > 0 