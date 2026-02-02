"""
飞书 + 扣子机器人对接服务
适合小白使用的简化版本
"""

import json
import requests
import hashlib
import base64
from flask import Flask, request

app = Flask(__name__)

# ========== 配置信息（需要你填写）==========
# 飞书配置
FEISHU_APP_ID = "cli_a90af75703791cd9"  # 替换成你的
FEISHU_APP_SECRET = "KshAbqeEAkIy0QgYrpc0Kgv54ojkzkKE"  # 替换成你的
FEISHU_VERIFICATION_TOKEN = ""  # 稍后会自动生成

# 扣子配置
COZE_API_URL = "https://3zqbsbrbyz.coze.site/stream_run"
COZE_API_TOKEN = "pat_PCws1DeeoWICjkMhB2wwXPCOduJhIBXyQWmNn7qzrNxqtRrC5kgpB0aCyrjyzmfh"  # 替换成你的

# ========== 功能函数 ==========

def get_tenant_access_token():
    """获取飞书访问凭证"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json().get("tenant_access_token")


def send_feishu_message(open_id, content):
    """发送消息到飞书"""
    token = get_tenant_access_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {"receive_id_type": "open_id"}
    data = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    response = requests.post(url, headers=headers, params=params, json=data)
    return response.json()


def call_coze_api(user_message):
    """调用扣子API"""
    headers = {
        "Authorization": f"Bearer {COZE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "content": {
            "query": {
                "prompt": [
                    {
                        "type": "text",
                        "content": {"text": user_message}
                    }
                ]
            }
        }
    }
    
    try:
        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # 根据扣子返回格式提取回复（可能需要调整）
        if isinstance(result, dict):
            return result.get('answer', str(result))
        return str(result)
    except Exception as e:
        return f"抱歉，调用AI时出错了：{str(e)}"


# ========== 路由处理 ==========

@app.route('/feishu/event', methods=['POST'])
def feishu_event():
    """接收飞书事件"""
    data = request.json
    
    # 1. 验证URL（首次配置时飞书会发送）
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}
    
    # 2. 处理消息事件
    if data.get("header", {}).get("event_type") == "im.message.receive_v1":
        event = data.get("event", {})
        
        # 提取消息内容
        message = event.get("message", {})
        content = json.loads(message.get("content", "{}"))
        user_message = content.get("text", "").strip()
        
        # 提取发送者ID
        sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id")
        
        if user_message and sender_id:
            print(f"收到消息: {user_message}")
            
            # 调用扣子API
            ai_response = call_coze_api(user_message)
            print(f"AI回复: {ai_response}")
            
            # 发送回复到飞书
            send_feishu_message(sender_id, ai_response)
    
    return {"code": 0}


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == '__main__':
    print("=" * 50)
    print("飞书扣子机器人已启动！")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
