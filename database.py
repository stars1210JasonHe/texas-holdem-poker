import sqlite3
import uuid
import time
import json
from typing import Optional, Dict, List, Any
import threading
from contextlib import contextmanager

class PokerDatabase:
    def __init__(self, db_path: str = 'poker_game.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    nickname TEXT NOT NULL,
                    chips INTEGER DEFAULT 1000,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    total_winnings INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    last_active REAL NOT NULL
                )
            ''')
            
            # 房间表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tables (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    small_blind INTEGER NOT NULL,
                    big_blind INTEGER NOT NULL,
                    max_players INTEGER NOT NULL,
                    initial_chips INTEGER NOT NULL,
                    game_mode TEXT NOT NULL DEFAULT 'blinds',
                    ante_percentage REAL DEFAULT 0.02,
                    game_stage TEXT NOT NULL DEFAULT 'waiting',
                    hand_number INTEGER DEFAULT 0,
                    pot INTEGER DEFAULT 0,
                    current_bet INTEGER DEFAULT 0,
                    current_player_id TEXT,
                    community_cards TEXT DEFAULT '[]',
                    created_by TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_activity REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES users (id),
                    FOREIGN KEY (current_player_id) REFERENCES users (id)
                )
            ''')
            
            # 房间玩家关系表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS table_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    chips INTEGER NOT NULL,
                    current_bet INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'waiting',
                    hole_cards TEXT DEFAULT '[]',
                    has_acted BOOLEAN DEFAULT 0,
                    is_bot BOOLEAN DEFAULT 0,
                    bot_level TEXT,
                    joined_at REAL NOT NULL,
                    FOREIGN KEY (table_id) REFERENCES tables (id),
                    FOREIGN KEY (player_id) REFERENCES users (id),
                    UNIQUE(table_id, player_id),
                    UNIQUE(table_id, position)
                )
            ''')
            
            conn.commit()
            print("数据库初始化完成")
    
    def create_user(self, nickname: str) -> str:
        """创建新用户，返回用户ID"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查昵称是否已存在
                cursor.execute('SELECT id FROM users WHERE nickname = ?', (nickname,))
                existing = cursor.fetchone()
                
                if existing:
                    # 如果昵称已存在，生成唯一昵称
                    base_nickname = nickname
                    counter = 1
                    while existing:
                        new_nickname = f"{base_nickname}_{counter}"
                        cursor.execute('SELECT id FROM users WHERE nickname = ?', (new_nickname,))
                        existing = cursor.fetchone()
                        if not existing:
                            nickname = new_nickname
                            break
                        counter += 1
                
                # 创建新用户
                user_id = str(uuid.uuid4())
                current_time = time.time()
                
                cursor.execute('''
                    INSERT INTO users (id, nickname, chips, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, nickname, 1000, current_time, current_time))
                
                conn.commit()
                print(f"创建新用户: {nickname} (ID: {user_id})")
                return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """根据ID获取用户信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_user_by_nickname(self, nickname: str) -> Optional[Dict]:
        """根据昵称获取用户信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE nickname = ?', (nickname,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def update_user_activity(self, user_id: str):
        """更新用户最后活动时间"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_active = ? WHERE id = ?
                ''', (time.time(), user_id))
                conn.commit()
    
    def create_table(self, title: str, created_by: str, small_blind: int = 10, 
                    big_blind: int = 20, max_players: int = 9, initial_chips: int = 1000,
                    game_mode: str = "blinds", ante_percentage: float = 0.02) -> str:
        """创建新房间"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                table_id = str(uuid.uuid4())
                current_time = time.time()
                
                cursor.execute('''
                    INSERT INTO tables (
                        id, title, small_blind, big_blind, max_players, initial_chips,
                        game_mode, ante_percentage, created_by, created_at, last_activity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (table_id, title, small_blind, big_blind, max_players, 
                      initial_chips, game_mode, ante_percentage, created_by, 
                      current_time, current_time))
                
                conn.commit()
                print(f"创建新房间: {title} (ID: {table_id}) by {created_by}, 模式: {game_mode}")
                return table_id
    
    def get_table(self, table_id: str) -> Optional[Dict]:
        """获取房间信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tables WHERE id = ? AND is_active = 1', (table_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all_active_tables(self) -> List[Dict]:
        """获取所有活跃房间"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, u.nickname as creator_nickname,
                       COUNT(tp.player_id) as player_count
                FROM tables t
                LEFT JOIN users u ON t.created_by = u.id
                LEFT JOIN table_players tp ON t.id = tp.table_id
                WHERE t.is_active = 1
                GROUP BY t.id
                ORDER BY t.created_at DESC
            ''')
            
            tables = []
            for row in cursor.fetchall():
                table_dict = dict(row)
                tables.append(table_dict)
            
            return tables
    
    def join_table(self, table_id: str, player_id: str, position: int = None) -> bool:
        """玩家加入房间"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查玩家是否已在房间中
                cursor.execute('''
                    SELECT id FROM table_players WHERE table_id = ? AND player_id = ?
                ''', (table_id, player_id))
                
                if cursor.fetchone():
                    print(f"玩家 {player_id} 已在房间 {table_id} 中")
                    return True
                
                # 获取房间信息
                table = self.get_table(table_id)
                if not table:
                    return False
                
                # 检查房间是否已满
                cursor.execute('''
                    SELECT COUNT(*) as count FROM table_players WHERE table_id = ?
                ''', (table_id,))
                
                current_players = cursor.fetchone()['count']
                if current_players >= table['max_players']:
                    return False
                
                # 找到空位
                if position is None:
                    cursor.execute('''
                        SELECT position FROM table_players WHERE table_id = ?
                        ORDER BY position
                    ''', (table_id,))
                    
                    occupied_positions = {row['position'] for row in cursor.fetchall()}
                    for i in range(table['max_players']):
                        if i not in occupied_positions:
                            position = i
                            break
                    
                    if position is None:
                        return False
                
                # 加入房间
                cursor.execute('''
                    INSERT INTO table_players (
                        table_id, player_id, position, chips, joined_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (table_id, player_id, position, table['initial_chips'], time.time()))
                
                # 更新房间活动时间
                cursor.execute('''
                    UPDATE tables SET last_activity = ? WHERE id = ?
                ''', (time.time(), table_id))
                
                conn.commit()
                print(f"玩家 {player_id} 加入房间 {table_id}，位置 {position}")
                return True
    
    def get_table_players(self, table_id: str) -> List[Dict]:
        """获取房间中的所有玩家"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tp.*, u.nickname
                FROM table_players tp
                LEFT JOIN users u ON tp.player_id = u.id
                WHERE tp.table_id = ?
                ORDER BY tp.position
            ''', (table_id,))
            
            players = []
            for row in cursor.fetchall():
                player_dict = dict(row)
                # 解析JSON字段
                player_dict['hole_cards'] = json.loads(player_dict['hole_cards'])
                
                # 判断是否是机器人（机器人名称包含特定关键词）
                nickname = player_dict['nickname'] or f"Bot_{player_dict['player_id'][:8]}"
                is_bot = any(keyword in nickname for keyword in ['新手', '菜鸟', '学徒', '小白', '萌新', '老司机', '高手', '大神', '专家', '老手', '大师', '传奇', '王者', '至尊', '无敌', 'Bot_'])
                
                player_dict['nickname'] = nickname
                player_dict['is_bot'] = is_bot
                    
                players.append(player_dict)
            
            return players
    
    def leave_table(self, table_id: str, player_id: str) -> bool:
        """玩家离开房间"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 从房间中移除玩家
                cursor.execute('''
                    DELETE FROM table_players WHERE table_id = ? AND player_id = ?
                ''', (table_id, player_id))
                
                # 检查房间是否还有玩家
                cursor.execute('''
                    SELECT COUNT(*) as count FROM table_players WHERE table_id = ?
                ''', (table_id,))
                
                remaining_players = cursor.fetchone()['count']
                
                # 如果房间为空，关闭房间
                if remaining_players == 0:
                    cursor.execute('''
                        UPDATE tables SET is_active = 0 WHERE id = ?
                    ''', (table_id,))
                    print(f"房间 {table_id} 已关闭（无玩家）")
                else:
                    # 更新房间活动时间
                    cursor.execute('''
                        UPDATE tables SET last_activity = ? WHERE id = ?
                    ''', (time.time(), table_id))
                
                conn.commit()
                print(f"玩家 {player_id} 离开房间 {table_id}，剩余玩家: {remaining_players}")
                return True
    
    def close_specific_table(self, table_id: str):
        """关闭指定的房间"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 关闭房间
                cursor.execute('''
                    UPDATE tables SET is_active = 0 WHERE id = ?
                ''', (table_id,))
                
                # 清理房间中的玩家记录
                cursor.execute('''
                    DELETE FROM table_players WHERE table_id = ?
                ''', (table_id,))
                
                conn.commit()
                print(f"关闭房间: {table_id}")
                return True

    def close_empty_tables(self):
        """关闭所有空房间和只有机器人的房间"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 查找没有玩家的活跃房间
                cursor.execute('''
                    SELECT t.id, t.title
                    FROM tables t
                    LEFT JOIN table_players tp ON t.id = tp.table_id
                    WHERE t.is_active = 1
                    GROUP BY t.id
                    HAVING COUNT(tp.player_id) = 0
                ''')
                
                empty_tables = cursor.fetchall()
                
                # 查找只有机器人的活跃房间 - 修复逻辑
                cursor.execute('''
                    SELECT DISTINCT t.id, t.title
                    FROM tables t
                    INNER JOIN table_players tp ON t.id = tp.table_id
                    LEFT JOIN users u ON tp.player_id = u.id
                    WHERE t.is_active = 1
                    GROUP BY t.id
                    HAVING COUNT(tp.player_id) > 0 AND COUNT(CASE WHEN u.nickname NOT LIKE '%新手%' 
                           AND u.nickname NOT LIKE '%菜鸟%' 
                           AND u.nickname NOT LIKE '%学徒%' 
                           AND u.nickname NOT LIKE '%小白%' 
                           AND u.nickname NOT LIKE '%萌新%' 
                           AND u.nickname NOT LIKE '%老司机%' 
                           AND u.nickname NOT LIKE '%高手%' 
                           AND u.nickname NOT LIKE '%大神%' 
                           AND u.nickname NOT LIKE '%专家%' 
                           AND u.nickname NOT LIKE '%老手%' 
                           AND u.nickname NOT LIKE '%大师%' 
                           AND u.nickname NOT LIKE '%传奇%' 
                           AND u.nickname NOT LIKE '%王者%' 
                           AND u.nickname NOT LIKE '%至尊%' 
                           AND u.nickname NOT LIKE '%无敌%' 
                           AND u.nickname NOT LIKE 'Bot_%' 
                           THEN 1 END) = 0
                ''')
                
                bot_only_tables = cursor.fetchall()
                
                # 合并需要关闭的房间
                tables_to_close = empty_tables + bot_only_tables
                
                for table in tables_to_close:
                    cursor.execute('''
                        UPDATE tables SET is_active = 0 WHERE id = ?
                    ''', (table['id'],))
                    
                    # 清理房间中的玩家记录
                    cursor.execute('''
                        DELETE FROM table_players WHERE table_id = ?
                    ''', (table['id'],))
                    
                    print(f"自动关闭房间: {table['title']} (ID: {table['id']})")
                
                if tables_to_close:
                    conn.commit()
                    print(f"共关闭 {len(tables_to_close)} 个房间（空房间: {len(empty_tables)}, 纯机器人房间: {len(bot_only_tables)}）")
                
                return len(tables_to_close)

# 全局数据库实例
db = PokerDatabase() 