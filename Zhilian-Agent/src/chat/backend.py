import os
import sys
import base64
import tempfile
from pprint import pprint
from typing import Optional, List, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import uuid
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
from agents import ReActAgent
# from qwen_agent.gui import WebUI  # 不再需要WebUI
from recognition import parse
from tools import MyImageGen, TextToSpeech, ImageUnderstanding, PhoneCallHandler, DatabaseQueryTool, database_description, HotSearch

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
        'multimodal': True,
        "max_input_tokens": 78500
    }
    tools = [
        # TaskDecomposer(),
        MyImageGen(),
        TextToSpeech(),
        ImageUnderstanding(),
        PhoneCallHandler(),
        HotSearch(),
        {
            "mcpServers": {
                "sqlite": {
                    "command": "uvx",
                    "args": [
                        "mcp-server-sqlite",
                        "--db-path",
                        "users.db"
                    ]
                },
                "amap-maps": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@amap/amap-maps-mcp-server"
                    ],
                    "env": {
                        "AMAP_MAPS_API_KEY": "2b5042a60254b76b209a898bc252fdd7"
                    }
                }
            }
        }
        # DatabaseQueryTool()
    ]
    return ReActAgent(
        llm=llm_cfg,
        name='general agent',
        description='This agent can solve problems,' +database_description,
        function_list=tools
    )

app = Flask(__name__)
CORS(app)

def process_content(content: List[Dict[str, Any]]) -> tuple:
    """
    处理请求内容，分离文本、图片和其他类型
    返回: (文本内容, 图片base64列表, 其他内容)
    """
    text_content = ""
    images = []
    other_content = []
    username = None
    
    for item in content:
        if 'text' in item:
            text_content += item['text'] + "\n"
        elif 'image' in item:
            images.append(item['image'])
        elif 'username' in item:
            username = item['username']
        else:
            other_content.append(item)
    
    return text_content.strip(), images, other_content, username

def save_base64_image(image_data: str) -> str:
    """
    将base64图片保存为临时文件，返回文件路径
    """
    PERMANENT_IMAGE_DIR = r'D:\CodeField\Zhilian-Agent\Zhilian-Agent\src\chat\images'
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
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(PERMANENT_IMAGE_DIR, filename)
    try:
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        logger.debug(f"图片保存成功: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"图片保存失败: {str(e)}")
        raise RuntimeError(f"无法保存图片: {str(e)}")

def replace_image_paths(text):
    # 正则表达式匹配图片路径格式
    pattern = r'"image_path"\s*:\s*"([^"]+)"'
    
    # 替换为指定格式
    replaced_text = re.sub(
        pattern,
        lambda m: '"image": "用户上传的图片"',
        text
    )
    
    return replaced_text

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
    text_content, images, other_content, username = process_content(content)

    if username:
        text_content = f"来自用户 {username} 的消息：\n{text_content}"
    
    # 如果有图片，保存为临时文件
    image_files = []
    for img in images:
        try:
            img_path = save_base64_image(img)
            logger.info("img_path: %s", img_path)
            image_files.append(img_path)
        except Exception as e:
            print(f"Error processing image: {str(e)}")
    
    # 构建agent输入
    agent_input = []
    if text_content:
        agent_input.append({'text': text_content})
    for img_path in image_files:
        agent_input.append({
            'image': img_path
        })
    logger.info("Agent Input: %s", agent_input)
    image_paths = [item['image'] for item in agent_input if isinstance(item, dict) and 'image' in item]
    logger.info("Agent Input Images: %s", image_paths)
    # 运行agent
    try:
        response = None
        for r in bot.run([{'role': 'user', 'content': agent_input}]):
            logger.info("Agent Response: %s", r)
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
                                    response_content.append({"audio": file_path})
                                elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                                    response_content.append({"image": file_path})
                
                # 构建响应内容
                if text_response.strip():
                    # response_content.append({"text": text_response.strip()})
                    processed_text = replace_image_paths(text_response.strip())
                    # response_content.append({"text": processed_text})
                    if "Final Answer:" in processed_text:
                        parts = processed_text.split("Final Answer:", 1)
                        thought = parts[0].strip()
                        final_answer = parts[1].strip()
                    else:
                        thought = processed_text
                        final_answer = None
                    if thought:
                        thought_lines = thought.split('\n')
                        thought_last_100_lines = '\n'.join(thought_lines[-300:])
                    else:
                        thought_last_100_lines = None

                    response_content.append({"thought": thought_last_100_lines})
                    if final_answer is not None:
                        response_content.append({"finalanswer": final_answer})
                
                return jsonify({
                    "messages": [{
                        "role": "assistant",
                        "content": response_content
                    }]
                })
    except Exception as e:
        print(f"Error during agent execution: {str(e)}")
        return jsonify({"messages": [{"text":"诗人我吃"}]}), 500
    
    return jsonify({"messages": []})

@app.route('/phonecallhandle', methods=['POST'])
def phone_call_handle():
    """
    专门处理电话呼叫的接口
    直接调用PhoneCallHandler工具处理电话号码
    """
    # 解析请求数据
    data = request.json
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({"error": "phone_number is required"}), 400
    
    # 创建PhoneCallHandler实例
    handler = PhoneCallHandler()
    
    # 准备工具参数
    params = {
        "phone_number": phone_number,
        "filename": f"call_{phone_number}.wav"
    }
    params_str = json.dumps(params)
    
    # 调用工具处理电话号码
    try:
        result_str = handler.call(params_str)
        result = json.loads(result_str)
        logger.info(f"Phone call {phone_number} handling result: {result}")
        
        # 确保返回结果中包含音频数据
        if "audio" not in result:
            return jsonify({"error": "Audio generation failed"}), 500
        
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        logger.error(f"Phone call handling failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Phone call handling failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    # 初始化agent
    bot = init_agent_service()
    
    # 获取公网可访问的端口（默认为12000）
    port = int(os.environ.get('GRADIO_SERVER_PORT', 12000))
    
    # 添加公网访问支持
    app.run(
        host="0.0.0.0", 
        port=port,
        debug=True,
        threaded=True,  # 启用多线程处理请求
        use_reloader=False,  # 关闭自动重载，避免端口冲突
        # ssl_context="adhoc"
    )