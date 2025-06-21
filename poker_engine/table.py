"""
牌桌管理类
Table management for poker game
"""

import uuid
import time
import random
from typing import List, Dict, Optional, Tuple
from enum import Enum
from .card import Card, Deck
from .player import Player, PlayerStatus, PlayerAction
from .bot import Bot, BotLevel
from .hand_evaluator import HandEvaluator, HandRank


class GameStage(Enum):
    """游戏阶段枚举"""
    WAITING = "waiting"
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    FINISHED = "finished"


class Table:
    """牌桌类"""
    
    def __init__(self, table_id: str, title: str, small_blind: int = 10, 
                 big_blind: int = 20, max_players: int = 9, initial_chips: int = 1000):
        self.id = table_id
        self.title = title
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.max_players = max_players
        self.initial_chips = initial_chips
        
        self.players: List[Player] = []
        self.seats: Dict[int, Optional[Player]] = {i: None for i in range(max_players)}
        
        self.game_stage = GameStage.WAITING
        self.hand_number = 0
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = big_blind
        
        self.dealer_position = 0
        self.current_player_position = 0
        
        self.enable_win_probability = True
        self.enable_card_tracking = True
        
        self.created_at = time.time()
        self.last_activity = time.time()
    
    def add_player(self, player: Player) -> bool:
        """添加玩家到牌桌"""
        if len(self.players) >= self.max_players:
            return False
        
        seat_number = self._find_empty_seat()
        if seat_number is None:
            return False
        
        if player.chips == 0:
            player.chips = self.initial_chips
        
        self.players.append(player)
        self.seats[seat_number] = player
        player.status = PlayerStatus.WAITING
        
        self.last_activity = time.time()
        return True
    
    def remove_player(self, player_id: str) -> Optional[Player]:
        """从牌桌移除玩家"""
        player = self.get_player(player_id)
        if not player:
            return None
        
        # 从座位中移除
        for seat_num, seated_player in self.seats.items():
            if seated_player and seated_player.id == player_id:
                self.seats[seat_num] = None
                break
        
        # 从玩家列表中移除
        self.players = [p for p in self.players if p.id != player_id]
        
        self.last_activity = time.time()
        return player
    
    def _find_empty_seat(self) -> Optional[int]:
        """查找空座位"""
        for seat_num in range(self.max_players):
            if self.seats[seat_num] is None:
                return seat_num
        return None
    
    def start_new_hand(self) -> bool:
        """开始新一手牌"""
        active_players = [p for p in self.players if p.status != PlayerStatus.DISCONNECTED]
        if len(active_players) < 2:
            return False
        
        # 重置游戏状态
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.hand_number += 1
        self.game_stage = GameStage.PRE_FLOP  # 明确设置为PRE_FLOP阶段
        
        self.deck.reset()
        self.deck.shuffle()
        
        for player in active_players:
            # 先重置玩家状态，再发牌
            player.reset_for_new_hand()
            player.status = PlayerStatus.PLAYING
            hole_cards = self.deck.deal_cards(2)
            player.deal_hole_cards(hole_cards)
        
        # 收取盲注
        if len(active_players) >= 2:
            sb_player = active_players[0]
            bb_player = active_players[1]
            
            sb_amount = sb_player.place_bet(self.small_blind)
            bb_amount = bb_player.place_bet(self.big_blind)
            self.pot += sb_amount + bb_amount
            self.current_bet = self.big_blind
            
            # 小盲注玩家需要补齐到大盲注才算完成初始行动
            sb_player.has_acted = False  # 小盲注玩家还需要决定是否跟注
            bb_player.has_acted = False  # 大盲注玩家有最后行动权
        
        self.last_activity = time.time()
        print(f"🎮 新手牌开始: 手牌#{self.hand_number}, 阶段={self.game_stage.value}, 活跃玩家={len(active_players)}")
        return True
    
    def process_player_action(self, player_id: str, action: PlayerAction, amount: int = 0) -> Dict:
        """处理玩家动作"""
        player = self.get_player(player_id)
        if not player:
            return {'success': False, 'message': '玩家不存在'}
        
        # 检查是否轮到该玩家行动
        current_player = self.get_current_player()
        if not current_player or current_player.id != player_id:
            return {'success': False, 'message': '现在不是您的回合'}
        
        actual_amount = 0
        action_description = ""
        
        try:
            if action == PlayerAction.FOLD:
                player.fold()
                action_description = "弃牌"
            elif action == PlayerAction.CHECK:
                if self.current_bet > player.current_bet:
                    return {'success': False, 'message': '当前有下注，无法过牌'}
                player.check()
                action_description = "过牌"
            elif action == PlayerAction.CALL:
                call_amount = self.current_bet - player.current_bet
                if call_amount <= 0:
                    return {'success': False, 'message': '无需跟注'}
                actual_amount = player.call(self.current_bet)
                self.pot += actual_amount
                action_description = f"跟注 ${actual_amount}"
            elif action == PlayerAction.BET:
                if self.current_bet > 0:
                    return {'success': False, 'message': '已有下注，请选择跟注或加注'}
                if amount <= 0:
                    return {'success': False, 'message': '下注金额必须大于0'}
                actual_amount = player.place_bet(amount)
                self.current_bet = player.current_bet
                self.pot += actual_amount
                action_description = f"下注 ${actual_amount}"
            elif action == PlayerAction.RAISE:
                if self.current_bet == 0:
                    return {'success': False, 'message': '没有下注，请选择下注'}
                if amount <= self.current_bet:
                    return {'success': False, 'message': f'加注金额必须大于当前下注 ${self.current_bet}'}
                raise_amount = amount - player.current_bet
                actual_amount = player.place_bet(raise_amount)
                self.current_bet = player.current_bet
                self.pot += actual_amount
                action_description = f"加注到 ${amount}"
            elif action == PlayerAction.ALL_IN:
                if player.chips == 0:
                    return {'success': False, 'message': '没有筹码可以全下'}
                actual_amount = player.place_bet(player.chips)
                self.current_bet = max(self.current_bet, player.current_bet)
                self.pot += actual_amount
                action_description = f"全下 ${actual_amount}"
            else:
                return {'success': False, 'message': '无效的动作'}
            
            # 标记玩家已行动
            player.has_acted = True
            self.last_activity = time.time()
            
            # 检查游戏流程
            flow_result = self.process_game_flow()
            
            return {
                'success': True,
                'action': action.value,
                'amount': actual_amount,
                'description': action_description,
                'hand_complete': flow_result.get('hand_complete', False),
                'stage_changed': flow_result.get('stage_changed', False),
                'winners': flow_result.get('winners', [])
            }
            
        except Exception as e:
            return {'success': False, 'message': f'动作执行失败: {str(e)}'}
    
    def process_bot_actions(self):
        """处理机器人动作 - 持续处理直到轮到人类玩家或游戏结束"""
        from .bot import Bot
        import time
        
        max_iterations = 10  # 防止无限循环
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            
            # 获取当前应该行动的玩家
            current_player = self.get_current_player()
            
            # 如果没有需要行动的玩家，检查游戏流程
            if not current_player:
                print("没有找到需要行动的玩家，检查游戏流程...")
                flow_result = self.process_game_flow()
                if flow_result['hand_complete'] or flow_result['stage_changed']:
                    print(f"游戏流程更新: {flow_result}")
                    break
                else:
                    print("游戏流程无变化，结束机器人处理")
                    break
            
            # 如果轮到人类玩家，停止处理
            if not isinstance(current_player, Bot):
                print(f"轮到人类玩家 {current_player.nickname} 行动，停止机器人处理")
                break
            
            # 处理机器人行动
            player = current_player
            print(f"轮到机器人 {player.nickname} 行动，当前投注: {self.current_bet}, 机器人投注: {player.current_bet}")
            
            # 构建游戏状态
            game_state = {
                'community_cards': self.community_cards,
                'current_bet': self.current_bet,
                'big_blind': self.big_blind,
                'pot_size': self.pot,
                'active_players': len([p for p in self.players if p.status == PlayerStatus.PLAYING]),
                'position': 'middle',  # 简化，可以后续改进位置判断
                'min_raise': self.min_raise
            }
            
            # 机器人决策
            action = player.decide_action(game_state)
            if action:
                action_type, amount = action
                action_desc = self._get_action_description(action_type, amount)
                print(f"🤖 {player.nickname} 决定: {action_desc}")
                
                # 稍微延迟，模拟思考时间（0.5-2秒）
                import random
                think_time = random.uniform(0.5, 2.0)
                time.sleep(think_time)
                
                # 显示机器人手牌（用于调试）
                if len(player.hole_cards) == 2:
                    card1_str = f"{player.hole_cards[0].rank.symbol}{player.hole_cards[0].suit.value}"
                    card2_str = f"{player.hole_cards[1].rank.symbol}{player.hole_cards[1].suit.value}"
                    print(f"🤖 {player.nickname} 手牌: {card1_str} {card2_str}")
                
                # 直接处理机器人动作，不通过process_player_action避免递归
                if action_type == PlayerAction.FOLD:
                    player.fold()
                    print(f"🤖 {player.nickname} 弃牌")
                elif action_type == PlayerAction.CHECK:
                    player.check()
                    print(f"🤖 {player.nickname} 过牌")
                elif action_type == PlayerAction.CALL:
                    call_amount = self.current_bet - player.current_bet
                    actual_amount = player.call(self.current_bet)
                    self.pot += actual_amount
                    print(f"🤖 {player.nickname} 跟注 ${actual_amount} (总投注: ${player.current_bet})")
                elif action_type == PlayerAction.BET:
                    actual_amount = player.place_bet(amount)
                    self.current_bet = player.current_bet
                    self.pot += actual_amount
                    print(f"🤖 {player.nickname} 下注 ${actual_amount} (总投注: ${player.current_bet})")
                elif action_type == PlayerAction.RAISE:
                    actual_amount = player.place_bet(amount - player.current_bet)
                    self.current_bet = player.current_bet
                    self.pot += actual_amount
                    print(f"🤖 {player.nickname} 加注到 ${amount} (总投注: ${player.current_bet})")
                elif action_type == PlayerAction.ALL_IN:
                    actual_amount = player.place_bet(player.chips)
                    self.current_bet = max(self.current_bet, player.current_bet)
                    self.pot += actual_amount
                    print(f"🤖 {player.nickname} 全下 ${actual_amount} (总投注: ${player.current_bet})")
                
                # 标记机器人已行动
                player.has_acted = True
                print(f"机器人 {player.nickname} 已完成行动，更新after_bet状态: {player.current_bet}")
                
                # 检查游戏流程是否需要推进
                flow_result = self.process_game_flow()
                if flow_result['hand_complete']:
                    print(f"手牌结束: {flow_result}")
                    # 返回手牌结束的结果
                    return flow_result
                elif flow_result['stage_changed']:
                    print(f"阶段变化: {flow_result}")
                    # 阶段变化后继续处理机器人
                    continue
                    
            else:
                print(f"机器人 {player.nickname} 无法做出决策，跳过")
                player.has_acted = True  # 标记为已行动避免卡死
        
        print(f"机器人处理完成，共处理 {iterations} 轮")
        
        # 返回最终的游戏流程状态
        final_flow_result = self.process_game_flow()
        return final_flow_result
    
    def add_player_at_position(self, player: Player, position: int) -> bool:
        """在指定位置添加玩家"""
        if position < 0 or position >= self.max_players:
            return False
        
        if self.seats[position] is not None:
            return False
        
        # 如果玩家已在其他位置，先移除
        for seat_num, seated_player in self.seats.items():
            if seated_player and seated_player.id == player.id:
                self.seats[seat_num] = None
                break
        
        # 添加到指定位置
        self.seats[position] = player
        
        # 如果不在玩家列表中，添加进去
        if player not in self.players:
            self.players.append(player)
        
        self.last_activity = time.time()
        return True
    
    def get_player_position(self, player_id: str) -> Optional[int]:
        """获取玩家的座位位置"""
        for position, player in self.seats.items():
            if player and player.id == player_id:
                return position
        return None

    def get_player(self, player_id: str) -> Optional[Player]:
        """获取指定ID的玩家"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def calculate_win_probability(self, player_id: str, simulations: int = 10000) -> Optional[Dict]:
        """计算玩家胜率"""
        if not self.enable_win_probability:
            return None
        
        player = self.get_player(player_id)
        if not player or len(player.hole_cards) != 2:
            return None
        
        wins = 0
        ties = 0
        
        for _ in range(simulations):
            # 简化的蒙特卡洛模拟
            our_hand = HandEvaluator.evaluate_hand(player.hole_cards, self.community_cards)
            
            # 模拟对手牌力
            opponent_stronger = False
            opponent_same = False
            
            # 简化：随机生成对手牌力
            for _ in range(len(self.players) - 1):
                opponent_strength = random.random()
                our_strength = our_hand[0].rank_value / 10.0
                
                if opponent_strength > our_strength:
                    opponent_stronger = True
                    break
                elif abs(opponent_strength - our_strength) < 0.01:
                    opponent_same = True
            
            if not opponent_stronger:
                if opponent_same:
                    ties += 1
                else:
                    wins += 1
        
        win_rate = wins / simulations
        tie_rate = ties / simulations
        lose_rate = 1 - win_rate - tie_rate
        
        return {
            'win': round(win_rate, 3),
            'tie': round(tie_rate, 3),
            'lose': round(lose_rate, 3)
        }
    
    def get_card_tracking_info(self) -> Dict:
        """获取记牌信息"""
        if not self.enable_card_tracking:
            return {}
        
        # 统计已知的牌
        known_cards = []
        known_cards.extend(self.community_cards)
        
        # 统计每种花色和点数的剩余数量
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        remaining_cards = {
            'suits': {suit: 13 for suit in suits},
            'ranks': {rank: 4 for rank in ranks},
            'total_remaining': 52 - len(known_cards)
        }
        
        # 减去已知的牌
        for card in known_cards:
            card_dict = card.to_dict()
            suit = card_dict['suit']
            rank = card_dict['rank']
            
            if suit in remaining_cards['suits']:
                remaining_cards['suits'][suit] -= 1
            if rank in remaining_cards['ranks']:
                remaining_cards['ranks'][rank] -= 1
        
        return {
            'known_cards': [card.to_dict() for card in known_cards],
            'remaining_cards': remaining_cards
        }
    
    def get_current_player(self) -> Optional[Player]:
        """获取当前应该行动的玩家"""
        if self.game_stage == GameStage.WAITING or self.game_stage == GameStage.FINISHED:
            return None
        
        # 只有PLAYING状态的玩家才需要行动
        active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
        if len(active_players) <= 1:
            return None
        
        print(f"寻找当前行动玩家，阶段：{self.game_stage.value}，当前投注：${self.current_bet}")
        
        # 按照简单顺序检查所有还在游戏的玩家
        for i, player in enumerate(self.players):
            print(f"检查位置{i}的玩家 {player.nickname}：状态={player.status.value}, 投注=${player.current_bet}, 已行动={player.has_acted}")
            
            # 只考虑还在游戏中的玩家
            if player.status == PlayerStatus.PLAYING:
                # 检查玩家是否需要行动
                needs_action = (not player.has_acted or 
                              (player.current_bet < self.current_bet and player.chips > 0))
                
                if needs_action:
                    print(f"找到需要行动的玩家：{player.nickname}")
                    return player
        
        print("没有找到需要行动的玩家")
        return None
    
    def get_table_state(self, player_id: Optional[str] = None) -> Dict:
        """获取牌桌状态"""
        current_player = self.get_current_player()
        return {
            'id': self.id,
            'title': self.title,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'max_players': self.max_players,
            'game_stage': self.game_stage.value,
            'hand_number': self.hand_number,
            'community_cards': [card.to_dict() for card in self.community_cards],
            'pot': self.pot,
            'current_bet': self.current_bet,
            'current_player_id': current_player.id if current_player else None,
            'players': [p.to_dict(include_hole_cards=(p.id == player_id)) for p in self.players],
            'can_start': len(self.players) >= 2 and self.game_stage == GameStage.WAITING,
            'created_at': self.created_at,
            'last_activity': self.last_activity
        }
    
    def is_betting_round_complete(self) -> bool:
        """检查当前投注回合是否完成"""
        active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
        
        if len(active_players) <= 1:
            return True
        
        # 检查所有活跃玩家是否都已行动且投注相等
        players_needing_action = []
        
        for player in active_players:
            # 如果玩家还有筹码但投注不相等，或者还未行动，则回合未完成
            if not player.has_acted or (player.current_bet < self.current_bet and player.chips > 0):
                players_needing_action.append(f"{player.nickname}(投注${player.current_bet}, 行动状态:{player.has_acted})")
        
        if players_needing_action:
            print(f"投注回合未完成，还有玩家需要行动: {players_needing_action}")
            return False
        
        print("所有活跃玩家都已完成行动，投注轮结束")
        return True
    
    def advance_to_next_stage(self) -> bool:
        """进入下一个游戏阶段"""
        if self.game_stage == GameStage.PRE_FLOP:
            # 发 flop (3张公共牌)
            new_cards = self.deck.deal_cards(3)
            self.community_cards.extend(new_cards)
            self.game_stage = GameStage.FLOP
            # 显示 flop 牌
            flop_str = " ".join([f"{card.rank.symbol}{card.suit.value}" for card in new_cards])
            print(f"🃏 Flop: {flop_str}")
        elif self.game_stage == GameStage.FLOP:
            # 发 turn (第4张公共牌)
            new_card = self.deck.deal_cards(1)[0]
            self.community_cards.append(new_card)
            self.game_stage = GameStage.TURN
            turn_str = f"{new_card.rank.symbol}{new_card.suit.value}"
            print(f"🃏 Turn: {turn_str}")
        elif self.game_stage == GameStage.TURN:
            # 发 river (第5张公共牌)
            new_card = self.deck.deal_cards(1)[0]
            self.community_cards.append(new_card)
            self.game_stage = GameStage.RIVER
            river_str = f"{new_card.rank.symbol}{new_card.suit.value}"
            print(f"🃏 River: {river_str}")
            
            # 显示完整的公共牌
            community_str = " ".join([f"{card.rank.symbol}{card.suit.value}" for card in self.community_cards])
            print(f"🃏 完整公共牌: {community_str}")
        elif self.game_stage == GameStage.RIVER:
            # 进入摊牌阶段
            self.game_stage = GameStage.SHOWDOWN
            self._determine_winner()
        else:
            return False
        
        # 重置当前投注和玩家下注金额，以及行动状态
        self.current_bet = 0
        for player in self.players:
            if player.status == PlayerStatus.PLAYING:
                player.current_bet = 0
                player.has_acted = False  # 重置行动状态
        
        self.last_activity = time.time()
        return True
    
    def is_hand_complete(self) -> bool:
        """检查本手牌是否结束"""
        active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
        
        # 如果只剩一个活跃玩家，游戏结束
        if len(active_players) <= 1:
            return True
        
        # 如果到了showdown阶段，游戏结束
        if self.game_stage == GameStage.SHOWDOWN:
            return True
        
        return False
    
    def _determine_winner(self) -> Optional[Player]:
        """确定获胜者"""
        active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
        
        if len(active_players) == 1:
            # 只有一个活跃玩家，直接获胜
            winner = active_players[0]
            winner.chips += self.pot
            self.game_stage = GameStage.FINISHED
            print(f"玩家 {winner.nickname} 获胜，赢得底池 ${self.pot}")
            return winner
        
        if len(active_players) > 1 and self.game_stage == GameStage.SHOWDOWN:
            # 摊牌阶段 - 显示所有玩家手牌
            print("=" * 60)
            print("🃏 摊牌阶段 - 所有玩家手牌:")
            
            # 显示公共牌
            community_str = " ".join([f"{card.rank.symbol}{card.suit.value}" for card in self.community_cards])
            print(f"🎴 公共牌: {community_str}")
            print("-" * 40)
            
            # 比较手牌强度
            from .hand_evaluator import HandEvaluator
            
            best_hand = None
            winner = None
            player_hands = []
            
            for player in active_players:
                if len(player.hole_cards) == 2:
                    card1_str = f"{player.hole_cards[0].rank.symbol}{player.hole_cards[0].suit.value}"
                    card2_str = f"{player.hole_cards[1].rank.symbol}{player.hole_cards[1].suit.value}"
                    
                    hand_rank, best_cards = HandEvaluator.evaluate_hand(player.hole_cards, self.community_cards)
                    player_type = "🤖" if player.is_bot else "👤"
                    
                    print(f"{player_type} {player.nickname}: {card1_str} {card2_str} -> {hand_rank.value[1]}")
                    
                    player_hands.append({
                        'player': player,
                        'hand_rank': hand_rank,
                        'hand_name': hand_rank.value[1]
                    })
                    
                    if best_hand is None or hand_rank.rank_value > best_hand.rank_value:
                        best_hand = hand_rank
                        winner = player
            
            print("-" * 40)
            if winner:
                winner.chips += self.pot
                self.game_stage = GameStage.FINISHED
                player_type = "🤖" if winner.is_bot else "👤"
                print(f"🏆 {player_type} {winner.nickname} 获胜！手牌：{best_hand.value[1]}，赢得底池 ${self.pot}")
                print("=" * 60)
                return winner
        
        return None
    
    def process_game_flow(self) -> Dict:
        """处理游戏流程，返回状态更新"""
        result = {
            'stage_changed': False,
            'hand_complete': False,
            'winner': None,
            'message': ''
        }
        
        # 如果游戏已经结束，不再处理
        if self.game_stage == GameStage.FINISHED:
            print(f"游戏已结束，跳过流程处理 (阶段: {self.game_stage.value})")
            return result
        
        active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
        print(f"游戏流程检查: 活跃玩家={len(active_players)}, 当前阶段={self.game_stage.value}, 底池=${self.pot}")
        
        # 打印玩家状态
        for player in self.players:
            print(f"  玩家 {player.nickname}: 状态={player.status.value}, 当前投注=${player.current_bet}, 筹码=${player.chips}")
        
        # 检查投注回合是否完成
        if self.is_betting_round_complete():
            print("投注回合完成！")
            if self.is_hand_complete():
                # 手牌结束
                print("手牌结束，确定获胜者...")
                winner = self._determine_winner()
                result['hand_complete'] = True
                result['winner'] = winner.to_dict() if winner else None
                if winner:
                    result['message'] = f"{winner.nickname} 获胜，赢得 ${self.pot}"
            else:
                # 进入下一阶段
                print(f"进入下一阶段，当前阶段: {self.game_stage.value}")
                if self.advance_to_next_stage():
                    result['stage_changed'] = True
                    result['message'] = f"进入 {self.game_stage.value} 阶段"
                    print(f"成功进入 {self.game_stage.value} 阶段")
                    
                    # 如果进入FINISHED阶段，表示手牌结束
                    if self.game_stage == GameStage.FINISHED:
                        print("🏆 游戏阶段为FINISHED，手牌已结束")
                        result['hand_complete'] = True
                        
                        # 强制查找获胜者
                        winner = None
                        max_chips = 0
                        
                        for player in self.players:
                            if player.chips > max_chips:
                                max_chips = player.chips
                                winner = player
                        
                        # 如果没找到，就选择第一个活跃玩家
                        if not winner:
                            active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
                            if active_players:
                                winner = active_players[0]
                        
                        if winner:
                            result['winner'] = winner.to_dict()
                            result['message'] = f"{winner.nickname} 获胜"
                            print(f"🏆 确定获胜者: {winner.nickname}, 筹码: {winner.chips}")
                        else:
                            print("⚠️ 未找到获胜者，创建默认获胜者")
                            if self.players:
                                winner = self.players[0]
                                result['winner'] = winner.to_dict()
                                result['message'] = f"{winner.nickname} 获胜（默认）"
        else:
            print("投注回合未完成，等待更多玩家行动")
        
        return result

    def _get_action_description(self, action_type: PlayerAction, amount: int) -> str:
        """获取动作的中文描述"""
        if action_type == PlayerAction.FOLD:
            return "弃牌"
        elif action_type == PlayerAction.CHECK:
            return "过牌"
        elif action_type == PlayerAction.CALL:
            return f"跟注 ${amount}"
        elif action_type == PlayerAction.BET:
            return f"下注 ${amount}"
        elif action_type == PlayerAction.RAISE:
            return f"加注到 ${amount}"
        elif action_type == PlayerAction.ALL_IN:
            return f"全下 ${amount}"
        else:
            return f"未知动作: {action_type.value}" 