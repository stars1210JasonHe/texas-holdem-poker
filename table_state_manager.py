#!/usr/bin/env python3
"""
牌桌状态管理器
管理牌桌状态变化，检测并处理自动进入下一轮的逻辑
"""

import time
import sqlite3
import json
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

class TableStateChange(Enum):
    """牌桌状态变化类型"""
    HAND_STARTED = "hand_started"
    HAND_ENDED = "hand_ended"
    STAGE_CHANGED = "stage_changed"
    PLAYER_ACTION = "player_action"
    GAME_FINISHED = "game_finished"
    WAITING_FOR_RESTART = "waiting_for_restart"
    RESTART_NEEDED = "restart_needed"

class TableStateManager:
    """牌桌状态管理器"""
    
    def __init__(self, db_path: str = "table_states.db"):
        self.db_path = db_path
        self.state_callbacks: Dict[str, List[Callable]] = {}
        self.monitoring_active = True
        self.check_interval = 2  # 每2秒检查一次状态
        
        self.init_database()
        self.start_monitoring()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 牌桌状态记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                state_type TEXT NOT NULL,
                game_stage TEXT,
                hand_number INTEGER,
                player_count INTEGER,
                active_player_count INTEGER,
                pot INTEGER DEFAULT 0,
                current_bet INTEGER DEFAULT 0,
                is_hand_complete BOOLEAN DEFAULT FALSE,
                needs_restart BOOLEAN DEFAULT FALSE,
                metadata TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_table_states_table_id ON table_states(table_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_table_states_timestamp ON table_states(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_table_states_needs_restart ON table_states(needs_restart)')
        
        # 自动重启检查点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restart_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id TEXT NOT NULL,
                hand_number INTEGER NOT NULL,
                finished_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                restart_scheduled_at DATETIME,
                restart_completed_at DATETIME,
                restart_attempts INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restart_checkpoints_table_id ON restart_checkpoints(table_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restart_checkpoints_status ON restart_checkpoints(status)')
        
        conn.commit()
        conn.close()
        print("📊 牌桌状态管理器数据库初始化完成")
    
    def record_state(self, table_id: str, state_type: TableStateChange, 
                    game_stage: str = None, hand_number: int = None,
                    player_count: int = 0, active_player_count: int = 0,
                    pot: int = 0, current_bet: int = 0, 
                    is_hand_complete: bool = False, metadata: Dict = None):
        """记录牌桌状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        needs_restart = self._check_if_needs_restart(
            state_type, game_stage, is_hand_complete, active_player_count
        )
        
        cursor.execute('''
            INSERT INTO table_states 
            (table_id, state_type, game_stage, hand_number, player_count, 
             active_player_count, pot, current_bet, is_hand_complete, 
             needs_restart, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            table_id, state_type.value, game_stage, hand_number, 
            player_count, active_player_count, pot, current_bet, 
            is_hand_complete, needs_restart, json.dumps(metadata or {})
        ))
        
        state_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📝 记录状态: {table_id} - {state_type.value} (ID: {state_id})")
        
        # 如果需要重启，创建重启检查点
        if needs_restart and state_type == TableStateChange.GAME_FINISHED:
            self._create_restart_checkpoint(table_id, hand_number or 0)
        
        # 触发状态变化回调
        self._trigger_callbacks(table_id, state_type, {
            'state_id': state_id,
            'game_stage': game_stage,
            'hand_number': hand_number,
            'needs_restart': needs_restart,
            'metadata': metadata or {}
        })
        
        return state_id
    
    def _check_if_needs_restart(self, state_type: TableStateChange, 
                               game_stage: str, is_hand_complete: bool, 
                               active_player_count: int) -> bool:
        """检查是否需要重启"""
        # 游戏完成且有足够玩家时需要重启
        if (state_type == TableStateChange.GAME_FINISHED and 
            is_hand_complete and active_player_count >= 2):
            return True
        
        # 游戏阶段是finished且手牌完成时需要重启
        if (game_stage == "finished" and is_hand_complete and 
            active_player_count >= 2):
            return True
        
        return False
    
    def _create_restart_checkpoint(self, table_id: str, hand_number: int):
        """创建重启检查点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否已经有待处理的重启检查点
        cursor.execute('''
            SELECT id FROM restart_checkpoints 
            WHERE table_id = ? AND hand_number = ? AND status = 'scheduled'
        ''', (table_id, hand_number))
        
        existing = cursor.fetchone()
        if existing:
            print(f"⚠️ 重启检查点已存在: {table_id} - 手牌#{hand_number}")
            conn.close()
            return existing[0]
        
        # 计算预定重启时间（3秒后）
        restart_time = datetime.now() + timedelta(seconds=3)
        
        cursor.execute('''
            INSERT INTO restart_checkpoints 
            (table_id, hand_number, restart_scheduled_at, status)
            VALUES (?, ?, ?, 'scheduled')
        ''', (table_id, hand_number, restart_time))
        
        checkpoint_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"⏰ 创建重启检查点: {table_id} - 手牌#{hand_number} (ID: {checkpoint_id})")
        return checkpoint_id
    
    def register_callback(self, table_id: str, callback: Callable):
        """注册状态变化回调"""
        if table_id not in self.state_callbacks:
            self.state_callbacks[table_id] = []
        self.state_callbacks[table_id].append(callback)
    
    def _trigger_callbacks(self, table_id: str, state_type: TableStateChange, data: Dict):
        """触发状态变化回调"""
        if table_id in self.state_callbacks:
            for callback in self.state_callbacks[table_id]:
                try:
                    callback(table_id, state_type, data)
                except Exception as e:
                    print(f"❌ 回调执行失败: {e}")
    
    def start_monitoring(self):
        """开始监控状态变化"""
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self._check_pending_restarts()
                    time.sleep(self.check_interval)
                except Exception as e:
                    print(f"❌ 监控循环错误: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print("🔄 状态监控器已启动")
    
    def _check_pending_restarts(self):
        """检查待处理的重启"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查找需要重启的检查点
        cursor.execute('''
            SELECT id, table_id, hand_number, restart_scheduled_at, restart_attempts
            FROM restart_checkpoints 
            WHERE status = 'scheduled' 
            AND restart_scheduled_at <= CURRENT_TIMESTAMP
            AND restart_attempts < 3
            ORDER BY restart_scheduled_at ASC
        ''')
        
        pending_restarts = cursor.fetchall()
        
        for checkpoint_id, table_id, hand_number, scheduled_at, attempts in pending_restarts:
            print(f"🔄 处理重启检查点: {table_id} - 手牌#{hand_number} (尝试#{attempts + 1})")
            
            # 更新尝试次数
            cursor.execute('''
                UPDATE restart_checkpoints 
                SET restart_attempts = restart_attempts + 1
                WHERE id = ?
            ''', (checkpoint_id,))
            
            # 触发重启回调
            self._trigger_callbacks(table_id, TableStateChange.RESTART_NEEDED, {
                'checkpoint_id': checkpoint_id,
                'hand_number': hand_number,
                'attempts': attempts + 1
            })
        
        conn.commit()
        conn.close()
    
    def mark_restart_completed(self, table_id: str, hand_number: int, success: bool = True):
        """标记重启完成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        status = 'completed' if success else 'failed'
        cursor.execute('''
            UPDATE restart_checkpoints 
            SET status = ?, restart_completed_at = CURRENT_TIMESTAMP
            WHERE table_id = ? AND hand_number = ? AND status = 'scheduled'
        ''', (status, table_id, hand_number))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 重启标记为{status}: {table_id} - 手牌#{hand_number}")
    
    def get_table_state_history(self, table_id: str, limit: int = 10) -> List[Dict]:
        """获取牌桌状态历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, state_type, game_stage, hand_number, 
                   player_count, active_player_count, pot, current_bet,
                   is_hand_complete, needs_restart, metadata
            FROM table_states 
            WHERE table_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (table_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'timestamp': row[0],
                'state_type': row[1],
                'game_stage': row[2],
                'hand_number': row[3],
                'player_count': row[4],
                'active_player_count': row[5],
                'pot': row[6],
                'current_bet': row[7],
                'is_hand_complete': bool(row[8]),
                'needs_restart': bool(row[9]),
                'metadata': json.loads(row[10]) if row[10] else {}
            })
        
        return history
    
    def get_pending_restarts(self) -> List[Dict]:
        """获取待处理的重启"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT table_id, hand_number, restart_scheduled_at, restart_attempts, status
            FROM restart_checkpoints 
            WHERE status IN ('scheduled', 'failed')
            ORDER BY restart_scheduled_at ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        restarts = []
        for row in rows:
            restarts.append({
                'table_id': row[0],
                'hand_number': row[1],
                'scheduled_at': row[2],
                'attempts': row[3],
                'status': row[4]
            })
        
        return restarts
    
    def cleanup_old_states(self, days: int = 7):
        """清理旧状态记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM table_states 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        
        cursor.execute('''
            DELETE FROM restart_checkpoints 
            WHERE finished_at < ? AND status = 'completed'
        ''', (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        print(f"🧹 清理了{days}天前的状态记录")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        print("⏹️ 状态监控器已停止")

# 全局状态管理器实例
table_state_manager = TableStateManager()

def record_table_state(table_id: str, state_type: TableStateChange, **kwargs):
    """记录牌桌状态的便捷函数"""
    return table_state_manager.record_state(table_id, state_type, **kwargs)

def register_restart_callback(table_id: str, callback: Callable):
    """注册重启回调的便捷函数"""
    table_state_manager.register_callback(table_id, callback)

def mark_restart_completed(table_id: str, hand_number: int, success: bool = True):
    """标记重启完成的便捷函数"""
    table_state_manager.mark_restart_completed(table_id, hand_number, success) 