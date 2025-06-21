#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库清理脚本
清理所有测试数据，重置数据库到初始状态
"""

import sqlite3
import os
import sys

def cleanup_database(db_path):
    """清理指定数据库"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print(f"✅ {db_path} 没有表需要清理")
            conn.close()
            return True
        
        # 清理所有表的数据
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # 保留sqlite内部表
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"🧹 清理表: {table_name}")
        
        # 重置自增序列
        cursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {db_path} 清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 清理 {db_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    print("🧹 开始清理数据库...")
    print("=" * 50)
    
    # 数据库文件列表
    databases = [
        'poker_game.db',
        'players.db', 
        'game_logs.db',
        'table_states.db'
    ]
    
    success_count = 0
    
    for db_file in databases:
        print(f"\n🔍 处理数据库: {db_file}")
        if cleanup_database(db_file):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 清理完成: {success_count}/{len(databases)} 个数据库成功清理")
    
    if success_count == len(databases):
        print("✅ 所有数据库清理成功！")
        return True
    else:
        print("⚠️ 部分数据库清理失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 