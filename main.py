import requests
import os
import datetime
import yfinance as yf
import akshare as ak
import pandas as pd

def get_beijing_time():
    """获取北京时间对象"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def get_single_market_data(ticker_code, name):
    """
    单个获取市场数据，解决 NaN 问题
    """
    print(f"正在获取 {name} ({ticker_code}) 数据...")
    try:
        tk = yf.Ticker(ticker_code)
        # 获取最近5天数据，确保能拿到至少2个有效交易日
        df = tk.history(period="5d")
        
        if len(df) < 2:
            return f"{name}: 数据不足"
            
        # 剔除空值并取最后两行
        df = df.dropna(subset=['Close'])
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        
        change_pct = (current_price - prev_price) / prev_price * 100
        direction = "📈" if change_pct >= 0 else "📉"
        
        # 价格保留两位，白银和原油特殊处理
        price_fmt = f"{current_price:.3f}" if "SI=F" in ticker_code else f"{current_price:.2f}"
        
        return f"{name}: ${price_fmt} ({direction}{change_pct:+.2f}%)"
    except Exception as e:
        print(f"{name} 获取失败: {e}")
        return f"{name}: 获取失败"

def get_a_shares():
    """A股指数：改用新浪财经接口 (Sina)"""
    print("正在获取A股指数 (Sina)...")
    indices = {
        "sh000905": "中证500",
        "sz399006": "创业板指",
        "sh000688": "科创50"
    }
    res = []
    try:
        for code, name in indices.items():
            # 获取最近2日行情
            df = ak.stock_zh_index_daily(symbol=code)
            if df.empty: continue
            
            curr_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            curr_price = float(curr_row['close'])
            prev_price = float(prev_row['close'])
            
            change_pct = (curr_price - prev_price) / prev_price * 100
            dir_icon = "📈" if change_pct >= 0 else "📉"
            res.append(f"{name}: {curr_price:.2f} ({dir_icon}{change_pct:+.2f}%)")
        
        return "\n".join(res) if res else "A股数据为空"
    except Exception as e:
        print(f"A股接口异常: {e}")
        return "A股指数获取失败"

def get_convertible_bond():
    """可转债打新：同花顺源"""
    print("正在检查可转债...")
    bj_today = get_beijing_time().strftime("%Y-%m-%d")
    try:
        df = ak.bond_zh_cov_info_ths()
        df['申购日期'] = pd.to_datetime(df['申购日期'], errors='coerce').dt.strftime('%Y-%m-%d')
        target = df[df['申购日期'] == bj_today]
        if not target.empty:
            return f"🔔 今日打新: {', '.join(target['债券简称'].tolist())}"
    except:
        pass
    return "今日无新债申购"

def send_to_feishu(content):
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    if not webhook_url: return
    
    bj_now = get_beijing_time()
    # 按照要求修改日期头和尾部更新时间
    date_head = bj_now.strftime("%Y年%m月%d日")
    full_time_str = bj_now.strftime("%Y-%m-%d %H:%M:%S")

    full_msg = (
        f"📅 【{date_head}】行情日报\n"
        f"{'='*25}\n"
        f"{content}\n"
        f"{'='*25}\n"
        f"💡 更新时间: {full_time_str}"
    )

    msg = {"msg_type": "text", "content": {"text": full_msg}}
    requests.post(webhook_url, json=msg, timeout=15)
    print("消息已发送")

if __name__ == "__main__":
    # 1. 加密货币
    crypto_list = [
        get_single_market_data("BTC-USD", "BTC"),
        get_single_market_data("ETH-USD", "ETH")
    ]
    
    # 2. 大宗商品 (增加黄金 GC=F)
    commodity_list = [
        get_single_market_data("GC=F", "黄金"),
        get_single_market_data("SI=F", "白银"),
        get_single_market_data("CL=F", "原油")
    ]
    
    # 3. 组装内容
    report = [
        "【加密货币】",
        "\n".join(crypto_list),
        "\n【大宗商品】",
        "\n".join(commodity_list),
        "\n【A 股指数】",
        get_a_shares(),
        "\n【申购提醒】",
        get_convertible_bond()
    ]
    
    final_report = "\n".join(report)
    print("\n--- 最终预览 ---\n" + final_report)
    send_to_feishu(final_report)