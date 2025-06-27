#!/usr/bin/env python3
"""
测试机器人决策修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_engine.table import Table, GameStage
from poker_engine.player import Player, PlayerStatus
from poker_engine.bot import Bot, BotLevel
from poker_engine.card import Deck
import time

def test_bot_decision_fix():
    """测试机器人决策修复"""
    print("🧪 测试机器人决策修复效果...")
    
    # 创建牌桌
    table = Table("test_table", "测试牌桌", small_blind=10, big_blind=20, max_players=5)
    
    # 添加1个人类玩家和3个机器人
    human = Player("human_1", "测试玩家", 1000)
    bot1 = Bot("bot_1", "新手1", 1000, BotLevel.BEGINNER)
    bot2 = Bot("bot_2", "老司机1", 1000, BotLevel.INTERMEDIATE) 
    bot3 = Bot("bot_3", "大师1", 1000, BotLevel.ADVANCED)
    
    # 添加玩家到牌桌
    table.add_player(human)
    table.add_player(bot1)
    table.add_player(bot2)
    table.add_player(bot3)
    
    print(f"✅ 牌桌创建成功，玩家数: {len(table.players)}")
    for i, player in enumerate(table.players):
        player_type = "🤖" if player.is_bot else "👤"
        print(f"  {i+1}. {player_type} {player.nickname} (${player.chips})")
    
    # 开始游戏
    print(f"\n🎮 开始新手牌...")
    success = table.start_new_hand()
    if not success:
        print("❌ 开始游戏失败")
        return
    
    print(f"✅ 游戏开始成功，阶段: {table.game_stage.value}")
    print(f"💰 底池: ${table.pot}, 当前投注: ${table.current_bet}")
    
    # 显示所有玩家状态
    print(f"\n👥 玩家状态:")
    for player in table.players:
        player_type = "🤖" if player.is_bot else "👤"
        card_info = ""
        if len(player.hole_cards) == 2:
            card1_str = f"{player.hole_cards[0].rank.symbol}{player.hole_cards[0].suit.value}"
            card2_str = f"{player.hole_cards[1].rank.symbol}{player.hole_cards[1].suit.value}"
            card_info = f"手牌: {card1_str} {card2_str}"
        print(f"  {player_type} {player.nickname}: 状态={player.status.value}, 投注=${player.current_bet}, 筹码=${player.chips}, {card_info}")
    
    # 获取当前应该行动的玩家
    current_player = table.get_current_player()
    if current_player:
        print(f"\n🎯 当前行动玩家: {current_player.nickname}")
    
    # 模拟人类玩家先弃牌，看机器人的行为
    print(f"\n🔧 模拟人类玩家弃牌...")
    if current_player and not current_player.is_bot:
        human.fold()
        human.has_acted = True
        print(f"👤 {human.nickname} 弃牌")
    
    # 现在处理机器人动作
    print(f"\n🤖 开始处理机器人动作...")
    
    before_bot_actions = {}
    for player in table.players:
        if player.is_bot:
            before_bot_actions[player.nickname] = {
                'status': player.status.value,
                'chips': player.chips,
                'current_bet': player.current_bet,
                'has_acted': player.has_acted
            }
    
    # 处理机器人动作
    result = table.process_bot_actions()
    
    print(f"\n📊 机器人处理结果: {result}")
    
    # 检查机器人行为
    print(f"\n🔍 机器人行为分析:")
    fold_count = 0
    action_count = 0
    
    for player in table.players:
        if player.is_bot:
            before = before_bot_actions[player.nickname]
            player_type = "🤖"
            
            if player.status.value != before['status']:
                action_count += 1
                if player.status == PlayerStatus.FOLDED:
                    fold_count += 1
                    print(f"  {player_type} {player.nickname}: {before['status']} -> {player.status.value} ❌")
                else:
                    print(f"  {player_type} {player.nickname}: {before['status']} -> {player.status.value} ✅")
            else:
                print(f"  {player_type} {player.nickname}: 状态未改变 ({player.status.value})")
            
            if player.has_acted != before['has_acted']:
                print(f"    行动状态: {before['has_acted']} -> {player.has_acted}")
            
            if player.current_bet != before['current_bet']:
                print(f"    投注: ${before['current_bet']} -> ${player.current_bet}")
    
    print(f"\n📈 统计结果:")
    print(f"  机器人总数: {len([p for p in table.players if p.is_bot])}")
    print(f"  有行动的机器人: {action_count}")
    print(f"  弃牌的机器人: {fold_count}")
    print(f"  弃牌率: {fold_count}/{len([p for p in table.players if p.is_bot])} = {fold_count/len([p for p in table.players if p.is_bot])*100:.1f}%")
    
    # 判断修复效果
    if fold_count >= 2:
        print(f"❌ 修复效果不佳：{fold_count}个机器人弃牌，可能仍有问题")
    elif fold_count == 1:
        print(f"⚠️ 修复部分有效：只有{fold_count}个机器人弃牌，情况有改善")
    else:
        print(f"✅ 修复效果良好：没有机器人异常弃牌")
    
    return fold_count < 2

def test_multiple_rounds():
    """测试多轮游戏，看是否稳定"""
    print(f"\n{'='*60}")
    print("🔄 测试多轮游戏稳定性...")
    
    fold_rates = []
    
    for round_num in range(3):
        print(f"\n🎮 第{round_num + 1}轮测试:")
        
        # 重新创建牌桌
        table = Table(f"test_table_{round_num}", f"测试牌桌{round_num + 1}", small_blind=10, big_blind=20)
        
        # 添加玩家
        human = Player(f"human_{round_num}", "测试玩家", 1000)
        bot1 = Bot(f"bot1_{round_num}", "新手1", 1000, BotLevel.BEGINNER)
        bot2 = Bot(f"bot2_{round_num}", "老司机1", 1000, BotLevel.INTERMEDIATE)
        bot3 = Bot(f"bot3_{round_num}", "大师1", 1000, BotLevel.ADVANCED)
        
        table.add_player(human)
        table.add_player(bot1)
        table.add_player(bot2)
        table.add_player(bot3)
        
        # 开始游戏
        success = table.start_new_hand()
        if not success:
            print(f"  ❌ 第{round_num + 1}轮开始失败")
            continue
        
        # 人类玩家弃牌
        current_player = table.get_current_player()
        if current_player and not current_player.is_bot:
            current_player.fold()
            current_player.has_acted = True
        
        # 处理机器人
        table.process_bot_actions()
        
        # 统计弃牌率
        bots = [p for p in table.players if p.is_bot]
        folded_bots = [p for p in bots if p.status == PlayerStatus.FOLDED]
        fold_rate = len(folded_bots) / len(bots) if bots else 0
        fold_rates.append(fold_rate)
        
        print(f"  机器人弃牌率: {len(folded_bots)}/{len(bots)} = {fold_rate*100:.1f}%")
    
    # 总体评估
    avg_fold_rate = sum(fold_rates) / len(fold_rates) if fold_rates else 0
    print(f"\n📊 多轮测试结果:")
    print(f"  平均弃牌率: {avg_fold_rate*100:.1f}%")
    print(f"  弃牌率范围: {min(fold_rates)*100:.1f}% - {max(fold_rates)*100:.1f}%")
    
    if avg_fold_rate < 0.5:  # 平均弃牌率低于50%
        print(f"✅ 修复效果稳定，机器人决策正常")
        return True
    else:
        print(f"❌ 修复效果不稳定，仍需改进")
        return False

if __name__ == "__main__":
    print("🚀 开始测试机器人决策修复效果...")
    
    # 单轮测试
    single_test_result = test_bot_decision_fix()
    
    # 多轮测试
    multi_test_result = test_multiple_rounds()
    
    print(f"\n{'='*60}")
    print("🎯 最终测试结果:")
    print(f"  单轮测试: {'✅ 通过' if single_test_result else '❌ 失败'}")
    print(f"  多轮测试: {'✅ 通过' if multi_test_result else '❌ 失败'}")
    
    if single_test_result and multi_test_result:
        print(f"🎉 机器人决策修复成功！")
    else:
        print(f"⚠️ 修复效果有限，建议进一步调试") 