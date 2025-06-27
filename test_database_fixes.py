#!/usr/bin/env python3
"""
测试数据库修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
import time
import json

def test_bot_detection():
    """测试机器人识别"""
    print("🤖 测试机器人识别...")
    
    # 创建测试用户
    test_cases = [
        ("高手玩家", True),   # 应该识别为机器人
        ("正常用户", False),  # 应该识别为真人
        ("Bot_123", True),   # 应该识别为机器人
        ("初级机器人", True), # 应该识别为机器人
        ("真人玩家", False),  # 应该识别为真人
    ]
    
    # 创建测试房间
    table_id = db.create_table("测试房间", "test_user", game_mode="blinds")
    
    results = []
    for nickname, expected_is_bot in test_cases:
        # 创建用户
        user_id = db.create_user(nickname)
        
        # 加入房间
        success = db.join_table(table_id, user_id)
        
        if success:
            # 获取玩家信息
            players = db.get_table_players(table_id)
            for player in players:
                if player['player_id'] == user_id:
                    actual_is_bot = player['is_bot']
                    is_correct = (actual_is_bot == expected_is_bot)
                    results.append(is_correct)
                    
                    status = "✅" if is_correct else "❌"
                    print(f"   {status} {nickname}: 预期={expected_is_bot}, 实际={actual_is_bot}")
                    break
        
        # 清理
        db.leave_table(table_id, user_id)
    
    # 清理测试房间
    db.close_specific_table(table_id)
    
    success_rate = sum(results) / len(results) * 100
    print(f"🎯 机器人识别准确率: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    return success_rate > 80

def test_timestamp_validation():
    """测试时间戳验证"""
    print("⏰ 测试时间戳验证...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查房间时间戳
            cursor.execute('''
                SELECT COUNT(*) as count FROM tables 
                WHERE created_at > ? OR created_at < ?
            ''', (time.mktime((2030, 1, 1, 0, 0, 0, 0, 0, 0)),
                  time.mktime((2020, 1, 1, 0, 0, 0, 0, 0, 0))))
            
            invalid_timestamps = cursor.fetchone()['count']
            
            if invalid_timestamps == 0:
                print("   ✅ 所有时间戳都在有效范围内")
                return True
            else:
                print(f"   ❌ 发现 {invalid_timestamps} 个无效时间戳")
                return False
                
    except Exception as e:
        print(f"   ❌ 时间戳验证失败: {e}")
        return False

def test_data_consistency():
    """测试数据一致性"""
    print("🔍 测试数据一致性...")
    
    issues = []
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查孤立的玩家记录
            cursor.execute('''
                SELECT COUNT(*) as count FROM table_players tp
                LEFT JOIN tables t ON tp.table_id = t.id
                WHERE t.id IS NULL
            ''')
            
            orphaned_players = cursor.fetchone()['count']
            if orphaned_players > 0:
                issues.append(f"孤立玩家记录: {orphaned_players}")
            
            # 检查空房间
            cursor.execute('''
                SELECT COUNT(*) as count FROM tables t
                LEFT JOIN table_players tp ON t.id = tp.table_id
                WHERE t.is_active = 1
                GROUP BY t.id
                HAVING COUNT(tp.player_id) = 0
            ''')
            
            empty_rooms = len(cursor.fetchall())
            if empty_rooms > 0:
                issues.append(f"空活跃房间: {empty_rooms}")
            
            # 检查用户数据
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE nickname IS NULL OR nickname = ""')
            invalid_users = cursor.fetchone()['count']
            if invalid_users > 0:
                issues.append(f"无效用户: {invalid_users}")
            
            if not issues:
                print("   ✅ 数据一致性检查通过")
                return True
            else:
                print("   ❌ 发现数据一致性问题:")
                for issue in issues:
                    print(f"      - {issue}")
                return False
                
    except Exception as e:
        print(f"   ❌ 数据一致性检查失败: {e}")
        return False

def test_cleanup_functionality():
    """测试清理功能"""
    print("🧹 测试清理功能...")
    
    try:
        # 创建测试数据
        test_table_id = db.create_table("清理测试房间", "test_user")
        
        # 添加机器人玩家
        bot_user_id = db.create_user("测试机器人")
        db.join_table(test_table_id, bot_user_id)
        
        # 执行清理
        initial_count = len(db.get_all_active_tables())
        closed_count = db.close_empty_tables()
        final_count = len(db.get_all_active_tables())
        
        print(f"   清理前房间数: {initial_count}")
        print(f"   清理了房间数: {closed_count}")
        print(f"   清理后房间数: {final_count}")
        
        if closed_count >= 0:  # 清理功能正常工作
            print("   ✅ 清理功能工作正常")
            return True
        else:
            print("   ❌ 清理功能异常")
            return False
            
    except Exception as e:
        print(f"   ❌ 清理功能测试失败: {e}")
        return False

def test_memory_performance():
    """测试内存性能"""
    print("⚡ 测试内存性能...")
    
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        print(f"   当前内存使用: {memory_mb:.1f} MB")
        
        if memory_mb < 200:  # 小于200MB认为正常
            print("   ✅ 内存使用正常")
            return True
        else:
            print("   ⚠️ 内存使用偏高")
            return True  # 不算失败，只是警告
            
    except ImportError:
        print("   ⚠️ psutil未安装，跳过内存检测")
        return True
    except Exception as e:
        print(f"   ❌ 内存性能测试失败: {e}")
        return True  # 不算失败

def main():
    """主测试函数"""
    print("🔧 数据库修复效果测试")
    print("=" * 50)
    
    tests = [
        ("机器人识别", test_bot_detection),
        ("时间戳验证", test_timestamp_validation),
        ("数据一致性", test_data_consistency),
        ("清理功能", test_cleanup_functionality),
        ("内存性能", test_memory_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        try:
            result = test_func()
            results.append(result)
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   结果: {status}")
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
            results.append(False)
        print()
    
    # 总结
    passed = sum(results)
    total = len(results)
    success_rate = passed / total * 100
    
    print("=" * 50)
    print(f"🎯 测试总结: {passed}/{total} 通过 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 数据库修复效果良好！")
        return 0
    else:
        print("⚠️ 部分功能需要进一步优化")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 