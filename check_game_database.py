#!/usr/bin/env python3
"""
检查游戏数据库记录
验证德州扑克游戏的胜负计算是否正确
"""

import sqlite3
import json
from datetime import datetime

def check_game_logs():
    """检查游戏日志数据库"""
    print("🗄️ 检查游戏日志数据库...")
    
    try:
        conn = sqlite3.connect('game_logs.db')
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 现有表: {tables}")
        
        if 'game_sessions' in tables:
            cursor.execute("SELECT COUNT(*) FROM game_sessions")
            session_count = cursor.fetchone()[0]
            print(f"🎮 游戏会话数量: {session_count}")
            
            if session_count > 0:
                cursor.execute('''
                    SELECT table_title, player_count, bot_count, total_hands, status, created_at
                    FROM game_sessions 
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''')
                sessions = cursor.fetchall()
                print("\n📋 最近的游戏会话:")
                for session in sessions:
                    print(f"  • {session[0]} | 玩家:{session[1]} 机器人:{session[2]} | 手牌:{session[3]} | {session[4]} | {session[5]}")
        
        if 'hands' in tables:
            cursor.execute("SELECT COUNT(*) FROM hands")
            hand_count = cursor.fetchone()[0]
            print(f"🃏 手牌记录数量: {hand_count}")
            
            if hand_count > 0:
                cursor.execute('''
                    SELECT hand_number, winner_nickname, pot, winning_amount, 
                           community_cards, status, ended_at
                    FROM hands 
                    WHERE status = 'completed'
                    ORDER BY ended_at DESC 
                    LIMIT 10
                ''')
                hands = cursor.fetchall()
                print("\n🏆 最近完成的手牌:")
                for hand in hands:
                    community = json.loads(hand[4]) if hand[4] else []
                    community_str = ', '.join([f"{card['rank']}{card['suit']}" for card in community[:5]])
                    print(f"  • 手牌#{hand[0]} | 赢家:{hand[1]} | 底池:{hand[2]} | 奖金:{hand[3]} | 公共牌:[{community_str}] | {hand[6]}")
        
        if 'player_actions' in tables:
            cursor.execute("SELECT COUNT(*) FROM player_actions")
            action_count = cursor.fetchone()[0]
            print(f"🎯 玩家动作数量: {action_count}")
            
            if action_count > 0:
                cursor.execute('''
                    SELECT player_nickname, action_type, amount, stage, timestamp
                    FROM player_actions 
                    ORDER BY timestamp DESC 
                    LIMIT 15
                ''')
                actions = cursor.fetchall()
                print("\n📝 最近的玩家动作:")
                for action in actions:
                    print(f"  • {action[0]} | {action[1]} | ${action[2]} | {action[3]} | {action[4]}")
        
        # 检查摊牌记录
        if 'showdown_details' in tables:
            cursor.execute("SELECT COUNT(*) FROM showdown_details")
            showdown_count = cursor.fetchone()[0]
            print(f"🎲 摊牌记录数量: {showdown_count}")
            
            if showdown_count > 0:
                cursor.execute('''
                    SELECT nickname, is_bot, hand_description, result, winnings, 
                           rank_position, created_at
                    FROM showdown_details 
                    ORDER BY created_at DESC 
                    LIMIT 10
                ''')
                showdowns = cursor.fetchall()
                print("\n🃏 最近的摊牌记录:")
                for showdown in showdowns:
                    bot_flag = "🤖" if showdown[1] else "👤"
                    print(f"  • {bot_flag}{showdown[0]} | {showdown[2]} | {showdown[3]} | 奖金:${showdown[4]} | 排名:{showdown[5]} | {showdown[6]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查游戏日志失败: {e}")

def check_main_database():
    """检查主数据库"""
    print("\n🗄️ 检查主数据库...")
    
    try:
        conn = sqlite3.connect('poker_game.db')
        cursor = conn.cursor()
        
        # 检查用户表
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"👥 用户数量: {user_count}")
        
        if user_count > 0:
            cursor.execute('''
                SELECT nickname, chips, has_helper, last_activity
                FROM users 
                ORDER BY last_activity DESC 
                LIMIT 10
            ''')
            users = cursor.fetchall()
            print("\n👤 最近活跃用户:")
            for user in users:
                helper_flag = "🔧" if user[2] else ""
                print(f"  • {user[0]} | 筹码:${user[1]} | {helper_flag} | {user[3]}")
        
        # 检查房间表
        cursor.execute("SELECT COUNT(*) FROM tables WHERE status = 'active'")
        table_count = cursor.fetchone()[0]
        print(f"🏠 活跃房间数量: {table_count}")
        
        if table_count > 0:
            cursor.execute('''
                SELECT title, max_players, game_mode, creator_nickname, created_at
                FROM tables 
                WHERE status = 'active'
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            tables = cursor.fetchall()
            print("\n🏠 活跃房间:")
            for table in tables:
                print(f"  • {table[0]} | {table[1]}人桌 | {table[2]} | 创建者:{table[3]} | {table[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查主数据库失败: {e}")

def analyze_win_loss_calculation():
    """分析胜负计算是否正确"""
    print("\n🧮 分析胜负计算...")
    
    try:
        conn = sqlite3.connect('game_logs.db')
        cursor = conn.cursor()
        
        # 检查是否有摊牌记录
        cursor.execute("SELECT COUNT(*) FROM showdown_details")
        if cursor.fetchone()[0] == 0:
            print("⚠️ 暂无摊牌记录，无法分析胜负计算")
            conn.close()
            return
        
        # 分析摊牌结果分布
        cursor.execute('''
            SELECT result, COUNT(*) as count
            FROM showdown_details 
            GROUP BY result
        ''')
        result_distribution = cursor.fetchall()
        print("📊 摊牌结果分布:")
        for result, count in result_distribution:
            print(f"  • {result}: {count} 次")
        
        # 分析手牌类型分布
        cursor.execute('''
            SELECT hand_rank, COUNT(*) as count
            FROM showdown_details 
            GROUP BY hand_rank
            ORDER BY count DESC
        ''')
        hand_distribution = cursor.fetchall()
        print("\n🃏 手牌类型分布:")
        for hand_type, count in hand_distribution:
            print(f"  • {hand_type}: {count} 次")
        
        # 分析奖金分配
        cursor.execute('''
            SELECT h.hand_number, h.pot, 
                   SUM(sd.winnings) as total_distributed
            FROM hands h
            JOIN showdown_details sd ON h.id = sd.hand_id
            WHERE h.status = 'completed'
            GROUP BY h.id, h.hand_number, h.pot
            HAVING h.pot != total_distributed
        ''')
        mismatched_pots = cursor.fetchall()
        
        if mismatched_pots:
            print("\n⚠️ 发现奖金分配不匹配的手牌:")
            for hand_num, pot, distributed in mismatched_pots:
                print(f"  • 手牌#{hand_num}: 底池${pot}, 实际分配${distributed}")
        else:
            print("\n✅ 所有手牌的奖金分配都正确匹配底池")
        
        # 检查排名逻辑
        cursor.execute('''
            SELECT hand_id, COUNT(DISTINCT rank_position) as unique_ranks,
                   COUNT(*) as total_players
            FROM showdown_details 
            GROUP BY hand_id
            HAVING unique_ranks != total_players AND total_players > 1
        ''')
        ranking_issues = cursor.fetchall()
        
        if ranking_issues:
            print("\n⚠️ 发现排名逻辑问题的手牌:")
            for hand_id, unique_ranks, total_players in ranking_issues:
                print(f"  • 手牌ID{hand_id}: {total_players}个玩家但只有{unique_ranks}个不同排名")
        else:
            print("\n✅ 所有手牌的排名逻辑都正确")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析胜负计算失败: {e}")

def main():
    """主函数"""
    print("🔍 德州扑克游戏数据库检查工具")
    print("=" * 50)
    
    check_main_database()
    check_game_logs()
    analyze_win_loss_calculation()
    
    print("\n" + "=" * 50)
    print("✅ 数据库检查完成")
    
    # 提供一些建议
    print("\n💡 检查建议:")
    print("1. 如果缺少记录，请先进行游戏测试")
    print("2. 观察胜负计算是否符合德州扑克规则")
    print("3. 检查机器人vs真人的胜率分布是否合理")
    print("4. 验证筹码变化与游戏结果的一致性")

if __name__ == "__main__":
    main() 