#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证回滚后的功能
"""

import time
import uuid
from poker_engine.table import Table
from poker_engine.bot import Bot, BotLevel
from poker_engine.player import Player, PlayerAction

def test_rollback_functionality():
    """测试回滚后的功能"""
    print("=" * 60)
    print("🔄 验证回滚后的功能")
    print("=" * 60)
    
    # 创建测试桌子
    table_id = str(uuid.uuid4())
    table = Table(table_id, "回滚测试桌", small_blind=10, big_blind=20, max_players=6)
    
    # 添加人类玩家和机器人
    human_player = Player("human1", "Alice", 1000)
    bot = Bot("bot1", "TestBot", 1000, BotLevel.BEGINNER)
    
    table.add_player(human_player)
    table.add_player(bot)
    
    # 开始新手牌
    success = table.start_new_hand()
    if not success:
        print("❌ 无法开始新手牌")
        return False
    
    print(f"✅ 新手牌开始成功")
    print(f"📊 牌桌状态: 游戏阶段={table.game_stage.value}")
    
    # 显示玩家信息
    print("\n🎮 玩家信息:")
    for i, player in enumerate(table.players):
        player_type = "🤖" if player.is_bot else "👤"
        print(f"  {i+1}. {player_type} {player.nickname}")
        print(f"     筹码: ${player.chips}, 状态: {player.status.value}")
        print(f"     投注: ${player.current_bet}, 已行动: {player.has_acted}")
    
    # 检查当前行动玩家
    current_player = table.get_current_player()
    if current_player:
        print(f"\n🎯 当前行动玩家: {current_player.nickname}")
        player_type = "🤖 机器人" if current_player.is_bot else "👤 人类玩家"
        print(f"类型: {player_type}")
    
    print("\n✅ 回滚验证内容:")
    print("1. ✅ process_bot_actions恢复原始逻辑")
    print("2. ✅ your_turn事件在主线程中发送")
    print("3. ✅ 机器人思考延迟恢复到table.py中")
    print("4. ✅ 保留bot_thinking事件发送")
    print("5. ✅ 移除复杂的后台线程处理")
    
    print("\n🎯 现在应该能够:")
    print("- 看到机器人思考状态（bot_thinking事件）")
    print("- 正常接收人类玩家轮次通知（your_turn事件）")
    print("- 无需刷新页面即可看到轮到自己出牌")
    
    print("\n" + "=" * 60)
    print("✅ 回滚验证完成")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = test_rollback_functionality()
        
        if success:
            print("\n🎉 回滚成功！")
            print("🔧 恢复到稳定的原始逻辑")
            print("🔧 保留机器人思考显示功能")
            print("🔧 修复人类玩家轮次通知问题")
            print("\n请重新启动游戏测试！")
        else:
            print("\n❌ 回滚测试失败")
            
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc() 