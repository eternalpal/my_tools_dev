import requests
import os
import datetime
import yfinance as yf
import pandas as pd
import re

def get_beijing_time():
    """获取北京时间"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def get_intl_data(ticker_code, name, is_index=False):
    """
    通过 yfinance 获取最新价格和准确的昨收价计算涨跌幅
    """
    print(f"正在同步 {name}...")
    try:
        tk = yf.Ticker(ticker_code)
        info = tk.fast_info
        
        current_price = info['last_price']
        prev_close = info['previous_close']
        
        # 容错：如果 fast_info 失败，尝试 history
        if current_price is None or prev_close is None:
            hist = tk.history(period="2d")
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]

        change_pct = (current_price - prev_close) / prev_close * 100
        direction = "📈" if change_pct >= 0 else "📉"
        
        # 格式化价格：指数不带 $ 符号，商品/币带 $
        prefix = "" if is_index else "$"
        # 白银保留三位，其余两位
        p_fmt = f"{current_price:.3f}" if "SI=F" in ticker_code else f"{current_price:.2f}"
        
        return f"{name}: {prefix}{p_fmt} ({direction}{change_pct:+.2f}%)"
    except Exception as e:
        print(f"{name} 获取异常: {e}")
        return f"{name}: 获取失败"

def get_a_shares():
    """直接请求新浪财经 API 获取 A 股实时数据"""
    print("正在同步 A 股指数...")
    codes = "s_sh000905,s_sz399006,s_sh000688"
    url = f"http://hq.sinajs.cn/list={codes}"
    headers = {"Referer": "http://finance.sina.com.cn"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        matches = re.findall(r'"(.*?)"', response.text)
        results = []
        for match in matches:
            data = match.split(',')
            name, price, change_pct = data[0], data[1], data[3]
            dir_icon = "📈" if float(change_pct) >= 0 else "📉"
            results.append(f"{name}: {float(price):.2f} ({dir_icon}{change_pct}%)")
        return "\n".join(results)
    except Exception as e:
        return "A 股指数获取失败"

def get_convertible_bond():
    """可转债打新：同花顺源"""
    import akshare as ak
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

if __name__ == "__main__":
    # 1. 国际市场 & 美股指数
    intl_market = [
        "【加密货币】",
        get_intl_data("BTC-USD", "BTC"),
        get_intl_data("ETH-USD", "ETH"),
        get_intl_data("SOL-USD", "SOL"),
        "\n【美股指数】",
        get_intl_data("^GSPC", "标普500", is_index=True),
        get_intl_data("^IXIC", "纳斯达克", is_index=True),
        "\n【大宗商品】",
        get_intl_data("GC=F", "黄金"),
        get_intl_data("SI=F", "白银"),
        get_intl_data("CL=F", "原油")
    ]
    
    # 2. 组装最终报表
    report = [
        "\n".join(intl_market),
        "\n【A 股指数】",
        get_a_shares(),
        "\n【申购提醒】",
        get_convertible_bond()
    ]
    
    final_report = "\n".join(report)
    print(final_report)
    send_to_feishu(final_report)