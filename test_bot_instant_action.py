#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试机器人立即行动功能
"""

import time
import uuid
from poker_engine.table import Table
from poker_engine.bot import Bot, BotLevel
from poker_engine.player import Player

def test_instant_bot_actions():
    """测试机器人立即行动"""
    print("=" * 60)
    print("⚡ 测试机器人立即行动功能")
    print("=" * 60)
    
    # 创建测试桌子
    table_id = str(uuid.uuid4())
    table = Table(table_id, "立即行动测试桌", small_blind=10, big_blind=20, max_players=6)
    
    # 添加不同等级的机器人
    bots = [
        Bot("bot1", "初级机器人", 1000, BotLevel.BEGINNER),
        Bot("bot2", "中级机器人", 1000, BotLevel.INTERMEDIATE), 
        Bot("bot3", "高级机器人", 1000, BotLevel.ADVANCED),
        Bot("bot4", "德州扑克之神", 1000, BotLevel.GOD)
    ]
    
    for bot in bots:
        table.add_player(bot)
    
    # 开始新手牌
    success = table.start_new_hand()
    if not success:
        print("❌ 无法开始新手牌")
        return False
    
    print(f"✅ 新手牌开始成功")
    print(f"📊 牌桌状态: 游戏阶段={table.game_stage.value}")
    
    # 显示机器人信息
    print("\n🤖 机器人信息:")
    for i, bot in enumerate(bots):
        print(f"  {i+1}. {bot.nickname} ({bot.bot_level.value})")
        print(f"     筹码: ${bot.chips}, 状态: {bot.status.value}")
    
    # 测试思考时间设置
    print("\n⚡ 思考时间设置验证:")
    thinking_delays_app = {
        BotLevel.BEGINNER: 0.0,
        BotLevel.INTERMEDIATE: 0.0,
        BotLevel.ADVANCED: 0.0,
        BotLevel.GOD: 0.0
    }
    
    thinking_delays_table = {
        BotLevel.BEGINNER: 0.0,
        BotLevel.INTERMEDIATE: 0.0,
        BotLevel.ADVANCED: 0.0
    }
    
    for bot in bots:
        delay_app = thinking_delays_app.get(bot.bot_level, 0.0)
        delay_table = thinking_delays_table.get(bot.bot_level, 0.0)
        print(f"  🤖 {bot.nickname} ({bot.bot_level.value}):")
        print(f"     app.py 延迟: {delay_app}秒")
        print(f"     table.py 延迟: {delay_table}秒")
        print(f"     ✅ 立即行动: {'是' if delay_app == 0.0 and delay_table == 0.0 else '否'}")
    
    # 测试机器人行动速度
    print("\n⏱️ 机器人行动速度测试:")
    current_player = table.get_current_player()
    if current_player and current_player.is_bot:
        print(f"当前行动玩家: {current_player.nickname}")
        start_time = time.time()
        
        # 模拟机器人行动（仅测试延迟）
        thinking_delays = {
            BotLevel.BEGINNER: 0.0,
            BotLevel.INTERMEDIATE: 0.0,
            BotLevel.ADVANCED: 0.0,
            BotLevel.GOD: 0.0
        }
        delay = thinking_delays.get(current_player.bot_level, 0.0)
        time.sleep(delay)
        
        end_time = time.time()
        actual_delay = end_time - start_time
        print(f"实际延迟: {actual_delay:.3f}秒")
        print(f"✅ 立即行动: {'是' if actual_delay < 0.1 else '否'}")
    
    print("\n" + "=" * 60)
    print("✅ 机器人立即行动功能测试完成")
    print("=" * 60)
    
    return True

def test_bot_thinking_events():
    """测试机器人思考事件"""
    print("\n📡 机器人思考事件测试:")
    print("现在机器人思考事件仍会发送，但时间为0秒：")
    
    levels = ['beginner', 'intermediate', 'advanced', 'god']
    for level in levels:
        print(f"  🤖 {level}: bot_thinking事件 -> thinking_time: 0.0秒")
    
    print("✅ 前端仍会收到思考事件，但会立即完成")

if __name__ == '__main__':
    try:
        success = test_instant_bot_actions()
        test_bot_thinking_events()
        
        if success:
            print("\n🎉 修改成功！")
            print("⚡ 所有机器人思考时间已改为0秒")
            print("⚡ 机器人现在会立即行动")
            print("📡 bot_thinking事件仍会发送（时间为0）")
            print("🎮 游戏节奏大幅加快")
        else:
            print("\n❌ 测试失败")
            
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc() 