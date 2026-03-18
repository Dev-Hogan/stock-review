# Bug: 市值和换手率无法获取

**状态**: Open

## 问题
1. 数据库 `stocks.market_cap` 始终为 NULL
2. `daily_klines` 表缺少 `turnover` 字段

## 原因
- baostock 未返回市值数据
- akshare 网络不稳定
- 换手率列名可能不匹配

## 待解决
- 找到可靠的数据源获取市值
- 验证换手率列名
