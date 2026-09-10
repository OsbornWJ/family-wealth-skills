#!/usr/bin/env python3
"""
个股挂单预警 - 随14:35盘中分析运行
监控当升科技(300073)和瀚蓝环境(600323)价格预警
"""
import urllib.request
import json

def get_realtime(code, prefix):
    url = f'https://hq.sinajs.cn/list={prefix}{code}'
    req = urllib.request.Request(url, headers={'Referer': 'https://finance.sina.com.cn'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    fields = data.split('"')[1].split(',')
    return {'name': fields[0], 'price': float(fields[3]), 'pre_close': float(fields[2]),
            'high': float(fields[4]), 'low': float(fields[5]),
            'chg': (float(fields[3]) - float(fields[2])) / float(fields[2]) * 100}

stocks = {'300073': ('sz', '当升科技'), '600323': ('sh', '瀚蓝环境')}
alerts = {'当升科技': [(45.0, '合理偏低区，可建试探仓'), (36.0, '低估区，可上主力仓')],
          '瀚蓝环境': [(28.0, '合理偏低区，可建试探仓'), (24.0, '低估区，可上主力仓')]}

print("个股挂单预警")
for code, (prefix, name) in stocks.items():
    d = get_realtime(code, prefix)
    print(f"{name} 现价:{d['price']:.2f} {d['chg']:+.2f}%  高:{d['high']:.2f} 低:{d['low']:.2f}")
    triggered = False
    for target, msg in alerts.get(name, []):
        if d['price'] <= target:
            print(f"  🔴 触发! ≤{target} → {msg}")
            triggered = True
    if not triggered:
        dists = [f"距{t:.0f}还差{(d['price']/t-1)*100:+.1f}%" for t, _ in alerts.get(name, [])]
        print(f"  未触发 | {' | '.join(dists)}")
