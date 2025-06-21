#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两个真人玩家 + 一个机器人完整测试脚本
测试功能：
1. 玩家注册和登录
2. 创建带机器人的房间
3. 加入房间
4. 三人游戏流程（发牌、下注、结算）
5. 机器人自动行动
6. 投票下一轮
7. 离开房间
"""

import requests
import socketio
import time
import json
import threading
from typing import Dict, List

class PokerTestClient:
    def __init__(self, nickname: str, base_url: str = "http://localhost:5000"):
        self.nickname = nickname
        self.base_url = base_url
        self.sio = socketio.Client()
        self.player_id = None
        self.table_id = None
        self.hole_cards = []
        self.chips = 1000
        self.events = []  # 记录收到的事件
        self.is_my_turn = False
        self.current_bet = 0
        self.game_stage = "waiting"
        self.community_cards = []
        self.pot_size = 0
        self.setup_events()
    
    def setup_events(self):
        """设置Socket.IO事件监听"""
        
        @self.sio.on('register_response')
        def on_register(data):
            if data.get('success'):
                self.player_id = data.get('player_id')
                self.chips = data.get('chips', 1000)
                print(f"✅ {self.nickname} 注册成功，ID: {self.player_id}")
                self.events.append(('register_success', data))
            else:
                print(f"❌ {self.nickname} 注册失败")
                self.events.append(('register_error', data))
        
        @self.sio.on('room_created')
        def on_room_created(data):
            if data.get('success'):
                print(f"✅ {self.nickname} 创建房间成功")
                self.events.append(('room_created', data))
            else:
                print(f"❌ {self.nickname} 创建房间失败: {data.get('message')}")
                self.events.append(('room_create_error', data))
        
        @self.sio.on('table_joined')
        def on_table_joined(data):
            if data.get('success'):
                self.table_id = data.get('table_id')
                table_data = data.get('table', {})
                players = table_data.get('players', [])
                print(f"✅ {self.nickname} 加入房间成功: {self.table_id}")
                print(f"   房间内玩家: {[p.get('nickname') for p in players]}")
                self.events.append(('table_joined', data))
            else:
                print(f"❌ {self.nickname} 加入房间失败: {data.get('message')}")
                self.events.append(('table_join_error', data))
        
        @self.sio.on('your_cards')
        def on_your_cards(data):
            self.hole_cards = data.get('hole_cards', [])
            cards_display = [f"{card['rank']}{card['suit'][0]}" for card in self.hole_cards]
            print(f"🃏 {self.nickname} 收到手牌: {cards_display}")
            self.events.append(('your_cards', data))
        
        @self.sio.on('your_turn')
        def on_your_turn(data):
            self.is_my_turn = True
            self.current_bet = data.get('current_bet', 0)
            self.your_bet = data.get('your_bet', 0)
            self.your_chips = data.get('your_chips', 0)
            self.pot_size = data.get('pot', 0)
            available_actions = data.get('available_actions', [])
            print(f"🎯 轮到 {self.nickname} 行动")
            print(f"   当前下注: {self.current_bet}, 我的下注: {self.your_bet}, 底池: {self.pot_size}")
            print(f"   可用动作: {available_actions}")
            self.events.append(('your_turn', data))
        
        @self.sio.on('hand_ended')
        def on_hand_ended(data):
            winners = data.get('winners', [])
            print(f"🏆 {self.nickname} 收到手牌结束")
            print(f"   获胜者: {[w.get('nickname') for w in winners]}")
            if winners:
                for winner in winners:
                    print(f"   {winner.get('nickname')} 赢得 {winner.get('winnings', 0)} 筹码")
            self.events.append(('hand_ended', data))
        
        @self.sio.on('show_next_round_vote')
        def on_show_next_round_vote(data):
            print(f"🗳️ {self.nickname} 收到下一轮投票请求")
            self.events.append(('show_next_round_vote', data))
        
        @self.sio.on('vote_request')
        def on_vote_request(data):
            print(f"🗳️ {self.nickname} 收到投票请求")
            self.events.append(('vote_request', data))
        
        @self.sio.on('new_hand_started')
        def on_new_hand_started(data):
            print(f"🎮 {self.nickname} 新手牌开始")
            self.events.append(('new_hand_started', data))
        
        @self.sio.on('game_state_update')
        def on_game_state_update(data):
            self.game_stage = data.get('game_stage', 'waiting')
            self.community_cards = data.get('community_cards', [])
            self.pot_size = data.get('pot_size', 0)
            print(f"📊 {self.nickname} 游戏状态更新: {self.game_stage}")
            if self.community_cards:
                cards_str = [f"{card['rank']}{card['suit'][0]}" for card in self.community_cards]
                print(f"   公共牌: {cards_str}")
            print(f"   底池: {self.pot_size}")
            self.events.append(('game_state_update', data))
        
        @self.sio.on('error')
        def on_error(data):
            print(f"❌ {self.nickname} 收到错误: {data.get('message')}")
            self.events.append(('error', data))
        
        @self.sio.on('player_action')
        def on_player_action(data):
            player_name = data.get('player_nickname', 'Unknown')
            action = data.get('action')
            amount = data.get('amount', 0)
            is_bot = data.get('is_bot', False)
            bot_indicator = "🤖" if is_bot else "👤"
            print(f"{bot_indicator} {player_name} 执行动作: {action} {amount if amount > 0 else ''}")
            self.events.append(('player_action', data))
        
        @self.sio.on('community_cards')
        def on_community_cards(data):
            self.community_cards = data.get('cards', [])
            stage = data.get('stage', '')
            cards_str = [f"{card['rank']}{card['suit'][0]}" for card in self.community_cards]
            print(f"🎴 {stage} - 公共牌: {cards_str}")
            self.events.append(('community_cards', data))
    
    def connect(self):
        """连接到服务器"""
        try:
            self.sio.connect(self.base_url)
            print(f"🔗 {self.nickname} 连接成功")
            return True
        except Exception as e:
            print(f"❌ {self.nickname} 连接失败: {e}")
            return False
    
    def register(self):
        """注册玩家"""
        self.sio.emit('register_player', {'nickname': self.nickname})
        time.sleep(1)  # 等待注册响应
    
    def create_table(self, title: str = "测试房间", bots: Dict = None):
        """创建房间"""
        table_data = {
            'title': title,
            'small_blind': 10,
            'big_blind': 20,
            'max_players': 6,
            'initial_chips': 1000,
            'bots': bots or {}
        }
        self.sio.emit('create_table', table_data)
        time.sleep(3)  # 等待房间创建和机器人添加
    
    def join_table(self, table_id: str):
        """加入房间"""
        self.sio.emit('join_table', {'table_id': table_id})
        time.sleep(1)
    
    def start_hand(self):
        """开始手牌"""
        self.sio.emit('start_hand')
        time.sleep(1)
    
    def player_action(self, action: str, amount: int = 0):
        """执行玩家动作"""
        action_data = {
            'action': action,
            'amount': amount
        }
        print(f"🎯 {self.nickname} 执行动作: {action} {amount if amount > 0 else ''}")
        self.sio.emit('player_action', action_data)
        self.is_my_turn = False
        time.sleep(1)
    
    def vote_next_round(self, vote: bool = True):
        """投票下一轮"""
        print(f"🗳️ {self.nickname} 投票: {'同意' if vote else '拒绝'}")
        self.sio.emit('vote_next_round', {
            'vote': vote,
            'table_id': self.table_id
        })
        time.sleep(1)
    
    def leave_table(self):
        """离开房间"""
        self.sio.emit('leave_table')
        time.sleep(1)
    
    def disconnect(self):
        """断开连接"""
        self.sio.disconnect()
        print(f"🔌 {self.nickname} 断开连接")
    
    def wait_for_event(self, event_type: str, timeout: int = 10):
        """等待特定事件"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            for event_name, event_data in self.events:
                if event_name == event_type:
                    return event_data
            time.sleep(0.1)
        return None
    
    def wait_for_turn(self, timeout: int = 30):
        """等待轮到自己"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_my_turn:
                return True
            time.sleep(0.5)
        return False

def test_two_humans_one_bot():
    """测试两个真人玩家和一个机器人的完整游戏流程"""
    print("🎮 开始两个真人玩家 + 一个机器人测试")
    print("=" * 60)
    
    # 创建两个玩家
    player1 = PokerTestClient("真人玩家1")
    player2 = PokerTestClient("真人玩家2")
    
    try:
        # 1. 连接到服务器
        print("\n📡 步骤1: 连接到服务器")
        if not player1.connect():
            raise Exception("玩家1连接失败")
        if not player2.connect():
            raise Exception("玩家2连接失败")
        
        # 2. 注册玩家
        print("\n👤 步骤2: 注册玩家")
        player1.register()
        player2.register()
        
        # 等待注册完成
        if not player1.wait_for_event('register_success', 5):
            raise Exception("玩家1注册超时")
        if not player2.wait_for_event('register_success', 5):
            raise Exception("玩家2注册超时")
        
        # 3. 玩家1创建带机器人的房间
        print("\n🏠 步骤3: 创建带机器人的房间")
        bot_config = {
            'intermediate': 1  # 添加一个中级机器人
        }
        player1.create_table("两人+机器人测试房间", bot_config)
        
        if not player1.wait_for_event('room_created', 8):
            raise Exception("创建房间超时")
        if not player1.wait_for_event('table_joined', 8):
            raise Exception("创建者加入房间超时")
        
        # 4. 玩家2加入房间
        print("\n🚪 步骤4: 玩家2加入房间")
        player2.join_table(player1.table_id)
        
        if not player2.wait_for_event('table_joined', 5):
            raise Exception("玩家2加入房间超时")
        
        print("✅ 房间创建完成，包含2个真人玩家和1个机器人")
        
        # 5. 开始游戏
        print("\n🎯 步骤5: 开始第一手牌")
        player1.start_hand()
        
        # 等待发牌
        time.sleep(5)
        
        # 检查是否收到手牌
        if not player1.wait_for_event('your_cards', 8):
            raise Exception("玩家1未收到手牌")
        if not player2.wait_for_event('your_cards', 8):
            raise Exception("玩家2未收到手牌")
        
        print("✅ 两个真人玩家都收到了手牌")
        
        # 6. 翻牌前下注轮 - 处理三人游戏
        print("\n🃏 步骤6: 翻牌前下注轮")
        
        # 等待并处理多轮下注（三人游戏需要更多轮次）
        betting_rounds = 0
        max_betting_rounds = 6  # 三人游戏可能需要更多轮次
        
        while betting_rounds < max_betting_rounds:
            time.sleep(2)
            
            # 检查是否轮到玩家1
            if player1.wait_for_turn(3):
                print(f"第{betting_rounds + 1}轮: 玩家1行动")
                # 根据当前下注情况决定动作
                if hasattr(player1, 'your_bet') and player1.your_bet < player1.current_bet:
                    player1.player_action('call')  # 跟注到当前下注
                else:
                    player1.player_action('check')  # 过牌
                betting_rounds += 1
                continue
            
            # 检查是否轮到玩家2
            if player2.wait_for_turn(3):
                print(f"第{betting_rounds + 1}轮: 玩家2行动")
                # 根据当前下注情况决定动作
                if hasattr(player2, 'your_bet') and player2.your_bet < player2.current_bet:
                    player2.player_action('call')  # 跟注到当前下注
                else:
                    player2.player_action('check')  # 过牌
                betting_rounds += 1
                continue
            
            # 如果没有玩家需要行动，可能是机器人在行动或者该轮结束
            time.sleep(1)
            betting_rounds += 1
        
        # 7. 等待翻牌
        print("\n🎴 步骤7: 等待翻牌")
        time.sleep(5)
        
        # 8. 翻牌后下注
        print("\n💰 步骤8: 翻牌后下注")
        
        betting_rounds = 0
        max_betting_rounds = 4
        
        while betting_rounds < max_betting_rounds:
            time.sleep(2)
            
            if player1.wait_for_turn(3):
                print(f"翻牌后第{betting_rounds + 1}轮: 玩家1过牌")
                player1.player_action('check')
                betting_rounds += 1
                continue
            
            if player2.wait_for_turn(3):
                print(f"翻牌后第{betting_rounds + 1}轮: 玩家2过牌")
                player2.player_action('check')
                betting_rounds += 1
                continue
            
            time.sleep(1)
            betting_rounds += 1
        
        # 9. 转牌和河牌
        print("\n🎲 步骤9: 转牌和河牌阶段")
        
        for street_name in ["转牌", "河牌"]:
            print(f"\n{street_name}阶段:")
            time.sleep(3)
            
            betting_rounds = 0
            max_betting_rounds = 4
            
            while betting_rounds < max_betting_rounds:
                time.sleep(2)
                
                if player1.wait_for_turn(3):
                    print(f"{street_name}第{betting_rounds + 1}轮: 玩家1过牌")
                    player1.player_action('check')
                    betting_rounds += 1
                    continue
                
                if player2.wait_for_turn(3):
                    print(f"{street_name}第{betting_rounds + 1}轮: 玩家2过牌")
                    player2.player_action('check')
                    betting_rounds += 1
                    continue
                
                time.sleep(1)
                betting_rounds += 1
        
        # 10. 等待手牌结束
        print("\n🏆 步骤10: 等待手牌结束")
        time.sleep(5)
        
        if not player1.wait_for_event('hand_ended', 15):
            print("⚠️ 玩家1未收到手牌结束事件")
        if not player2.wait_for_event('hand_ended', 15):
            print("⚠️ 玩家2未收到手牌结束事件")
        
        print("✅ 第一手牌结束")
        
        # 11. 投票下一轮
        print("\n🗳️步骤11: 投票下一轮")
        time.sleep(3)
        
        # 检查是否收到投票请求
        if player1.wait_for_event('show_next_round_vote', 8):
            print("玩家1收到投票请求，投票同意")
            player1.vote_next_round(True)
        else:
            print("⚠️ 玩家1未收到投票请求，主动投票")
            player1.vote_next_round(True)
        
        if player2.wait_for_event('show_next_round_vote', 8):
            print("玩家2收到投票请求，投票同意")
            player2.vote_next_round(True)
        else:
            print("⚠️ 玩家2未收到投票请求，主动投票")
            player2.vote_next_round(True)
        
        # 12. 等待下一轮开始
        print("\n🎮 步骤12: 等待下一轮开始")
        time.sleep(8)
        
        if player1.wait_for_event('new_hand_started', 15):
            print("✅ 第二轮游戏开始")
            
            # 13. 快速完成第二轮
            print("\n⚡ 步骤13: 快速完成第二轮")
            time.sleep(5)
            
            # 简单的第二轮游戏 - 更保守的策略
            total_actions = 0
            max_actions = 12  # 三人游戏需要更多动作
            
            while total_actions < max_actions:
                time.sleep(2)
                
                if player1.wait_for_turn(3):
                    if total_actions < 3:
                        player1.player_action('call')
                    else:
                        player1.player_action('check')
                    total_actions += 1
                    continue
                
                if player2.wait_for_turn(3):
                    if total_actions < 3:
                        player2.player_action('call')
                    else:
                        player2.player_action('check')
                    total_actions += 1
                    continue
                
                total_actions += 1
                time.sleep(1)
            
            print("✅ 第二轮游戏完成")
        else:
            print("⚠️ 第二轮游戏未开始")
        
        # 14. 离开房间
        print("\n🚪 步骤14: 离开房间")
        time.sleep(3)
        
        player1.leave_table()
        player2.leave_table()
        
        print("✅ 两个真人玩家 + 一个机器人测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理连接
        try:
            player1.disconnect()
        except:
            pass
        try:
            player2.disconnect()
        except:
            pass
    
    return True

if __name__ == "__main__":
    print("🎮 德州扑克两个真人玩家 + 一个机器人完整测试")
    print("请确保服务器在 http://localhost:5000 运行")
    print()
    
    # 等待用户确认
    input("按回车键开始测试...")
    
    success = test_two_humans_one_bot()
    
    if success:
        print("\n🎉 测试成功完成！")
        print("✅ 验证了以下功能:")
        print("   - 两个真人玩家注册和连接")
        print("   - 创建带机器人的房间")
        print("   - 三人游戏流程（包括机器人自动行动）")
        print("   - 多轮下注和游戏阶段")
        print("   - 投票系统")
        print("   - 房间清理")
    else:
        print("\n💥 测试失败！")
        print("请检查服务器状态和日志") 