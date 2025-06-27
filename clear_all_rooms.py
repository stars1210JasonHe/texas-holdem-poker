#!/usr/bin/env python3
"""
清理所有房间数据的脚本
Clear all room data from the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
import sqlite3
import time

def clear_all_rooms():
    """清理数据库中的所有房间和玩家数据"""
    print("🧹 开始清理所有房间数据...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 查看清理前的数据统计
            cursor.execute('SELECT COUNT(*) as count FROM tables WHERE is_active = 1')
            active_tables_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM tables')
            total_tables_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM table_players')
            total_players_count = cursor.fetchone()['count']
            
            print(f"📊 清理前统计:")
            print(f"   - 活跃房间: {active_tables_count}")
            print(f"   - 总房间数: {total_tables_count}")
            print(f"   - 房间玩家记录: {total_players_count}")
            
            if total_tables_count == 0 and total_players_count == 0:
                print("✅ 数据库中没有房间数据，无需清理")
                return
            
            # 2. 获取所有房间信息（用于日志）
            cursor.execute('SELECT id, title, created_at FROM tables')
            all_tables = cursor.fetchall()
            
            # 3. 清理所有房间玩家记录
            print("🗑️  清理房间玩家记录...")
            cursor.execute('DELETE FROM table_players')
            player_records_deleted = cursor.rowcount
            print(f"   删除了 {player_records_deleted} 条玩家记录")
            
            # 4. 清理所有房间记录
            print("🗑️  清理房间记录...")
            cursor.execute('DELETE FROM tables')
            tables_deleted = cursor.rowcount
            print(f"   删除了 {tables_deleted} 个房间")
            
            # 5. 重置自增主键
            print("🔄 重置表结构...")
            cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("table_players")')
            
            # 6. 提交更改
            conn.commit()
            
            # 7. 验证清理结果
            cursor.execute('SELECT COUNT(*) as count FROM tables')
            remaining_tables = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM table_players')
            remaining_players = cursor.fetchone()['count']
            
            print(f"\n✅ 清理完成!")
            print(f"📊 清理后统计:")
            print(f"   - 剩余房间: {remaining_tables}")
            print(f"   - 剩余玩家记录: {remaining_players}")
            
            if remaining_tables == 0 and remaining_players == 0:
                print("🎉 所有房间数据已成功清理!")
            else:
                print("⚠️  警告: 仍有数据残留")
            
            # 8. 显示被清理的房间详情
            if all_tables:
                print(f"\n📋 已清理的房间列表:")
                for table in all_tables:
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(table['created_at']))
                    print(f"   - {table['title']} (ID: {table['id'][:8]}...) 创建于: {created_time}")
            
    except Exception as e:
        print(f"❌ 清理过程中出错: {e}")
        raise

def clear_inactive_rooms_only():
    """仅清理非活跃房间"""
    print("🧹 开始清理非活跃房间...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查找非活跃房间
            cursor.execute('SELECT * FROM tables WHERE is_active = 0')
            inactive_tables = cursor.fetchall()
            
            if not inactive_tables:
                print("✅ 没有找到非活跃房间")
                return
            
            print(f"找到 {len(inactive_tables)} 个非活跃房间")
            
            # 清理非活跃房间的玩家记录
            for table in inactive_tables:
                cursor.execute('DELETE FROM table_players WHERE table_id = ?', (table['id'],))
                print(f"   清理房间 {table['title']} 的玩家记录")
            
            # 删除非活跃房间
            cursor.execute('DELETE FROM tables WHERE is_active = 0')
            deleted_count = cursor.rowcount
            
            conn.commit()
            print(f"✅ 清理完成，删除了 {deleted_count} 个非活跃房间")
            
    except Exception as e:
        print(f"❌ 清理过程中出错: {e}")
        raise

def show_room_status():
    """显示当前房间状态"""
    print("📊 当前房间状态:")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 活跃房间
            cursor.execute('''
                SELECT t.*, COUNT(tp.player_id) as player_count
                FROM tables t
                LEFT JOIN table_players tp ON t.id = tp.table_id
                WHERE t.is_active = 1
                GROUP BY t.id
                ORDER BY t.created_at DESC
            ''')
            
            active_tables = cursor.fetchall()
            
            if active_tables:
                print(f"\n🟢 活跃房间 ({len(active_tables)} 个):")
                for table in active_tables:
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(table['created_at']))
                    last_activity = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(table['last_activity']))
                    print(f"   📋 {table['title']}")
                    print(f"      ID: {table['id']}")
                    print(f"      玩家: {table['player_count']}/{table['max_players']}")
                    print(f"      模式: {table['game_mode']}")
                    print(f"      阶段: {table['game_stage']}")
                    print(f"      创建: {created_time}")
                    print(f"      活动: {last_activity}")
                    print()
            else:
                print("🟢 没有活跃房间")
            
            # 非活跃房间
            cursor.execute('SELECT COUNT(*) as count FROM tables WHERE is_active = 0')
            inactive_count = cursor.fetchone()['count']
            
            if inactive_count > 0:
                print(f"🔴 非活跃房间: {inactive_count} 个")
            
            # 总统计
            cursor.execute('SELECT COUNT(*) as count FROM tables')
            total_tables = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM table_players')
            total_player_records = cursor.fetchone()['count']
            
            print(f"📈 总统计:")
            print(f"   - 房间总数: {total_tables}")
            print(f"   - 玩家记录: {total_player_records}")
            
    except Exception as e:
        print(f"❌ 查询状态时出错: {e}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            # 清理所有房间
            clear_all_rooms()
        elif command == "inactive":
            # 仅清理非活跃房间
            clear_inactive_rooms_only()
        elif command == "status":
            # 显示状态
            show_room_status()
        else:
            print("❌ 未知命令")
            print("用法:")
            print("  python clear_all_rooms.py all      - 清理所有房间")
            print("  python clear_all_rooms.py inactive - 仅清理非活跃房间")
            print("  python clear_all_rooms.py status   - 显示房间状态")
            return
    else:
        # 交互式菜单
        print("🎮 房间数据清理工具")
        print("=" * 50)
        
        # 先显示状态
        show_room_status()
        
        print("\n请选择操作:")
        print("1. 清理所有房间数据 (包括活跃房间)")
        print("2. 仅清理非活跃房间")
        print("3. 重新显示房间状态")
        print("4. 退出")
        
        while True:
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == "1":
                confirm = input("⚠️  确定要清理所有房间数据吗? 这将删除所有房间和玩家记录! (输入 'YES' 确认): ")
                if confirm == "YES":
                    clear_all_rooms()
                else:
                    print("❌ 操作已取消")
                break
                
            elif choice == "2":
                clear_inactive_rooms_only()
                break
                
            elif choice == "3":
                show_room_status()
                continue
                
            elif choice == "4":
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请输入 1-4")

if __name__ == "__main__":
    main() 