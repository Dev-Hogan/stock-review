# 实施计划

## 数据源调研结论

根据 akshare 文档调研，数据支持情况如下：

### ✅ 支持的数据
| 数据类型 | 接口名称 | 是否支持历史查询 |
|---------|---------|----------------|
| 股票基本信息 | `stock_individual_info_em` | - |
| 日 K 线数据 | `stock_zh_a_hist_em` | ✅ 支持 |
| 分钟 K 线数据 | `stock_zh_a_hist_min_em` | ✅ 支持按日期范围 |
| 分时数据 | `stock_zh_a_hist_min_em` | ✅ 支持 (1/5/15/30/60 分钟) |
| 实时五档行情 | `stock_bid_ask_em` | ❌ 仅实时 |

### ❌ 不支持的数据
| 数据类型 | 接口名称 | 限制说明 |
|---------|---------|---------|
| 历史分笔成交 | `stock_zh_a_tick_tx` | 仅最近一个交易日 |
| 历史五档行情 | - | 完全不支持 |

### 📌 方案选择
**采用 B 方案**: 使用分钟级 K 线数据做简化版回放，逐笔成交和五档行情作为未来功能扩展。

---

## 功能实施顺序

### 阶段 1: 基础架构
- [ ] 后端项目初始化（Poetry、目录结构、FastAPI）
- [ ] 前端项目初始化（Vue 3 + Vite + TypeScript）
- [ ] SQLite 数据库初始化
- [ ] 基础布局组件（侧边栏、顶栏、路由）
- [ ] API 调用封装

### 阶段 2: 数据层（核心基础）
- [ ] 股票基本信息获取与存储
- [ ] 日 K 线数据获取与存储
- [ ] 分钟 K 线数据获取与存储（**用于回放**）
- [ ] 数据缓存层实现
- [ ] 盘后批量更新脚本

> ⚠️ **TODO - 未来功能扩展**
> - [ ] 历史逐笔成交数据（akshare 不支持，需找替代数据源）
> - [ ] 历史五档行情数据（akshare 不支持，需找替代数据源）

### 阶段 3: API 接口
- [ ] 股票查询接口（搜索、基本信息）
- [ ] K 线数据接口（日 K/分钟 K）
- [ ] 分时数据接口（分钟级）
- [ ] 自选股管理接口（增删改查）
- [ ] 配置管理接口

### 阶段 4: 交易看板（核心功能）
- [ ] 股票搜索组件
- [ ] 自选股列表组件
- [ ] Lightweight Charts 集成
- [ ] K 线图表组件（日 K/分钟 K 切换）
- [ ] 技术指标叠加（MA）
- [ ] 交易看板页面集成

> ⚠️ **简化版**
> - [ ] 成交明细面板（先用分钟级数据模拟）
> - [ ] 买卖五档面板（仅显示实时，历史回放暂不显示）

### 阶段 5: 盘口回放（核心功能）
- [ ] 历史回放数据接口（基于分钟 K 线）
- [ ] 日期选择器
- [ ] 时间轴控制组件（播放/暂停/进度）
- [ ] 单股分时回放（分钟级）
- [ ] 多股网格布局
- [ ] 多股同步回放控制
- [ ] 图表数据降采样优化

### 阶段 6: 股票筛选
- [ ] 大模型调用封装（Ollama）
- [ ] 自然语言转因子代码
- [ ] 因子代码安全校验
- [ ] 因子执行引擎
- [ ] 筛选执行接口
- [ ] 股票筛选页面
- [ ] 筛选结果列表展示

### 阶段 7: 增强功能
- [ ] 自选股分类管理
- [ ] 指标配置面板（添加/删除/修改参数）
- [ ] 数据预加载机制
- [ ] 前端虚拟滚动

### 阶段 8: 系统设置
- [ ] 系统设置页面
- [ ] 大模型配置（Ollama 地址、模型名称）
- [ ] 数据源配置
- [ ] 配置持久化

### 阶段 9: 优化与完善
- [ ] 性能测试与优化
- [ ] UI 细节优化
- [ ] Bug 修复
- [ ] 文档完善

### 阶段 10: 未来功能扩展（TODO）
- [ ] 寻找历史逐笔成交数据源（Tushare/Baostock 等）
- [ ] 寻找历史五档行情数据源
- [ ] 实现秒级精度回放
- [ ] 完整的逐笔成交面板
- [ ] 完整的五档行情回放

---

## 技术细节

### 后端 API 路由设计
```
/api/
  /stocks/
    GET    /list          # 股票列表（支持搜索）
    GET    /<code>/info   # 股票基本信息
    GET    /<code>/daily  # 日 K 线数据
    GET    /<code>/minute # 分钟 K 线数据（支持日期范围）
  
  /watchlist/
    GET    /              # 获取自选股列表
    POST   /              # 添加自选股
    DELETE /<code>        # 删除自选股
    PUT    /category      # 更新分类
  
  /screen/
    POST   /execute       # 执行筛选
    GET    /result/<id>   # 获取筛选结果
  
  /config/
    GET    /              # 获取配置
    PUT    /              # 更新配置
```

### 数据库表设计
```sql
-- 股票基础信息
CREATE TABLE stocks (
  code VARCHAR(10) PRIMARY KEY,
  name VARCHAR(50),
  industry VARCHAR(50),
  market_cap DECIMAL(20,2),
  updated_at DATETIME
);

-- 日 K 线数据
CREATE TABLE daily_klines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code VARCHAR(10),
  date DATE,
  open DECIMAL(10,2),
  high DECIMAL(10,2),
  low DECIMAL(10,2),
  close DECIMAL(10,2),
  volume BIGINT,
  amount BIGINT,
  UNIQUE(stock_code, date)
);

-- 分钟 K 线数据（用于回放）
CREATE TABLE minute_klines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code VARCHAR(10),
  datetime DATETIME,
  open DECIMAL(10,2),
  high DECIMAL(10,2),
  low DECIMAL(10,2),
  close DECIMAL(10,2),
  volume BIGINT,
  amount BIGINT,
  UNIQUE(stock_code, datetime)
);

-- 自选股
CREATE TABLE watchlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code VARCHAR(10),
  category VARCHAR(50),
  sort_order INTEGER,
  UNIQUE(stock_code)
);

-- 配置
CREATE TABLE configs (
  key VARCHAR(100) PRIMARY KEY,
  value TEXT,
  updated_at DATETIME
);
```

### 前端组件结构
```
src/components/
  Chart/
    KLineChart.vue          # K 线主图表
    TimeShareChart.vue      # 分时图表
    IndicatorConfig.vue     # 指标配置
  WatchList/
    WatchList.vue           # 自选股列表
    WatchCategory.vue       # 分类管理
  OrderBook/
    OrderBookPanel.vue      # 买卖五档（实时）
  Trades/
    TradeList.vue           # 成交明细（分钟级模拟）
  Replay/
    ReplayControl.vue       # 回放控制条
    MultiReplayLayout.vue   # 多股网格布局
  Search/
    StockSearch.vue         # 股票搜索
```

---

## 注意事项

1. **数据量估算**
   - 5000 只股票 × 250 交易日 × 240 分钟 = 3 亿分钟 K 线数据
   - 建议先存储最近 1 年数据，约 1 亿条记录

2. **性能优化**
   - 分钟 K 线数据添加索引：`(stock_code, datetime)`
   - 使用分页查询，避免一次性加载大量数据
   - 前端图表数据降采样（超过 1000 个点时）

3. **回放实现**
   - 基于分钟 K 线数据，每 1 分钟更新一次图表
   - 时间轴进度 = 已播放分钟数 / 总分钟数（240 分钟）
   - 多股回放时共享同一个时间轴状态

4. **未来扩展**
   - 如果找到历史逐笔数据源，可升级到秒级回放
   - 五档行情历史数据可单独表存储

---

## 参考资源

- AkShare 文档：https://akshare.akfamily.xyz/
- Lightweight Charts: https://github.com/tradingview/lightweight-charts
- Vue 3 + Vite: https://vuejs.org/
- FastAPI: https://fastapi.tiangolo.com/
