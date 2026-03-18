import requests
import os
import datetime
import yfinance as yf
import akshare as ak
import pandas as pd

def get_beijing_time():
    """获取北京时间对象"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def get_international_markets():
    """
    使用 yfinance 一次性获取加密货币和大宗商品的价格及涨跌幅
    BTC, ETH, 黄金(GC=F), 白银(SI=F), 原油(CL=F)
    """
    print("正在获取国际市场数据(yfinance)...")
    tickers = {
        "BTC-USD": "BTC",
        "ETH-USD": "ETH",
        "GC=F": "黄金",
        "SI=F": "白银",
        "CL=F": "原油"
    }
    
    results = {"crypto": [], "commodity": []}
    
    try:
        # 下载最近2天的数据以计算涨跌幅
        data = yf.download(list(tickers.keys()), period="2d", interval="1d", group_by='ticker', progress=False)
        
        for ticker, name in tickers.items():
            try:
                # 获取该代码的数据
                df = data[ticker]
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                
                # 计算涨跌幅
                change_pct = (current_price - prev_price) / prev_price * 100
                direction = "📈" if change_pct >= 0 else "📉"
                
                # 格式化输出
                formatted_str = f"{name}: ${current_price:.2f} ({direction}{change_pct:+.2f}%)"
                
                if "USD" in ticker:
                    results["crypto"].append(formatted_str)
                else:
                    results["commodity"].append(formatted_str)
            except:
                results["crypto" if "USD" in ticker else "commodity"].append(f"{name}: 获取失败")
    except Exception as e:
        print(f"yfinance 运行异常: {e}")
        
    return results

def get_a_shares():
    """A股指数：东财 vs 新浪 (双备份)"""
    print("正在获取A股指数...")
    try:
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
        targets = ["中证500", "创业板指", "科创50"]
        res = []
        for name in targets:
            row = df[df['名称'] == name]
            if not row.empty:
                change = row['涨跌幅'].values[0]
                dir_icon = "📈" if float(change) >= 0 else "📉"
                res.append(f"{name}: {row['最新价'].values[0]} ({dir_icon}{change}%)")
        if res: return "\n".join(res)
    except:
        return "A股指数获取失败 (EM)"

def get_convertible_bond():
    """可转债打新：同花顺 vs 东财 (双备份)"""
    print("正在获取可转债信息...")
    bj_today = get_beijing_time().strftime("%Y-%m-%d")
    
    # 尝试同花顺
    try:
        df = ak.bond_zh_cov_info_ths()
        df['申购日期'] = pd.to_datetime(df['申购日期'], errors='coerce').dt.strftime('%Y-%m-%d')
        target = df[df['申购日期'] == bj_today]
        if not target.empty:
            return f"🔔 今日打新: {', '.join(target['债券简称'].tolist())}"
    except:
        pass

    # 尝试东财
    try:
        df = ak.bond_cov_comparison()
        df['申购日期'] = pd.to_datetime(df['申购日期'], errors='coerce').dt.strftime('%Y-%m-%d')
        target = df[df['申购日期'] == bj_today]
        if not target.empty:
            return f"🔔 今日打新: {', '.join(target['证券简称'].tolist())}"
    except:
        pass

    return "今日无新债申购"

def send_to_feishu(content):
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    if not webhook_url: return
    
    bj_now = get_beijing_time()
    date_head = bj_now.strftime("%Y年%m月%d日")
    time_str = bj_now.strftime("%H:%M:%S")

    # 构建最终消息体
    full_msg = (
        f"📅 【{date_head}】行情日报\n"
        f"{'='*25}\n"
        f"{content}\n"
        f"{'='*25}\n"
        f"💡 更新时间: 北京 {time_str}"
    )

    msg = {"msg_type": "text", "content": {"text": full_msg}}
    requests.post(webhook_url, json=msg, timeout=15)
    print("消息已推送到飞书")

if __name__ == "__main__":
    print("开始执行金融监控任务...")
    
    # 1. 获取国际市场
    intl_data = get_international_markets()
    
    # 2. 组装报表
    report_sections = [
        "【加密货币】",
        "\n".join(intl_data["crypto"]),
        "\n【大宗商品】",
        "\n".join(intl_data["commodity"]),
        "\n【A 股指数】",
        get_a_shares(),
        "\n【申购提醒】",
        get_convertible_bond()
    ]
    
    final_content = "\n".join(report_sections)
    print("\n--- 预览 ---\n" + final_content)
    
    # 3. 推送
    send_to_feishu(final_content)