import os
import time
import json5
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

AGENT_CARD = {
    "name": "EchoAgent",
    "description": "一个简单的代理，它会回显用户消息，并能用OpenAI整理微博热搜。",
    "url": "http://localhost:5000",
    "version": "1.0",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False
    }
}

# 从环境变量读取 API Key
client = OpenAI(

    api_key=os.getenv("DASHSCOPE_API_KEY"),  
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# 缓存配置
CACHE_DATA = None
CACHE_TIME = 0
CACHE_TTL = 300


@app.get("/.well-known/agent.json")
def get_agent_card():
    return jsonify(AGENT_CARD)


@app.post("/tasks/send")
def handle_task():
    global CACHE_DATA, CACHE_TIME
    task_request = request.get_json()
    task_id = task_request.get("id")

    try:
        top_k: int = task_request["message"]["parts"][0]["text"]
    except Exception:
        return jsonify({"error": "Invalid request format"}), 400

    now = time.time()
    if CACHE_DATA and (now - CACHE_TIME) < CACHE_TTL:
        print("使用缓存结果")
        final_text = CACHE_DATA
    else:
        print("调用微博 API + OpenAI SDK")
        weibo_url = "https://v2.xxapi.cn/api/weibohot"
        response = requests.get(weibo_url)
        if response.status_code != 200:
            raise RuntimeError(f"Weibo API failed: {response.status_code}, {response.text}")
        weibo_data = response.json()["data"][:top_k]

        prompt = (f"""
            你是一个榜单整理助手，请将下面的微博热搜数据整理成美观的前{top_k}榜单。
            要求：
            - 输出标题为“🔥 今日微博热搜 TOP {top_k}”
            - 使用 1️⃣、2️⃣、3️⃣... 这样的emoji编号
            - 每行格式：编号  话题标题
            - 最后加上“━━━━━━━━━━━━━━━━━━━━\n数据来源：微博热搜”
            - 不要添加多余解释，不要额外文字

            微博热搜原始数据：
            {json5.dumps(weibo_data, ensure_ascii=False)}
            """)

        completion = client.chat.completions.create(
            model="Moonshot-Kimi-K2-Instruct",
            messages=[
                {"role": "system", "content": "你是一个微博热搜数据整理助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        final_text = completion.choices[0].message.content.strip()

        CACHE_DATA = final_text
        CACHE_TIME = now

    response_task = {
        "id": task_id,
        "status": {"state": "completed"},
        "messages": [
            task_request.get("message", {}),
            {
                "role": "agent",
                "parts": [{"text": final_text}]
            }
        ]
    }
    return jsonify(response_task)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
