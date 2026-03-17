# Stock Review - A 股智能筛选工具

基于自然语言的 A 股股票筛选工具，通过大模型将你的交易策略转化为可执行的筛选因子。

## 特性

- 🤖 **自然语言策略**：用中文描述筛选条件，大模型自动生成因子代码
- 📊 **全市场覆盖**：支持 5000+ A 股实时筛选
- ⚡ **异步并发**：5 分钟内完成全市场扫描
- 🎯 **多输入方式**：CLI 命令 / 交互式对话 / 配置文件
- 📈 **HTML 报告**：生成带图表的可视化报告
- 🔧 **Web 配置**：Gradio 界面管理参数和因子

## 快速开始

### 安装依赖

```bash
# 使用 Poetry 管理依赖
poetry install
```

### 初始化配置

```bash
# 首次运行配置向导
stock init

# 或打开 Web 配置界面
stock config
```

### 获取股票数据

```bash
# 更新全市场股票数据（盘后执行）
stock fetch

# 获取指定股票数据
stock fetch --code 600519
```

### 执行筛选

```bash
# 命令行直接筛选
stock filter --pattern "放量上涨且突破 20 日均线"

# 交互式对话模式
stock filter --interactive

# 使用配置文件
stock filter --config strategy.yaml
```

### 生成报告

```bash
# 生成 HTML 报告
stock report --output report.html
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `stock init` | 初始化配置 |
| `stock fetch` | 获取/更新数据 |
| `stock filter` | 执行筛选 |
| `stock report` | 生成报告 |
| `stock config` | 打开配置界面 |
| `stock factors` | 管理因子模板 |

## 技术栈

- Python 3.10+
- akshare - 数据获取
- SQLite - 数据存储
- Ollama - 本地大模型
- Gradio - Web UI
- Poetry - 依赖管理

## 项目结构

```
stock-review/
├── src/
│   ├── data/          # 数据层
│   ├── strategies/    # 策略层
│   ├── cli/           # CLI 层
│   ├── ui/            # UI 层
│   └── utils/         # 工具
├── tests/
├── configs/
├── data/
└── pyproject.toml
```

## 许可证

MIT License