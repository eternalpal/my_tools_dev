import requests
import datetime
import os
import json

def get_bitcoin_price():
    url = "https://api.coindesk.com/v1/bpi/currentprice.json"
    response = requests.get(url)
    data = response.json()
    price = data["bpi"]["USD"]["rate"]
    return price

def send_to_feishu(message):
    # 从 GitHub 的环境变量中获取你的飞书 Webhook
    webhook_url = os.environ.get("FEISHU_WEBHOOK")
    
    if not webhook_url:
        print("❌ 错误：未找到 FEISHU_WEBHOOK 环境变量！")
        return

    # 飞书机器人要求的请求头和数据格式
    headers = {'Content-Type': 'application/json'}
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    
    # 发送推送请求
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("✅ 飞书推送成功！")
        else:
            print(f"❌ 飞书推送失败，状态码: {response.status_code}, 详情: {response.text}")
    except Exception as e:
        print(f"❌ 推送发生异常: {e}")

if __name__ == "__main__":
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price = get_bitcoin_price()
    
    # 组装我们要推送的消息字符串（如果飞书配置了自定义词，这里必须要包含那个词）
    msg = f"🔔 比特币价格早报\n获取时间: {now}\n当前价格: ${price} USD"
    
    print("开始执行任务...")
    print(msg)
    
    # 调用飞书推送函数
    send_to_feishu(msg)