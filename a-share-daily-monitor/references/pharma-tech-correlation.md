# 创新药 vs 科技股 相关性分析

通过 `fund_open_fund_info_em` 拉取各ETF净值走势，计算日收益率皮尔逊相关系数，量化持仓间的影响程度。

## 方法

```python
# 拉取净值
ak.fund_open_fund_info_em(symbol='589720', indicator='单位净值走势')  # 创新药
ak.fund_open_fund_info_em(symbol='515980', indicator='单位净值走势')  # AI
ak.fund_open_fund_info_em(symbol='512760', indicator='单位净值走势')  # 芯片
ak.fund_open_fund_info_em(symbol='588000', indicator='单位净值走势')  # 科创50ETF

# 日期列必须转换
df['日期_d'] = pd.to_datetime(df['净值日期']).dt.date
```

## 历史结果 (2026-05-21)

近60日日收益率相关性：
- 创新药 vs AI: +0.47 (中等正相关)
- 创新药 vs 芯片: +0.20 (弱正相关)
- 创新药 vs 科创50: +0.55 (中等正相关)

涨跌同步率（同涨同跌天数占比）：
- 创新药 vs AI: 68%
- 创新药 vs 芯片: 72%
- 创新药 vs 科创50: 75%

## 结论

创新药与科技股中等相关（0.2~0.55），不是强相关（0.8+）。
科技股大跌 -5% 时创新药大概跟跌 1~3%，不会腰斩式回调。
创新药的独立逻辑（ASCO临床、FDA审批）形成部分隔离。
但如果ASCO不及预期 + 科技同步下跌 = 双重打击，需要硬止损保护。
