import os
import sys
import base64
import tempfile
from pprint import pprint
from typing import Optional, List, Dict, Any
from flask import Flask, request, jsonify

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
from agents import ReActAgent
# from qwen_agent.gui import WebUI  # 不再需要WebUI
from recognition import parse
# from planner import TaskDecomposer
from tools import MyImageGen, TextToSpeech

ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')

os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d'
os.environ['GRADIO_SERVER_PORT'] = '12000'

# 全局agent实例
bot = None

def init_agent_service():
    llm_cfg = {
        'model': 'qwen-max',
        'model_server': 'dashscope',
        'api_key': os.getenv('DASHSCOPE_API_KEY'),
    }
    tools = [
        # TaskDecomposer(),
        MyImageGen(),
        TextToSpeech(),
        # PhoneCallHandler(),
    ]
    return ReActAgent(
        llm=llm_cfg,
        name='general agent',
        description='This agent can solve the problem',
        function_list=tools
    )

app = Flask(__name__)

def process_content(content: List[Dict[str, Any]]) -> tuple:
    """
    处理请求内容，分离文本、图片和其他类型
    返回: (文本内容, 图片base64列表, 其他内容)
    """
    text_content = ""
    images = []
    other_content = []
    
    for item in content:
        if 'text' in item:
            text_content += item['text'] + "\n"
        elif 'image' in item:
            images.append(item['image'])
        else:
            other_content.append(item)
    
    return text_content.strip(), images, other_content

def save_base64_image(image_data: str) -> str:
    """
    将base64图片保存为临时文件，返回文件路径
    """
    # 分离MIME类型和实际数据
    if ',' in image_data:
        mime_type, base64_str = image_data.split(',', 1)
    else:
        mime_type = 'image/png'
        base64_str = image_data
    
    # 确定文件扩展名
    if 'png' in mime_type:
        ext = 'png'
    elif 'jpeg' in mime_type or 'jpg' in mime_type:
        ext = 'jpg'
    else:
        ext = 'png'  # 默认
    
    # 解码并保存
    image_bytes = base64.b64decode(base64_str)
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
        f.write(image_bytes)
        return f.name

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    global bot
    if bot is None:
        bot = init_agent_service()
    
    # 解析请求数据
    data = request.json
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    
    # 只处理最后一条用户消息
    last_message = messages[-1]
    if last_message['role'] != 'user':
        return jsonify({"error": "Last message should be from user"}), 400
    
    # 处理消息内容
    content = last_message.get('content', [])
    text_content, images, other_content = process_content(content)
    
    # 如果有图片，保存为临时文件
    image_files = []
    for img in images:
        try:
            img_path = save_base64_image(img)
            image_files.append(img_path)
        except Exception as e:
            print(f"Error processing image: {str(e)}")
    
    # 构建agent输入
    agent_input = []
    if text_content:
        agent_input.append({'text': text_content})
    for img_path in image_files:
        agent_input.append({'file': img_path})
    
    # 运行agent
    try:
        response = None
        for r in bot.run([{'role': 'user', 'content': agent_input}]):
            response = r
        
        # 处理agent响应
        if response:
            last_response = response[-1]
            if last_response['role'] == 'assistant':
                assistant_content = last_response['content']
                
                # 解析响应内容
                response_content = []
                text_response = ""
                audio_data = None
                image_data = None
                
                if isinstance(assistant_content, str):
                    text_response = assistant_content
                elif isinstance(assistant_content, list):
                    for item in assistant_content:
                        if isinstance(item, dict):
                            if 'text' in item:
                                text_response += item['text'] + "\n"
                            elif 'file' in item:
                                file_path = item['file']
                                if file_path.endswith(('.mp3', '.wav')):
                                    # 处理音频文件
                                    with open(file_path, 'rb') as f:
                                        audio_data = base64.b64encode(f.read()).decode('utf-8')
                                    os.unlink(file_path)  # 删除临时文件
                                elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                                    # 处理图片文件
                                    with open(file_path, 'rb') as f:
                                        image_data = base64.b64encode(f.read()).decode('utf-8')
                                    os.unlink(file_path)  # 删除临时文件
                
                # 构建响应内容
                if text_response.strip():
                    response_content.append({"text": text_response.strip()})
                if audio_data:
                    response_content.append({"audio": audio_data, "mime_type": "audio/mp3"})
                if image_data:
                    response_content.append({"image": image_data, "mime_type": "image/png"})
                
                # 删除用户上传的临时图片
                for img_path in image_files:
                    if os.path.exists(img_path):
                        os.unlink(img_path)
                
                return jsonify({
                    "messages": [{
                        "role": "assistant",
                        "content": response_content
                    }]
                })
    except Exception as e:
        print(f"Error during agent execution: {str(e)}")
        return jsonify({"error": "Agent execution failed"}), 500
    
    return jsonify({"messages": []})

if __name__ == '__main__':
    # 初始化agent
    bot = init_agent_service()
    app.run(host="0.0.0.0", port=12000, debug=True)