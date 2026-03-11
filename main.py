import requests
import datetime
import os
import json

def get_bitcoin_price():
    """
    多数据源备份获取价格：依次尝试 币安、Coinbase、Kraken
    """
    sources = [
        {
            "name": "Binance",
            "url": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            "parse": lambda d: round(float(d["price"]), 2)
        },
        {
            "name": "Coinbase",
            "url": "https://api.coinbase.com/v2/prices/BTC-USD/spot",
            "parse": lambda d: round(float(d["data"]["amount"]), 2)
        },
        {
            "name": "Kraken",
            "url": "https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD",
            "parse": lambda d: round(float(d["result"]["XXBTZUSD"]["c"][0]), 2)
        }
    ]

    errors = []
    for source in sources:
        try:
            print(f"正在尝试从 {source['name']} 获取价格...")
            response = requests.get(source['url'], timeout=10)
            response.raise_for_status() # 如果返回 403 等错误会抛出异常
            data = response.json()
            price = source['parse'](data)
            print(f"✅ 成功从 {source['name']} 获取价格: {price}")
            return price, source['name']
        except Exception as e:
            error_msg = f"{source['name']} 失败: {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
    
    # 如果全部失败，抛出异常
    raise Exception(f"所有接口均不可用: {'; '.join(errors)}")

def send_to_feishu(message):
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    if not webhook_url:
        print("❌ 未设置 FEISHU_WEBHOOK")
        return

    headers = {'Content-Type': 'application/json'}
    payload = {"msg_type": "text", "content": {"text": message}}
    
    try:
        requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        print("🚀 消息已推送到飞书")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        price, source_name = get_bitcoin_price()
        msg = (f"🔔 比特币价格早报\n"
               f"------------------\n"
               f"当前价格: ${price} USD\n"
               f"数据来源: {source_name}\n"
               f"获取时间: {now} (UTC)\n"
               f"------------------\n"
               f"注：来自 GitHub Actions 自动推送")
    except Exception as e:
        msg = f"❌ 比特币任务运行失败\n时间: {now}\n错误原因: {str(e)}"

    print(msg)
    send_to_feishu(msg)