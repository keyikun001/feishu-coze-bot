"""
飞书 + 扣子机器人对接服务
适合小白使用的简化版本
"""

import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ========== 配置信息（需要你填写）==========
# 飞书配置
FEISHU_APP_ID = "cli_a90af75703791cd9"  # 你的App ID
FEISHU_APP_SECRET = "KshAbqeEAkIy0QgYrpc0Kgv54ojkzkKE"  # 【重要】替换成你的真实Secret

# 扣子配置
COZE_API_URL = "https://3zqbsbrbyz.coze.site/stream_run"
COZE_API_TOKEN = "pat_ywD1J2fekVbT5LRXsSnZajy3EpBGBJcZk7eszDSy5ccZ9ae6IpM1DKkgI7WUqYZs"  # 【重要】替换成你的真实Token（pat_开头）

# ========== 功能函数 ==========

def get_tenant_access_token():
    """获取飞书访问凭证"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        return result.get("tenant_access_token")
    except Exception as e:
        print(f"获取token失败: {e}")
        return None


def send_feishu_message(open_id, content):
    """发送消息到飞书"""
    token = get_tenant_access_token()
    if not token:
        return {"error": "无法获取访问令牌"}
    
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
    try:
        response = requests.post(url, headers=headers, params=params, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"发送消息失败: {e}")
        return {"error": str(e)}


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
        
        # 根据扣子返回格式提取回复
        if isinstance(result, dict):
            return result.get('answer', str(result))
        return str(result)
    except Exception as e:
        print(f"调用扣子API失败: {e}")
        return f"抱歉，AI暂时无法回复：{str(e)}"


# ========== 路由处理 ==========

@app.route('/feishu/event', methods=['POST'])
def feishu_event():
    """接收飞书事件"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data"}), 400
        
        print(f"收到请求: {json.dumps(data, ensure_ascii=False)}")
        
        # 1. URL验证（首次配置时）
        if data.get("type") == "url_verification":
            challenge = data.get("challenge",
