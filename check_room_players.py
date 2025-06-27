#!/usr/bin/env python3
"""
检查房间中的玩家详情
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
import time

def check_room_players():
    """检查所有活跃房间中的玩家详情"""
    print("🔍 检查房间玩家详情...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取所有活跃房间
            cursor.execute('SELECT * FROM tables WHERE is_active = 1')
            tables = cursor.fetchall()
            
            if not tables:
                print("✅ 没有活跃房间")
                return
            
            for table in tables:
                print(f"\n📋 房间: {table['title']} (ID: {table['id']})")
                created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(table['created_at']))
                last_activity = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(table['last_activity']))
                print(f"   创建时间: {created_time}")
                print(f"   最后活动: {last_activity}")
                print(f"   游戏阶段: {table['game_stage']}")
                
                # 获取房间中的玩家
                cursor.execute('''
                    SELECT tp.*, u.nickname, u.last_active
                    FROM table_players tp
                    LEFT JOIN users u ON tp.player_id = u.id
                    WHERE tp.table_id = ?
                    ORDER BY tp.position
                ''', (table['id'],))
                
                players = cursor.fetchall()
                
                if players:
                    print(f"   👥 玩家列表 ({len(players)} 人):")
                    for player in players:
                        last_active = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(player['last_active'])) if player['last_active'] else '未知'
                        joined_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(player['joined_at']))
                        bot_info = " [机器人]" if player['is_bot'] else " [真人]"
                        print(f"      位置 {player['position']}: {player['nickname']}{bot_info}")
                        print(f"         筹码: ${player['chips']}, 状态: {player['status']}")
                        print(f"         加入时间: {joined_at}")
                        print(f"         最后活动: {last_active}")
                else:
                    print("   👥 房间中没有玩家")
                
                print("-" * 60)
                
    except Exception as e:
        print(f"❌ 检查过程中出错: {e}")

if __name__ == "__main__":
    check_room_players() 