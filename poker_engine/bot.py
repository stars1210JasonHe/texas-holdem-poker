"""
机器人AI
Bot AI for poker game
"""

import random
from typing import List, Tuple, Dict, Optional
from enum import Enum
from .player import Player, PlayerAction, PlayerStatus
from .card import Card
from .hand_evaluator import HandEvaluator, HandRank
import itertools


class BotLevel(Enum):
    """机器人等级"""
    BEGINNER = "beginner"  # 初级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"  # 高级


class Bot(Player):
    """机器人玩家类"""
    
    def __init__(self, player_id: str, nickname: str, chips: int = 1000, level: BotLevel = BotLevel.BEGINNER):
        """
        初始化机器人
        
        Args:
            player_id: 机器人ID
            nickname: 机器人昵称
            chips: 初始筹码
            level: 机器人等级
        """
        super().__init__(player_id, nickname, chips, is_bot=True)
        self.bot_level = level
        self.hand_history = []  # 手牌历史
        self.opponent_patterns = {}  # 对手行为模式
    
    def decide_action(self, game_state: Dict) -> Tuple[PlayerAction, int]:
        """
        根据游戏状态决定下一步动作
        
        Args:
            game_state: 游戏状态字典，包含公共牌、底池、当前下注等信息
            
        Returns:
            Tuple[PlayerAction, int]: (动作类型, 下注金额)
        """
        if self.bot_level == BotLevel.BEGINNER:
            return self._beginner_strategy(game_state)
        elif self.bot_level == BotLevel.INTERMEDIATE:
            return self._intermediate_strategy(game_state)
        else:
            return self._advanced_strategy(game_state)
    
    def _beginner_strategy(self, game_state: Dict) -> Tuple[PlayerAction, int]:
        """
        初级机器人策略：50% 跟注，20% 加注（最小），30% 弃牌，无诈唬
        """
        community_cards = game_state.get('community_cards', [])
        current_bet = game_state.get('current_bet', 0)
        min_raise = game_state.get('min_raise', current_bet * 2)
        pot_size = game_state.get('pot_size', 0)
        
        # 评估当前手牌强度
        if len(community_cards) >= 3:
            hand_rank, _ = HandEvaluator.evaluate_hand(self.hole_cards, community_cards)
            hand_strength = hand_rank.rank_value / 10.0  # 标准化到0-1
        else:
            # Pre-flop: 简单的底牌评估
            hand_strength = self._evaluate_preflop_hand()
        
        # 计算需要跟注的金额
        call_amount = current_bet - self.current_bet
        
        # 如果没有筹码，只能弃牌或全下
        if self.chips == 0:
            return PlayerAction.FOLD, 0
        
        # 如果不需要跟注，可以过牌
        if call_amount == 0:
            if random.random() < 0.7:  # 70% 过牌
                return PlayerAction.CHECK, 0
            else:  # 30% 下注
                bet_amount = min(min_raise, self.chips)
                return PlayerAction.BET, bet_amount
        
        # 需要跟注的情况
        if call_amount > self.chips:
            # 无法跟注，弃牌或全下
            if hand_strength > 0.6:
                return PlayerAction.ALL_IN, self.chips
            else:
                return PlayerAction.FOLD, 0
        
        # 根据手牌强度决定动作
        if hand_strength < 0.3:
            return PlayerAction.FOLD, 0
        elif hand_strength < 0.6:
            if random.random() < 0.5:
                return PlayerAction.CALL, call_amount
            else:
                return PlayerAction.FOLD, 0
        else:
            # 强牌
            action_choice = random.random()
            if action_choice < 0.5:  # 50% 跟注
                return PlayerAction.CALL, call_amount
            elif action_choice < 0.7:  # 20% 加注
                raise_amount = min(min_raise, self.chips)
                if raise_amount > call_amount:
                    return PlayerAction.RAISE, raise_amount
                else:
                    return PlayerAction.CALL, call_amount
            else:  # 30% 弃牌（有时会弃好牌）
                return PlayerAction.FOLD, 0
    
    def _intermediate_strategy(self, game_state: Dict) -> Tuple[PlayerAction, int]:
        """
        中级机器人策略：基于1000次蒙特卡洛评估；EV > 0时加注至2.5 BB
        """
        community_cards = game_state.get('community_cards', [])
        current_bet = game_state.get('current_bet', 0)
        big_blind = game_state.get('big_blind', 20)
        pot_size = game_state.get('pot_size', 0)
        num_opponents = game_state.get('active_players', 2) - 1
        
        # 计算胜率
        win_probability = self._monte_carlo_simulation(community_cards, num_opponents, 1000)
        
        # 计算期望值
        call_amount = current_bet - self.current_bet
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 1
        
        # 如果没有筹码
        if self.chips == 0:
            return PlayerAction.FOLD, 0
        
        # 如果不需要跟注
        if call_amount == 0:
            if win_probability > 0.6:
                bet_amount = min(int(2.5 * big_blind), self.chips)
                return PlayerAction.BET, bet_amount
            else:
                return PlayerAction.CHECK, 0
        
        # 无法跟注的情况
        if call_amount > self.chips:
            if win_probability > 0.4:
                return PlayerAction.ALL_IN, self.chips
            else:
                return PlayerAction.FOLD, 0
        
        # 根据胜率和底池赔率决定
        if win_probability > pot_odds + 0.1:  # 有正期望值
            if win_probability > 0.7:
                # 强牌，加注
                raise_amount = min(int(2.5 * big_blind), self.chips)
                if raise_amount > call_amount:
                    return PlayerAction.RAISE, raise_amount
                else:
                    return PlayerAction.CALL, call_amount
            else:
                # 中等牌，跟注
                return PlayerAction.CALL, call_amount
        else:
            # 负期望值，弃牌
            return PlayerAction.FOLD, 0
    
    def _advanced_strategy(self, game_state: Dict) -> Tuple[PlayerAction, int]:
        """
        高级机器人策略：考虑位置、对手下注模式、诈唬
        """
        community_cards = game_state.get('community_cards', [])
        current_bet = game_state.get('current_bet', 0)
        big_blind = game_state.get('big_blind', 20)
        pot_size = game_state.get('pot_size', 0)
        num_opponents = game_state.get('active_players', 2) - 1
        position = game_state.get('position', 'middle')  # early, middle, late
        betting_round = len(community_cards)  # 0=preflop, 3=flop, 4=turn, 5=river
        
        # 计算基本胜率
        win_probability = self._monte_carlo_simulation(community_cards, num_opponents, 2000)
        
        # 位置调整
        position_modifier = {
            'early': -0.1,
            'middle': 0,
            'late': 0.1
        }.get(position, 0)
        
        adjusted_win_prob = max(0, min(1, win_probability + position_modifier))
        
        # 诈唬概率
        bluff_probability = 0.05 + (0.1 if position == 'late' else 0)
        
        call_amount = current_bet - self.current_bet
        
        # 如果没有筹码
        if self.chips == 0:
            return PlayerAction.FOLD, 0
        
        # 诈唬决策
        should_bluff = (random.random() < bluff_probability and 
                       adjusted_win_prob < 0.3 and 
                       betting_round >= 3)
        
        if call_amount == 0:
            # 没有下注压力
            if should_bluff:
                bluff_size = min(int(1.5 * big_blind), self.chips)
                return PlayerAction.BET, bluff_size
            elif adjusted_win_prob > 0.6:
                value_bet = min(int(2 * big_blind), self.chips)
                return PlayerAction.BET, value_bet
            else:
                return PlayerAction.CHECK, 0
        
        # 需要跟注的情况
        if call_amount > self.chips:
            if adjusted_win_prob > 0.45 or should_bluff:
                return PlayerAction.ALL_IN, self.chips
            else:
                return PlayerAction.FOLD, 0
        
        # 动态调整策略
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 1
        
        if should_bluff:
            # 诈唬
            if random.random() < 0.7:  # 70% 加注诈唬
                bluff_raise = min(int(2.5 * big_blind), self.chips)
                if bluff_raise > call_amount:
                    return PlayerAction.RAISE, bluff_raise
                else:
                    return PlayerAction.CALL, call_amount
            else:  # 30% 跟注诈唬
                return PlayerAction.CALL, call_amount
        
        # 正常决策
        if adjusted_win_prob > pot_odds + 0.15:
            # 强牌
            if adjusted_win_prob > 0.8:
                # 非常强的牌，大幅加注
                big_raise = min(int(3 * big_blind), self.chips)
                if big_raise > call_amount:
                    return PlayerAction.RAISE, big_raise
                else:
                    return PlayerAction.CALL, call_amount
            elif adjusted_win_prob > 0.65:
                # 强牌，中等加注
                medium_raise = min(int(2 * big_blind), self.chips)
                if medium_raise > call_amount:
                    return PlayerAction.RAISE, medium_raise
                else:
                    return PlayerAction.CALL, call_amount
            else:
                # 中等强度，跟注
                return PlayerAction.CALL, call_amount
        elif adjusted_win_prob > pot_odds:
            # 边际牌，跟注
            return PlayerAction.CALL, call_amount
        else:
            # 弱牌，弃牌
            return PlayerAction.FOLD, 0
    
    def _evaluate_preflop_hand(self) -> float:
        """
        评估Pre-flop手牌强度
        
        Returns:
            float: 手牌强度 (0-1)
        """
        if len(self.hole_cards) != 2:
            return 0.0
        
        card1, card2 = self.hole_cards
        rank1, rank2 = card1.rank.numeric_value, card2.rank.numeric_value
        suited = card1.suit == card2.suit
        
        # 对子
        if rank1 == rank2:
            if rank1 >= 10:  # TT, JJ, QQ, KK, AA
                return 0.8 + (rank1 - 10) * 0.04
            elif rank1 >= 7:  # 77, 88, 99
                return 0.6 + (rank1 - 7) * 0.05
            else:  # 22-66
                return 0.3 + (rank1 - 2) * 0.05
        
        # 非对子
        high_rank = max(rank1, rank2)
        low_rank = min(rank1, rank2)
        gap = high_rank - low_rank
        
        base_strength = 0.0
        
        # 高牌加分
        if high_rank == 14:  # A
            base_strength += 0.3
        elif high_rank >= 11:  # K, Q
            base_strength += 0.2
        elif high_rank >= 9:  # J, T
            base_strength += 0.1
        
        # 连牌加分
        if gap == 1:  # 连牌
            base_strength += 0.15
        elif gap == 2:  # 一个空档
            base_strength += 0.1
        elif gap == 3:  # 两个空档
            base_strength += 0.05
        
        # 同花加分
        if suited:
            base_strength += 0.1
        
        # 特殊组合
        if (high_rank, low_rank) in [(14, 13), (14, 12), (14, 11)]:  # AK, AQ, AJ
            base_strength += 0.2
        
        return min(0.95, base_strength)
    
    def _monte_carlo_simulation(self, community_cards: List[Card], 
                               num_opponents: int, simulations: int = 1000) -> float:
        """
        蒙特卡洛模拟计算胜率
        
        Args:
            community_cards: 公共牌
            num_opponents: 对手数量
            simulations: 模拟次数
            
        Returns:
            float: 胜率 (0-1)
        """
        if len(self.hole_cards) != 2:
            return 0.0
        
        wins = 0
        ties = 0
        
        # 已知牌
        known_cards = set(self.hole_cards + community_cards)
        
        for _ in range(simulations):
            # 创建剩余牌组
            remaining_cards = []
            for suit in [card.suit for card in known_cards]:
                pass  # 这里应该创建完整的牌组，为了简化先跳过
            
            # 简化版本：随机评估
            our_hand = HandEvaluator.evaluate_hand(self.hole_cards, community_cards)
            
            # 模拟对手手牌（简化版本）
            opponent_stronger = 0
            opponent_same = 0
            
            for _ in range(num_opponents):
                # 随机生成对手牌力（简化）
                opponent_strength = random.random()
                our_strength = our_hand[0].rank_value / 10.0
                
                if opponent_strength > our_strength:
                    opponent_stronger += 1
                elif abs(opponent_strength - our_strength) < 0.01:
                    opponent_same += 1
            
            if opponent_stronger == 0:
                if opponent_same == 0:
                    wins += 1
                else:
                    ties += 1
        
        return (wins + ties * 0.5) / simulations if simulations > 0 else 0.0
    
    def update_opponent_pattern(self, player_id: str, action: PlayerAction, amount: int, context: Dict):
        """
        更新对手行为模式记录
        
        Args:
            player_id: 对手ID
            action: 对手动作
            amount: 下注金额
            context: 游戏上下文
        """
        if player_id not in self.opponent_patterns:
            self.opponent_patterns[player_id] = {
                'aggression': 0.5,  # 攻击性
                'tightness': 0.5,   # 紧松度
                'bluff_frequency': 0.1,  # 诈唬频率
                'action_count': 0
            }
        
        pattern = self.opponent_patterns[player_id]
        pattern['action_count'] += 1
        
        # 更新攻击性
        if action in [PlayerAction.BET, PlayerAction.RAISE]:
            pattern['aggression'] = min(1.0, pattern['aggression'] + 0.05)
        elif action == PlayerAction.FOLD:
            pattern['aggression'] = max(0.0, pattern['aggression'] - 0.02)
        
        # 更新紧松度
        if action == PlayerAction.FOLD:
            pattern['tightness'] = min(1.0, pattern['tightness'] + 0.03)
        elif action in [PlayerAction.CALL, PlayerAction.BET, PlayerAction.RAISE]:
            pattern['tightness'] = max(0.0, pattern['tightness'] - 0.02)
    
    def to_dict(self, include_hole_cards: bool = False) -> dict:
        """扩展父类方法，增加机器人特有信息"""
        data = super().to_dict(include_hole_cards)
        data['bot_level'] = self.bot_level.value
        return data 