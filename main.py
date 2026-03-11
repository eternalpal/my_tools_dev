import requests
import os
import json
import datetime
import yfinance as yf
import akshare as ak

def get_crypto(symbol="ETH"):
    """获取加密货币价格，增加多源备份"""
    print(f"正在获取 {symbol} 价格...")
    # 源1: 币安
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        res = requests.get(url, timeout=10).json()
        if 'price' in res:
            return f"{symbol}: ${round(float(res['price']), 2)} (Binance)"
    except:
        pass
    
    # 源2: Coinbase (对 GitHub Actions 极其友好)
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        res = requests.get(url, timeout=10).json()
        return f"{symbol}: ${res['data']['amount']} (Coinbase)"
    except Exception as e:
        return f"{symbol}: 获取失败 ({e})"

def get_commodities():
    """获取白银和原油价格 (Yahoo Finance)"""
    print("正在获取大宗商品数据...")
    try:
        # SI=F 白银, CL=F 原油
        tickers = yf.Tickers('SI=F CL=F')
        silver_price = tickers.tickers['SI=F'].fast_info['lastPrice']
        oil_price = tickers.tickers['CL=F'].fast_info['lastPrice']
        return f"白银: ${round(silver_price, 3)} | 原油: ${round(oil_price, 2)}"
    except Exception as e:
        return f"大宗商品获取失败: {e}"

def get_a_shares():
    """获取 A 股指数 (AkShare)"""
    print("正在获取 A 股指数...")
    try:
        df = ak.stock_zh_index_spot() 
        target_indices = {"000905": "中证500", "399006": "创业板指", "000688": "科创50"}
        result = []
        for code, name in target_indices.items():
            # 兼容性处理：防止代码匹配不到
            row = df[df['代码'].str.contains(code)]
            if not row.empty:
                price = row['最新价'].values[0]
                change_pct = row['涨跌幅'].values[0]
                result.append(f"{name}: {price} ({change_pct}%)")
        return "\n".join(result) if result else "未匹配到 A 股指数数据"
    except Exception as e:
        return f"A 股数据获取失败: {e}"

def get_convertible_bond():
    """获取今日是否有可转债打新"""
    print("正在检查可转债...")
    try:
        df = ak.bond_zh_cov_ipo_summary()
        # 获取北京时间 (UTC+8)
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        today_bonds = df[df['申购日期'] == bj_time]
        if today_bonds.empty:
            return "今日无新债申购"
        else:
            names = today_bonds['债券简称'].tolist()
            return f"🔔 今日打新提醒: {', '.join(names)}"
    except Exception as e:
        return f"可转债数据获取失败: {e}"

def send_to_feishu(content):
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    if not webhook_url:
        print("❌ 未设置 FEISHU_WEBHOOK")
        return
    
    # 获取当前北京时间显示在报表里
    bj_now = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    
    msg = {
        "msg_type": "text",
        "content": {
            "text": f"📊 金融市场监控报表\n{'-'*25}\n{content}\n{'-'*25}\n推送时间(北京): {bj_now}"
        }
    }
    r = requests.post(webhook_url, json=msg)
    print(f"飞书推送结果: {r.status_code}")

if __name__ == "__main__":
    # 分段收集，每一段都包在 try-except 里，确保某一部分挂了不影响其他部分显示
    results = []
    
    # 1. 加密货币
    results.append("【加密货币】")
    results.append(get_crypto("BTC"))
    results.append(get_crypto("ETH"))
    
    # 2. 大宗商品
    results.append("\n【大宗商品】")
    results.append(get_commodities())
    
    # 3. A 股指数
    results.append("\n【A 股指数】")
    results.append(get_a_shares())
    
    # 4. 打新提醒
    results.append("\n【申购提醒】")
    results.append(get_convertible_bond())
    
    full_report = "\n".join(results)
    print("\n--- 生成的报表 ---\n")
    print(full_report)
    
    send_to_feishu(full_report)