import requests
import os
import json
import datetime
import yfinance as yf
import akshare as ak

def get_crypto():
    """获取 ETH 价格"""
    url = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
    res = requests.get(url).json()
    return f"ETH: ${round(float(res['price']), 2)}"

def get_commodities():
    """获取白银和原油价格 (Yahoo Finance)"""
    # SI=F 是白银, CL=F 是原油
    data = yf.download(["SI=F", "CL=F"], period="1d", interval="1m")
    silver = round(data['Close']['SI=F'].iloc[-1], 3)
    oil = round(data['Close']['CL=F'].iloc[-1], 2)
    return f"白银: ${silver} | 原油: ${oil}"

def get_a_shares():
    """获取 A 股指数 (AkShare)"""
    # 获取实时行情
    df = ak.stock_zh_index_spot() 
    # 筛选我们需要的部分指数
    target_indices = {
        "000905": "中证500",
        "399006": "创业板指",
        "000688": "科创50"
    }
    result = []
    for code, name in target_indices.items():
        row = df[df['代码'].str.contains(code)]
        if not row.empty:
            price = row['最新价'].values[0]
            change = row['涨跌额'].values[0]
            result.append(f"{name}: {price} ({change})")
    return "\n".join(result)

def get_convertible_bond():
    """获取今日是否有可转债打新"""
    df = ak.bond_zh_cov_ipo_summary()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # 筛选申购日期是今天的债
    today_bonds = df[df['申购日期'] == today]
    if today_bonds.empty:
        return "今日无新债申购"
    else:
        names = today_bonds['债券简称'].tolist()
        return f"今日打新提醒: {', '.join(names)}"

def send_to_feishu(content):
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    msg = {
        "msg_type": "text",
        "content": {"text": f"📊 金融市场监控报表\n{'-'*20}\n{content}\n{'-'*20}\n时间: {datetime.datetime.now()}"}
    }
    requests.post(webhook_url, json=msg)

if __name__ == "__main__":
    try:
        reports = []
        reports.append(f"【加密货币】\n{get_crypto()}")
        reports.append(f"\n【大宗商品】\n{get_commodities()}")
        reports.append(f"\n【A 股指数】\n{get_a_shares()}")
        reports.append(f"\n【打新提醒】\n{get_convertible_bond()}")
        
        full_report = "\n".join(reports)
        print(full_report)
        send_to_feishu(full_report)
    except Exception as e:
        print(f"运行出错: {e}")