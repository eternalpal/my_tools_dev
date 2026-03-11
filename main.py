import datetime
import requests

def get_current_time():
    """获取当前北京时间"""
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def send_message(content):
    """模拟推送消息（可替换为企业微信/钉钉/Server酱等真实推送渠道）"""
    print(f"【推送消息】{content}")
    # 示例：如果用Server酱推送（需替换为自己的SCKEY）
    # url = "https://sctapi.ftqq.com/SC123456.send"  # 替换为你的SCKEY
    # data = {"text": "定时任务通知", "desp": content}
    # requests.post(url, data=data)

if __name__ == "__main__":
    current_time = get_current_time()
    # 自定义推送内容
    content = f"当前北京时间：{current_time}\n这是GitHub Actions定时触发的消息！"
    send_message(content)