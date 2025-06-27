# 🃏 德州扑克游戏 / Texas Hold'em Poker Game

一个功能完整、体验丰富的在线多人德州扑克游戏，集成了智能AI、实时交互、数据分析和沉浸式音效体验。

A full-featured, experience-rich online multiplayer Texas Hold'em poker game with intelligent AI, real-time interaction, data analysis, and immersive audio experience.

![GitHub stars](https://img.shields.io/github/stars/stars1210JasonHe/texas-holdem-poker?style=social)
![GitHub forks](https://img.shields.io/github/forks/stars1210JasonHe/texas-holdem-poker?style=social)
![GitHub license](https://img.shields.io/github/license/stars1210JasonHe/texas-holdem-poker)
![Python version](https://img.shields.io/badge/python-3.8%2B-blue)

[中文](#中文版) | [English](#english-version)

---

## 中文版

### 🎯 项目概述

这是一个基于Web的实时多人德州扑克游戏平台，支持人机对战、智能辅助、数据分析和沉浸式音效。无论您是德州扑克新手还是资深玩家，都能在这里找到适合的游戏体验。

#### 🎮 在线体验
- **快速开始**: 无需注册，输入昵称即可开始游戏
- **多人对战**: 支持最多9人同时在线游戏
- **智能AI**: 提供不同难度的机器人对手
- **实时互动**: WebSocket实现低延迟实时通信

### ✨ 核心特性

#### 🎲 游戏体验
- **🃏 标准德州扑克规则** - 完整实现Hold'em游戏逻辑
- **👥 多人在线对战** - 支持2-9人实时游戏
- **🤖 智能AI机器人** - 三种难度级别的AI对手
- **🎵 沉浸式音效** - 智能背景音乐系统，根据游戏状态自动切换
- **📱 响应式设计** - 适配桌面、平板和手机设备
- **🔄 断线重连** - 网络断线后自动恢复游戏状态

#### 🧠 智能辅助
- **📊 实时胜率计算** - 蒙特卡洛模拟计算当前手牌胜率
- **🃏 记牌助手** - 跟踪已出现牌面，显示剩余牌组信息
- **📈 数据分析** - 详细的游戏统计和历史记录
- **🎯 决策建议** - 基于概率的最优决策提示
- **👀 观察者模式** - 零筹码玩家可继续观察游戏

#### 🎵 音乐系统
- **🎶 智能音乐切换** - 根据游戏场景自动播放相应音乐
- **🎛️ 音乐控制面板** - 播放/暂停、音量调节、位置自定义
- **⌨️ 快捷键操作** - M键切换播放，Ctrl+M打开设置
- **💾 偏好记忆** - 自动保存音量、静音状态等用户设置
- **📱 响应式界面** - 适配不同设备的音乐控制体验

#### 💾 数据管理
- **🗃️ 完整数据持久化** - SQLite数据库存储所有游戏数据
- **📋 摊牌记录系统** - 详细记录每次摊牌的牌型和排名
- **📊 个人统计面板** - 胜率、奖金、手牌历史等数据分析
- **🔍 历史查询** - 支持摊牌历史的详细查询和回顾
- **⚡ 状态恢复** - 游戏意外中断后的状态自动恢复

### 🛠️ 技术架构

#### 后端技术栈
- **🐍 Python 3.8+** - 核心开发语言
- **🌶️ Flask** - Web应用框架
- **🔌 Flask-SocketIO** - 实时通信
- **🗄️ SQLite** - 数据存储
- **🎯 自研游戏引擎** - 德州扑克核心逻辑

#### 前端技术栈
- **🌐 HTML5 + CSS3** - 现代Web标准
- **⚡ JavaScript ES6+** - 交互逻辑
- **🎨 Tailwind CSS** - 现代化UI框架
- **🔌 Socket.IO** - 实时通信客户端
- **🎵 Web Audio API** - 音频播放控制

### 🚀 快速开始

#### 环境要求
- **Python 3.8+**
- **现代浏览器** (Chrome 80+, Firefox 75+, Edge 80+, Safari 13+)

#### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/stars1210JasonHe/texas-holdem-poker.git
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

5. **开始游戏**
```
浏览器访问: http://localhost:5000
```

### 🎮 游戏指南

#### 基础操作
- **♠️ 过牌 (Check)** - 不下注，传递行动权
- **💰 跟注 (Call)** - 跟进当前下注额
- **📈 加注 (Raise/Bet)** - 增加下注金额
- **🗑️ 弃牌 (Fold)** - 放弃当前手牌
- **🎯 全下 (All-in)** - 投入所有筹码

#### 🎵 音乐体验
- **🏠 大厅音乐** - 轻松舒缓的背景音乐
- **🎲 游戏桌音乐** - 专注沉稳的游戏配乐
- **⚡ 紧张时刻** - 轮到行动或大额下注时的刺激音乐

#### AI机器人级别
- **🟢 简单 (Beginner)** - 保守型打法，适合新手练习
- **🟡 中等 (Intermediate)** - 平衡型打法，有一定技巧
- **🔴 困难 (Advanced)** - 激进型打法，善于虚张声势

### 🔧 高级配置

#### 游戏房间设置
```python
DEFAULT_SETTINGS = {
    'small_blind': 10,      # 小盲注
    'big_blind': 20,        # 大盲注  
    'initial_chips': 1000,  # 初始筹码
    'max_players': 9,       # 最大玩家数
    'auto_start_delay': 3   # 自动开始延迟(秒)
}
```

#### 音乐文件配置
```bash
# 音乐文件路径 (static/audio/)
lobby-music.mp3    # 大厅背景音乐
table-music.mp3    # 游戏桌音乐  
action-music.mp3   # 紧张时刻音乐
```

### 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/stars1210JasonHe/texas-holdem-poker)
- **问题反馈**: [GitHub Issues](https://github.com/stars1210JasonHe/texas-holdem-poker/issues)

---

## English Version

### 🎯 Project Overview

This is a web-based real-time multiplayer Texas Hold'em poker game platform that supports human-AI battles, intelligent assistance, data analysis, and immersive audio effects. Whether you're a Texas Hold'em beginner or veteran player, you can find a suitable gaming experience here.

#### 🎮 Online Experience
- **Quick Start**: No registration required, just enter a nickname to start playing
- **Multiplayer Battles**: Support up to 9 players online simultaneously
- **Smart AI**: Provides robot opponents of different difficulty levels
- **Real-time Interaction**: WebSocket enables low-latency real-time communication

### ✨ Core Features

#### 🎲 Gaming Experience
- **🃏 Standard Texas Hold'em Rules** - Complete implementation of Hold'em game logic
- **👥 Multiplayer Online Battles** - Support 2-9 players real-time gaming
- **🤖 Smart AI Robots** - Three difficulty levels of AI opponents
- **🎵 Immersive Audio** - Smart background music system that automatically switches based on game state
- **📱 Responsive Design** - Compatible with desktop, tablet, and mobile devices
- **🔄 Disconnect Reconnection** - Automatic game state recovery after network disconnection

#### 🧠 Intelligent Assistance
- **📊 Real-time Win Rate Calculation** - Monte Carlo simulation for current hand win probability
- **🃏 Card Tracking Assistant** - Track revealed cards and display remaining deck information
- **📈 Data Analysis** - Detailed game statistics and historical records
- **🎯 Decision Suggestions** - Optimal decision tips based on probability
- **👀 Observer Mode** - Zero-chip players can continue observing the game

#### 🎵 Music System
- **🎶 Smart Music Switching** - Automatically play appropriate music based on game scenarios
- **🎛️ Music Control Panel** - Play/pause, volume adjustment, position customization
- **⌨️ Keyboard Shortcuts** - M key for play/pause, Ctrl+M for settings
- **💾 Preference Memory** - Automatically save volume, mute state, and other user settings
- **📱 Responsive Interface** - Music control experience adapted for different devices

#### 💾 Data Management
- **🗃️ Complete Data Persistence** - SQLite database stores all game data
- **📋 Showdown Recording System** - Detailed recording of hand types and rankings for each showdown
- **📊 Personal Statistics Panel** - Win rate, prize money, hand history data analysis
- **🔍 Historical Query** - Support detailed query and review of showdown history
- **⚡ State Recovery** - Automatic state recovery after unexpected game interruption

### 🛠️ Technical Architecture

#### Backend Technology Stack
- **🐍 Python 3.8+** - Core development language
- **🌶️ Flask** - Web application framework
- **🔌 Flask-SocketIO** - Real-time communication
- **🗄️ SQLite** - Data storage
- **🎯 Self-developed Game Engine** - Texas Hold'em core logic

#### Frontend Technology Stack
- **🌐 HTML5 + CSS3** - Modern web standards
- **⚡ JavaScript ES6+** - Interactive logic
- **🎨 Tailwind CSS** - Modern UI framework
- **🔌 Socket.IO** - Real-time communication client
- **🎵 Web Audio API** - Audio playback control

### 🚀 Quick Start

#### Requirements
- **Python 3.8+**
- **Modern Browser** (Chrome 80+, Firefox 75+, Edge 80+, Safari 13+)

#### Installation Steps

1. **Clone the project**
```bash
git clone https://github.com/stars1210JasonHe/texas-holdem-poker.git
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

4. **Start service**
```bash
python app.py
```

5. **Start gaming**
```
Visit in browser: http://localhost:5000
```

### 🎮 Game Guide

#### Basic Operations
- **♠️ Check** - No bet, pass action to next player
- **💰 Call** - Match the current bet amount
- **📈 Raise/Bet** - Increase the bet amount
- **🗑️ Fold** - Give up current hand
- **🎯 All-in** - Bet all remaining chips

#### 🎵 Music Experience
- **🏠 Lobby Music** - Relaxing and soothing background music
- **🎲 Game Table Music** - Focused and calm game soundtrack
- **⚡ Tense Moments** - Exciting music when it's your turn or during big bets

#### AI Robot Levels
- **🟢 Beginner** - Conservative playstyle, suitable for beginners
- **🟡 Intermediate** - Balanced playstyle with some skills
- **🔴 Advanced** - Aggressive playstyle, good at bluffing

### 🔧 Advanced Configuration

#### Game Room Settings
```python
DEFAULT_SETTINGS = {
    'small_blind': 10,      # Small blind
    'big_blind': 20,        # Big blind
    'initial_chips': 1000,  # Initial chips
    'max_players': 9,       # Maximum players
    'auto_start_delay': 3   # Auto start delay (seconds)
}
```

#### Music File Configuration
```bash
# Music file paths (static/audio/)
lobby-music.mp3    # Lobby background music
table-music.mp3    # Game table music
action-music.mp3   # Tense moment music
```

### 🚀 Deployment Guide

#### Development Environment
```bash
# Start development server
python app.py

# Enable debug mode
export FLASK_ENV=development
python app.py
```

#### Production Environment

##### Using Gunicorn + Nginx
```bash
# Install Gunicorn
pip install gunicorn

# Start service
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

##### Nginx Configuration Example
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 🤝 Contributing

#### How to Contribute
1. **Fork the project** to your GitHub account
2. **Create branch** `git checkout -b feature/your-feature`
3. **Commit changes** `git commit -m 'Add some feature'`
4. **Push branch** `git push origin feature/your-feature`
5. **Submit Pull Request**

#### Code Standards
- **Python**: Follow PEP 8 code standards
- **JavaScript**: Use ESLint code checking
- **Commit Messages**: Use conventional commit format
- **Documentation**: Update related documentation and comments

### 📄 License

This project is based on the [MIT License](LICENSE) open source license.

### 📞 Contact

- **Project Homepage**: [GitHub Repository](https://github.com/stars1210JasonHe/texas-holdem-poker)
- **Issue Feedback**: [GitHub Issues](https://github.com/stars1210JasonHe/texas-holdem-poker/issues)
- **Feature Suggestions**: [GitHub Discussions](https://github.com/stars1210JasonHe/texas-holdem-poker/discussions)

---

## 🌟 Star History

如果这个项目对您有帮助，请考虑给我们一个 ⭐ Star！

If this project helps you, please consider giving us a ⭐ Star!

[![Star History Chart](https://api.star-history.com/svg?repos=stars1210JasonHe/texas-holdem-poker&type=Date)](https://star-history.com/#stars1210JasonHe/texas-holdem-poker&Date)

---

<div align="center">

**🃏 享受德州扑克的乐趣，体验智能游戏的魅力！ 🃏**

**🃏 Enjoy the fun of Texas Hold'em and experience the charm of intelligent gaming! 🃏**

Made with ❤️ by [Jason He](https://github.com/stars1210JasonHe)

</div>
