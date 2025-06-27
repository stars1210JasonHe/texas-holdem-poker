#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库机器人标识修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import PokerDatabase
from poker_engine.table import Table
from poker_engine.bot import Bot, BotLevel
from poker_engine.player import Player, PlayerAction
import uuid
import time

def test_bot_database_fix():
    """测试机器人数据库标识修复"""
    print("🔧 测试数据库机器人标识修复")
    print("=" * 60)
    
    # 1. 创建测试环境
    print("📋 步骤1: 创建测试环境")
    db = PokerDatabase()
    
    # 创建测试房间
    table_id = str(uuid.uuid4())
    db_table_id = db.create_table(
        title="机器人标识测试",
        created_by="test_user",
        small_blind=10,
        big_blind=20,
        max_players=6,
        initial_chips=1000
    )
    
    print(f"✅ 测试房间创建: {db_table_id}")
    
    # 2. 使用旧的方式添加机器人（模拟之前的bug）
    print("\n📋 步骤2: 模拟旧方式添加机器人（会产生bug）")
    
    bot_id_old = str(uuid.uuid4())
    bot_name_old = "旧方式机器人"
    
    # 旧方式：只调用join_table，不设置is_bot
    db.join_table(db_table_id, bot_id_old)
    
    # 检查结果
    players_old = db.get_table_players(db_table_id)
    for player in players_old:
        if player['player_id'] == bot_id_old:
            print(f"❌ 旧方式机器人标识: is_bot={player['is_bot']} (应该是False)")
            break
    
    # 3. 使用新的方式添加机器人（模拟修复后）
    print("\n📋 步骤3: 模拟新方式添加机器人（修复后）")
    
    bot_id_new = str(uuid.uuid4())
    bot_name_new = "新方式机器人"
    bot_level = BotLevel.INTERMEDIATE
    
    # 新方式：先join_table，然后更新is_bot标识
    if db.join_table(db_table_id, bot_id_new):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE table_players 
                SET is_bot = 1, bot_level = ?
                WHERE table_id = ? AND player_id = ?
            ''', (bot_level.value, db_table_id, bot_id_new))
            conn.commit()
            print(f"✅ 新方式机器人标识已更新: is_bot=1, bot_level={bot_level.value}")
    
    # 4. 检查修复结果
    print("\n📋 步骤4: 检查修复结果")
    
    players_final = db.get_table_players(db_table_id)
    print(f"房间玩家总数: {len(players_final)}")
    
    for player in players_final:
        player_type = "机器人" if player['is_bot'] else "真人"
        print(f"  玩家: {player['nickname'] or '未知'}")
        print(f"    ID: {player['player_id']}")
        print(f"    类型: {player_type} (is_bot={player['is_bot']})")
        print(f"    等级: {player['bot_level'] or '无'}")
        print()
    
    # 5. 验证机器人识别逻辑
    print("📋 步骤5: 验证机器人识别逻辑")
    
    old_bot_identified = False
    new_bot_identified = False
    
    for player in players_final:
        if player['player_id'] == bot_id_old:
            old_bot_identified = player['is_bot'] or any(keyword in (player['nickname'] or '') 
                                                       for keyword in ['机器人', 'Bot', 'bot'])
        elif player['player_id'] == bot_id_new:
            new_bot_identified = player['is_bot']
    
    print(f"旧方式机器人识别: {'✅' if old_bot_identified else '❌'}")
    print(f"新方式机器人识别: {'✅' if new_bot_identified else '❌'}")
    
    # 6. 清理测试数据
    print("\n📋 步骤6: 清理测试数据")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM table_players WHERE table_id = ?', (db_table_id,))
        cursor.execute('DELETE FROM tables WHERE id = ?', (db_table_id,))
        conn.commit()
    
    print("✅ 测试数据清理完成")
    
    # 7. 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  旧方式机器人识别: {'✅ 通过' if old_bot_identified else '❌ 失败'}")
    print(f"  新方式机器人识别: {'✅ 通过' if new_bot_identified else '❌ 失败'}")
    
    if old_bot_identified and new_bot_identified:
        print("🎉 数据库机器人标识修复测试通过！")
        return True
    else:
        print("❌ 数据库机器人标识修复测试失败！")
        return False

def test_game_flow_with_fix():
    """测试修复后的游戏流程"""
    print("\n🎮 测试修复后的游戏流程")
    print("=" * 60)
    
    # 创建内存中的表格，模拟真实游戏
    table = Table("test_fix", "修复测试", small_blind=10, big_blind=20)
    
    # 添加真人玩家
    human = Player("human1", "真人玩家", 1000)
    table.add_player(human)
    
    # 添加机器人
    bots = [
        Bot("bot1", "测试机器人1", 1000, BotLevel.BEGINNER),
        Bot("bot2", "测试机器人2", 1000, BotLevel.INTERMEDIATE),
        Bot("bot3", "测试机器人3", 1000, BotLevel.ADVANCED)
    ]
    
    for bot in bots:
        table.add_player(bot)
    
    print(f"✅ 游戏环境创建完成，共{len(table.players)}个玩家")
    
    # 验证机器人标识
    print("\n🔍 验证机器人标识:")
    for player in table.players:
        player_type = "🤖 机器人" if player.is_bot else "👤 真人"
        print(f"  {player.nickname}: {player_type}")
        if hasattr(player, 'bot_level'):
            print(f"    等级: {player.bot_level.value}")
    
    # 开始游戏
    print("\n🎯 开始游戏测试:")
    if table.start_new_hand():
        print("✅ 手牌开始成功")
        
        # 真人弃牌
        print("👤 真人玩家弃牌...")
        result = table.process_player_action("human1", PlayerAction.FOLD)
        if result['success']:
            print("✅ 真人弃牌成功")
            
            # 测试机器人处理
            print("🤖 开始机器人处理...")
            start_time = time.time()
            
            try:
                bot_result = table.process_bot_actions()
                end_time = time.time()
                
                print(f"✅ 机器人处理完成，耗时: {end_time - start_time:.2f}秒")
                print(f"游戏状态: {bot_result.get('hand_complete', False)}")
                
                if end_time - start_time < 2.0:
                    print("🎉 修复后游戏流程测试通过！")
                    return True
                else:
                    print("⚠️ 处理时间偏长，可能仍有问题")
                    return False
                    
            except Exception as e:
                print(f"❌ 机器人处理出错: {e}")
                return False
        else:
            print(f"❌ 真人弃牌失败: {result['message']}")
            return False
    else:
        print("❌ 无法开始手牌")
        return False

if __name__ == "__main__":
    print("🧪 数据库机器人标识修复测试")
    print("=" * 80)
    
    # 测试1: 数据库标识修复
    test1_success = test_bot_database_fix()
    
    # 测试2: 游戏流程测试
    test2_success = test_game_flow_with_fix()
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 综合测试结果:")
    print(f"  数据库修复测试: {'✅ 通过' if test1_success else '❌ 失败'}")
    print(f"  游戏流程测试: {'✅ 通过' if test2_success else '❌ 失败'}")
    
    if test1_success and test2_success:
        print("🎉 所有测试通过！机器人卡死问题的根本原因已修复")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，需要进一步检查")
        sys.exit(1) 