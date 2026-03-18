# Stock Review - 股票筛选与分析工具

基于自然语言的 A 股股票筛选与盘口回放工具，通过大模型将你的交易策略转化为可执行的筛选因子，支持历史盘口回放和多股同步分析。

## 特性

- 🤖 **自然语言策略**：用中文描述筛选条件，大模型自动生成因子代码
- 📊 **全市场覆盖**：支持 5000+ A 股实时筛选
- ⚡ **异步并发**：5 分钟内完成全市场扫描
- 📈 **盘口回放**：历史分时数据回放，复刻每日盘中情况
- 🎯 **多股同步**：支持多只股票同时回放，时间轴同步控制
- 🖥️ **Web 界面**：Vue 3 + FastAPI 现代化 Web 应用
- 📉 **专业图表**：Lightweight Charts (TradingView) 专业 K 线图表

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- pnpm

### 安装依赖

**后端依赖：**
```bash
pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy akshare python-multipart python-dotenv aiohttp click
```

**前端依赖：**
```bash
cd web
pnpm install
```

### 启动项目

**方式 1：分别启动（推荐开发时使用）**

终端 1 - 启动后端：
```bash
python -m uvicorn src.api.app:app --reload --port 8000
```

终端 2 - 启动前端：
```bash
cd web
pnpm dev
```

**方式 2：使用启动脚本**

Windows:
```bash
start-dev.bat
```

Linux/Mac:
```bash
bash start-dev.sh
```

### 访问应用

- **前端页面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 功能模块

### 股票筛选
通过自然语言描述筛选条件，大模型自动生成因子代码并执行筛选。

### 交易看板
- 自选股管理（添加/删除/分类）
- 个股 K 线图表（日 K/分钟 K 切换）
- 实时行情数据
- 技术指标叠加（MA、VWAP 等）

### 盘口回放
- 选择历史日期进行回放
- 单股/多股同步回放
- 时间轴控制（播放/暂停/进度）
- 分钟级数据回放

### 系统设置
- 大模型配置（Ollama/OpenAI/DeepSeek/自定义）
- 第三方大模型 API 接入（自定义名称、URL、API Key、模型名称）
- 连接测试功能
- 在线对话测试
- 数据源配置
- 筛选参数预设

## 技术栈

**后端:**
- FastAPI - Web 框架
- SQLAlchemy - 数据库 ORM
- AkShare - 数据获取
- SQLite - 数据存储

**前端:**
- Vue 3 + TypeScript
- Vite - 构建工具
- Pinia - 状态管理
- Vue Router - 路由
- Lightweight Charts - 图表库

## 项目结构

```
stock-review/
├── src/
│   ├── api/           # API 层
│   │   ├── app.py     # FastAPI 应用
│   │   ├── routes/    # 路由
│   │   └── schemas/   # Pydantic 模型
│   ├── data/          # 数据层
│   │   ├── fetcher.py # akshare 数据获取
│   │   ├── storage.py # SQLite 存储
│   │   └── models.py  # 数据模型
│   ├── strategies/    # 策略层
│   │   ├── generator.py # 因子代码生成
│   │   └── executor.py  # 因子执行
│   ├── cli/           # CLI 层
│   │   └── main.py
│   └── utils/         # 工具
├── web/               # Web 前端
│   ├── src/
│   │   ├── api/       # API 调用
│   │   ├── components/# 组件
│   │   ├── stores/    # 状态管理
│   │   ├── views/     # 页面
│   │   └── router/    # 路由
│   ├── package.json
│   └── vite.config.ts
├── configs/           # 配置文件
├── data/              # 数据存储
├── pyproject.toml
├── PLAN.md            # 项目计划
├── IMPLEMENTATION_PLAN.md  # 实施计划
└── README.md
```

## 开发计划

详见 [PLAN.md](./PLAN.md) 和 [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

### 当前进度

- ✅ 阶段 1: 基础架构（FastAPI + Vue 3）
- ⏳ 阶段 2: 数据层（akshare 数据获取）
- ⏸️ 阶段 3: API 接口
- ⏸️ 阶段 4: 交易看板
- ⏸️ 阶段 5: 盘口回放

## 注意事项

1. **数据源限制**：akshare 不支持历史逐笔成交和五档行情数据，当前使用分钟级 K 线数据模拟回放
2. **未来扩展**：可接入 Tushare 等数据源实现秒级精度回放

## 许可证

MIT License
