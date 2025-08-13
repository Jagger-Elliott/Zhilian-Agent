import requests
import uuid
 
# 1. 通过获取其代理卡片发现代理
AGENT_BASE_URL = "http://localhost:5000"
agent_card_url = f"{AGENT_BASE_URL}/.well-known/agent.json"
response = requests.get(agent_card_url)
if response.status_code != 200:
    raise RuntimeError(f"Failed to get agent card: {response.status_code}")
agent_card = response.json()
print("Discovered Agent:", agent_card["name"], "-", agent_card.get("description", ""))
 
# 2. 为代理准备任务请求
task_id = str(uuid.uuid4())  # 生成一个随机唯一任务ID
user_text = "帮我查一下当前微博热搜前十条？"
task_payload = {
    "id": task_id,
    "message": {
        "role": "user",
        "parts": [
            {"text": user_text}
        ]
    }
}
 
# 3. 将任务发送到代理的 tasks/send 端点
tasks_send_url = f"{AGENT_BASE_URL}/tasks/send"
result = requests.post(tasks_send_url, json=task_payload)
if result.status_code != 200:
    raise RuntimeError(f"Task request failed: {result.status_code}, {result.text}")
task_response = result.json()
 
# 4. 处理代理的响应
# 响应应包含任务ID、状态和消息（包括代理的回复）。
if task_response.get("status", {}).get("state") == "completed":
    # 列表中的最后一条消息应该是代理的答案（因为我们的代理在消息中包含历史）。
    messages = task_response.get("messages", [])
    if messages:
        agent_message = messages[-1]  # 最后一条消息（来自代理）
        agent_reply_text = ""
        # 从代理的消息部分中提取文本
        for part in agent_message.get("parts", []):
            if "text" in part:
                agent_reply_text += part["text"]
        print("Agent's reply:", agent_reply_text)
    else:
        print("No messages in response!")
else:
    print("Task did not complete. Status:", task_response.get("status"))