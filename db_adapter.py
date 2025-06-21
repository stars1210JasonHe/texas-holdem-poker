from database import PokerDatabase
from poker_engine.player import Player
from poker_engine.bot import Bot, BotLevel
import uuid
from typing import Optional

class DatabaseAdapter:
    def __init__(self, db_path: str = 'poker_game.db'):
        self.db = PokerDatabase(db_path)
    
    def create_or_get_player(self, nickname: str) -> Player:
        """创建或获取玩家，确保昵称唯一性"""
        # 首先尝试通过昵称查找现有玩家
        existing_player = self.db.get_player_by_nickname(nickname)
        
        if existing_player:
            # 玩家已存在，重新创建Player对象
            if existing_player['is_bot']:
                bot_level = getattr(BotLevel, existing_player['bot_level'].upper()) if existing_player['bot_level'] else BotLevel.BEGINNER
                player = Bot(existing_player['id'], existing_player['nickname'], existing_player['chips'], bot_level)
            else:
                player = Player(existing_player['id'], existing_player['nickname'], existing_player['chips'])
            
            player.session_id = existing_player['session_id']
            return player
        
        # 生成唯一昵称
        base_nickname = nickname
        counter = 1
        unique_nickname = base_nickname
        
        while self.db.get_player_by_nickname(unique_nickname):
            unique_nickname = f"{base_nickname}{counter}"
            counter += 1
        
        # 创建新玩家
        player_id = str(uuid.uuid4())
        player = Player(player_id, unique_nickname)
        
        # 保存到数据库
        self.db.create_player(player_id, unique_nickname)
        
        return player
    
    def create_bot(self, nickname: str, chips: int, bot_level: BotLevel) -> Bot:
        """创建机器人玩家"""
        player_id = str(uuid.uuid4())
        bot = Bot(player_id, nickname, chips, bot_level)
        
        # 保存到数据库
        self.db.create_player(player_id, nickname, is_bot=True, bot_level=bot_level.value.lower(), chips=chips)
        
        return bot
    
    def update_player_session(self, player_id: str, session_id: str = None):
        """更新玩家会话信息"""
        self.db.update_player_session(player_id, session_id)
    
    def find_player_table(self, player_id: str) -> Optional[str]:
        """查找玩家所在的牌桌"""
        return self.db.find_player_table(player_id)
    
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """通过ID获取玩家对象"""
        player_data = self.db.get_player(player_id)
        if not player_data:
            return None
        
        if player_data['is_bot']:
            bot_level = getattr(BotLevel, player_data['bot_level'].upper()) if player_data['bot_level'] else BotLevel.BEGINNER
            player = Bot(player_data['id'], player_data['nickname'], player_data['chips'], bot_level)
        else:
            player = Player(player_data['id'], player_data['nickname'], player_data['chips'])
        
        player.session_id = player_data['session_id']
        return player 