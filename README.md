# 🃏 德州扑克游戏 / Texas Hold'em Poker Game

[English](#english) | [中文](#中文)

---

## 中文

一个功能完整的在线多人德州扑克游戏，支持人机对战、实时交互和智能辅助功能。

### ✨ 特色功能

- 🎮 **多人在线游戏** - 支持最多9人同时游戏，局域网实时对战
- 🤖 **智能AI机器人** - 提供多种难度级别的AI对手陪练
- 📊 **实时胜率计算** - 蒙特卡洛模拟计算当前手牌胜率
- 🃏 **记牌助手** - 帮助跟踪已出现的牌面信息
- 🎯 **标准德州扑克规则** - 完整实现德州扑克游戏逻辑
- 💾 **数据持久化** - SQLite数据库存储游戏数据和玩家信息
- 🔄 **断线重连** - 支持网络断线后自动重连
- 📱 **响应式UI** - 现代化Web界面，支持各种设备
- 🏆 **详细摊牌记录** - 完整记录每次摊牌的牌型和排名
- 👀 **零筹码观察者模式** - 没有筹码的玩家可以观察游戏

### 🛠️ 技术栈

- **后端**: Python 3.8+, Flask, Flask-SocketIO
- **前端**: HTML5, CSS3, JavaScript, Tailwind CSS
- **数据库**: SQLite
- **实时通信**: WebSocket (Socket.IO)
- **游戏引擎**: 自研德州扑克核心引擎

### 📦 安装与部署

#### 环境要求

- Python 3.8 或更高版本
- 现代浏览器 (Chrome, Firefox, Edge, Safari)

#### 快速开始

1. **克隆项目**
```bash
git clone https://github.com/your-username/texas-holdem-poker.git
cd texas-holdem-poker
```

2. **创建虚拟环境**
```bash
python -m venv poker_env
# Windows
poker_env\Scripts\activate
# macOS/Linux
source poker_env/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动服务**
```bash
python app.py
```

5. **访问游戏**
```
打开浏览器访问: http://localhost:5000
```

### 🎮 游戏说明

#### 游戏流程

1. **进入大厅** - 输入昵称进入游戏大厅
2. **创建/加入房间** - 创建新房间或加入现有房间
3. **添加机器人** - 可选择添加不同难度的AI对手
4. **开始游戏** - 至少2名玩家即可开始游戏
5. **游戏对局** - 按照标准德州扑克规则进行游戏

#### 操作说明

- **过牌 (Check)** - 不下注，将行动权传递给下一位玩家
- **跟注 (Call)** - 跟进当前的下注额
- **加注/下注 (Bet/Raise)** - 增加下注金额
- **弃牌 (Fold)** - 放弃当前手牌
- **全下 (All-in)** - 投入所有剩余筹码

#### 辅助功能

- **胜率计算器** - 点击相应按钮查看当前手牌胜率
- **记牌助手** - 显示已知牌面和剩余牌组信息
- **自动开始下轮** - 投票系统决定是否开始新一轮游戏
- **摊牌详情** - 查看详细的摊牌结果和牌型排名

#### 零筹码处理

- **观察者模式** - 筹码用完的玩家自动成为观察者
- **继续观看** - 可以查看其他玩家的手牌和游戏进程
- **机器人处理** - 零筹码机器人自动退出游戏流程

### 🔧 配置说明

#### 房间设置

- **小盲注**: 默认 $10
- **大盲注**: 默认 $20  
- **最大玩家数**: 1-9人可调
- **初始筹码**: 默认 $1000

#### AI机器人级别

- **简单 (Beginner)** - 保守型打法，适合新手练习
- **中等 (Intermediate)** - 平衡型打法，有一定技巧
- **困难 (Advanced)** - 激进型打法，善于虚张声势

### 📁 项目结构

```
texas-holdem-poker/
├── app.py                    # 主应用程序
├── database.py              # 数据库操作
├── db_adapter.py            # 数据库适配器
├── game_logger.py           # 游戏日志记录
├── player_persistence.py    # 玩家数据持久化
├── table_state_manager.py   # 牌桌状态管理
├── poker_engine/            # 游戏引擎核心
│   ├── __init__.py
│   ├── bot.py              # AI机器人逻辑
│   ├── card.py             # 扑克牌类
│   ├── hand_evaluator.py   # 牌型评估器
│   ├── player.py           # 玩家类
│   └── table.py            # 牌桌类
├── templates/               # HTML模板
│   ├── base.html
│   ├── index.html          # 首页
│   ├── lobby.html          # 游戏大厅
│   └── table.html          # 游戏桌面
├── static/                  # 静态资源
├── tests/                   # 测试文件
└── requirements.txt         # 项目依赖
```

### 🎯 核心功能模块

#### 游戏引擎 (poker_engine)

- **Card & Deck**: 扑克牌和牌组管理
- **Player**: 玩家状态和行为管理  
- **Table**: 游戏桌面和回合控制
- **HandEvaluator**: 牌型识别和比较
- **Bot**: AI玩家决策逻辑

#### 数据管理

- **Database**: SQLite数据库操作
- **GameLogger**: 详细的游戏过程记录
- **PlayerPersistence**: 玩家数据持久化
- **TableStateManager**: 游戏状态恢复机制

#### 摊牌系统

- **详细记录**: 记录所有玩家的底牌和牌型
- **排名显示**: 显示玩家排名和奖金分配
- **历史查询**: 提供摊牌历史查询API
- **可视化**: 现代化的摊牌结果展示界面

### 🧪 测试

运行测试用例:

```bash
# 测试双人游戏
python test_two_humans.py

# 测试人机对战
python test_two_humans_one_bot.py

# 测试摊牌功能
python test_showdown.py
```

### 🚀 部署建议

#### 局域网部署

1. 确保防火墙允许5000端口访问
2. 修改`app.py`中的host为服务器IP
3. 局域网内其他设备通过IP:5000访问

#### 生产环境部署

建议使用以下配置:

- **Web服务器**: Nginx + Gunicorn
- **进程管理**: Supervisor 或 systemd
- **数据库**: 可升级至PostgreSQL/MySQL
- **缓存**: Redis (用于session管理)

### 📊 性能优化

- 使用eventlet提供高并发WebSocket支持
- SQLite连接池和事务优化
- 前端资源压缩和缓存
- AI决策算法优化

### 🆕 最新更新

#### v2.0 (2025-06)

- ✨ **全新摊牌记录系统**
  - 详细记录每次摊牌的所有玩家信息
  - 显示牌型排名和奖金分配
  - 提供摊牌历史查询功能

- ✨ **零筹码玩家处理**
  - 新增观察者模式，零筹码玩家可继续观看
  - 优化游戏流程，跳过无筹码玩家
  - 改进机器人零筹码处理逻辑

- 🔧 **核心引擎优化**
  - 改进手牌评估算法
  - 优化游戏状态管理
  - 增强玩家动作验证

### 🤝 贡献指南

欢迎提交Issues和Pull Requests！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 📜 开源协议

本项目采用 MIT 协议，详情请查看 [LICENSE](LICENSE) 文件。

### 🔗 相关链接

- [德州扑克规则说明](https://zh.wikipedia.org/wiki/德州撲克)
- [Flask-SocketIO文档](https://flask-socketio.readthedocs.io/)
- [项目问题反馈](../../issues)

### 📞 技术支持

如有技术问题或建议，请通过以下方式联系:

- 创建Issue: [GitHub Issues](../../issues)
- 项目地址: [GitHub Repository](https://github.com/your-username/texas-holdem-poker)

---

**享受游戏，理性娱乐！🎲**

## English

A full-featured online multiplayer Texas Hold'em poker game with AI opponents, real-time interaction, and intelligent assistance features.

### ✨ Key Features

- 🎮 **Multiplayer Online Gaming** - Support up to 9 players simultaneously in LAN real-time battles
- 🤖 **Smart AI Bots** - Multiple difficulty levels of AI opponents for practice
- 📊 **Real-time Win Probability** - Monte Carlo simulation for current hand win rates
- 🃏 **Card Tracking Assistant** - Help track revealed card information
- 🎯 **Standard Texas Hold'em Rules** - Complete implementation of poker game logic
- 💾 **Data Persistence** - SQLite database for game data and player information storage
- 🔄 **Reconnection Support** - Automatic reconnection after network disconnection
- 📱 **Responsive UI** - Modern web interface supporting various devices
- 🏆 **Detailed Showdown Records** - Complete recording of showdown hand types and rankings
- 👀 **Zero-Chip Observer Mode** - Players without chips can observe the game

### 🛠️ Technology Stack

- **Backend**: Python 3.8+, Flask, Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript, Tailwind CSS
- **Database**: SQLite
- **Real-time Communication**: WebSocket (Socket.IO)
- **Game Engine**: Custom Texas Hold'em core engine

### 📦 Installation & Deployment

#### Requirements

- Python 3.8 or higher
- Modern browser (Chrome, Firefox, Edge, Safari)

#### Quick Start

1. **Clone the project**
```bash
git clone https://github.com/your-username/texas-holdem-poker.git
cd texas-holdem-poker
```

2. **Create virtual environment**
```bash
python -m venv poker_env
# Windows
poker_env\Scripts\activate
# macOS/Linux
source poker_env/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start the service**
```bash
python app.py
```

5. **Access the game**
```
Open browser and visit: http://localhost:5000
```

### 🎮 Game Instructions

#### Game Flow

1. **Enter Lobby** - Input nickname to enter the game lobby
2. **Create/Join Room** - Create new room or join existing room
3. **Add Bots** - Optionally add AI opponents with different difficulty levels
4. **Start Game** - At least 2 players required to start the game
5. **Game Session** - Play according to standard Texas Hold'em rules

#### Controls

- **Check** - No bet, pass action to next player
- **Call** - Match the current bet amount
- **Bet/Raise** - Increase the bet amount
- **Fold** - Give up current hand
- **All-in** - Bet all remaining chips

#### Assistant Features

- **Win Rate Calculator** - Click button to view current hand win probability
- **Card Tracker** - Display known cards and remaining deck information
- **Auto Start Next Round** - Voting system to decide whether to start new round
- **Showdown Details** - View detailed showdown results and hand rankings

#### Zero-Chip Handling

- **Observer Mode** - Players without chips automatically become observers
- **Continue Watching** - Can view other players' hands and game progress
- **Bot Handling** - Zero-chip bots automatically exit game flow

### 🔧 Configuration

#### Room Settings

- **Small Blind**: Default $10
- **Big Blind**: Default $20
- **Max Players**: 1-9 players adjustable
- **Initial Chips**: Default $1000

#### AI Bot Levels

- **Beginner** - Conservative playstyle, suitable for beginners
- **Intermediate** - Balanced playstyle with some skills
- **Advanced** - Aggressive playstyle, good at bluffing

### 📁 Project Structure

```
texas-holdem-poker/
├── app.py                    # Main application
├── database.py              # Database operations
├── db_adapter.py            # Database adapter
├── game_logger.py           # Game logging
├── player_persistence.py    # Player data persistence
├── table_state_manager.py   # Table state management
├── poker_engine/            # Game engine core
│   ├── __init__.py
│   ├── bot.py              # AI bot logic
│   ├── card.py             # Poker card class
│   ├── hand_evaluator.py   # Hand evaluation
│   ├── player.py           # Player class
│   └── table.py            # Table class
├── templates/               # HTML templates
│   ├── base.html
│   ├── index.html          # Home page
│   ├── lobby.html          # Game lobby
│   └── table.html          # Game table
├── static/                  # Static resources
├── tests/                   # Test files
└── requirements.txt         # Project dependencies
```

### 🎯 Core Modules

#### Game Engine (poker_engine)

- **Card & Deck**: Poker card and deck management
- **Player**: Player state and behavior management
- **Table**: Game table and round control
- **HandEvaluator**: Hand type recognition and comparison
- **Bot**: AI player decision logic

#### Data Management

- **Database**: SQLite database operations
- **GameLogger**: Detailed game process recording
- **PlayerPersistence**: Player data persistence
- **TableStateManager**: Game state recovery mechanism

#### Showdown System

- **Detailed Recording**: Record all players' hole cards and hand types
- **Ranking Display**: Show player rankings and prize distribution
- **History Query**: Provide showdown history query API
- **Visualization**: Modern showdown results display interface

### 🧪 Testing

Run test cases:

```bash
# Test two human players
python test_two_humans.py

# Test human vs bot
python test_two_humans_one_bot.py

# Test showdown functionality
python test_showdown.py
```

### 🚀 Deployment Suggestions

#### LAN Deployment

1. Ensure firewall allows port 5000 access
2. Modify host in `app.py` to server IP
3. Other devices in LAN access via IP:5000

#### Production Environment

Recommended configuration:

- **Web Server**: Nginx + Gunicorn
- **Process Management**: Supervisor or systemd
- **Database**: Upgrade to PostgreSQL/MySQL
- **Cache**: Redis (for session management)

### 📊 Performance Optimization

- Use eventlet for high-concurrency WebSocket support
- SQLite connection pooling and transaction optimization
- Frontend resource compression and caching
- AI decision algorithm optimization

### 🆕 Latest Updates

#### v2.0 (2025-06)

- ✨ **New Showdown Recording System**
  - Detailed recording of all player information in each showdown
  - Display hand rankings and prize distribution
  - Provide showdown history query functionality

- ✨ **Zero-Chip Player Handling**
  - Added observer mode for zero-chip players to continue watching
  - Optimized game flow to skip players without chips
  - Improved bot zero-chip handling logic

- 🔧 **Core Engine Optimization**
  - Improved hand evaluation algorithm
  - Optimized game state management
  - Enhanced player action validation

### 🤝 Contributing

Welcome to submit Issues and Pull Requests!

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🔗 Related Links

- [Texas Hold'em Rules](https://en.wikipedia.org/wiki/Texas_hold_%27em)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [Project Issues](../../issues)

### 📞 Technical Support

For technical questions or suggestions, please contact via:

- Create Issue: [GitHub Issues](../../issues)
- Project Repository: [GitHub Repository](https://github.com/your-username/texas-holdem-poker)

---

**Enjoy the game, play responsibly! 🎲**
