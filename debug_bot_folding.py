#!/usr/bin/env python3
"""
调试机器人弃牌问题的专门工具
Debug tool for bot folding issue
"""

import sqlite3
import json
from typing import List, Dict, Any
from poker_engine.bot import Bot, BotLevel
from poker_engine.player import PlayerStatus, Player
from poker_engine.table import Table, GameStage
from poker_engine.card import Deck

def debug_database_bots():
    """调试数据库中的机器人数据"""
    print("🔍 调试数据库中的机器人数据...")
    
    try:
        conn = sqlite3.connect('poker_game.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(table_players)")
        columns = cursor.fetchall()
        print(f"\n📋 table_players 表结构:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']} (默认: {col['dflt_value']})")
        
        # 查找所有机器人记录
        cursor.execute("""
            SELECT tp.*, u.nickname as user_nickname
            FROM table_players tp
            LEFT JOIN users u ON tp.player_id = u.id
            WHERE tp.is_bot = 1 OR u.nickname LIKE '%机器人%' OR u.nickname LIKE '%新手%' OR u.nickname LIKE '%老司机%' OR u.nickname LIKE '%大师%'
        """)
        
        bot_records = cursor.fetchall()
        print(f"\n🤖 找到 {len(bot_records)} 条机器人记录:")
        
        for bot in bot_records:
            # 安全地访问字段 - sqlite3.Row对象使用字典式访问
            player_id = bot['player_id'] if 'player_id' in bot.keys() else 'unknown'
            nickname = bot['nickname'] if bot['nickname'] else (bot['user_nickname'] if 'user_nickname' in bot.keys() else 'Unknown')
            is_bot = bot['is_bot'] if 'is_bot' in bot.keys() else 0
            bot_level = bot['bot_level'] if 'bot_level' in bot.keys() else 'unknown'
            status = bot['status'] if 'status' in bot.keys() else 'unknown'
            chips = bot['chips'] if 'chips' in bot.keys() else 0
            current_bet = bot['current_bet'] if 'current_bet' in bot.keys() else 0
            has_acted = bot['has_acted'] if 'has_acted' in bot.keys() else 0
            
            print(f"  - ID: {player_id[:8]}... | 昵称: {nickname} | is_bot: {is_bot} | bot_level: {bot_level} | 状态: {status} | 筹码: {chips} | 投注: {current_bet} | 已行动: {has_acted}")
        
        # 分析机器人弃牌模式
        folded_bots = [bot for bot in bot_records if bot['status'] == 'folded']
        if folded_bots:
            print(f"\n❌ 发现 {len(folded_bots)} 个弃牌的机器人:")
            for bot in folded_bots:
                nickname = bot['nickname'] if bot['nickname'] else (bot['user_nickname'] if 'user_nickname' in bot.keys() else 'Unknown')
                current_bet = bot['current_bet'] if 'current_bet' in bot.keys() else 0
                print(f"  - {nickname}: 投注${current_bet}后弃牌")
                
                # 如果投注很少就弃牌，这是可疑的
                if current_bet <= 50:  # 假设初始筹码1000，投注50以下属于小额
                    print(f"    ⚠️ 可疑: 小额投注后弃牌")
        
        # 查找活跃房间
        cursor.execute("SELECT * FROM tables WHERE is_active = 1")
        active_tables = cursor.fetchall()
        print(f"\n🏠 活跃房间数: {len(active_tables)}")
        
        for table in active_tables:
            print(f"  - 房间: {table['title']} | 阶段: {table['game_stage']} | 手牌: {table['hand_number']} | 底池: {table['pot']} | 当前投注: {table['current_bet']}")
            
            # 查找该房间的玩家
            cursor.execute("SELECT * FROM table_players WHERE table_id = ? ORDER BY position", (table['id'],))
            players = cursor.fetchall()
            
            print(f"    房间玩家 ({len(players)}人):")
            for p in players:
                is_bot_flag = "🤖" if p['is_bot'] else "👤"
                print(f"      {is_bot_flag} 位置{p['position']}: {p['nickname']} | 状态: {p['status']} | 筹码: {p['chips']} | 投注: {p['current_bet']} | 已行动: {p['has_acted']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库调试失败: {e}")
        import traceback
        traceback.print_exc()

def simulate_bot_decision():
    """模拟机器人决策过程"""
    print("\n🧠 模拟机器人决策过程...")
    
    # 创建一个简单的测试场景
    from poker_engine.card import Card, Rank, Suit
    
    # 创建几个不同等级的机器人
    bots = [
        Bot("bot1", "新手1", 1000, BotLevel.BEGINNER),
        Bot("bot2", "老司机1", 1000, BotLevel.INTERMEDIATE), 
        Bot("bot3", "大师1", 1000, BotLevel.ADVANCED)
    ]
    
    # 给机器人发牌
    deck = Deck()
    deck.shuffle()
    
    for bot in bots:
        hole_cards = deck.deal_cards(2)
        bot.deal_hole_cards(hole_cards)
        print(f"🃏 {bot.nickname} 手牌: {hole_cards[0].rank.symbol}{hole_cards[0].suit.value} {hole_cards[1].rank.symbol}{hole_cards[1].suit.value}")
    
    # 模拟不同的游戏状态
    game_states = [
        # 翻前无投注
        {
            'community_cards': [],
            'current_bet': 0,
            'big_blind': 20,
            'pot_size': 30,
            'active_players': 3,
            'position': 'middle',
            'min_raise': 20
        },
        # 翻前有大盲注
        {
            'community_cards': [],
            'current_bet': 20,
            'big_blind': 20,
            'pot_size': 30,
            'active_players': 3,
            'position': 'middle',
            'min_raise': 40
        },
        # 翻后小投注
        {
            'community_cards': [
                Card(Rank.ACE, Suit.HEARTS),
                Card(Rank.KING, Suit.SPADES),
                Card(Rank.QUEEN, Suit.DIAMONDS)
            ],
            'current_bet': 30,
            'big_blind': 20,
            'pot_size': 90,
            'active_players': 3,
            'position': 'middle',
            'min_raise': 60
        }
    ]
    
    for i, game_state in enumerate(game_states):
        print(f"\n📊 游戏状态 {i+1}:")
        print(f"  - 公共牌: {len(game_state['community_cards'])}张")
        print(f"  - 当前投注: ${game_state['current_bet']}")
        print(f"  - 底池: ${game_state['pot_size']}")
        
        for bot in bots:
            # 重置机器人状态
            bot.current_bet = 0
            bot.has_acted = False
            bot.status = PlayerStatus.PLAYING
            
            try:
                action, amount = bot.decide_action(game_state)
                print(f"  🤖 {bot.nickname} ({bot.bot_level.value}): {action.value}" + (f" ${amount}" if amount > 0 else ""))
                
                # 检查是否总是弃牌
                if action.value == "fold" and game_state['current_bet'] == 0:
                    print(f"    ⚠️ 警告: {bot.nickname} 在无需投注时选择弃牌!")
                elif action.value == "fold" and game_state['current_bet'] <= bot.chips * 0.1:
                    print(f"    ⚠️ 可疑: {bot.nickname} 在小额投注时就弃牌 (投注${game_state['current_bet']}, 筹码${bot.chips})")
                    
            except Exception as e:
                print(f"  ❌ {bot.nickname} 决策失败: {e}")

def check_table_logic():
    """检查牌桌逻辑"""
    print("\n🎯 检查牌桌逻辑...")
    
    # 创建测试牌桌
    table = Table("test_table", "测试房间", game_mode="ante", ante_percentage=0.02)
    
    # 添加测试玩家
    human = Player("human1", "真人玩家", 1000)
    bot1 = Bot("bot1", "新手1", 1000, BotLevel.BEGINNER)
    bot2 = Bot("bot2", "老司机1", 1000, BotLevel.INTERMEDIATE)
    bot3 = Bot("bot3", "大师1", 1000, BotLevel.ADVANCED)
    
    table.add_player(human)
    table.add_player(bot1) 
    table.add_player(bot2)
    table.add_player(bot3)
    
    print(f"玩家数量: {len(table.players)}")
    for i, p in enumerate(table.players):
        print(f"  {i}: {p.nickname} ({'机器人' if p.is_bot else '真人'}) - 筹码: ${p.chips}")
    
    # 开始新手牌
    if table.start_new_hand():
        print(f"\n✅ 新手牌开始成功")
        print(f"  - 游戏阶段: {table.game_stage.value}")
        print(f"  - 底池: ${table.pot}")
        print(f"  - 当前投注: ${table.current_bet}")
        print(f"  - 庄家: {[p.nickname for p in table.players if p.is_dealer]}")
        
        # 检查玩家状态
        print(f"\n玩家状态:")
        for p in table.players:
            print(f"  - {p.nickname}: 状态={p.status.value}, 投注=${p.current_bet}, 已行动={p.has_acted}, 筹码=${p.chips}")
        
        # 找到当前行动玩家
        current_player = table.get_current_player()
        if current_player:
            print(f"\n👆 当前行动玩家: {current_player.nickname}")
            
            # 如果是机器人，测试其决策
            if isinstance(current_player, Bot):
                game_state = {
                    'community_cards': table.community_cards,
                    'current_bet': table.current_bet,
                    'big_blind': table.big_blind,
                    'pot_size': table.pot,
                    'active_players': len([p for p in table.players if p.status == PlayerStatus.PLAYING]),
                    'position': 'middle',
                    'min_raise': table.min_raise
                }
                
                try:
                    action, amount = current_player.decide_action(game_state)
                    print(f"🤖 {current_player.nickname} 决策: {action.value}" + (f" ${amount}" if amount > 0 else ""))
                    
                    # 分析决策合理性
                    if action.value == "fold" and table.current_bet == 0:
                        print("❌ 异常: 机器人在ante模式下无需投注时选择弃牌!")
                    elif action.value == "fold" and table.current_bet <= current_player.chips * 0.05:
                        print(f"⚠️ 疑问: 机器人在小额投注(${table.current_bet})时就弃牌")
                        
                except Exception as e:
                    print(f"❌ 机器人决策失败: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("❌ 没有找到当前行动玩家")
    else:
        print("❌ 新手牌开始失败")

def main():
    """主函数"""
    print("🔍 机器人弃牌问题调试工具")
    print("=" * 50)
    
    # 1. 调试数据库中的机器人数据
    debug_database_bots()
    
    # 2. 模拟机器人决策过程
    simulate_bot_decision()
    
    # 3. 检查牌桌逻辑
    check_table_logic()
    
    print("\n" + "=" * 50)
    print("✅ 调试完成")

if __name__ == "__main__":
    main() 