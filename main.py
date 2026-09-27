## v4.0 (Current)
## 增加一个A股新股发行的内容，检索是否有新股发行，包括沪深A股各个板块，北京交易所等。
## 增加一个未来发行新股，新可转债的内容，用来提示未来附近时间将要发现的新股，可转债。

import requests
import os
import datetime
import yfinance as yf
import pandas as pd
import re

def get_beijing_time():
    """获取标准北京时间 (UTC+8)"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def get_intl_data(ticker_code, name, is_index=False):
    """通过 yfinance 获取最新价格与基于昨收价的精准涨跌幅"""
    print(f"正在同步 {name}...")
    try:
        tk = yf.Ticker(ticker_code)
        info = tk.fast_info
        
        current_price = info.get('last_price')
        prev_close = info.get('previous_close')
        
        if current_price is None or prev_close is None:
            hist = tk.history(period="5d").dropna(subset=['Close'])
            if len(hist) < 2:
                return f"{name}: 数据不足"
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]

        change_pct = (current_price - prev_close) / prev_close * 100
        direction = "📈" if change_pct >= 0 else "📉"
        
        prefix = "" if is_index else "$"
        p_fmt = f"{current_price:.3f}" if "SI=F" in ticker_code else f"{current_price:.2f}"
        return f"{name}: {prefix}{p_fmt} ({direction}{change_pct:+.2f}%)"
    except Exception as e:
        print(f"❌ {name} 获取异常: {e}")
        return f"{name}: 获取失败"

def get_a_shares():
    """通过新浪原生 API 获取 A 股指数（规避机房 IP 拦截）"""
    print("正在同步 A 股指数...")
    codes = "s_sh000905,s_sz399006,s_sh000688"
    url = f"http://hq.sinajs.cn/list={codes}"
    headers = {"Referer": "http://finance.sina.com.cn"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        matches = re.findall(r'"(.*?)"', response.text)
        results = []
        for match in matches:
            if not match: continue
            data = match.split(',')
            name, price, change_pct = data[0], data[1], data[3]
            dir_icon = "📈" if float(change_pct) >= 0 else "📉"
            results.append(f"{name}: {float(price):.2f} ({dir_icon}{change_pct}%)")
        return "\n".join(results) if results else "A 股数据为空"
    except Exception as e:
        print(f"❌ A 股指数获取异常: {e}")
        return "A 股指数获取失败"

def get_ipo_stocks(today_date, future_limit):
    """获取全市场新股申购（主板、创业板、科创板、北交所）"""
    print("正在检索 A 股新股发行信息...")
    today_list = []
    future_list = []
    try:
        import akshare as ak
        # symbol="全部股票" 覆盖沪深主板、科创板、创业板、北交所全板块
        df = ak.stock_xgsglb_em(symbol="全部股票")
        
        date_col = next((c for c in df.columns if '申购日期' in c or '发行日期' in c), '申购日期')
        name_col = next((c for c in df.columns if '简称' in c), '股票简称')
        code_col = next((c for c in df.columns if '申购代码' in c or '代码' in c), '申购代码')
        board_col = next((c for c in df.columns if '板块' in c or '交易所' in c), None)

        df['clean_date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
        df = df.dropna(subset=['clean_date'])

        # 1. 今日新股
        df_today = df[df['clean_date'] == today_date]
        for _, row in df_today.iterrows():
            name = str(row[name_col]).strip()
            code = str(row[code_col]).strip()
            board = f"[{row[board_col]}]" if board_col and pd.notna(row[board_col]) else ""
            today_list.append(f"{name}({code}) {board}".strip())

        # 2. 未来 7 天待发新股
        df_future = df[(df['clean_date'] > today_date) & (df['clean_date'] <= future_limit)]
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for _, row in df_future.iterrows():
            d = row['clean_date']
            d_str = d.strftime('%m-%d')
            w_str = weekdays[d.weekday()]
            name = str(row[name_col]).strip()
            code = str(row[code_col]).strip()
            board = f"[{row[board_col]}]" if board_col and pd.notna(row[board_col]) else ""
            future_list.append((d, f"{d_str}({w_str}) [新股] {name}({code}) {board}".strip()))

    except Exception as e:
        print(f"❌ 新股数据获取异常: {e}")
        
    return today_list, future_list

def get_ipo_bonds(today_date, future_limit):
    """获取可转债发行信息（今日与未来预告）"""
    print("正在检索可转债发行信息...")
    today_list = []
    future_list = []
    import akshare as ak
    
    df = None
    # 优先同花顺，备选东财
    try:
        df = ak.bond_zh_cov_info_ths()
    except Exception as e:
        print(f"同花顺接口失败，转东财: {e}")
        try:
            df = ak.bond_cov_comparison()
        except:
            pass

    if df is not None and not df.empty:
        try:
            date_col = next((c for c in df.columns if '申购日期' in c or '发行日期' in c), '申购日期')
            name_col = next((c for c in df.columns if '简称' in c), '债券简称')
            code_col = next((c for c in df.columns if '代码' in c), '债券代码')

            df['clean_date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
            df = df.dropna(subset=['clean_date'])

            # 1. 今日转债
            df_today = df[df['clean_date'] == today_date]
            for _, row in df_today.iterrows():
                name = str(row[name_col]).strip()
                code = str(row[code_col]).strip()
                today_list.append(f"{name}({code})")

            # 2. 未来 7 天待发转债
            df_future = df[(df['clean_date'] > today_date) & (df['clean_date'] <= future_limit)]
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            for _, row in df_future.iterrows():
                d = row['clean_date']
                d_str = d.strftime('%m-%d')
                w_str = weekdays[d.weekday()]
                name = str(row[name_col]).strip()
                code = str(row[code_col]).strip()
                future_list.append((d, f"{d_str}({w_str}) [转债] {name}({code})"))
        except Exception as e:
            print(f"❌ 解析可转债失败: {e}")

    return today_list, future_list

def get_subscription_calendar():
    """整合新股与可转债的打新日历（今日 + 未来 7 天）"""
    bj_now = get_beijing_time()
    today_date = bj_now.date()
    future_limit = today_date + datetime.timedelta(days=7) # 扫描未来 7 天内

    # 获取数据
    today_stocks, future_stocks = get_ipo_stocks(today_date, future_limit)
    today_bonds, future_bonds = get_ipo_bonds(today_date, future_limit)

    output = []

    # 1. 组装【今日申购】
    output.append("🔔【今日打新】")
    has_today = False
    if today_stocks:
        output.append(f"• 新股: {', '.join(today_stocks)}")
        has_today = True
    if today_bonds:
        output.append(f"• 转债: {', '.join(today_bonds)}")
        has_today = True
    if not has_today:
        output.append("• 今日暂无新股/新债申购")

    # 2. 组装【未来待发预告】
    output.append("\n📅【未来预告 (7天内)】")
    # 合并未来日程并按实际日期升序排序
    all_future = future_stocks + future_bonds
    all_future.sort(key=lambda x: x[0])
    
    if all_future:
        for _, text in all_future:
            output.append(f"• {text}")
    else:
        output.append("• 近期 7 天内暂无待申购安排")

    return "\n".join(output)

def send_to_feishu(content):
    """推送通知到飞书群（支持多 Webhook）"""
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    if not webhook_url:
        print("⚠️ 未配置 FEISHU_WEBHOOK")
        return
    
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
    
    for url in webhook_url.split(','):
        u = url.strip()
        if not u: continue
        try:
            requests.post(u, json=msg, timeout=15)
            print("消息已推送到飞书")
        except Exception as e:
            print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    print("=== 开始执行金融监控任务 ===")
    
    # 1. 国际市场 & 美股指数
    intl_market = [
        "【加密货币】",
        get_intl_data("BTC-USD", "BTC"),
        get_intl_data("ETH-USD", "ETH"),
        "\n【美股指数】",
        get_intl_data("^GSPC", "标普500", is_index=True),
        get_intl_data("^IXIC", "纳斯达克", is_index=True),
        "\n【大宗商品】",
        get_intl_data("GC=F", "黄金"),
        get_intl_data("SI=F", "白银"),
        get_intl_data("CL=F", "原油")
    ]
    
    # 2. 组装整份报表
    report = [
        "\n".join(intl_market),
        "\n【A 股指数】",
        get_a_shares(),
        "\n【打新日历】",
        get_subscription_calendar()
    ]
    
    final_report = "\n".join(report)
    print("\n--- 报表预览 ---\n" + final_report + "\n")
    
    send_to_feishu(final_report)
    print("=== 任务执行完毕 ===")