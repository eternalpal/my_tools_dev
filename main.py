import requests
import os
import datetime
import yfinance as yf
import akshare as ak
import pandas as pd
import time

def get_crypto(symbol="ETH"):
    """加密货币：优先 Coinbase (最稳)"""
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        res = requests.get(url, timeout=10).json()
        return f"{symbol}: ${res['data']['amount']} (Coinbase)"
    except:
        return f"{symbol}: 获取失败"

def get_commodities():
    """大宗商品：Yahoo Finance"""
    try:
        tickers = yf.Tickers('SI=F CL=F')
        silver = tickers.tickers['SI=F'].fast_info['lastPrice']
        oil = tickers.tickers['CL=F'].fast_info['lastPrice']
        return f"白银: ${round(silver, 3)} | 原油: ${round(oil, 2)}"
    except:
        return "大宗商品获取失败"

def get_a_shares():
    """A股指数：东财 vs 新浪 (双备份)"""
    # 方案1: 东方财富
    try:
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
        targets = {"中证500": "中证500", "创业板指": "创业板指", "科创50": "科创50"}
        result = []
        for name in targets.values():
            row = df[df['名称'] == name]
            if not row.empty:
                result.append(f"{name}: {row['最新价'].values[0]} ({row['涨跌幅'].values[0]}%)")
        if result: return "\n".join(result)
    except:
        print("东财指数接口失效，尝试新浪...")
    
    # 方案2: 新浪财经 (历史最稳接口)
    try:
        indices = {"sh000905": "中证500", "sz399006": "创业板指", "sh000688": "科创50"}
        result = []
        for code, name in indices.items():
            df = ak.stock_zh_index_daily(symbol=code)
            last_row = df.iloc[-1]
            result.append(f"{name}: {last_row['close']}")
        return "\n".join(result) + " (Sina)"
    except:
        return "A股指数所有接口均失败"

def get_convertible_bond():
    """可转债打新：同花顺 vs 东财 (双备份)"""
    # 获取北京日期格式 YYYY-MM-DD
    bj_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    bj_today_str = bj_now.strftime("%Y-%m-%d")
    
    # 方案1: 同花顺源 (对应你截图的页面)
    try:
        print("尝试同花顺新债接口...")
        df = ak.bond_zh_cov_info_ths()
        # 统一转化日期并筛选
        df['申购日期'] = pd.to_datetime(df['申购日期'], errors='coerce').dt.strftime('%Y-%m-%d')
        target = df[df['申购日期'] == bj_today_str]
        if not target.empty:
            return f"🔔 今日打新提醒: {', '.join(target['债券简称'].tolist())} (THS)"
    except Exception as e:
        print(f"同花顺接口失败: {e}")

    # 方案2: 东方财富源 (备份)
    try:
        print("尝试东财新债接口...")
        df = ak.bond_cov_comparison()
        df['申购日期'] = pd.to_datetime(df['申购日期'], errors='coerce').dt.strftime('%Y-%m-%d')
        target = df[df['申购日期'] == bj_today_str]
        if not target.empty:
            return f"🔔 今日打新提醒: {', '.join(target['证券简称'].tolist())} (EM)"
    except Exception as e:
        print(f"东财接口失败: {e}")

    return "今日无新债申购"

def send_to_feishu(content):
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    if not webhook_url: return
    bj_now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    msg = {
        "msg_type": "text",
        "content": {"text": f"📊 金融监控报表\n{'-'*25}\n{content}\n{'-'*25}\n时间(北京): {bj_now_str}"}
    }
    requests.post(webhook_url, json=msg, timeout=10)

if __name__ == "__main__":
    print("开始任务运行...")
    results = [
        "【加密货币】", get_crypto("BTC"), get_crypto("ETH"),
        "\n【大宗商品】", get_commodities(),
        "\n【A 股指数】", get_a_shares(),
        "\n【申购提醒】", get_convertible_bond()
    ]
    full_report = "\n".join(results)
    print("\n" + full_report)
    send_to_feishu(full_report)