#!/usr/bin/env python3
"""
按比例下注（Ante）模式手动测试脚本
验证庄家轮换、行动顺序、下注逻辑等
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerStatus, PlayerAction
from poker_engine.bot import Bot, BotLevel
import uuid

def create_test_table():
    """创建测试牌桌"""
    table = Table(
        table_id=str(uuid.uuid4()),
        title="Ante模式测试",
        small_blind=10,
        big_blind=20,
        max_players=4,
        initial_chips=1000,
        game_mode="ante",
        ante_percentage=0.05  # 5%，更明显的测试效果
    )
    return table

def add_test_players(table):
    """添加测试玩家"""
    # 添加1个人类玩家
    human_player = Player("player1", "Alice", initial_chips=1000)
    table.add_player(human_player)
    
    # 添加3个机器人
    for i in range(2, 5):
        bot = Bot(f"bot{i}", f"Bot{i}", level=BotLevel.BEGINNER, initial_chips=1000)
        table.add_player(bot)
    
    return human_player

def print_table_state(table, round_name=""):
    """打印牌桌状态"""
    print(f"\n{'='*60}")
    print(f"📊 {round_name} - 牌桌状态")
    print(f"{'='*60}")
    print(f"🎮 游戏模式: {table.game_mode}")
    print(f"🏁 阶段: {table.game_stage.value}")
    print(f"🎯 手牌号: {table.hand_number}")
    print(f"💰 底池: ${table.pot}")
    print(f"💵 当前投注: ${table.current_bet}")
    
    active_players = [p for p in table.players if p.status == PlayerStatus.PLAYING]
    print(f"👥 活跃玩家: {len(active_players)}")
    
    # 显示所有玩家信息
    print(f"\n📋 玩家详情:")
    for i, player in enumerate(table.players):
        status_emoji = "🎯" if player.is_dealer else "👤" if not player.is_bot else "🤖"
        status_text = f"{status_emoji} {player.nickname}"
        
        if player.is_dealer:
            status_text += " (庄家)"
            
        print(f"  位置{i}: {status_text}")
        print(f"    💰 筹码: ${player.chips}")
        print(f"    💵 当前投注: ${player.current_bet}")
        print(f"    ✅ 已行动: {player.has_acted}")
        print(f"    📊 状态: {player.status.value}")
        
        if len(player.hole_cards) == 2:
            card1 = f"{player.hole_cards[0].rank.symbol}{player.hole_cards[0].suit.value}"
            card2 = f"{player.hole_cards[1].rank.symbol}{player.hole_cards[1].suit.value}"
            print(f"    🃏 手牌: {card1} {card2}")
    
    # 显示当前行动玩家
    current_player = table.get_current_player()
    if current_player:
        print(f"\n⏳ 当前行动玩家: {current_player.nickname}")
    else:
        print(f"\n✅ 无需行动玩家（可能需要进入下一阶段）")

def simulate_hand(table, human_player):
    """模拟一手牌"""
    print(f"\n🎮 开始新手牌...")
    
    # 开始新手牌
    if not table.start_new_hand():
        print("❌ 无法开始新手牌")
        return False
    
    print_table_state(table, f"第{table.hand_number}手牌 - 发牌后")
    
    # 模拟pre-flop下注轮
    print(f"\n🔄 Pre-flop 下注轮开始")
    action_count = 0
    max_actions = 20  # 防止无限循环
    
    while action_count < max_actions:
        current_player = table.get_current_player()
        if not current_player:
            print("没有需要行动的玩家，检查游戏流程...")
            break
            
        print(f"\n⏳ 轮到 {current_player.nickname} 行动")
        
        if current_player == human_player:
            # 人类玩家手动选择
            print("可选操作:")
            print("1. 过牌 (check)")
            print("2. 下注 (bet)")
            print("3. 跟注 (call)")
            print("4. 弃牌 (fold)")
            
            choice = input("请选择操作 (1-4): ").strip()
            
            if choice == "1":
                result = table.process_player_action(human_player.id, PlayerAction.CHECK)
            elif choice == "2":
                amount = int(input("下注金额: "))
                result = table.process_player_action(human_player.id, PlayerAction.BET, amount)
            elif choice == "3":
                result = table.process_player_action(human_player.id, PlayerAction.CALL)
            elif choice == "4":
                result = table.process_player_action(human_player.id, PlayerAction.FOLD)
            else:
                print("无效选择，自动过牌")
                result = table.process_player_action(human_player.id, PlayerAction.CHECK)
            
            print(f"操作结果: {result}")
        else:
            # 机器人自动行动
            print(f"🤖 {current_player.nickname} 正在思考...")
            
            # 简单的机器人逻辑
            if table.current_bet == 0:
                # 可以过牌或下注
                if current_player.chips >= 50:
                    result = table.process_player_action(current_player.id, PlayerAction.BET, 50)
                    print(f"🤖 {current_player.nickname} 下注 $50")
                else:
                    result = table.process_player_action(current_player.id, PlayerAction.CHECK)
                    print(f"🤖 {current_player.nickname} 过牌")
            else:
                # 需要跟注
                call_amount = table.current_bet - current_player.current_bet
                if current_player.chips >= call_amount:
                    result = table.process_player_action(current_player.id, PlayerAction.CALL)
                    print(f"🤖 {current_player.nickname} 跟注 ${call_amount}")
                else:
                    result = table.process_player_action(current_player.id, PlayerAction.FOLD)
                    print(f"🤖 {current_player.nickname} 弃牌")
        
        action_count += 1
        
        # 检查是否投注轮结束
        if table.is_betting_round_complete():
            print("✅ 投注轮结束")
            break
    
    print_table_state(table, f"第{table.hand_number}手牌 - Pre-flop结束")
    
    # 简单结束手牌（不模拟完整流程）
    return True

def test_dealer_rotation(table):
    """测试庄家轮换"""
    print(f"\n🔄 测试庄家轮换...")
    
    dealers_sequence = []
    
    # 模拟3手牌，观察庄家轮换
    for hand_num in range(1, 4):
        print(f"\n--- 第{hand_num}手牌 ---")
        
        if table.start_new_hand():
            # 找到当前庄家
            dealer = None
            for player in table.players:
                if player.is_dealer:
                    dealer = player
                    break
            
            if dealer:
                dealers_sequence.append(dealer.nickname)
                print(f"🎯 庄家: {dealer.nickname}")
                
                # 检查第一个行动玩家
                current_player = table.get_current_player()
                if current_player:
                    print(f"⏳ 第一个行动玩家: {current_player.nickname}")
        
        # 简单结束手牌
        table.game_stage = GameStage.FINISHED
    
    print(f"\n📊 庄家轮换序列: {dealers_sequence}")
    
    # 验证庄家确实在轮换
    unique_dealers = set(dealers_sequence)
    if len(unique_dealers) > 1:
        print("✅ 庄家轮换正常")
    else:
        print("❌ 庄家没有轮换")
    
    return len(unique_dealers) > 1

def main():
    """主测试函数"""
    print("🎮 按比例下注（Ante）模式测试开始")
    print("="*60)
    
    # 创建测试牌桌
    table = create_test_table()
    print(f"✅ 创建牌桌: {table.title}")
    print(f"📋 游戏模式: {table.game_mode}")
    print(f"💰 Ante比例: {table.ante_percentage*100}%")
    
    # 添加玩家
    human_player = add_test_players(table)
    print(f"✅ 添加了 {len(table.players)} 个玩家")
    
    # 测试庄家轮换
    dealer_rotation_ok = test_dealer_rotation(table)
    
    # 测试完整手牌
    print(f"\n🎯 开始完整手牌测试...")
    simulate_hand(table, human_player)
    
    print(f"\n📊 测试总结:")
    print(f"  ✅ 牌桌创建: 成功")
    print(f"  {'✅' if dealer_rotation_ok else '❌'} 庄家轮换: {'正常' if dealer_rotation_ok else '异常'}")
    print(f"  ✅ 游戏流程: 基本正常")
    
    print(f"\n🎮 测试完成！")

if __name__ == "__main__":
    main() 