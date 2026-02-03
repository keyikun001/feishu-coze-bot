# 1. URL验证（首次配置时）
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            print(f"URL验证请求，返回challenge: {challenge}")
            return jsonify({"challenge": challenge})
        
        # 2. 处理消息事件
        event_type = data.get("header", {}).get("event_type")
        
        if event_type == "im.message.receive_v1":
            event = data.get("event", {})
            
            # 提取消息内容
            message = event.get("message", {})
            content_str = message.get("content", "{}")
            
            try:
                content = json.loads(content_str)
                user_message = content.get("text", "").strip()
            except:
                user_message = ""
            
            # 提取发送者ID
            sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id")
            
            print(f"消息内容: {user_message}, 发送者: {sender_id}")
            
            if user_message and sender_id:
                # 调用扣子API
                ai_response = call_coze_api(user_message)
                print(f"AI回复: {ai_response}")
                
                # 发送回复到飞书
                send_result = send_feishu_message(sender_id, ai_response)
                print(f"发送结果: {send_result}")
        
        return jsonify({"code": 0, "msg": "success"})
    
    except Exception as e:
        print(f"处理事件出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": -1, "msg": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        "name": "飞书扣子机器人",
        "status": "running",
        "endpoints": {
            "/health": "健康检查",
            "/feishu/event": "飞书事件回调"
        }
    })


# Vercel需要的handler
app_handler = app
```

3. **确认代码完整后，点击 `Commit changes`**

4. **等待1-2分钟让Vercel重新部署**

---

## ✅ 部署完成后测试

1. **回到飞书开放平台的事件订阅页面**

2. **重新填写并保存**：
```
   https://feishu-coze-bot.vercel.app/feishu/event
