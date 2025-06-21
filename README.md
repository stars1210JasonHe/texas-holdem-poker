# 🃏 德州扑克游戏 (Texas Hold'em Poker Game)

一个功能完整的在线多人德州扑克游戏，支持人机对战、实时交互和智能辅助功能。

## ✨ 特色功能

- 🎮 **多人在线游戏** - 支持最多9人同时游戏，局域网实时对战
- 🤖 **智能AI机器人** - 提供多种难度级别的AI对手陪练
- 📊 **实时胜率计算** - 蒙特卡洛模拟计算当前手牌胜率
- 🃏 **记牌助手** - 帮助跟踪已出现的牌面信息
- 🎯 **标准德州扑克规则** - 完整实现德州扑克游戏逻辑
- 💾 **数据持久化** - SQLite数据库存储游戏数据和玩家信息
- 🔄 **断线重连** - 支持网络断线后自动重连
- 📱 **响应式UI** - 现代化Web界面，支持各种设备

## 🛠️ 技术栈

- **后端**: Python 3.8+, Flask, Flask-SocketIO
- **前端**: HTML5, CSS3, JavaScript, Tailwind CSS
- **数据库**: SQLite
- **实时通信**: WebSocket (Socket.IO)
- **游戏引擎**: 自研德州扑克核心引擎

## 📦 安装与部署

### 环境要求

- Python 3.8 或更高版本
- 现代浏览器 (Chrome, Firefox, Edge, Safari)

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd Games-for-family
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动服务**
```bash
python app.py
```

4. **访问游戏**
```
打开浏览器访问: http://localhost:5000
```

## 🎮 游戏说明

### 游戏流程

1. **进入大厅** - 输入昵称进入游戏大厅
2. **创建/加入房间** - 创建新房间或加入现有房间
3. **添加机器人** - 可选择添加不同难度的AI对手
4. **开始游戏** - 至少2名玩家即可开始游戏
5. **游戏对局** - 按照标准德州扑克规则进行游戏

### 操作说明

- **过牌 (Check)** - 不下注，将行动权传递给下一位玩家
- **跟注 (Call)** - 跟进当前的下注额
- **加注/下注 (Bet/Raise)** - 增加下注金额
- **弃牌 (Fold)** - 放弃当前手牌
- **全下 (All-in)** - 投入所有剩余筹码

### 辅助功能

- **胜率计算器** - 点击相应按钮查看当前手牌胜率
- **记牌助手** - 显示已知牌面和剩余牌组信息
- **自动开始下轮** - 投票系统决定是否开始新一轮游戏

## 🔧 配置说明

### 房间设置

- **小盲注**: 默认 $10
- **大盲注**: 默认 $20  
- **最大玩家数**: 1-9人可调
- **初始筹码**: 默认 $1000

### AI机器人级别

- **简单 (Easy)** - 保守型打法，适合新手练习
- **中等 (Medium)** - 平衡型打法，有一定技巧
- **困难 (Hard)** - 激进型打法，善于虚张声势

## 📁 项目结构

```
Games for family/
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

## 🎯 核心功能模块

### 游戏引擎 (poker_engine)

- **Card & Deck**: 扑克牌和牌组管理
- **Player**: 玩家状态和行为管理  
- **Table**: 游戏桌面和回合控制
- **HandEvaluator**: 牌型识别和比较
- **Bot**: AI玩家决策逻辑

### 数据管理

- **Database**: SQLite数据库操作
- **GameLogger**: 详细的游戏过程记录
- **PlayerPersistence**: 玩家数据持久化
- **TableStateManager**: 游戏状态恢复机制

## 🧪 测试

运行测试用例:

```bash
# 测试双人游戏
python test_two_humans.py

# 测试人机对战
python test_two_humans_one_bot.py
```

## 🚀 部署建议

### 局域网部署

1. 确保防火墙允许5000端口访问
2. 修改`app.py`中的host为服务器IP
3. 局域网内其他设备通过IP:5000访问

### 生产环境部署

建议使用以下配置:

- **Web服务器**: Nginx + Gunicorn
- **进程管理**: Supervisor 或 systemd
- **数据库**: 可升级至PostgreSQL/MySQL
- **缓存**: Redis (用于session管理)

## 📊 性能优化

- 使用eventlet提供高并发WebSocket支持
- SQLite连接池和事务优化
- 前端资源压缩和缓存
- AI决策算法优化

## 🤝 贡献指南

欢迎提交Issues和Pull Requests！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📜 开源协议

本项目采用 MIT 协议，详情请查看 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [德州扑克规则说明](https://zh.wikipedia.org/wiki/德州撲克)
- [Flask-SocketIO文档](https://flask-socketio.readthedocs.io/)
- [项目问题反馈](../../issues)

## 📞 技术支持

如有技术问题或建议，请通过以下方式联系:

- 创建Issue: [GitHub Issues](../../issues)
- 邮件联系: [您的邮箱]

---

**享受游戏，理性娱乐！🎲**
