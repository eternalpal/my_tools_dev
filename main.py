import requests
import os
import datetime
import yfinance as yf
import pandas as pd
import re

def get_beijing_time():
    """获取北京时间"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def get_intl_data(ticker_code, name):
    """
    通过 yfinance 获取最新价格和准确的昨收价计算涨跌幅
    """
    print(f"正在同步 {name}...")
    try:
        tk = yf.Ticker(ticker_code)
        # 获取 fast_info 数据，这包含交易所定义的昨收价
        info = tk.fast_info
        
        current_price = info['last_price']
        prev_close = info['previous_close']
        
        if not current_price or not prev_close:
            # 如果 fast_info 为空，退回到 history 获取
            hist = tk.history(period="2d")
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]

        change_pct = (current_price - prev_close) / prev_close * 100
        direction = "📈" if change_pct >= 0 else "📉"
        
        # 价格精度格式化
        p_fmt = f"{current_price:.3f}" if "SI=F" in ticker_code else f"{current_price:.2f}"
        return f"{name}: ${p_fmt} ({direction}{change_pct:+.2f}%)"
    except Exception as e:
        return f"{name}: 获取失败"

def get_a_shares():
    """
    直接请求新浪财经 API 获取 A 股实时数据 (最准确、防封锁)
    """
    print("正在同步 A 股指数...")
    # s_sh000905 中证500, s_sz399006 创业板, s_sh000688 科创50
    codes = "s_sh000905,s_sz399006,s_sh000688"
    url = f"http://hq.sinajs.cn/list={codes}"
    headers = {"Referer": "http://finance.sina.com.cn"} # 新浪必须带 referer
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        text = response.text
        # 解析数据，示例: var hq_str_s_sh000905="中证500,5322.84,18.23,0.34,1234,5678";
        matches = re.findall(r'"(.*?)"', text)
        results = []
        for match in matches:
            data = match.split(',')
            name, price, _, change_pct = data[0], data[1], data[2], data[3]
            dir_icon = "📈" if float(change_pct) >= 0 else "📉"
            results.append(f"{name}: {float(price):.2f} ({dir_icon}{change_pct}%)")
        return "\n".join(results)
    except Exception as e:
        print(f"新浪接口异常: {e}")
        return "A 股指数获取失败"

def get_convertible_bond():
    """可转债打新：同花顺源"""
    import akshare as ak # 仅在此处按需引入
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
    # 国际市场数据 (yfinance 使用交易所定义的昨收价)
    intl_list = [
        "【加密货币】",
        get_intl_data("BTC-USD", "BTC"),
        get_intl_data("ETH-USD", "ETH"),
        "\n【大宗商品】",
        get_intl_data("GC=F", "黄金"),
        get_intl_data("SI=F", "白银"),
        get_intl_data("CL=F", "原油")
    ]
    
    report = [
        "\n".join(intl_list),
        "\n【A 股指数】",
        get_a_shares(),
        "\n【申购提醒】",
        get_convertible_bond()
    ]
    
    final_report = "\n".join(report)
    print(final_report)
    send_to_feishu(final_report)