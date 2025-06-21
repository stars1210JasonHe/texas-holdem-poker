"""
德州扑克游戏主应用
Texas Hold'em Poker Game Main Application
"""

import uuid
import time
import re
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import eventlet
import threading
import sqlite3
from datetime import datetime

from poker_engine import Player, Table, Bot, BotLevel
from poker_engine.player import PlayerAction, PlayerStatus
from poker_engine.table import GameStage
from database import db
from game_logger import (
    log_table_created, log_hand_started, log_hand_ended, 
    log_player_action, log_stage_change, game_logger
)
from table_state_manager import (
    record_table_state, register_restart_callback, mark_restart_completed,
    TableStateChange
)
from player_persistence import update_player_chips, get_player


# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'poker_game_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', 
                  logger=False, engineio_logger=False, ping_timeout=30, ping_interval=25)

# 全局状态管理
tables: Dict[str, Table] = {}
players: Dict[str, Player] = {}
player_sessions: Dict[str, str] = {}  # session_id -> player_id
session_tables: Dict[str, str] = {}   # session_id -> table_id

# 游戏日志状态管理
table_sessions: Dict[str, int] = {}   # table_id -> session_id (日志会话ID)
current_hands: Dict[str, int] = {}    # table_id -> hand_id (当前手牌ID)

# 添加下一轮开始相关的数据结构
next_round_votes = {}  # {table_id: {player_id: True/False}}

def process_bot_actions(table_id: str):
    """处理机器人动作"""
    try:
        if table_id not in tables:
            return
        
        table = tables[table_id]
        
        # 🔧 修复：如果游戏已结束，不处理机器人动作
        if table.game_stage == GameStage.FINISHED:
            print(f"🛑 游戏已结束，停止机器人处理 (table_id: {table_id})")
            return None
        
        result = table.process_bot_actions()
        
        # 调试：打印机器人处理结果
        print(f"🤖 机器人处理结果: {result}")
        print(f"🤖 游戏阶段: {table.game_stage.value}")
        
        # 检查是否手牌结束
        if result and result.get('hand_complete'):
            print(f"🏆 机器人处理导致手牌结束")
            winner = result.get('winner')
            winners = [winner] if winner else []
            print(f"🏆 准备调用handle_hand_end，winner: {winner}, winners: {winners}")
            handle_hand_end(table_id, winners)
            return result
        else:
            print(f"🔍 手牌未结束，继续游戏流程")
        
        # 广播更新后的桌面状态
        socketio.emit('table_updated', table.get_table_state(), room=table_id)
        
        # 检查是否轮到人类玩家行动
        current_player = table.get_current_player()
        if current_player and not current_player.is_bot:
            # 找到该玩家的session并发送行动通知
            player_session = None
            for session_id, session_info in player_sessions.items():
                if session_info['player_id'] == current_player.id:
                    player_session = session_id
                    break
            
            if player_session:
                print(f"🎯 轮到人类玩家 {current_player.nickname} 行动")
                socketio.emit('your_turn', {
                    'current_bet': table.current_bet,
                    'min_bet': table.big_blind,
                    'pot': table.pot,
                    'your_bet': current_player.current_bet,
                    'your_chips': current_player.chips
                }, room=player_session)
        
        return result
    except Exception as e:
        print(f"❌ 处理机器人动作失败: {e}")
        return None

def handle_restart_needed(table_id: str, state_type, data: Dict):
    """处理需要重启的回调"""
    try:
        print(f"🔄 收到重启信号: {table_id} - {data}")
        
        # 检查房间是否还存在
        if table_id not in tables:
            print(f"❌ 房间 {table_id} 不存在，跳过重启")
            return
        
        table = tables[table_id]
        hand_number = data.get('hand_number', 0)
        
        print(f"🔍 检查房间状态: table_id={table_id}, 房间存在=True")
        print(f"🔍 房间玩家数量: {len(table.players)}")
        
        # 检查玩家状态
        active_players = [p for p in table.players if p.status != PlayerStatus.DISCONNECTED]
        print(f"🔍 当前玩家状态:")
        for player in table.players:
            player_type = "🤖" if player.is_bot else "👤"
            print(f"  {player_type} {player.nickname}: 状态={player.status.value}, 筹码=${player.chips}")
        
        if len(active_players) < 2:
            print(f"❌ 玩家数量不足，无法重启 (需要>=2，当前={len(active_players)})")
            mark_restart_completed(table_id, hand_number, success=False)
            return
        
        print("✅ 房间检查通过，开始新手牌...")
        
        # 开始新手牌
        success = table.start_new_hand()
        if not success:
            print(f"❌ 新手牌创建失败")
            mark_restart_completed(table_id, hand_number, success=False)
            return
        
        print(f"✅ 新手牌创建成功，手牌编号: {table.hand_number}")
        
        # 记录手牌开始到日志数据库
        if table_id in table_sessions:
            session_id_log = table_sessions[table_id]
            hand_id = log_hand_started(session_id_log, table.hand_number, table_id)
            current_hands[table_id] = hand_id
        
        # 记录状态变化
        record_table_state(
            table_id, TableStateChange.HAND_STARTED,
            game_stage=table.game_stage.value,
            hand_number=table.hand_number,
            player_count=len(table.players),
            active_player_count=len(active_players),
            pot=table.pot,
            current_bet=table.current_bet
        )
        
        # 发送手牌给人类玩家
        for player in table.players:
            if not player.is_bot and player.status == PlayerStatus.PLAYING:
                player_session = None
                for session_id, player_id in player_sessions.items():
                    if player_id == player.id:
                        player_session = session_id
                        break
                
                if player_session and len(player.hole_cards) == 2:
                    print(f"📤 发送手牌给玩家: {player.nickname}")
                    socketio.emit('your_cards', {
                        'hole_cards': [card.to_dict() for card in player.hole_cards]
                    }, room=player_session)
        
        # 广播新手牌开始
        print(f"📡 广播新手牌开始事件...")
        socketio.emit('hand_started', {
            'table': table.get_table_state()
        }, room=table_id)
        
        print(f"房间 {table.title} 自动开始新手牌")
        
        # 后台显示所有玩家的手牌
        print("=" * 50)
        print(f"🃏 新一轮玩家手牌信息 (手牌#{table.hand_number})：")
        for i, player in enumerate(table.players):
            if player.status == PlayerStatus.PLAYING and len(player.hole_cards) == 2:
                card1 = player.hole_cards[0]
                card2 = player.hole_cards[1]
                card1_str = f"{card1.rank.symbol}{card1.suit.value}"
                card2_str = f"{card2.rank.symbol}{card2.suit.value}"
                player_type = "🤖" if player.is_bot else "👤"
                print(f"  {player_type} {player.nickname}: {card1_str} {card2_str} (筹码: ${player.chips}, 状态: {player.status.value})")
        print(f"🎯 游戏阶段: {table.game_stage.value}")
        print(f"💰 当前底池: ${table.pot}")
        print(f"💵 当前投注: ${table.current_bet}")
        print("=" * 50)
        
        # 启动机器人处理
        def start_bot_processing():
            time.sleep(1)  # 给玩家一点时间接收状态
            process_bot_actions(table_id)
        
        threading.Thread(target=start_bot_processing, daemon=True).start()
        
        # 标记重启完成
        mark_restart_completed(table_id, hand_number, success=True)
        
        # 🔧 新增：在重启前保存所有玩家筹码到数据库
        print(f"💾 保存玩家筹码到数据库...")
        for player in table.players:
            if not player.is_bot:  # 只保存人类玩家
                try:
                    update_player_chips(player.id, player.chips)
                    print(f"💰 保存玩家筹码: {player.nickname} -> ${player.chips}")
                except Exception as e:
                    print(f"❌ 保存筹码失败: {player.nickname} - {e}")
        
        # 如果房间没有人类玩家了，关闭房间
        human_players = [p for p in table.players if not p.is_bot]
        if len(human_players) == 0:
            print(f"房间 {table_id} 已关闭（无人类玩家）")
            if table_id in tables:
                del tables[table_id]
            if table_id in next_round_votes:
                del next_round_votes[table_id]
        
    except Exception as e:
        print(f"❌ 处理重启失败: {e}")
        hand_number = data.get('hand_number', 0)
        mark_restart_completed(table_id, hand_number, success=False)


def validate_nickname(nickname: str) -> bool:
    """验证昵称格式"""
    if not nickname or len(nickname.strip()) == 0:
        return False
    
    nickname = nickname.strip()
    if len(nickname) > 20 or len(nickname) < 1:
        return False
    
    # 允许中文、英文、数字和基本符号
    pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9_\-\s]+$'
    return bool(re.match(pattern, nickname))


# REST API 路由

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/lobby')
def lobby():
    """大厅页面"""
    return render_template('lobby.html')


@app.route('/table/<table_id>')
def table_page(table_id):
    """牌桌页面"""
    if table_id not in tables:
        return "牌桌不存在", 404
    return render_template('table.html', table_id=table_id)


@app.route('/api/join', methods=['POST'])
def join_game():
    """加入游戏 - 创建或获取用户"""
    try:
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        
        if not validate_nickname(nickname):
            return jsonify({
                'success': False,
                'message': '昵称无效。请使用2-20个字符，仅包含字母、数字、中文和基本符号。'
            }), 400
        
        # 检查是否已存在该昵称的用户
        existing_user = db.get_user_by_nickname(nickname)
        
        if existing_user:
            # 用户已存在，返回现有用户信息
            player_id = existing_user['id']
            print(f"用户 {nickname} 已存在，ID: {player_id}")
        else:
            # 创建新用户
            player_id = db.create_user(nickname)
            print(f"创建新用户 {nickname}，ID: {player_id}")
        
        # 更新用户活动时间
        db.update_user_activity(player_id)
        
        # 获取最新用户信息
        user_data = db.get_user(player_id)
        
        # 创建Player对象（用于游戏逻辑）
        if player_id not in players:
            player = Player(player_id, nickname, user_data['chips'])
            players[player_id] = player
        
        return jsonify({
            'success': True,
            'player': {
                'id': player_id,
                'nickname': nickname,
                'chips': user_data['chips']
            }
        })
        
    except Exception as e:
        print(f"加入游戏失败: {e}")
        return jsonify({
            'success': False,
            'message': '服务器错误，请稍后重试'
        }), 500


@app.route('/api/tables', methods=['GET'])
def get_tables():
    """获取所有活跃房间列表"""
    try:
        # 从数据库获取活跃房间
        db_tables = db.get_all_active_tables()
        
        # 转换为前端需要的格式
        tables_data = []
        for table_data in db_tables:
            # 同步内存中的Table对象
            table_id = table_data['id']
            if table_id not in tables:
                # 如果内存中没有，创建一个新的Table对象
                table = Table(
                    table_id=table_id,
                    title=table_data['title'],
                    small_blind=table_data['small_blind'],
                    big_blind=table_data['big_blind'],
                    max_players=table_data['max_players'],
                    initial_chips=table_data['initial_chips']
                )
                tables[table_id] = table
            
            # 构建返回数据
            table_info = {
                'id': table_id,
                'title': table_data['title'],
                'small_blind': table_data['small_blind'],
                'big_blind': table_data['big_blind'],
                'max_players': table_data['max_players'],
                'current_players': table_data['player_count'],
                'game_stage': table_data['game_stage'],
                'created_by': table_data['creator_nickname'],
                'created_at': table_data['created_at']
            }
            tables_data.append(table_info)
        
        return jsonify({
            'success': True,
            'tables': tables_data
        })
        
    except Exception as e:
        print(f"获取房间列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取房间列表失败'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取服务器统计信息"""
    try:
        # 获取在线玩家数（通过session管理）
        online_players = len(player_sessions)
        print(f"🔍 当前在线玩家数: {online_players}, 会话: {list(player_sessions.keys())}")
        
        # 获取活跃房间数 - 使用内存中的tables而不是数据库
        active_tables = len(tables)
        
        # 计算总游戏中玩家数
        total_players_in_game = 0
        for table in tables.values():
            human_players = [p for p in table.players if not p.is_bot]
            total_players_in_game += len(human_players)
        
        stats = {
            'online_players': online_players,
            'active_tables': active_tables,
            'players_in_game': total_players_in_game
        }
        
        print(f"📊 统计信息: {stats}")
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取统计信息失败'
        }), 500


# WebSocket 事件处理

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'session_id': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """处理玩家断线"""
    try:
        session_id = request.sid
        
        if session_id in player_sessions:
            player_info = player_sessions[session_id]
            nickname = player_info['nickname']
            player_id = player_info['player_id']
            
            print(f"玩家 {nickname} 断线")
            
            # 立即清理会话，避免重复计数
            del player_sessions[session_id]
            print(f"会话 {session_id} 立即清理完成")
            
            # 从session_tables中清理
            if session_id in session_tables:
                del session_tables[session_id]
            
            # 广播更新统计信息
            online_players = len(player_sessions)
            active_tables = len(tables)
            socketio.emit('stats_update', {
                'online_players': online_players,
                'active_tables': active_tables
            })
            
            # 设置90秒后移除玩家（如果没有重新连接）
            def remove_player_delayed():
                import time
                time.sleep(90)
                
                # 检查玩家是否重新连接
                reconnected = False
                for sid, session in player_sessions.items():
                    if session['player_id'] == player_id:
                        reconnected = True
                        break
                
                if not reconnected:
                    print(f"90秒后移除未重连的玩家 {nickname}")
                    
                    # 从所有房间中移除玩家
                    tables_to_check = []
                    for table_id, table in list(tables.items()):
                        players_to_remove = [p for p in table.players if p.id == player_id]
                        for player in players_to_remove:
                            table.remove_player(player.id)
                            db.leave_table(table_id, player.id)  # 从数据库移除
                            socketio.emit('player_left', {
                                'nickname': player.nickname,
                                'remaining_players': len(table.players)
                            }, room=table_id)
                            tables_to_check.append(table_id)
                    
                    # 检查并清理空房间
                    for table_id in set(tables_to_check):
                        check_and_cleanup_table(table_id)
                        
                    # 再次广播更新统计信息
                    online_players = len(player_sessions)
                    active_tables = len(tables)
                    socketio.emit('stats_update', {
                        'online_players': online_players,
                        'active_tables': active_tables
                    })
            
            socketio.start_background_task(remove_player_delayed)
            
            print(f"玩家 {nickname} 断线，会话已清理，等待重连...")
    except Exception as e:
        print(f"处理断线错误: {e}")


@socketio.on('register_player')
def handle_register_player(data):
    """处理玩家注册"""
    try:
        nickname = data.get('nickname', '').strip()
        if not nickname:
            emit('error', {'message': '昵称不能为空'})
            return
        
        # 检查是否已经有相同昵称的玩家在线
        existing_player = None
        for table_id, table in tables.items():
            for player in table.players:
                if player.nickname == nickname and not player.is_bot:
                    existing_player = player
                    break
            if existing_player:
                break
        
        # 清理当前会话的重复会话（基于昵称）
        old_sessions_to_remove = []
        for sid, session_info in player_sessions.items():
            if session_info['nickname'] == nickname and sid != request.sid:
                old_sessions_to_remove.append(sid)
        
        if old_sessions_to_remove:
            print(f"发现玩家 {nickname} 的重复会话，清理旧会话")
            for old_sid in old_sessions_to_remove:
                print(f"移除旧会话: {old_sid}")
                if old_sid in player_sessions:
                    del player_sessions[old_sid]
                if old_sid in session_tables:
                    del session_tables[old_sid]
                # 断开旧连接
                try:
                    socketio.disconnect(old_sid)
                except Exception as e:
                    print(f"断开旧连接失败: {e}")
            
            print(f"玩家 {nickname} 旧会话已清理")
        
        # 创建或获取玩家数据
        player_data = db.get_user_by_nickname(nickname)
        if not player_data:
            # 使用database.py的create_user方法创建用户
            player_id = db.create_user(nickname)
            player_data = db.get_user(player_id)
        
        if not player_data:
            emit('error', {'message': '玩家创建失败'})
            return
        
        # 注册会话
        session_id = request.sid
        player_sessions[session_id] = {
            'player_id': player_data['id'],
            'nickname': nickname,
            'timestamp': datetime.now()
        }
        
        print(f"玩家会话注册成功: {nickname} (ID: {player_data['id']}, Session: {session_id})")
        
        emit('register_response', {
            'success': True,
            'nickname': nickname,
            'player_id': player_data['id'],
            'chips': player_data.get('chips', 1000)
        })
        
        # 广播更新统计信息
        online_players = len(player_sessions)
        active_tables = len(tables)
        socketio.emit('stats_update', {
            'online_players': online_players,
            'active_tables': active_tables
        })
        
    except Exception as e:
        print(f"玩家注册错误: {e}")
        emit('error', {'message': '注册失败，请重试'})


@socketio.on('create_table')
def handle_create_table(data):
    """创建牌桌"""
    try:
        session_id = request.sid
        if session_id not in player_sessions:
            emit('error', {'message': '请先登录'})
            return
        
        player_info = player_sessions[session_id]
        player_id = player_info['player_id']
        nickname = player_info['nickname']
        
        # 获取创建参数
        title = data.get('name', data.get('title', '新牌桌')).strip()
        small_blind = int(data.get('small_blind', 10))
        big_blind = int(data.get('big_blind', 20))
        max_players = int(data.get('max_players', 9))
        initial_chips = int(data.get('initial_chips', 1000))
        bots_config = data.get('bots', {})
        
        # 验证参数
        if not title or len(title) > 50:
            emit('error', {'message': '房间名称无效'})
            return
        
        if small_blind <= 0 or big_blind <= small_blind or max_players < 2 or max_players > 9:
            emit('error', {'message': '游戏参数无效'})
            return
        
        # 生成房间ID
        import uuid
        table_id = str(uuid.uuid4())
        
        # 创建房间到数据库
        try:
            db_table_id = db.create_table(
                title=title,
                created_by=player_id,
                small_blind=small_blind,
                big_blind=big_blind,
                max_players=max_players,
                initial_chips=initial_chips
            )
            if db_table_id:
                table_id = db_table_id
        except Exception as e:
            print(f"数据库创建房间失败: {e}")
            emit('error', {'message': '创建房间失败，请重试'})
            return
        
        # 创建内存中的Table对象
        table = Table(
            table_id=table_id,
            title=title,
            small_blind=small_blind,
            big_blind=big_blind,
            max_players=max_players,
            initial_chips=initial_chips
        )
        
        tables[table_id] = table
        
        # 创建Player对象
        player_data = db.get_user(player_id)
        if not player_data:
            emit('error', {'message': '玩家数据获取失败'})
            return
        
        player = Player(player_id, nickname, player_data.get('chips', initial_chips))
        
        # 创建者自动加入房间
        if table.add_player(player) and db.join_table(table_id, player_id):
            join_room(table_id)
            session_tables[session_id] = table_id
            
            # 添加机器人
            bots_added = 0
            total_bots_requested = 0
            if bots_config:
                from poker_engine.bot import Bot, BotLevel
                import uuid
                
                bot_names = {
                    'beginner': ['新手', '菜鸟', '学徒', '小白', '萌新'],
                    'intermediate': ['老司机', '高手', '大神', '专家', '老手'],
                    'advanced': ['大师', '传奇', '王者', '至尊', '无敌']
                }
                
                for level, count in bots_config.items():
                    if level in bot_names and count > 0:
                        total_bots_requested += count
                        available_names = bot_names[level]
                        
                        for i in range(count):
                            if len(table.players) >= max_players:
                                break
                                
                            bot_name = f"{available_names[i % len(available_names)]}{bots_added + 1}"
                            bot_id = str(uuid.uuid4())
                            
                            try:
                                level_enum = BotLevel[level.upper()]
                            except KeyError:
                                level_enum = BotLevel.BEGINNER
                            
                            bot = Bot(bot_id, bot_name, initial_chips, level_enum)
                            
                            if table.add_player(bot):
                                # 在users表中创建机器人记录
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    current_time = time.time()
                                    cursor.execute('''
                                        INSERT OR IGNORE INTO users (id, nickname, chips, created_at, last_active)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (bot_id, bot_name, initial_chips, current_time, current_time))
                                    conn.commit()
                                
                                # 将机器人也保存到数据库
                                db.join_table(table_id, bot_id)
                                bots_added += 1
                                print(f"机器人 {bot_name} ({level}) 加入房间 {title}")
                            else:
                                print(f"添加机器人 {bot_name} 失败")
            
            emit('room_created', {
                'success': True,
                'table_id': table_id,
                'message': f'房间 "{title}" 创建成功！添加了 {bots_added}/{total_bots_requested} 个机器人'
            })
            
            # 同时发送table_joined事件
            table_state = table.get_table_state()
            print(f"🔍 发送table_joined事件，玩家数: {len(table_state.get('players', []))}")
            for p in table_state.get('players', []):
                print(f"  - {p.get('nickname')} (is_bot: {p.get('is_bot')})")
            
            emit('table_joined', {
                'success': True,
                'table_id': table_id,
                'table': table_state
            })
            
            # 广播新房间创建给所有在大厅的用户
            socketio.emit('lobby_update', {
                'type': 'new_table',
                'table': {
                    'id': table_id,
                    'title': title,
                    'small_blind': small_blind,
                    'big_blind': big_blind,
                    'max_players': max_players,
                    'current_players': len([p for p in table.players if not p.is_bot]),
                    'game_stage': 'waiting',
                    'created_by': nickname
                }
            })
            
            # 广播更新统计信息
            online_players = len(player_sessions)
            active_tables = len(tables)
            socketio.emit('stats_update', {
                'online_players': online_players,
                'active_tables': active_tables
            })
            
            print(f"玩家 {player.nickname} 创建并加入房间 {title} (ID: {table_id}), 添加了 {bots_added} 个机器人")
        else:
            emit('error', {'message': '加入房间失败'})
            
    except Exception as e:
        print(f"创建房间失败: {e}")
        emit('error', {'message': f'创建房间失败: {str(e)}'})


@socketio.on('join_table')
def handle_join_table(data):
    """加入牌桌"""
    try:
        session_id = request.sid
        table_id = data.get('table_id')
        
        if session_id not in player_sessions:
            emit('error', {'message': '请先登录'})
            return
        
        if not table_id:
            emit('error', {'message': '房间ID无效'})
            return
        
        # 检查房间是否存在，先从内存检查，再从数据库检查
        table = tables.get(table_id)
        if not table:
            # 如果内存中没有，尝试从数据库加载
            db_table = db.get_table(table_id)
            if not db_table:
                emit('error', {'message': '房间不存在'})
                return
            
            # 重新创建内存中的Table对象
            table = Table(
                table_id=table_id,
                title=db_table['title'],
                small_blind=db_table['small_blind'],
                big_blind=db_table['big_blind'],
                max_players=db_table['max_players'],
                initial_chips=db_table['initial_chips']
            )
            tables[table_id] = table
            print(f"从数据库重新加载房间: {table.title}")
        
        player_id = player_sessions[session_id]['player_id']
        nickname = player_sessions[session_id]['nickname']
        
        # 动态获取或创建玩家对象
        player = players.get(player_id)
        if not player:
            # 从数据库获取玩家信息
            player_data = db.get_user(player_id)
            if not player_data:
                emit('error', {'message': '玩家数据不存在'})
                return
            
            # 创建玩家对象
            player = Player(player_id, nickname, player_data['chips'])
            players[player_id] = player
            print(f"动态创建玩家对象: {nickname} (ID: {player_id})")
        
        # 检查玩家是否已在房间中（重连情况）
        db_players = db.get_table_players(table_id)
        existing_player = None
        
        for db_player in db_players:
            if db_player['player_id'] == player_id:
                existing_player = db_player
                break
        
        if existing_player:
            # 玩家重连
            session_tables[session_id] = table_id
            join_room(table_id)
            
            # 重新加载所有玩家到内存（包括机器人）
            for db_player in db_players:
                table_player = table.get_player(db_player['player_id'])
                if not table_player:
                    # 内存中没有，需要重新添加
                    if db_player.get('is_bot', False):
                        # 重新创建机器人
                        from poker_engine.bot import Bot, BotLevel
                        try:
                            # 从nickname推断机器人等级
                            if '新手' in db_player['nickname'] or '菜鸟' in db_player['nickname'] or '学徒' in db_player['nickname']:
                                level = BotLevel.BEGINNER
                            elif '老司机' in db_player['nickname'] or '高手' in db_player['nickname'] or '大神' in db_player['nickname']:
                                level = BotLevel.INTERMEDIATE
                            elif '大师' in db_player['nickname'] or '传奇' in db_player['nickname'] or '王者' in db_player['nickname']:
                                level = BotLevel.ADVANCED
                            else:
                                level = BotLevel.BEGINNER
                            
                            bot = Bot(db_player['player_id'], db_player['nickname'], db_player['chips'], level)
                            bot.current_bet = db_player['current_bet']
                            bot.status = PlayerStatus[db_player['status'].upper()]
                            table.add_player_at_position(bot, db_player['position'])
                        except Exception as e:
                            print(f"重新创建机器人失败: {e}")
                    else:
                        # 重新创建人类玩家
                        if db_player['player_id'] == player_id:
                            player.chips = db_player['chips']
                            player.current_bet = db_player['current_bet']
                            player.status = PlayerStatus[db_player['status'].upper()]
                            table.add_player_at_position(player, db_player['position'])
            
            emit('table_joined', {
                'success': True,
                'table_id': table_id,
                'table': table.get_table_state(player_id),
                'reconnected': True
            })
            
            # 如果游戏正在进行且玩家有手牌，发送手牌
            table_player = table.get_player(player_id)
            if table_player and table.game_stage != GameStage.WAITING and len(table_player.hole_cards) == 2:
                emit('your_cards', {
                    'hole_cards': [card.to_dict() for card in table_player.hole_cards]
                })
                print(f"玩家 {player.nickname} 重连，发送手牌: {[f'{card.rank.symbol}{card.suit.value}' for card in table_player.hole_cards]}")
            
            print(f"玩家 {player.nickname} 重连到房间 {table.title}")
            return
        
        # 新玩家加入
        if db.join_table(table_id, player_id):
            # 内存中也要加入
            if table.add_player(player):
                session_tables[session_id] = table_id
                join_room(table_id)
                
                emit('table_joined', {
                    'success': True,
                    'table_id': table_id,
                    'table': table.get_table_state(player_id),
                    'reconnected': False
                })
                
                # 向房间内其他玩家广播新玩家加入
                emit('player_joined', {
                    'player': {
                        'id': player.id,
                        'nickname': player.nickname,
                        'chips': player.chips,
                        'position': table.get_player_position(player_id)
                    }
                }, room=table_id, include_self=False)
                
                print(f"玩家 {player.nickname} 加入房间 {table.title}")
            else:
                emit('error', {'message': '房间已满或加入失败'})
        else:
            emit('error', {'message': '无法加入房间'})
            
    except Exception as e:
        print(f"加入房间失败: {e}")
        emit('error', {'message': f'加入房间失败: {str(e)}'})


@socketio.on('get_table_state')
def handle_get_table_state(data):
    """手动获取牌桌状态 - 用于处理连接问题时的备用方案"""
    try:
        session_id = request.sid
        table_id = data.get('table_id')
        
        if session_id not in player_sessions:
            emit('error', {'message': '请先登录'})
            return
        
        if not table_id:
            emit('error', {'message': '房间ID无效'})
            return
        
        # 检查房间是否存在
        table = tables.get(table_id)
        if not table:
            emit('error', {'message': '房间不存在'})
            return
        
        player_id = player_sessions[session_id]['player_id']
        
        # 确保玩家在正确的Socket.IO房间中
        join_room(table_id)
        session_tables[session_id] = table_id
        
        # 发送牌桌状态
        table_state = table.get_table_state(player_id)
        print(f"🔄 手动发送牌桌状态给 {session_id}，玩家数: {len(table_state.get('players', []))}")
        for p in table_state.get('players', []):
            print(f"  - {p.get('nickname')} (is_bot: {p.get('is_bot')})")
        
        emit('table_joined', {
            'success': True,
            'table_id': table_id,
            'table': table_state,
            'reconnected': True  # 标记为重连，避免重复通知
        })
        
        # 如果玩家有手牌，也发送手牌信息
        table_player = table.get_player(player_id)
        if table_player and table.game_stage != GameStage.WAITING and len(table_player.hole_cards) == 2:
            emit('your_cards', {
                'hole_cards': [card.to_dict() for card in table_player.hole_cards]
            })
        
    except Exception as e:
        print(f"❌ 获取牌桌状态异常: {e}")
        traceback.print_exc()
        emit('error', {'message': '服务器错误'})


@socketio.on('add_bot')
def handle_add_bot(data):
    """添加机器人到牌桌"""
    try:
        session_id = request.sid
        if session_id not in player_sessions:
            emit('error', {'message': '请先登录'})
            return
        
        # 查找玩家所在的房间
        table_id = None
        for tid, table in tables.items():
            for player in table.players:
                if player.id == player_sessions[session_id]['player_id']:
                    table_id = tid
                    break
            if table_id:
                break
        
        if not table_id or table_id not in tables:
            emit('error', {'message': '您不在任何房间中'})
            return
        
        table = tables[table_id]
        
        # 检查房间是否已满
        if len(table.players) >= table.max_players:
            emit('error', {'message': '房间已满'})
            return
        
        # 获取机器人等级
        from poker_engine.bot import Bot, BotLevel
        import uuid
        
        level_str = data.get('level', 'beginner')
        try:
            level_enum = BotLevel[level_str.upper()]
        except KeyError:
            level_enum = BotLevel.BEGINNER
        
        # 生成机器人名称
        bot_names = {
            'beginner': ['新手', '菜鸟', '学徒', '小白', '萌新'],
            'intermediate': ['老司机', '高手', '大神', '专家', '老手'],
            'advanced': ['大师', '传奇', '王者', '至尊', '无敌']
        }
        
        available_names = bot_names.get(level_str, ['机器人'])
        existing_bots = [p for p in table.players if p.is_bot]
        bot_name = f"{available_names[len(existing_bots) % len(available_names)]}{len(existing_bots) + 1}"
        
        # 创建机器人
        bot_id = str(uuid.uuid4())
        bot = Bot(bot_id, bot_name, 1000, level_enum)
        
        # 添加到房间
        if table.add_player(bot):
            emit('bot_added', {
                'success': True,
                'bot': bot.to_dict(),
                'message': f'机器人 {bot_name} ({level_str}) 已加入房间'
            }, room=table_id)
            
            print(f"机器人 {bot_name} ({level_str}) 加入房间 {table.title}")
        else:
            emit('error', {'message': '添加机器人失败'})
            
    except Exception as e:
        print(f"添加机器人失败: {e}")
        emit('error', {'message': f'添加机器人失败: {str(e)}'})


@socketio.on('start_hand')
def handle_start_hand():
    """开始手牌"""
    try:
        session_id = request.sid
        if session_id not in player_sessions:
            emit('error', {'message': '请先登录'})
            return
        
        # 查找玩家所在的房间
        table_id = None
        player_id = player_sessions[session_id]['player_id']
        
        for tid, table in tables.items():
            for player in table.players:
                if player.id == player_id:
                    table_id = tid
                    break
            if table_id:
                break
        
        if not table_id or table_id not in tables:
            emit('error', {'message': '您不在任何房间中'})
            return
        
        table = tables[table_id]
        
        # 检查玩家数量
        if len(table.players) < 2:
            emit('error', {'message': '至少需要2名玩家才能开始游戏'})
            return
        
        # 检查游戏状态
        if table.game_stage != GameStage.WAITING:
            emit('error', {'message': '游戏已在进行中'})
            return
        
        # 开始新手牌
        if table.start_new_hand():
            # 广播手牌开始事件
            socketio.emit('hand_started', {
                'table': table.get_table_state(),
                'message': '新手牌开始！'
            }, room=table_id)
            
            # 发送玩家手牌给各自的玩家
            for player in table.players:
                if not player.is_bot and player.hole_cards:
                    player_session = None
                    for sid, session in player_sessions.items():
                        if session['player_id'] == player.id:
                            player_session = sid
                            break
                    
                    if player_session:
                        print(f"📤 发送手牌给玩家 {player.nickname}: {[f'{card.rank.symbol}{card.suit.value}' for card in player.hole_cards]}")
                        socketio.emit('your_cards', {
                            'hole_cards': [card.to_dict() for card in player.hole_cards]
                        }, room=player_session)
            
            print(f"房间 {table.title} 开始新手牌")
            
            # 后台显示所有玩家的手牌
            print("=" * 50)
            print(f"🃏 新一轮玩家手牌信息 (手牌#{table.hand_number})：")
            for i, player in enumerate(table.players):
                if player.status == PlayerStatus.PLAYING and len(player.hole_cards) == 2:
                    card1 = player.hole_cards[0]
                    card2 = player.hole_cards[1]
                    card1_str = f"{card1.rank.symbol}{card1.suit.value}"
                    card2_str = f"{card2.rank.symbol}{card2.suit.value}"
                    player_type = "🤖" if player.is_bot else "👤"
                    print(f"  {player_type} {player.nickname}: {card1_str} {card2_str} (筹码: ${player.chips}, 状态: {player.status.value})")
            print(f"🎯 游戏阶段: {table.game_stage.value}")
            print(f"💰 当前底池: ${table.pot}")
            print(f"💵 当前投注: ${table.current_bet}")
            print("=" * 50)
            
            # 开始机器人处理和行动通知
            socketio.start_background_task(process_bot_actions_delayed, table_id)
        else:
            emit('error', {'message': '开始游戏失败'})
            
    except Exception as e:
        print(f"开始手牌失败: {e}")
        emit('error', {'message': f'开始游戏失败: {str(e)}'})


@socketio.on('player_action')
def handle_player_action(data):
    """处理玩家动作"""
    try:
        session_id = request.sid
        
        if session_id not in player_sessions:
            emit('error', {'message': '请先登录'})
            return
        
        if session_id not in session_tables:
            emit('error', {'message': '请先加入房间'})
            return
        
        player_id = player_sessions[session_id]['player_id']
        table_id = session_tables[session_id]
        table = tables.get(table_id)
        
        if not table:
            emit('error', {'message': '房间不存在'})
            return
        
        action_str = data.get('action')
        amount = data.get('amount', 0)
        
        if not action_str:
            emit('error', {'message': '无效的动作'})
            return
        
        # 转换字符串动作为枚举
        from poker_engine.player import PlayerAction
        action_map = {
            'fold': PlayerAction.FOLD,
            'check': PlayerAction.CHECK,
            'call': PlayerAction.CALL,
            'bet': PlayerAction.BET,
            'raise': PlayerAction.RAISE,
            'all_in': PlayerAction.ALL_IN
        }
        
        action = action_map.get(action_str.lower())
        if not action:
            emit('error', {'message': f'无效的动作: {action_str}'})
            return
        
        # 执行玩家动作
        result = table.process_player_action(player_id, action, amount)
        
        # 记录玩家动作到日志数据库
        if table_id in current_hands and result.get('success'):
            hand_id = current_hands[table_id]
            player = table.get_player(player_id)
            if player:
                log_player_action(
                    hand_id, player_id, player.nickname, action_str, 
                    amount, table.game_stage.value, 
                    player.chips + result.get('amount', 0),  # chips_before
                    player.chips  # chips_after
                )
        
        # 调试：打印result的完整内容
        print(f"🔍 玩家动作处理结果: {result}")
        
        if result.get('success'):
            # 发送动作处理结果
            emit('action_processed', {
                'table': table.get_table_state(),
                'action': result.get('action'),
                'player_id': player_id,
                'amount': result.get('amount', 0),
                'description': result.get('description', '')
            }, room=table_id)
            
            # 检查手牌是否结束
            hand_ended = False
            winners = []
            
            if result.get('hand_complete'):
                print(f"🏆 玩家动作直接导致手牌结束")
                hand_ended = True
                # 注意：牌桌引擎返回的是'winner'而不是'winners'
                winner = result.get('winner')
                winners = [winner] if winner else []
            else:
                # 手牌未结束，处理机器人动作
                try:
                    print(f"👤 {result.get('description', '')} 完成，开始处理机器人动作...")
                    bot_result = process_bot_actions(table_id)  # 使用修改后的函数
                    print(f"🔍 机器人处理结果: {bot_result}")
                    
                    # 检查机器人动作后是否手牌结束
                    if bot_result and bot_result.get('hand_complete'):
                        print(f"🏆 机器人动作导致手牌结束")
                        hand_ended = True
                        winners = [bot_result.get('winner')] if bot_result.get('winner') else []
                    # 注意：process_bot_actions已经会发送状态更新和行动通知了
                except Exception as bot_error:
                    print(f"处理机器人动作时出错: {bot_error}")
                    # 即使机器人处理出错，也要发送状态更新
                    emit('table_updated', table.get_table_state(), room=table_id)
            
            # 统一处理手牌结束后的状态记录
            if hand_ended:
                print(f"🏆 手牌结束，调用handle_hand_end函数")
                handle_hand_end(table_id, winners)
            
    except Exception as e:
        print(f"处理玩家动作失败: {e}")
        emit('error', {'message': f'动作执行失败: {str(e)}'})


@socketio.on('leave_table')
def handle_leave_table():
    """离开牌桌"""
    try:
        session_id = request.sid
        
        if session_id not in player_sessions:
            return
        
        if session_id not in session_tables:
            return
        
        player_id = player_sessions[session_id]['player_id']
        table_id = session_tables[session_id]
        table = tables.get(table_id)
        
        if table:
            # 从牌桌移除玩家
            table.remove_player(player_id)
            
            # 从数据库移除玩家
            db.leave_table(table_id, player_id)
            
            # 向房间内其他玩家广播玩家离开
            emit('player_left', {
                'player_id': player_id
            }, room=table_id, include_self=False)
            
            print(f"玩家 {player_id} 离开房间 {table.title}")
            
            # 立即检查是否需要清理房间
            check_and_cleanup_table(table_id)
        
        # 清理会话
        if session_id in session_tables:
            del session_tables[session_id]
        
        leave_room(table_id)
        
        # 广播大厅更新
        socketio.emit('lobby_update')
        
        # 获取统计信息并广播
        online_players = len(player_sessions)
        active_tables = len(tables)
        socketio.emit('stats_update', {
            'online_players': online_players,
            'active_tables': active_tables
        })
        
    except Exception as e:
        print(f"离开房间失败: {e}")


def check_and_cleanup_table(table_id):
    """立即检查并清理单个房间"""
    try:
        if table_id not in tables:
            return
        
        table = tables[table_id]
        human_players = [p for p in table.players if not p.is_bot]
        
        # 如果房间没有人类玩家，立即关闭
        if len(human_players) == 0:
            print(f"房间 {table.title} 没有人类玩家，立即关闭")
            
            # 从数据库关闭房间
            db.close_specific_table(table_id)
            
            # 从内存中删除房间
            if table_id in tables:
                del tables[table_id]
                print(f"从内存中清理房间: {table_id}")
            
            # 清理投票记录
            if table_id in next_round_votes:
                del next_round_votes[table_id]
                print(f"清理房间 {table_id} 的投票记录")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"检查清理房间 {table_id} 时出错: {e}")
        return False

def cleanup_empty_tables():
    """定期清理空房间和只有机器人的房间"""
    try:
        closed_count = db.close_empty_tables()
        
        # 同时清理内存中的房间
        tables_to_remove = []
        for table_id, table in tables.items():
            human_players = [p for p in table.players if not p.is_bot]
            if len(table.players) == 0 or len(human_players) == 0:
                tables_to_remove.append(table_id)
        
        for table_id in tables_to_remove:
            if table_id in tables:
                del tables[table_id]
                print(f"从内存中清理房间: {table_id}")
        
        if closed_count > 0:
            print(f"定期清理：关闭了 {closed_count} 个房间")
    except Exception as e:
        print(f"清理房间时出错: {e}")


@socketio.on('vote_next_round')
def handle_vote_next_round(data):
    """处理下一轮投票"""
    try:
        session_id = request.sid
        if session_id not in player_sessions:
            emit('error', {'message': '未找到玩家会话'})
            return
        
        table_id = data.get('table_id')
        print(f"🗳️ 投票请求: table_id={table_id}, 当前房间数={len(tables)}")
        print(f"🗳️ 当前房间列表: {list(tables.keys())}")
        
        # 检查房间是否存在
        if not table_id:
            print(f"❌ 无效的房间ID")
            emit('error', {'message': '无效的房间ID'})
            return
            
        if table_id not in tables:
            print(f"❌ 房间 {table_id} 不存在")
            # 尝试从数据库恢复房间信息或提示用户
            emit('error', {'message': '房间不存在，请重新创建房间'})
            return
        
        table = tables[table_id]
        player_id = player_sessions[session_id]['player_id']
        
        # 检查玩家是否在房间中
        player = None
        for p in table.players:
            if p.id == player_id:
                player = p
                break
        
        if not player:
            emit('error', {'message': '玩家不在房间中'})
            return
        
        # 初始化投票记录
        if table_id not in next_round_votes:
            next_round_votes[table_id] = {}
        
        # 记录投票
        next_round_votes[table_id][player_id] = True
        print(f"玩家 {player.nickname} 投票开始下一轮")
        
        # 机器人自动投票
        for p in table.players:
            if p.is_bot and p.id not in next_round_votes[table_id]:
                next_round_votes[table_id][p.id] = True
                print(f"机器人 {p.nickname} 自动投票开始下一轮")
        
        # 检查是否所有人类玩家都投票了
        all_voted = True
        human_players = [p for p in table.players if not p.is_bot]
        print(f"🗳️ 投票检查: 人类玩家数={len(human_players)}, 当前投票数={len(next_round_votes[table_id])}")
        
        for p in human_players:  # 只检查人类玩家
            if p.id not in next_round_votes[table_id]:
                all_voted = False
                print(f"🗳️ 玩家 {p.nickname} 还未投票")
                break
        
        if all_voted:
            print(f"✅ 所有人类玩家都已投票，准备开始下一轮")
        
        # 广播投票状态
        vote_status = {
            'votes': len(next_round_votes[table_id]),
            'required': len(human_players),
            'players_voted': [p.nickname for p in table.players if p.id in next_round_votes[table_id]]
        }
        socketio.emit('next_round_vote_update', vote_status, room=table_id)
        
        # 如果所有人都投票了，开始下一轮
        if all_voted:
            print(f"🎮 所有人投票完成，调用start_next_round")
            start_next_round(table_id)
            
    except Exception as e:
        print(f"下一轮投票错误: {e}")
        emit('error', {'message': '投票失败'})

def start_next_round(table_id):
    """开始下一轮游戏"""
    try:
        if table_id not in tables:
            return
        
        table = tables[table_id]
        
        # 清理投票记录
        if table_id in next_round_votes:
            del next_round_votes[table_id]
        
        # 重置所有玩家状态
        for player in table.players:
            player.status = 'playing'
            player.current_bet = 0
            player.total_bet = 0
            player.has_acted = False
            player.hole_cards = []
        
        # 开始新手牌
        success = table.start_new_hand()
        print(f"🎮 table.start_new_hand() 返回: {success}")
        
        if not success:
            print(f"❌ 新手牌开始失败")
            return
        
        print(f"🎮 房间 {table.title} 开始下一轮")
        
        # 广播新手牌开始
        game_state = table.get_table_state()
        print(f"🎮 广播new_hand_started事件到房间 {table_id}")
        socketio.emit('new_hand_started', game_state, room=table_id)
        
        # 广播玩家手牌给各自的玩家
        for player in table.players:
            if not player.is_bot and player.hole_cards:
                player_session = None
                for sid, session in player_sessions.items():
                    if session['player_id'] == player.id:
                        player_session = sid
                        break
                
                if player_session:
                    print(f"📤 发送手牌给玩家 {player.nickname}: {[f'{card.rank.symbol}{card.suit.value}' for card in player.hole_cards]}")
                    socketio.emit('your_cards', {
                        'hole_cards': [card.to_dict() for card in player.hole_cards]
                    }, room=player_session)
        
        # 开始机器人处理
        socketio.start_background_task(process_bot_actions_delayed, table_id)
        
    except Exception as e:
        print(f"开始下一轮错误: {e}")

def process_bot_actions_delayed(table_id, delay=1):
    """延迟处理机器人动作"""
    import time
    time.sleep(delay)
    if table_id in tables:
        print(f"🤖 开始处理机器人动作 (table_id: {table_id})")
        process_bot_actions(table_id)

def handle_hand_end(table_id, winners):
    """处理手牌结束"""
    try:
        if table_id not in tables:
            print(f"❌ handle_hand_end: 房间 {table_id} 不存在")
            return
        
        table = tables[table_id]
        
        # 调试：打印传入的获胜者信息
        print(f"🏆 handle_hand_end 收到获胜者信息: {winners}")
        print(f"🏆 获胜者类型: {type(winners)}")
        
        # 如果没有获胜者信息，强制创建一个
        if not winners or (isinstance(winners, list) and len(winners) == 0):
            print("⚠️ 没有获胜者信息，创建默认获胜者")
            if table.players:
                # 找筹码最多的玩家
                winner = max(table.players, key=lambda p: p.chips)
                winners = [winner]
                print(f"🏆 创建默认获胜者: {winner.nickname}")
        
        # 保存玩家筹码到数据库
        for player in table.players:
            if not player.is_bot:
                update_player_chips(player.id, player.chips)
        
        # 处理获胜者信息
        winner_list = []
        winner_message = "手牌结束"
        
        if winners:
            if isinstance(winners, list):
                if len(winners) > 0:
                    # 处理列表中的获胜者（可能是Player对象或字典）
                    winner_list = []
                    for w in winners:
                        if hasattr(w, 'nickname'):  # Player对象
                            winner_list.append({'nickname': w.nickname, 'chips': w.chips})
                        elif isinstance(w, dict) and 'nickname' in w:  # 字典
                            winner_list.append({'nickname': w['nickname'], 'chips': w.get('chips', 0)})
                    
                    if winner_list:
                        winner_message = f"手牌结束，{winner_list[0]['nickname']} 获胜"
                    else:
                        winner_message = "手牌结束，无获胜者"
                else:
                    winner_message = "手牌结束，无获胜者"
            else:
                # 单个获胜者（可能是Player对象或字典）
                if hasattr(winners, 'nickname'):  # Player对象
                    winner_list = [{'nickname': winners.nickname, 'chips': winners.chips}]
                    winner_message = f"手牌结束，{winners.nickname} 获胜"
                elif isinstance(winners, dict) and 'nickname' in winners:  # 字典
                    winner_list = [{'nickname': winners['nickname'], 'chips': winners.get('chips', 0)}]
                    winner_message = f"手牌结束，{winners['nickname']} 获胜"
                else:
                    winner_list = []
                    winner_message = "手牌结束，无获胜者"
        else:
            winner_message = "手牌结束，无获胜者"
        
        # 广播手牌结束信息和更新后的游戏状态
        updated_game_state = table.get_table_state()
        socketio.emit('hand_ended', {
            'winners': winner_list,
            'message': winner_message,
            'table_state': updated_game_state  # 包含更新后的筹码信息
        }, room=table_id)
        
        # 检查是否还有足够玩家继续游戏
        active_players = [p for p in table.players if p.chips > 0]
        if len(active_players) < 2:
            socketio.emit('game_over', {
                'message': '游戏结束，玩家筹码不足'
            }, room=table_id)
            return
        
        # 提示开始下一轮投票
        human_players = [p for p in table.players if not p.is_bot]
        if len(human_players) > 0:
            socketio.emit('show_next_round_vote', {
                'message': '准备开始下一轮？',
                'required_votes': len(human_players)
            }, room=table_id)
        else:
            # 如果只有机器人，自动开始下一轮
            socketio.start_background_task(start_next_round, table_id)
        
    except Exception as e:
        print(f"处理手牌结束错误: {e}")



if __name__ == '__main__':
    import os
    # 只在主进程中执行初始化（避免debug模式重复加载）
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🃏 德州扑克游戏服务器启动中...")
        print("📊 数据库初始化完成")
        
        # 启动时清理空房间
        print("🧹 清理空房间...")
        cleanup_empty_tables()
        
        # 启动定期清理任务
        import threading
        def periodic_cleanup():
            import time
            while True:
                time.sleep(300)  # 每5分钟清理一次
                cleanup_empty_tables()
        
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        
        print("🌐 服务器地址: http://192.168.178.39:5000")
        print("🎮 游戏已准备就绪！")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 