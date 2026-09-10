---
name: a-share-comps-analysis
description: Use when 需要 A 股可比公司估值表、行业定位或机构级 comps。
license: MIT
compatibility: Requires Python 3 and network for China market data APIs. No API keys for default quote path.
metadata:
  author: stunner
  version: "1.0.0"
  tags: "a-share,equity-research,valuation,comps,financial-analysis"
  hermes_related: "a-share-stock-fundamental-analysis,a-share-dcf-model,a-share-earnings-analysis"
  openclaw: '{"requires":{"bins":["python3"]}}'
---

# A股可比公司分析（Comparable Company Analysis）

**适用场景：** 个股估值对比、行业定位、投资委员会材料、IPO定价参考
**不适用：** 无可比公司的独特业务模式、严重亏损公司（用营收倍数替代）

---

## ⚠️ 数据源优先级（A股版）

1. **第一优先：AKShare** — `ak.stock_financial_abstract_ths()` / `ak.stock_financial_analysis_indicator()` 获取财务数据
2. **第二优先：新浪财报** — `ak.stock_financial_report_sina()` 获取详细财报
3. **第三优先：东方财富** — `ak.stock_financial_abstract()` 获取核心指标
4. **禁用：web_search作为一手数据源** — 只能用于交叉验证

**数据验证：** 每家公司的Revenue/Growth/Margin必须与官方财报交叉核对

---

## 核心框架

### 第一步：定义可比公司池

根据 **申万一级/二级行业分类** 筛选：
- 同行业（申万行业代码一致）
- 相似营收规模（±3倍以内）
- 相似业务模式
- **宁可少不要滥**：5个好comps > 10个强行拼凑

用 `ak.stock_board_industry_cons_em()` 获取行业成分股。

### 第二步：核心指标表（必含）

```
┌──────────────┬────────────┬────────┬──────────┬──────────┬───────────┐
│ 公司         │ 营收(亿)   │ 增速%  │毛利率%   │净利率%   │ ROE%      │
├──────────────┼────────────┼────────┼──────────┼──────────┼───────────┤
│ [公司A]      │ [公式]     │ [公式] │ [公式]   │ [公式]   │ [公式]    │
│ [公司B]      │ [公式]     │ [公式] │ [公式]   │ [公式]   │ [公式]    │
│              │            │        │          │          │           │
│ 中位数       │ =MEDIAN    │ =MEDIAN│ =MEDIAN  │ =MEDIAN  │ =MEDIAN   │
│ 75分位       │ =QUARTILE  │ =Q     │ =Q       │ =Q       │ =Q        │
│ 25分位       │ =QUARTILE  │ =Q     │ =Q       │ =Q       │ =Q        │
└──────────────┴────────────┴────────┴──────────┴──────────┴───────────┘
```

### 第三步：估值倍数表（必含）

```
┌──────────────┬──────────┬──────────┬─────────┬────────┬────────┐
│ 公司         │ 市值(亿) │ EV(亿)   │PE(TTM)  │PB      │ EV/EBITDA│
├──────────────┼──────────┼──────────┼─────────┼────────┼────────┤
│ [公司A]      │ [公式]   │ [公式]   │[公式]   │[公式]  │[公式]  │
│              │          │          │         │        │        │
│ 中位数       │ =MEDIAN  │ =MEDIAN  │=MEDIAN  │=MEDIAN │=MEDIAN │
│ 75分位       │ =Q3      │ =Q3      │=Q3      │=Q3     │=Q3     │
│ 25分位       │ =Q1      │ =Q1      │=Q1      │=Q1     │=Q1     │
└──────────────┴──────────┴──────────┴─────────┴────────┴────────┘
```

**关键公式（A股版）：**
- PE(TTM) = 总市值 / 近12个月归母净利润
- PB = 总市值 / 归母净资产
- EV = 总市值 + 有息负债 - 货币资金
- EV/EBITDA = 国内较少用，可替换为EV/营收进行交叉验证

### 第四步：AKShare 数据获取示例

```python
import akshare as ak

# 1. 获取财务指标（含营收、净利润、ROE等）
df = ak.stock_financial_abstract_ths(symbol="600519")  # 茅台

# 2. 获取估值数据
df_val = ak.stock_a_lg_indicator(symbol="600519")  # 含PE/PB

# 3. 获取行业成分股
df_ind = ak.stock_board_industry_cons_em(symbol="白酒概念")

# 4. 实时行情（市值用）
df_rt = ak.stock_zh_a_spot_em()
```

### 第五步：行业特定指标选择

| 行业 | 核心指标 | 可选指标 | 跳过 |
|:---|:---|:---|:---|
| 白酒/消费 | 毛利率、ROE、PE | 预收款、合同负债 | EV/EBITDA |
| 科技/半导体 | 营收增速、研发占比 | 毛利率趋势 | PB（轻资产） |
| 银行/金融 | ROE、不良率、PB | 净息差、拨备覆盖率 | EV指标 |
| 医药/器械 | 研发费用率、毛利率 | 管线价值 | PE（亏损时用PS） |
| 周期行业（钢铁/化工） | PB、ROE、资产负债率 | 股息率 | PE（周期高点失真） |

### 第六步：统计基准

**必做：** 对每个可比指标（增速、毛利率、净利率、ROE、PE、PB）计算：
- 最大值 / 75分位 / **中位数** / 25分位 / 最小值

**不要做：** 对规模指标（营收绝对值、市值绝对值）做统计——不同规模公司不可比。

### 第七步：输出格式

- **主表：** Python/pandas DataFrame 展示，或 openpyxl 输出为 .xlsx
- **数据源注释：** 每个硬编码的输入数据（营收、净利润等）必须添加来源注释
- **输出检查清单（必做）：**
  - [ ] 所有公司确实可比（同一申万二级行业）
  - [ ] 数据来自同一财报周期（最新年报/季报）
  - [ ] 单位统一（亿元）
  - [ ] 每个输入数据标注来源（AKShare/financial_report_sina等）
  - [ ] PE/PB合理性检查（高于行业均值5倍以上需标注原因）
  - [ ] 勾稽检验：PE × EPS = 股价 ✓

### 第八步：异常值&红旗警示

- 🚩 PE > 100x 而无超高速增长故事
- 🚩 毛利率与行业均值偏离>20%
- 🚩 ROE > 40%（不可持续，检查是否为一次性收益）
- 🚩 营收增速为负但PE > 50x
- 🚩 经营现金流与净利润长期背离

---

## 原则总结

1. **结构决定洞察** — 正确的表头迫使正确的思考
2. **少即是多** — 5-8个核心指标 > 20个噪音指标
3. **中位数优于平均数** — 避免极端值扭曲
4. **可比性是王道** — 宁缺毋滥
5. **文档化每一个数据来源** — A股数据源差异大，必须标注清晰
