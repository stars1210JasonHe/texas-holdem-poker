#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单调试测试脚本
"""

import sys
import os

def test_basic_imports():
    """测试基本导入"""
    print("[DEBUG] 开始测试基本导入...")
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        print("[DEBUG] 路径设置完成")
        
        from poker_engine.table import Table
        print("[DEBUG] Table 导入成功")
        
        from poker_engine.player import Player
        print("[DEBUG] Player 导入成功")
        
        return True
    except Exception as e:
        print(f"[ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("[DEBUG] 开始测试基本功能...")
    
    try:
        from poker_engine.table import Table
        from poker_engine.player import Player
        
        # 创建牌桌
        table = Table("test", "测试桌", max_players=6)
        print("[DEBUG] 牌桌创建成功")
        
        # 创建玩家
        player = Player("p1", "Alice", 1000)
        print("[DEBUG] 玩家创建成功")
        
        # 添加玩家
        result = table.add_player(player)
        print(f"[DEBUG] 添加玩家结果: {result}")
        
        print(f"[DEBUG] 桌子玩家数: {len(table.players)}")
        
        return True
    except Exception as e:
        print(f"[ERROR] 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== 简单调试测试 ===")
    
    # 测试导入
    import_ok = test_basic_imports()
    if not import_ok:
        print("[FAIL] 导入测试失败")
        return
    
    # 测试功能
    func_ok = test_basic_functionality()
    if not func_ok:
        print("[FAIL] 功能测试失败")
        return
        
    print("[SUCCESS] 基本测试通过")

if __name__ == "__main__":
    main() 