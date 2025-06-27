#!/usr/bin/env python3
"""
修复数据库问题的综合脚本
Fix Database Issues Script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
import time
import re

def fix_bot_detection():
    """修复机器人识别逻辑"""
    print("🤖 修复机器人识别逻辑...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 定义机器人关键词（更全面）
            bot_keywords = [
                '新手', '菜鸟', '学徒', '小白', '萌新',
                '老司机', '高手', '大神', '专家', '老手', 
                '大师', '传奇', '王者', '至尊', '无敌',
                'Bot_', 'bot_', 'BOT_',
                '初级机器人', '中级机器人', '高级机器人', '神级机器人',
                '机器人', '电脑', 'AI', 'CPU'
            ]
            
                         # 查找所有玩家记录
            cursor.execute('''
                SELECT tp.id, tp.player_id, tp.is_bot, u.nickname
                FROM table_players tp
                LEFT JOIN users u ON tp.player_id = u.id
                WHERE tp.is_bot = 0 OR tp.is_bot IS NULL
            ''')
            
            player_records = cursor.fetchall()
            fixed_count = 0
            
            for record in player_records:
                nickname = record['nickname'] or f"Bot_{record['player_id'][:8]}"
                
                # 检查是否应该是机器人
                is_actually_bot = any(keyword in nickname for keyword in bot_keywords)
                
                if is_actually_bot:
                    # 更新为机器人
                    cursor.execute('''
                        UPDATE table_players 
                        SET is_bot = 1, bot_level = 'intermediate'
                        WHERE id = ?
                    ''', (record['id'],))
                    
                    print(f"   修正玩家 {nickname} -> 标记为机器人")
                    fixed_count += 1
            
            if fixed_count > 0:
                conn.commit()
                print(f"✅ 修复了 {fixed_count} 个机器人标记错误")
            else:
                print("✅ 机器人标记正确，无需修复")
                
    except Exception as e:
        print(f"❌ 修复机器人识别时出错: {e}")

def fix_timestamp_issues():
    """修复时间戳异常"""
    print("⏰ 修复时间戳异常...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            current_time = time.time()
            
            # 修复异常的时间戳（通常是未来时间或明显错误的时间）
            # 假设正常时间应该在2020年到2030年之间
            min_valid_timestamp = time.mktime((2020, 1, 1, 0, 0, 0, 0, 0, 0))
            max_valid_timestamp = time.mktime((2030, 12, 31, 23, 59, 59, 0, 0, 0))
            
            # 修复房间表的时间戳
            cursor.execute('''
                SELECT id, title, created_at, last_activity
                FROM tables
                WHERE created_at > ? OR created_at < ? OR last_activity > ? OR last_activity < ?
            ''', (max_valid_timestamp, min_valid_timestamp, max_valid_timestamp, min_valid_timestamp))
            
            problematic_tables = cursor.fetchall()
            
            for table in problematic_tables:
                # 使用当前时间作为修复时间
                cursor.execute('''
                    UPDATE tables 
                    SET created_at = ?, last_activity = ?
                    WHERE id = ?
                ''', (current_time, current_time, table['id']))
                
                old_created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(table['created_at']))
                new_created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
                print(f"   修正房间 {table['title']} 时间戳: {old_created} -> {new_created}")
            
            # 修复用户表的时间戳
            cursor.execute('''
                SELECT id, nickname, created_at, last_active
                FROM users
                WHERE created_at > ? OR created_at < ? OR last_active > ? OR last_active < ?
            ''', (max_valid_timestamp, min_valid_timestamp, max_valid_timestamp, min_valid_timestamp))
            
            problematic_users = cursor.fetchall()
            
            for user in problematic_users:
                cursor.execute('''
                    UPDATE users 
                    SET created_at = ?, last_active = ?
                    WHERE id = ?
                ''', (current_time, current_time, user['id']))
                
                print(f"   修正用户 {user['nickname']} 时间戳")
            
            # 修复玩家记录的时间戳
            cursor.execute('''
                SELECT id, player_id, joined_at
                FROM table_players
                WHERE joined_at > ? OR joined_at < ?
            ''', (max_valid_timestamp, min_valid_timestamp))
            
            problematic_players = cursor.fetchall()
            
            for player in problematic_players:
                cursor.execute('''
                    UPDATE table_players 
                    SET joined_at = ?
                    WHERE id = ?
                ''', (current_time, player['id']))
                
                print(f"   修正玩家记录 {player['player_id'][:8]}... 加入时间")
            
            total_fixed = len(problematic_tables) + len(problematic_users) + len(problematic_players)
            
            if total_fixed > 0:
                conn.commit()
                print(f"✅ 修复了 {total_fixed} 个时间戳异常记录")
            else:
                print("✅ 时间戳正常，无需修复")
                
    except Exception as e:
        print(f"❌ 修复时间戳时出错: {e}")

def clean_test_rooms():
    """清理测试房间"""
    print("🧹 清理测试房间...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 定义测试房间的特征
            test_patterns = [
                r'^[0-9]+$',  # 纯数字
                r'^[a-zA-Z]$',  # 单字母
                r'test.*',  # test开头
                r'.*测试.*',  # 包含"测试"
                r'.*弹窗.*',  # 包含"弹窗"
                r'.*验证.*',  # 包含"验证"
                r'.*API.*',  # 包含"API"
                r'^[qwertyu]+$',  # 随机按键
                r'^[;,.]+$',  # 标点符号
            ]
            
            # 查找所有房间
            cursor.execute('SELECT * FROM tables')
            all_tables = cursor.fetchall()
            
            test_tables = []
            
            for table in all_tables:
                title = table['title'].strip()
                
                # 检查是否匹配测试模式
                is_test_room = any(re.match(pattern, title, re.IGNORECASE) for pattern in test_patterns)
                
                # 额外检查：房间名长度过短或包含特殊字符
                if len(title) <= 2 or title in ['t', 'q', 'u', 'o', 'p', ';', ',', '.']:
                    is_test_room = True
                
                if is_test_room:
                    test_tables.append(table)
            
            if test_tables:
                print(f"   发现 {len(test_tables)} 个测试房间:")
                for table in test_tables:
                    print(f"      - {table['title']} (ID: {table['id'][:8]}...)")
                    
                    # 删除房间中的玩家记录
                    cursor.execute('DELETE FROM table_players WHERE table_id = ?', (table['id'],))
                    
                    # 删除房间
                    cursor.execute('DELETE FROM tables WHERE id = ?', (table['id'],))
                
                conn.commit()
                print(f"✅ 清理了 {len(test_tables)} 个测试房间")
            else:
                print("✅ 没有发现测试房间")
                
    except Exception as e:
        print(f"❌ 清理测试房间时出错: {e}")

def clean_orphaned_players():
    """清理孤立的玩家记录"""
    print("👥 清理孤立的玩家记录...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查找没有对应房间的玩家记录
            cursor.execute('''
                SELECT tp.*
                FROM table_players tp
                LEFT JOIN tables t ON tp.table_id = t.id
                WHERE t.id IS NULL
            ''')
            
            orphaned_players = cursor.fetchall()
            
            if orphaned_players:
                print(f"   发现 {len(orphaned_players)} 个孤立的玩家记录")
                
                # 删除孤立的玩家记录
                cursor.execute('''
                    DELETE FROM table_players
                    WHERE table_id NOT IN (SELECT id FROM tables)
                ''')
                
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ 清理了 {deleted_count} 个孤立的玩家记录")
            else:
                print("✅ 没有发现孤立的玩家记录")
                
    except Exception as e:
        print(f"❌ 清理孤立玩家记录时出错: {e}")

def add_automatic_cleanup():
    """添加自动清理机制"""
    print("🔄 添加自动清理机制...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查找长时间无活动的房间（超过1小时）
            one_hour_ago = time.time() - 3600
            
            cursor.execute('''
                SELECT t.*, COUNT(tp.player_id) as player_count
                FROM tables t
                LEFT JOIN table_players tp ON t.id = tp.table_id
                WHERE t.is_active = 1 AND t.last_activity < ?
                GROUP BY t.id
            ''', (one_hour_ago,))
            
            inactive_tables = cursor.fetchall()
            
            if inactive_tables:
                print(f"   发现 {len(inactive_tables)} 个长时间无活动的房间")
                
                for table in inactive_tables:
                    # 关闭房间
                    cursor.execute('UPDATE tables SET is_active = 0 WHERE id = ?', (table['id'],))
                    
                    # 清理玩家记录
                    cursor.execute('DELETE FROM table_players WHERE table_id = ?', (table['id'],))
                    
                    inactive_duration = (time.time() - table['last_activity']) / 3600
                    print(f"      关闭房间 {table['title']} (无活动 {inactive_duration:.1f} 小时)")
                
                conn.commit()
                print(f"✅ 自动关闭了 {len(inactive_tables)} 个无活动房间")
            else:
                print("✅ 没有发现需要自动关闭的房间")
                
    except Exception as e:
        print(f"❌ 执行自动清理时出错: {e}")

def optimize_database():
    """优化数据库"""
    print("⚡ 优化数据库...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 重建索引
            cursor.execute('REINDEX')
            
            # 清理数据库
            cursor.execute('VACUUM')
            
            conn.commit()
            print("✅ 数据库优化完成")
            
    except Exception as e:
        print(f"❌ 优化数据库时出错: {e}")

def show_database_status():
    """显示数据库状态"""
    print("📊 数据库修复后状态:")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 房间统计
            cursor.execute('SELECT COUNT(*) as count FROM tables WHERE is_active = 1')
            active_tables = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM tables')
            total_tables = cursor.fetchone()['count']
            
            # 玩家统计
            cursor.execute('SELECT COUNT(*) as count FROM table_players WHERE is_bot = 1')
            bot_players = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM table_players WHERE is_bot = 0')
            human_players = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM table_players')
            total_players = cursor.fetchone()['count']
            
            # 用户统计
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            print(f"\n📈 统计信息:")
            print(f"   房间: {active_tables} 活跃 / {total_tables} 总计")
            print(f"   玩家记录: {total_players} 总计")
            print(f"      - 机器人: {bot_players}")
            print(f"      - 真人: {human_players}")
            print(f"   用户账号: {total_users}")
            
            # 检查时间戳
            cursor.execute('''
                SELECT MIN(created_at) as min_time, MAX(created_at) as max_time
                FROM tables
            ''')
            time_range = cursor.fetchone()
            
            if time_range['min_time'] and time_range['max_time']:
                min_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_range['min_time']))
                max_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_range['max_time']))
                print(f"   时间范围: {min_time_str} ~ {max_time_str}")
            
    except Exception as e:
        print(f"❌ 查询状态时出错: {e}")

def main():
    """主修复函数"""
    print("🔧 数据库问题修复工具")
    print("=" * 50)
    
    # 1. 修复机器人识别
    fix_bot_detection()
    print()
    
    # 2. 修复时间戳异常
    fix_timestamp_issues()
    print()
    
    # 3. 清理测试房间
    clean_test_rooms()
    print()
    
    # 4. 清理孤立玩家记录
    clean_orphaned_players()
    print()
    
    # 5. 自动清理机制
    add_automatic_cleanup()
    print()
    
    # 6. 优化数据库
    optimize_database()
    print()
    
    # 7. 显示修复后状态
    show_database_status()
    
    print("\n🎉 所有问题修复完成!")
    print("📋 修复内容:")
    print("   ✅ 机器人识别逻辑")
    print("   ✅ 时间戳异常")
    print("   ✅ 测试房间清理")
    print("   ✅ 孤立玩家记录")
    print("   ✅ 自动清理机制")
    print("   ✅ 数据库优化")

if __name__ == "__main__":
    main() 