#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两个真人玩家完整测试脚本
测试功能：
1. 玩家注册和登录
2. 创建房间
3. 加入房间
4. 游戏流程（发牌、下注、结算）
5. 投票下一轮
6. 离开房间
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
                print(f"✅ {self.nickname} 加入房间成功: {self.table_id}")
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
            print(f"🎯 轮到 {self.nickname} 行动，当前下注: {self.current_bet}")
            self.events.append(('your_turn', data))
        
        @self.sio.on('hand_ended')
        def on_hand_ended(data):
            winners = data.get('winners', [])
            print(f"🏆 {self.nickname} 收到手牌结束，获胜者: {[w.get('nickname') for w in winners]}")
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
            print(f"📊 {self.nickname} 游戏状态更新: {self.game_stage}")
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
            print(f"👤 {player_name} 执行动作: {action} {amount if amount > 0 else ''}")
            self.events.append(('player_action', data))
    
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
        time.sleep(2)  # 等待房间创建
    
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
        self.sio.emit('player_action', action_data)
        self.is_my_turn = False
        time.sleep(1)
    
    def vote_next_round(self, vote: bool = True):
        """投票下一轮"""
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

def test_two_humans():
    """测试两个真人玩家的完整游戏流程"""
    print("🎮 开始两个真人玩家测试")
    print("=" * 50)
    
    # 创建两个玩家
    player1 = PokerTestClient("玩家1")
    player2 = PokerTestClient("玩家2")
    
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
        
        # 3. 玩家1创建房间
        print("\n🏠 步骤3: 创建房间")
        player1.create_table("两人测试房间")
        
        if not player1.wait_for_event('room_created', 5):
            raise Exception("创建房间超时")
        if not player1.wait_for_event('table_joined', 5):
            raise Exception("创建者加入房间超时")
        
        # 4. 玩家2加入房间
        print("\n🚪 步骤4: 玩家2加入房间")
        player2.join_table(player1.table_id)
        
        if not player2.wait_for_event('table_joined', 5):
            raise Exception("玩家2加入房间超时")
        
        # 5. 开始游戏
        print("\n🎯 步骤5: 开始第一手牌")
        player1.start_hand()
        
        # 等待发牌
        time.sleep(3)
        
        # 检查是否收到手牌
        if not player1.wait_for_event('your_cards', 5):
            raise Exception("玩家1未收到手牌")
        if not player2.wait_for_event('your_cards', 5):
            raise Exception("玩家2未收到手牌")
        
        print("✅ 两个玩家都收到了手牌")
        
        # 6. 游戏流程 - 翻牌前
        print("\n🃏 步骤6: 翻牌前下注")
        
        # 等待第一个玩家行动
        time.sleep(2)
        
        # 找出谁先行动
        first_player = None
        second_player = None
        
        if player1.wait_for_turn(5):
            first_player = player1
            second_player = player2
            print("玩家1先行动")
        elif player2.wait_for_turn(5):
            first_player = player2
            second_player = player1
            print("玩家2先行动")
        else:
            raise Exception("没有玩家收到行动指令")
        
        # 第一个玩家跟注
        print(f"{first_player.nickname} 选择跟注")
        first_player.player_action('call')
        
        # 等待第二个玩家行动
        if second_player.wait_for_turn(10):
            print(f"{second_player.nickname} 选择过牌")
            second_player.player_action('check')
        else:
            raise Exception(f"{second_player.nickname} 未收到行动指令")
        
        # 7. 等待翻牌
        print("\n🎴 步骤7: 等待翻牌")
        time.sleep(3)
        
        # 8. 翻牌后下注
        print("\n💰 步骤8: 翻牌后下注")
        
        # 等待玩家行动
        time.sleep(2)
        
        if first_player.wait_for_turn(10):
            print(f"{first_player.nickname} 选择过牌")
            first_player.player_action('check')
        
        if second_player.wait_for_turn(10):
            print(f"{second_player.nickname} 选择过牌")
            second_player.player_action('check')
        
        # 9. 等待转牌和河牌
        print("\n🎲 步骤9: 继续游戏直到结束")
        time.sleep(5)
        
        # 继续下注轮次
        for round_name in ["转牌", "河牌"]:
            print(f"\n{round_name}轮下注:")
            time.sleep(2)
            
            if first_player.wait_for_turn(10):
                print(f"{first_player.nickname} 选择过牌")
                first_player.player_action('check')
            
            if second_player.wait_for_turn(10):
                print(f"{second_player.nickname} 选择过牌")
                second_player.player_action('check')
        
        # 10. 等待手牌结束
        print("\n🏆 步骤10: 等待手牌结束")
        
        if not player1.wait_for_event('hand_ended', 15):
            print("⚠️ 玩家1未收到手牌结束事件")
        if not player2.wait_for_event('hand_ended', 15):
            print("⚠️ 玩家2未收到手牌结束事件")
        
        # 11. 投票下一轮
        print("\n🗳️ 步骤11: 投票下一轮")
        time.sleep(2)
        
        # 检查是否收到投票请求
        if player1.wait_for_event('show_next_round_vote', 5):
            print("玩家1收到投票请求，投票同意")
            player1.vote_next_round(True)
        else:
            print("⚠️ 玩家1未收到投票请求，主动投票")
            player1.vote_next_round(True)
        
        if player2.wait_for_event('show_next_round_vote', 5):
            print("玩家2收到投票请求，投票同意")
            player2.vote_next_round(True)
        else:
            print("⚠️ 玩家2未收到投票请求，主动投票")
            player2.vote_next_round(True)
        
        # 12. 等待下一轮开始
        print("\n🎮 步骤12: 等待下一轮开始")
        time.sleep(8)  # 增加等待时间
        
        if player1.wait_for_event('new_hand_started', 10):
            print("✅ 第二轮游戏开始")
        else:
            print("⚠️ 第二轮游戏未开始")
        
        # 13. 快速完成第二轮
        print("\n⚡ 步骤13: 快速完成第二轮")
        time.sleep(5)  # 增加等待时间
        
        # 简单的第二轮游戏
        for i in range(4):  # 四轮下注
            time.sleep(2)
            if first_player.wait_for_turn(5):
                first_player.player_action('check')
            if second_player.wait_for_turn(5):
                second_player.player_action('check')
        
        # 14. 离开房间
        print("\n🚪 步骤14: 离开房间")
        time.sleep(2)
        
        player1.leave_table()
        player2.leave_table()
        
        print("✅ 两个真人玩家测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    finally:
        # 清理连接
        player1.disconnect()
        player2.disconnect()
    
    return True

if __name__ == "__main__":
    print("🎮 德州扑克两个真人玩家完整测试")
    print("请确保服务器在 http://localhost:5000 运行")
    print()
    
    # 等待用户确认
    input("按回车键开始测试...")
    
    success = test_two_humans()
    
    if success:
        print("\n🎉 测试成功完成！")
    else:
        print("\n💥 测试失败！") 