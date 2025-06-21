# 🎮 德州扑克多人在线游戏

一个功能完整的德州扑克多人在线游戏，支持真人玩家和AI机器人混合游戏。

## ✨ 主要特性

### 🎯 核心功能
- **多人实时对战**: 支持2-6人同时游戏
- **智能AI机器人**: 三种难度级别的AI对手
- **完整游戏流程**: 从发牌到摊牌的完整德州扑克体验
- **实时通信**: 基于WebSocket的实时游戏状态同步
- **投票系统**: 玩家投票决定是否进行下一轮游戏

### 🤖 AI机器人系统
- **新手级**: 保守策略，适合练习
- **中级**: 平衡策略，有一定挑战性
- **高级**: 激进策略，高难度挑战

### 🎲 游戏特色
- **标准德州扑克规则**: 完全符合国际标准
- **多轮游戏支持**: 可连续进行多轮游戏
- **实时房间管理**: 动态创建和管理游戏房间
- **玩家状态追踪**: 实时显示玩家筹码和状态

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Flask 3.0+
- Socket.IO

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/texas-holdem-poker.git
cd texas-holdem-poker
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动服务器**
```bash
python app.py
```

4. **访问游戏**
打开浏览器访问: `http://localhost:5000`

## 🎮 游戏玩法

### 基本流程
1. **进入大厅**: 查看在线玩家和可用房间
2. **创建/加入房间**: 创建新房间或加入现有房间
3. **开始游戏**: 等待玩家就位后开始发牌
4. **游戏进行**: 按照德州扑克规则进行游戏
5. **投票下一轮**: 游戏结束后投票是否继续

### 操作说明
- **弃牌 (Fold)**: 放弃当前手牌
- **过牌 (Check)**: 不下注但继续游戏
- **跟注 (Call)**: 跟上当前最高下注
- **下注 (Bet)**: 主动下注
- **加注 (Raise)**: 在别人下注基础上加注
- **全下 (All-in)**: 投入所有筹码

## 🧪 测试系统

项目包含完整的自动化测试套件：

### 运行测试

1. **两人游戏测试**
```bash
python test_two_humans.py
```

2. **两人+机器人游戏测试**
```bash
python test_two_humans_one_bot.py
```

### 测试覆盖
- ✅ 玩家注册和连接
- ✅ 房间创建和管理
- ✅ 游戏流程完整性
- ✅ AI机器人行为
- ✅ 投票和多轮游戏
- ✅ 错误处理和恢复

## 🏗️ 项目结构

```
texas-holdem-poker/
├── app.py                      # 主应用程序
├── database.py                 # 数据库管理
├── requirements.txt            # 依赖包列表
├── README.md                   # 项目说明
├── 
├── poker_engine/               # 游戏引擎
│   ├── __init__.py
│   ├── bot.py                  # AI机器人
│   ├── card.py                 # 扑克牌逻辑
│   ├── deck.py                 # 牌堆管理
│   ├── hand_evaluator.py       # 牌型评估
│   ├── player.py               # 玩家类
│   ├── table.py                # 游戏桌逻辑
│   └── game_logic.py           # 核心游戏逻辑
│
├── templates/                  # HTML模板
│   ├── base.html               # 基础模板
│   ├── index.html              # 首页
│   ├── lobby.html              # 游戏大厅
│   └── table.html              # 游戏桌面
│
├── static/                     # 静态资源
│   ├── css/                    # 样式文件
│   ├── js/                     # JavaScript文件
│   └── images/                 # 图片资源
│
└── tests/                      # 测试文件
    ├── test_two_humans.py      # 两人游戏测试
    ├── test_two_humans_one_bot.py  # 混合游戏测试
    └── cleanup_database.py     # 数据库清理工具
```

## 🛠️ 技术栈

### 后端技术
- **Flask**: Web框架
- **Flask-SocketIO**: WebSocket通信
- **SQLite**: 数据库
- **Python**: 主要编程语言

### 前端技术
- **HTML5**: 页面结构
- **CSS3**: 样式设计
- **JavaScript**: 交互逻辑
- **Socket.IO**: 实时通信

### 核心算法
- **德州扑克规则引擎**: 完整的游戏逻辑实现
- **AI决策算法**: 基于概率和策略的机器人AI
- **牌型评估算法**: 高效的手牌强度计算

## 🔧 配置说明

### 游戏配置
- **小盲注**: 默认 $10
- **大盲注**: 默认 $20
- **初始筹码**: 每位玩家 $1000
- **最大玩家数**: 6人

### 服务器配置
- **端口**: 5000
- **调试模式**: 开发环境启用
- **日志级别**: INFO

## 📊 数据库设计

### 主要数据表
- **users**: 用户信息
- **tables**: 游戏房间
- **table_players**: 房间玩家关系
- **game_logs**: 游戏日志
- **player_stats**: 玩家统计

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2024-06-22)
- ✅ 完整的德州扑克游戏实现
- ✅ 多人实时对战功能
- ✅ AI机器人系统
- ✅ 投票和多轮游戏支持
- ✅ 完整的测试套件

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和测试者。

---

**享受游戏吧！🎉** 