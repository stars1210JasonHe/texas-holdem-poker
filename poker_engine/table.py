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
                 big_blind: int = 20, max_players: int = 9, initial_chips: int = 1000,
                 game_mode: str = "blinds", ante_percentage: float = 0.02):
        self.id = table_id
        self.title = title
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.max_players = max_players
        self.initial_chips = initial_chips
        
        # 新增游戏模式参数
        self.game_mode = game_mode  # "blinds" 或 "ante"
        self.ante_percentage = ante_percentage  # 按比例下注的百分比 (例如 0.02 = 2%)
        
        self.players: List[Player] = []
        self.seats: Dict[int, Optional[Player]] = {i: None for i in range(max_players)}
        
        self.game_stage = GameStage.WAITING
        self.hand_number = 0
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = big_blind if game_mode == "blinds" else max(1, int(initial_chips * ante_percentage))
        
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
        
        # 轮换庄家位置（每手牌轮换）
        if self.hand_number > 0:  # 第一手牌庄家位置为0，之后每手牌轮换
            self.dealer_position = (self.dealer_position + 1) % len(active_players)
        
        # 重置游戏状态
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.hand_number += 1
        self.game_stage = GameStage.PRE_FLOP  # 明确设置为PRE_FLOP阶段
        
        self.deck.reset()
        self.deck.shuffle()
        
        # 清除所有玩家的庄家标记
        for player in self.players:
            player.is_dealer = False
        
        # 设置当前庄家
        if len(active_players) > 0:
            active_players[self.dealer_position].is_dealer = True
            print(f"🎯 庄家: {active_players[self.dealer_position].nickname} (位置 {self.dealer_position})")
        
        for player in active_players:
            # 先重置玩家状态，再发牌
            player.reset_for_new_hand()
            player.status = PlayerStatus.PLAYING
            hole_cards = self.deck.deal_cards(2)
            player.deal_hole_cards(hole_cards)
        
        # 根据游戏模式收取初始下注
        if self.game_mode == "blinds":
            # 传统大小盲注模式
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
                
                print(f"🎮 大小盲注模式: 小盲${self.small_blind}, 大盲${self.big_blind}")
        
        elif self.game_mode == "ante":
            # 按比例下注模式 - 所有人都下注相同比例
            ante_amount = int(self.initial_chips * self.ante_percentage)
            if ante_amount < 1:
                ante_amount = 1  # 最少1个筹码
            
            total_ante = 0
            for player in active_players:
                actual_ante = player.place_bet(ante_amount)
                total_ante += actual_ante
            
            self.pot = total_ante
            # 重要：ante模式下，初始current_bet应该为0，让玩家可以自由选择过牌或下注
            self.current_bet = 0
            
            # 所有玩家已经完成初始ante下注，现在可以选择行动（过牌或下注）
            for player in active_players:
                player.has_acted = False  # 允许玩家在ante基础上继续行动
                # 重要：重置玩家的current_bet，因为ante不算作"下注"，而是入场费
                player.current_bet = 0
            
            print(f"🎮 按比例下注模式: 每人缴纳ante ${ante_amount} (筹码的{self.ante_percentage*100:.1f}%), 总底池${total_ante}, 现在开始下注轮（current_bet=${self.current_bet})")
        
        self.last_activity = time.time()
        print(f"🎮 新手牌开始: 手牌#{self.hand_number}, 阶段={self.game_stage.value}, 活跃玩家={len(active_players)}, 模式={self.game_mode}")
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
                    
                # 下注逻辑（ante和blinds模式都一样）
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
            
            result = {
                'success': True,
                'action': action.value,
                'amount': actual_amount,
                'description': action_description,
                'hand_complete': flow_result.get('hand_complete', False),
                'stage_changed': flow_result.get('stage_changed', False),
                'winners': flow_result.get('winners', [])
            }
            
            # 如果手牌结束，传递完整的获胜者和摊牌信息
            if flow_result.get('hand_complete'):
                result['winner'] = flow_result.get('winner')
                result['showdown_info'] = flow_result.get('showdown_info', {})
                print(f"🎯 玩家动作传递摊牌信息: winner={result['winner']}, showdown_info存在={bool(result['showdown_info'])}")
            
            return result
            
        except Exception as e:
            return {'success': False, 'message': f'动作执行失败: {str(e)}'}
    
    def process_bot_actions(self):
        """处理机器人动作 - 持续处理直到轮到人类玩家或游戏结束"""
        from .bot import Bot
        import time
        
        max_iterations = 20  # 增加最大迭代次数
        iterations = 0
        consecutive_no_action = 0  # 连续无动作计数
        
        while iterations < max_iterations:
            iterations += 1
            had_action_this_round = False
            
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
                    consecutive_no_action += 1
                    if consecutive_no_action >= 3:  # 连续3次无动作就退出
                        print("连续多次无动作，强制结束处理")
                        break
                    continue
            
            # 如果轮到人类玩家，停止处理
            if not isinstance(current_player, Bot):
                print(f"轮到人类玩家 {current_player.nickname} 行动，停止机器人处理")
                break
                
            # 重置连续无动作计数
            consecutive_no_action = 0
            
            # 处理机器人行动
            player = current_player
            print(f"🤖 轮到机器人 {player.nickname} 行动，状态: {player.status.value}, 当前投注: {self.current_bet}, 机器人投注: {player.current_bet}")
            
            # 检查机器人状态是否合法
            if player.status not in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]:
                print(f"🤖 机器人 {player.nickname} 状态不合法: {player.status.value}，跳过")
                player.has_acted = True
                continue
            
            # 检查机器人是否有足够筹码
            if player.chips <= 0 and player.status != PlayerStatus.ALL_IN:
                print(f"🤖 机器人 {player.nickname} 筹码不足，自动全下")
                player.status = PlayerStatus.ALL_IN
                player.has_acted = True
                continue
            
            # 构建游戏状态
            game_state = {
                'community_cards': self.community_cards,
                'current_bet': self.current_bet,
                'big_blind': self.big_blind,
                'pot_size': self.pot,
                'active_players': len([p for p in self.players if p.status == PlayerStatus.PLAYING]),
                'position': 'middle',  # 简化，可以后续改进位置判断
                'min_raise': self.min_raise,
                'all_players': self.players  # 为GOD级别机器人提供所有玩家信息
            }
            
            # 机器人决策 - 添加异常处理
            action = None
            try:
                action = player.decide_action(game_state)
            except Exception as e:
                print(f"❌ 机器人 {player.nickname} 决策出错: {e}")
                
            # 如果机器人无法决策，提供默认行动
            if not action:
                print(f"🤖 机器人 {player.nickname} 无法决策，使用默认策略")
                # 默认策略：如果能过牌就过牌，否则弃牌
                call_amount = self.current_bet - player.current_bet
                if call_amount == 0:
                    action = (PlayerAction.CHECK, 0)
                    print(f"🤖 {player.nickname} 默认行动: 过牌")
                else:
                    action = (PlayerAction.FOLD, 0)
                    print(f"🤖 {player.nickname} 默认行动: 弃牌")
            
            if action:
                action_type, amount = action
                action_desc = self._get_action_description(action_type, amount)
                
                # 根据机器人等级添加思考时间延迟
                from .bot import BotLevel
                thinking_delays = {
                    BotLevel.BEGINNER: 0.0,      # 初级 0秒（立即）
                    BotLevel.INTERMEDIATE: 0.0,  # 中级 0秒（立即）  
                    BotLevel.ADVANCED: 0.0,      # 高级 0秒（立即）
                    BotLevel.GOD: 0.0            # 神级 0秒（立即）
                }
                
                delay = thinking_delays.get(player.bot_level, 0.0)
                if delay > 0:
                    print(f"🤖 {player.nickname} ({player.bot_level.value}) 思考中... ({delay}秒)")
                    time.sleep(delay)
                
                print(f"🤖 {player.nickname} 决定: {action_desc}")
                
                # 显示机器人手牌（用于调试）
                if len(player.hole_cards) == 2:
                    card1_str = f"{player.hole_cards[0].rank.symbol}{player.hole_cards[0].suit.value}"
                    card2_str = f"{player.hole_cards[1].rank.symbol}{player.hole_cards[1].suit.value}"
                    print(f"🤖 {player.nickname} 手牌: {card1_str} {card2_str}")
                
                # 直接处理机器人动作，不通过process_player_action避免递归
                try:
                    if action_type == PlayerAction.FOLD:
                        player.fold()
                        print(f"🤖 {player.nickname} 弃牌")
                    elif action_type == PlayerAction.CHECK:
                        player.check()
                        print(f"🤖 {player.nickname} 过牌")
                    elif action_type == PlayerAction.CALL:
                        call_amount = self.current_bet - player.current_bet
                        if call_amount > 0:
                            actual_amount = player.call(self.current_bet)
                            self.pot += actual_amount
                            print(f"🤖 {player.nickname} 跟注 ${actual_amount} (总投注: ${player.current_bet})")
                        else:
                            # 无需跟注，相当于过牌
                            player.check()
                            print(f"🤖 {player.nickname} 过牌（无需跟注）")
                    elif action_type == PlayerAction.BET:
                        if amount > 0 and amount <= player.chips:
                            actual_amount = player.place_bet(amount)
                            self.current_bet = player.current_bet
                            self.pot += actual_amount
                            print(f"🤖 {player.nickname} 下注 ${actual_amount} (总投注: ${player.current_bet})")
                        else:
                            # 无效下注，改为过牌
                            player.check()
                            print(f"🤖 {player.nickname} 下注无效，改为过牌")
                    elif action_type == PlayerAction.RAISE:
                        raise_amount = amount - player.current_bet
                        if raise_amount > 0 and raise_amount <= player.chips:
                            actual_amount = player.place_bet(raise_amount)
                            self.current_bet = player.current_bet
                            self.pot += actual_amount
                            print(f"🤖 {player.nickname} 加注到 ${amount} (总投注: ${player.current_bet})")
                        else:
                            # 无效加注，改为跟注
                            call_amount = self.current_bet - player.current_bet
                            if call_amount > 0 and call_amount <= player.chips:
                                actual_amount = player.call(self.current_bet)
                                self.pot += actual_amount
                                print(f"🤖 {player.nickname} 加注无效，改为跟注 ${actual_amount}")
                            else:
                                player.check()
                                print(f"🤖 {player.nickname} 加注无效，改为过牌")
                    elif action_type == PlayerAction.ALL_IN:
                        if player.chips > 0:
                            actual_amount = player.place_bet(player.chips)
                            self.current_bet = max(self.current_bet, player.current_bet)
                            self.pot += actual_amount
                            print(f"🤖 {player.nickname} 全下 ${actual_amount} (总投注: ${player.current_bet})")
                        else:
                            player.check()
                            print(f"🤖 {player.nickname} 无筹码全下，改为过牌")
                    
                    # 标记机器人已行动
                    player.has_acted = True
                    had_action_this_round = True
                    print(f"✅ 机器人 {player.nickname} 已完成行动")
                    
                except Exception as e:
                    print(f"❌ 机器人 {player.nickname} 执行动作时出错: {e}")
                    # 出错时强制弃牌
                    player.fold()
                    player.has_acted = True
                    had_action_this_round = True
                    print(f"🤖 {player.nickname} 因错误强制弃牌")
                
                # 检查游戏流程是否需要推进
                flow_result = self.process_game_flow()
                if flow_result['hand_complete']:
                    print(f"🏆 机器人动作导致手牌结束: {flow_result}")
                    # 返回手牌结束的结果，包含完整的摊牌信息
                    return flow_result
                elif flow_result['stage_changed']:
                    print(f"阶段变化: {flow_result}")
                    # 阶段变化后继续处理机器人
                    continue
                    
            else:
                print(f"❌ 机器人 {player.nickname} 彻底无法决策，强制弃牌")
                player.fold()
                player.has_acted = True
                had_action_this_round = True
            
            # 如果本轮没有任何动作，增加无动作计数
            if not had_action_this_round:
                consecutive_no_action += 1
                print(f"⚠️ 本轮无动作 ({consecutive_no_action}/3)")
                if consecutive_no_action >= 3:
                    print("连续3轮无动作，强制结束处理")
                    break
        
        print(f"🏁 机器人处理完成，共处理 {iterations} 轮")
        
        # 检查是否有遗留的机器人未完成行动
        remaining_bots = []
        for player in self.players:
            if (isinstance(player, Bot) and 
                player.status == PlayerStatus.PLAYING and 
                not player.has_acted):
                remaining_bots.append(player.nickname)
        
        if remaining_bots:
            print(f"⚠️ 发现未完成行动的机器人: {remaining_bots}")
            # 让这些机器人正常决策，而不是强制弃牌
            for player in self.players:
                if (isinstance(player, Bot) and 
                    player.status == PlayerStatus.PLAYING and 
                    not player.has_acted):
                    print(f"🔧 补充处理机器人 {player.nickname}")
                    
                    # 构建游戏状态，让机器人正常决策
                    game_state = {
                        'community_cards': self.community_cards,
                        'current_bet': self.current_bet,
                        'big_blind': self.big_blind,
                        'pot_size': self.pot,
                        'active_players': len([p for p in self.players if p.status == PlayerStatus.PLAYING]),
                        'position': 'middle',
                        'min_raise': self.min_raise,
                        'all_players': self.players
                    }
                    
                    # 让机器人正常决策
                    action = None
                    try:
                        action = player.decide_action(game_state)
                        print(f"🤖 {player.nickname} 补充决策: {action}")
                    except Exception as e:
                        print(f"❌ 机器人 {player.nickname} 补充决策出错: {e}")
                    
                    # 如果机器人无法决策，使用更合理的兜底策略
                    if not action:
                        call_amount = self.current_bet - player.current_bet
                        if call_amount <= 0:
                            action = (PlayerAction.CHECK, 0)
                            print(f"🤖 {player.nickname} 兜底策略: 过牌")
                        elif call_amount <= player.chips * 0.1:  # 只有在成本很低时才跟注
                            action = (PlayerAction.CALL, call_amount)
                            print(f"🤖 {player.nickname} 兜底策略: 跟注${call_amount}")
                        else:
                            action = (PlayerAction.FOLD, 0)
                            print(f"🤖 {player.nickname} 兜底策略: 弃牌")
                    
                    # 执行机器人决策
                    if action:
                        action_type, amount = action
                        try:
                            if action_type == PlayerAction.FOLD:
                                player.fold()
                                print(f"🤖 {player.nickname} 弃牌")
                            elif action_type == PlayerAction.CHECK:
                                player.check()
                                print(f"🤖 {player.nickname} 过牌")
                            elif action_type == PlayerAction.CALL:
                                call_amount = self.current_bet - player.current_bet
                                if call_amount > 0:
                                    actual_amount = player.call(self.current_bet)
                                    self.pot += actual_amount
                                    print(f"🤖 {player.nickname} 跟注 ${actual_amount}")
                                else:
                                    player.check()
                                    print(f"🤖 {player.nickname} 过牌（无需跟注）")
                            elif action_type == PlayerAction.BET:
                                if amount > 0 and amount <= player.chips:
                                    actual_amount = player.place_bet(amount)
                                    self.current_bet = player.current_bet
                                    self.pot += actual_amount
                                    print(f"🤖 {player.nickname} 下注 ${actual_amount}")
                                else:
                                    player.check()
                                    print(f"🤖 {player.nickname} 下注无效，改为过牌")
                            elif action_type == PlayerAction.RAISE:
                                raise_amount = amount - player.current_bet
                                if raise_amount > 0 and raise_amount <= player.chips:
                                    actual_amount = player.place_bet(raise_amount)
                                    self.current_bet = player.current_bet
                                    self.pot += actual_amount
                                    print(f"🤖 {player.nickname} 加注到 ${amount}")
                                else:
                                    # 尝试跟注
                                    call_amount = self.current_bet - player.current_bet
                                    if call_amount > 0 and call_amount <= player.chips:
                                        actual_amount = player.call(self.current_bet)
                                        self.pot += actual_amount
                                        print(f"🤖 {player.nickname} 加注无效，改为跟注 ${actual_amount}")
                                    else:
                                        player.check()
                                        print(f"🤖 {player.nickname} 加注无效，改为过牌")
                            elif action_type == PlayerAction.ALL_IN:
                                if player.chips > 0:
                                    actual_amount = player.place_bet(player.chips)
                                    self.current_bet = max(self.current_bet, player.current_bet)
                                    self.pot += actual_amount
                                    print(f"🤖 {player.nickname} 全下 ${actual_amount}")
                                else:
                                    player.check()
                                    print(f"🤖 {player.nickname} 无筹码全下，改为过牌")
                        except Exception as e:
                            print(f"❌ 执行机器人动作失败: {e}")
                            player.fold()
                            print(f"🤖 {player.nickname} 因错误弃牌")
                    
                    player.has_acted = True
        
        # 返回最终的游戏流程状态
        final_flow_result = self.process_game_flow()
        print(f"🏁 机器人处理完成，最终流程结果: hand_complete={final_flow_result.get('hand_complete')}, winner={final_flow_result.get('winner')}")
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
        
        # 只有PLAYING状态的玩家才需要行动（排除BROKE观察者）
        active_players = [p for p in self.players if p.status == PlayerStatus.PLAYING]
        if len(active_players) <= 1:
            return None
        
        print(f"寻找当前行动玩家，阶段：{self.game_stage.value}，当前投注：${self.current_bet}")
        
        # 根据游戏模式确定行动顺序
        if self.game_mode == "ante":
            # ante模式：从庄家下一位开始行动（确保公平轮换）
            # 找到当前庄家在active_players中的位置
            dealer_index_in_active = None
            for i, player in enumerate(active_players):
                if player.is_dealer:
                    dealer_index_in_active = i
                    break
            
            if dealer_index_in_active is None:
                print("警告：没有找到庄家，使用第一个玩家作为庄家")
                dealer_index_in_active = 0
                
            # 从庄家下一位开始检查
            start_position = (dealer_index_in_active + 1) % len(active_players)
            
            # 按照庄家后的顺序检查玩家
            for i in range(len(active_players)):
                player_index = (start_position + i) % len(active_players)
                player = active_players[player_index]
                
                print(f"检查位置{player_index}的玩家 {player.nickname}：状态={player.status.value}, 投注=${player.current_bet}, 已行动={player.has_acted}, 筹码=${player.chips}")
                
                if player.chips > 0:
                    # 检查玩家是否需要行动
                    needs_action = (not player.has_acted or 
                                  (player.current_bet < self.current_bet and player.chips > 0))
                    
                    if needs_action:
                        print(f"找到需要行动的玩家：{player.nickname} (庄家后第{i+1}位)")
                        return player
        else:
            # blinds模式：按照原有逻辑（小盲、大盲顺序）
            for i, player in enumerate(self.players):
                print(f"检查位置{i}的玩家 {player.nickname}：状态={player.status.value}, 投注=${player.current_bet}, 已行动={player.has_acted}, 筹码=${player.chips}")
                
                # 只考虑还在游戏中的玩家（排除没有筹码的观察者）
                if player.status == PlayerStatus.PLAYING and player.chips > 0:
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
            'game_mode': self.game_mode,
            'ante_percentage': self.ante_percentage,
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
        # 区分能继续行动的玩家和全下玩家
        playing_players = [p for p in self.players if p.status == PlayerStatus.PLAYING and p.chips > 0]
        all_in_players = [p for p in self.players if p.status == PlayerStatus.ALL_IN]
        
        print(f"投注回合检查: 可行动玩家={len(playing_players)}, 全下玩家={len(all_in_players)}")
        
        # 如果没有可以继续行动的玩家，回合结束
        if len(playing_players) <= 1:
            print("只剩一个或零个可行动玩家，投注回合结束")
            return True
        
        # 检查所有可以行动的玩家是否都已行动且投注相等
        players_needing_action = []
        
        for player in playing_players:
            # 如果玩家还有筹码但投注不相等，或者还未行动，则回合未完成
            if not player.has_acted or (player.current_bet < self.current_bet and player.chips > 0):
                players_needing_action.append(f"{player.nickname}(投注${player.current_bet}, 行动状态:{player.has_acted})")
        
        if players_needing_action:
            print(f"投注回合未完成，还有玩家需要行动: {players_needing_action}")
            return False
        
        print("所有可行动玩家都已完成行动，投注轮结束")
        print(f"  - 可行动玩家投注状况: {[(p.nickname, p.current_bet, p.chips) for p in playing_players]}")
        print(f"  - 全下玩家投注状况: {[(p.nickname, p.current_bet, p.chips) for p in all_in_players]}")
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
            # 注意：不在这里调用_determine_winner，让process_game_flow处理
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
        # 包括全下的玩家在活跃玩家中
        active_players = [p for p in self.players if p.status in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]]
        
        # 如果只剩一个活跃玩家，游戏结束
        if len(active_players) <= 1:
            return True
        
        # 如果到了showdown阶段，游戏结束
        if self.game_stage == GameStage.SHOWDOWN:
            return True
        
        return False
    
    def _determine_winner(self) -> Dict:
        """确定获胜者，返回详细的摊牌信息"""
        # 包括全下的玩家在胜负判定中（ALL_IN 和 PLAYING 状态）
        active_players = [p for p in self.players if p.status in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]]
        
        print(f"🏆 _determine_winner 被调用:")
        print(f"  - 活跃玩家数: {len(active_players)}")
        print(f"  - 游戏阶段: {self.game_stage.value}")
        print(f"  - 公共牌数量: {len(self.community_cards)}")
        
        showdown_info = {
            'winner': None,
            'showdown_players': [],
            'community_cards': [card.to_dict() for card in self.community_cards],
            'pot': self.pot,
            'is_showdown': len(active_players) > 1
        }
        
        if len(active_players) == 1:
            # 只有一个活跃玩家，直接获胜（没有摊牌）
            winner = active_players[0]
            winner.chips += self.pot
            self.game_stage = GameStage.FINISHED
            
            showdown_info['winner'] = winner
            showdown_info['is_showdown'] = False
            showdown_info['win_reason'] = 'others_folded'
            
            # 即使其他人弃牌，也显示获胜者的手牌（如果有的话）
            if len(winner.hole_cards) == 2:
                card1_str = f"{winner.hole_cards[0].rank.symbol}{winner.hole_cards[0].suit.value}"
                card2_str = f"{winner.hole_cards[1].rank.symbol}{winner.hole_cards[1].suit.value}"
                
                # 如果有足够的公共牌，评估手牌
                hand_description = "未知牌型"
                if len(self.community_cards) >= 3:
                    from .hand_evaluator import HandEvaluator
                    hand_rank, best_cards = HandEvaluator.evaluate_hand(winner.hole_cards, self.community_cards)
                    hand_description = HandEvaluator.hand_to_string((hand_rank, best_cards))
                
                # 创建获胜者的摊牌信息
                winner_info = {
                    'player': winner,
                    'player_id': winner.id,
                    'nickname': winner.nickname,
                    'is_bot': winner.is_bot,
                    'hole_cards': [card.to_dict() for card in winner.hole_cards],
                    'hole_cards_str': f"{card1_str} {card2_str}",
                    'hand_description': hand_description,
                    'rank': 1,
                    'result': 'winner',
                    'winnings': self.pot
                }
                
                showdown_info['showdown_players'] = [winner_info]
                
                player_type = "🤖" if winner.is_bot else "👤"
                print(f"{player_type} {winner.nickname} 获胜（其他玩家弃牌），手牌: {card1_str} {card2_str}，赢得底池 ${self.pot}")
            else:
                print(f"玩家 {winner.nickname} 获胜（其他玩家弃牌），赢得底池 ${self.pot}")
            
            return showdown_info
        
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
            
            player_hands = []
            
            for player in active_players:
                if len(player.hole_cards) == 2:
                    card1_str = f"{player.hole_cards[0].rank.symbol}{player.hole_cards[0].suit.value}"
                    card2_str = f"{player.hole_cards[1].rank.symbol}{player.hole_cards[1].suit.value}"
                    
                    hand_rank, best_cards = HandEvaluator.evaluate_hand(player.hole_cards, self.community_cards)
                    hand_description = HandEvaluator.hand_to_string((hand_rank, best_cards))
                    player_type = "🤖" if player.is_bot else "👤"
                    
                    print(f"{player_type} {player.nickname}: {card1_str} {card2_str} -> {hand_description}")
                    
                    player_hand_info = {
                        'player': player,
                        'player_id': player.id,
                        'nickname': player.nickname,
                        'is_bot': player.is_bot,
                        'hole_cards': [card.to_dict() for card in player.hole_cards],
                        'hole_cards_str': f"{card1_str} {card2_str}",
                        'hand_rank': hand_rank,
                        'hand_name': hand_rank.value[1],
                        'hand_description': hand_description,
                        'rank_value': hand_rank.rank_value,
                        'kickers': best_cards
                    }
                    
                    player_hands.append(player_hand_info)
            
            # 按手牌强度排序（降序，最强的在前面）
            player_hands.sort(key=lambda x: (x['rank_value'], x['kickers']), reverse=True)
            
            # 确定获胜者和排名
            winner = None
            if player_hands:
                winner = player_hands[0]['player']
                winner.chips += self.pot
                self.game_stage = GameStage.FINISHED
                
                # 添加排名信息
                for i, hand_info in enumerate(player_hands):
                    hand_info['rank'] = i + 1
                    hand_info['final_chips'] = hand_info['player'].chips
                    if i == 0:
                        hand_info['result'] = 'winner'
                        hand_info['winnings'] = self.pot
                    else:
                        hand_info['result'] = 'loser'
                        hand_info['winnings'] = 0
                
                showdown_info['winner'] = winner
                showdown_info['showdown_players'] = player_hands
                showdown_info['win_reason'] = 'best_hand'
                
                print("-" * 40)
                print("🏆 摊牌结果排名:")
                for i, hand_info in enumerate(player_hands):
                    rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    player_type = "🤖" if hand_info['is_bot'] else "👤"
                    print(f"{rank_emoji} {player_type} {hand_info['nickname']}: {hand_info['hand_description']} "
                          f"({'赢得 $' + str(self.pot) if i == 0 else '输掉'})")
                
                player_type = "🤖" if winner.is_bot else "👤"
                print(f"🏆 {player_type} {winner.nickname} 获胜！手牌：{player_hands[0]['hand_description']}，赢得底池 ${self.pot}")
                print("=" * 60)
        
        # 调试：打印最终的摊牌信息
        print(f"🏁 摊牌信息总结:")
        print(f"  - is_showdown: {showdown_info['is_showdown']}")
        print(f"  - showdown_players数量: {len(showdown_info['showdown_players'])}")
        print(f"  - winner: {showdown_info['winner'].nickname if showdown_info['winner'] else None}")
        
        return showdown_info
    
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
        
        # 包括全下的玩家在内的活跃玩家（用于判断是否需要继续游戏）
        active_players = [p for p in self.players if p.status in [PlayerStatus.PLAYING, PlayerStatus.ALL_IN]]
        print(f"游戏流程检查: 活跃玩家={len(active_players)}, 当前阶段={self.game_stage.value}, 底池=${self.pot}")
        
        # 打印玩家状态
        for player in self.players:
            print(f"  玩家 {player.nickname}: 状态={player.status.value}, 当前投注=${player.current_bet}, 筹码=${player.chips}")
        
        # 检查投注回合是否完成
        if self.is_betting_round_complete():
            print("投注回合完成！")
            
            # 先检查是否只剩一个玩家（提前结束）
            if len(active_players) <= 1:
                print("只剩一个玩家，手牌提前结束")
                showdown_result = self._determine_winner()
                result['hand_complete'] = True
                result['showdown_info'] = showdown_result
                result['winner'] = showdown_result.get('winner', None)
                if result['winner']:
                    result['message'] = f"{result['winner'].nickname} 获胜，赢得 ${showdown_result['pot']}"
            else:
                # 进入下一阶段
                print(f"进入下一阶段，当前阶段: {self.game_stage.value}")
                if self.advance_to_next_stage():
                    result['stage_changed'] = True
                    result['message'] = f"进入 {self.game_stage.value} 阶段"
                    print(f"成功进入 {self.game_stage.value} 阶段")
                    
                    # 如果进入SHOWDOWN阶段，手牌结束，需要确定获胜者
                    if self.game_stage == GameStage.SHOWDOWN:
                        print("🏆 进入SHOWDOWN阶段，开始摊牌")
                        showdown_result = self._determine_winner()
                        result['hand_complete'] = True
                        result['showdown_info'] = showdown_result
                        result['winner'] = showdown_result.get('winner', None)
                        if result['winner']:
                            result['message'] = f"{result['winner'].nickname} 获胜，赢得 ${showdown_result['pot']}"
                        
                        # 摊牌完成后直接返回，不再处理FINISHED阶段
                        print(f"🏆 摊牌完成，返回结果，游戏阶段: {self.game_stage.value}")
                        return result
                    
                    # 如果进入FINISHED阶段，表示手牌结束
                    elif self.game_stage == GameStage.FINISHED:
                        print("🏆 游戏阶段为FINISHED，手牌已结束")
                        result['hand_complete'] = True
                        
                        # 这种情况通常是在_determine_winner中已经设置了游戏阶段为FINISHED
                        # 应该已经有摊牌信息了，不需要重复处理
                        print("⚠️ 游戏阶段已为FINISHED，可能缺少摊牌信息")
                        
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
                            result['winner'] = winner
                            result['message'] = f"{winner.nickname} 获胜"
                            print(f"🏆 确定获胜者: {winner.nickname}, 筹码: {winner.chips}")
                        else:
                            print("⚠️ 未找到获胜者，创建默认获胜者")
                            if self.players:
                                winner = self.players[0]
                                result['winner'] = winner
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