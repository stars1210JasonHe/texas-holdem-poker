#!/usr/bin/env python3
"""
分析最近的游戏日志，找出机器人异常弃牌的原因
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta

def analyze_recent_games():
    """分析最近的游戏记录"""
    print("🔍 分析最近的游戏记录...")
    
    try:
        # 连接游戏日志数据库
        try:
            conn = sqlite3.connect('game_logs.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        except Exception as e:
            print(f"⚠️ 无法连接游戏日志数据库: {e}")
            print("可能游戏日志功能未启用或数据库不存在")
            return
        
        # 获取最近的4个游戏会话
        cursor.execute('''
            SELECT * FROM game_sessions 
            ORDER BY created_at DESC 
            LIMIT 4
        ''')
        recent_sessions = cursor.fetchall()
        
        if not recent_sessions:
            print("❌ 没有找到最近的游戏记录")
            return
        
        print(f"📋 找到 {len(recent_sessions)} 个最近的游戏会话:")
        
        for session in recent_sessions:
            print(f"\n{'='*60}")
            print(f"🎮 游戏会话 #{session['id']}: {session['table_title']}")
            print(f"   开始时间: {session['created_at']}")
            print(f"   玩家数量: {session['player_count']} 人 + {session['bot_count']} 机器人")
            print(f"   状态: {session['status']}")
            
            # 获取这个会话的所有手牌
            cursor.execute('''
                SELECT * FROM hands 
                WHERE session_id = ?
                ORDER BY hand_number ASC
            ''', (session['id'],))
            hands = cursor.fetchall()
            
            print(f"   总手牌数: {len(hands)}")
            
            for hand in hands:
                print(f"\n  🃏 手牌 #{hand['hand_number']} (ID: {hand['id']})")
                print(f"     开始: {hand['started_at']}")
                if hand['ended_at']:
                    print(f"     结束: {hand['ended_at']}")
                print(f"     阶段: {hand['stage']}")
                print(f"     底池: ${hand['pot'] or 0}")
                
                if hand['winner_nickname']:
                    print(f"     获胜者: {hand['winner_nickname']} (${hand['winning_amount'] or 0})")
                
                # 获取这手牌的所有玩家动作
                cursor.execute('''
                    SELECT * FROM player_actions 
                    WHERE hand_id = ?
                    ORDER BY timestamp ASC
                ''', (hand['id'],))
                actions = cursor.fetchall()
                
                print(f"     玩家动作记录:")
                
                if not actions:
                    print(f"       ❌ 没有动作记录")
                    continue
                
                # 按玩家分组统计动作
                player_actions = {}
                fold_players = []
                
                for action in actions:
                    player_name = action['player_nickname']
                    action_type = action['action_type']
                    amount = action['amount'] or 0
                    stage = action['stage'] or 'unknown'
                    
                    if player_name not in player_actions:
                        player_actions[player_name] = []
                    
                    player_actions[player_name].append({
                        'action': action_type,
                        'amount': amount,
                        'stage': stage,
                        'time': action['timestamp']
                    })
                    
                    if action_type == 'fold':
                        fold_players.append(player_name)
                
                # 显示每个玩家的动作
                for player_name, actions_list in player_actions.items():
                    is_bot = any(name in player_name for name in ['新手', '老司机', '大师', '菜鸟', '高手', '传奇', '王者'])
                    player_type = "🤖" if is_bot else "👤"
                    
                    print(f"       {player_type} {player_name}:")
                    for action_info in actions_list:
                        action_desc = f"{action_info['action']}"
                        if action_info['amount'] > 0:
                            action_desc += f" ${action_info['amount']}"
                        action_desc += f" ({action_info['stage']})"
                        print(f"         - {action_desc}")
                
                # 分析异常弃牌模式
                bot_fold_count = len([p for p in fold_players if any(name in p for name in ['新手', '老司机', '大师', '菜鸟', '高手', '传奇', '王者'])])
                human_fold_count = len([p for p in fold_players if not any(name in p for name in ['新手', '老司机', '大师', '菜鸟', '高手', '传奇', '王者'])])
                
                if bot_fold_count >= 2:  # 如果有2个或更多机器人弃牌
                    print(f"       🚨 异常检测: {bot_fold_count}个机器人弃牌, {human_fold_count}个真人弃牌")
                
                # 检查是否有异常的连续弃牌模式
                consecutive_folds = 0
                max_consecutive_folds = 0
                
                for action in actions:
                    if action['action_type'] == 'fold':
                        consecutive_folds += 1
                        max_consecutive_folds = max(max_consecutive_folds, consecutive_folds)
                    else:
                        consecutive_folds = 0
                
                if max_consecutive_folds >= 3:
                    print(f"       ⚠️ 检测到连续弃牌: 最多{max_consecutive_folds}个连续弃牌")
        
        conn.close()
        
        # 也检查主数据库中的玩家状态
        print(f"\n{'='*60}")
        print("🔍 检查主数据库中的当前玩家状态...")
        
        try:
            from database import db
            
            # 获取所有活跃房间中的玩家
            with db.get_connection() as main_conn:
                main_cursor = main_conn.cursor()
                
                main_cursor.execute('''
                    SELECT t.title, t.game_stage, tp.*, u.nickname
                    FROM tables t
                    JOIN table_players tp ON t.id = tp.table_id
                    LEFT JOIN users u ON tp.player_id = u.id
                    WHERE t.is_active = 1
                    ORDER BY t.id, tp.position
                ''')
                
                current_players = main_cursor.fetchall()
                
                if current_players:
                    current_table = None
                    for row in current_players:
                        if current_table != row['title']:
                            current_table = row['title']
                            print(f"\n🏠 房间: {current_table} (阶段: {row['game_stage']})")
                        
                        player_type = "🤖" if row['is_bot'] else "👤"
                        nickname = row['nickname'] or 'Unknown'
                        print(f"   {player_type} {nickname}: 位置{row['position']}, ${row['chips']}筹码, 状态:{row['status']}, 投注:${row['current_bet']}")
                else:
                    print("   没有活跃的房间")
        
        except Exception as e:
            print(f"   检查主数据库失败: {e}")
    
    except Exception as e:
        print(f"❌ 分析游戏记录失败: {e}")
        import traceback
        traceback.print_exc()

def check_game_logs_db():
    """检查游戏日志数据库是否存在和可访问"""
    try:
        conn = sqlite3.connect('game_logs.db')
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 游戏日志数据库表: {[table[0] for table in tables]}")
        
        # 检查各表的记录数
        for table_name in ['game_sessions', 'hands', 'player_actions', 'game_events']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count} 条记录")
            except Exception as e:
                print(f"   {table_name}: 表不存在或查询失败 ({e})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 游戏日志数据库检查失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始分析最近游戏的机器人弃牌问题...")
    
    # 首先检查游戏日志数据库
    if check_game_logs_db():
        analyze_recent_games()
    else:
        print("⚠️ 游戏日志数据库不可用，只能检查当前状态")
        
        # 检查当前数据库状态
        try:
            from database import db
            print("\n🔍 检查当前数据库状态...")
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM tables WHERE is_active = 1')
                active_tables = cursor.fetchone()[0]
                print(f"活跃房间数: {active_tables}")
                
                if active_tables > 0:
                    cursor.execute('''
                        SELECT t.title, tp.player_id, u.nickname, tp.status, tp.is_bot, tp.bot_level
                        FROM tables t
                        JOIN table_players tp ON t.id = tp.table_id
                        LEFT JOIN users u ON tp.player_id = u.id
                        WHERE t.is_active = 1
                        ORDER BY t.id, tp.position
                    ''')
                    
                    players = cursor.fetchall()
                    current_table = None
                    
                    for player in players:
                        if current_table != player['title']:
                            current_table = player['title']
                            print(f"\n🏠 房间: {current_table}")
                        
                        player_type = "🤖" if player['is_bot'] else "👤"
                        nickname = player['nickname'] or 'Unknown'
                        status = player['status']
                        
                        if player['is_bot'] and status == 'folded':
                            print(f"   ❌ {player_type} {nickname}: {status} (异常弃牌)")
                        else:
                            print(f"   ✅ {player_type} {nickname}: {status}")
        
        except Exception as e:
            print(f"检查当前状态失败: {e}") 