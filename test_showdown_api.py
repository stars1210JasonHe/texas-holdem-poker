#!/usr/bin/env python3
"""
测试摊牌记录API
"""

import requests
import json
import sqlite3
from datetime import datetime

def test_showdown_api():
    """测试摊牌记录API功能"""
    
    # 1. 首先创建一些测试数据
    print("🧪 创建测试数据...")
    
    # 连接数据库并插入测试数据
    conn = sqlite3.connect('game_logs.db')
    cursor = conn.cursor()
    
    # 插入测试手牌
    cursor.execute('''
        INSERT OR IGNORE INTO hands (id, table_id, hand_number, status, pot, winner_nickname, ended_at)
        VALUES (999, 'test_table', 1, 'completed', 100, 'TestPlayer', ?)
    ''', (datetime.now().isoformat(),))
    
    # 插入测试摊牌详情
    test_showdown_data = [
        (999, 'test_player_123', 'TestPlayer', 0, '[{"rank":"A","suit":"♠"},{"rank":"K","suit":"♠"}]', 
         'straight_flush', '皇家同花顺', 1, 'winner', 100, 1100),
        (999, 'bot_456', 'TestBot', 1, '[{"rank":"Q","suit":"♥"},{"rank":"J","suit":"♥"}]',
         'pair', '一对', 2, 'loser', 0, 900)
    ]
    
    for data in test_showdown_data:
        cursor.execute('''
            INSERT OR IGNORE INTO showdown_details 
            (hand_id, player_id, nickname, is_bot, hole_cards, hand_rank, hand_description, 
             rank_position, result, winnings, final_chips)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    conn.commit()
    conn.close()
    print("✅ 测试数据创建完成")
    
    # 2. 测试API端点
    base_url = 'http://localhost:5000'
    
    print("\n🔍 测试玩家摊牌统计API...")
    try:
        response = requests.get(f'{base_url}/api/player_showdown_summary/test_player_123')
        print(f"状态码: {response.status_code}")
        data = response.json()
        print("响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get('success'):
            print("✅ 摊牌统计API测试成功")
        else:
            print("❌ 摊牌统计API返回错误")
            
    except Exception as e:
        print(f"❌ 摊牌统计API测试失败: {e}")
    
    print("\n🔍 测试玩家摊牌历史API...")
    try:
        response = requests.get(f'{base_url}/api/player_showdown_history/test_player_123?limit=10')
        print(f"状态码: {response.status_code}")
        data = response.json()
        print("响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get('success'):
            print("✅ 摊牌历史API测试成功")
        else:
            print("❌ 摊牌历史API返回错误")
            
    except Exception as e:
        print(f"❌ 摊牌历史API测试失败: {e}")
    
    print("\n🧹 清理测试数据...")
    conn = sqlite3.connect('game_logs.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM showdown_details WHERE hand_id = 999')
    cursor.execute('DELETE FROM hands WHERE id = 999')
    conn.commit()
    conn.close()
    print("✅ 测试数据清理完成")

if __name__ == '__main__':
    test_showdown_api() 