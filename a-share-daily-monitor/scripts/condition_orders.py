# 条件单 + 大跌定投 混合策略配置（示例参数，发布包通用）
# 真实成本从 portfolio JSON 加载，勿把个人成交价写回本文件。

# === 条件单（深调抄底）— 示例档位，请按自身计划修改 ===
CONDITION_ORDERS = {
    '515980': {
        'tiers': [(1.10, 4000), (1.05, 5000), (0.99, 5000)],
        'label': '示例-AI ETF'
    },
    '512760': {
        'tiers': [(1.25, 3000), (1.18, 4000), (1.10, 5000), (1.00, 5000)],
        'label': '示例-芯片ETF'
    },
}

DIP_DCA = {
    '515980': {
        'single_day': -5.0,
        'cumulative': -5.0,
        'shares': 2000,
        'amount': 2500,
        'label': '示例-AI ETF',
        'note': '稳健品种'
    },
    '512760': {
        'single_day': -5.0,
        'cumulative': -6.0,
        'shares': 2000,
        'amount': 3000,
        'label': '示例-芯片ETF',
        'note': '高弹性'
    },
    '512660': {
        'single_day': -4.0,
        'cumulative': -5.0,
        'shares': 2000,
        'amount': 1500,
        'label': '示例-军工ETF',
        'note': '阴跌品种'
    },
}

from portfolio_config import load_portfolio
_PF = load_portfolio()
COST_PRICE = _PF["cost_price"]
STOCK_COST = _PF["stock_cost"]
