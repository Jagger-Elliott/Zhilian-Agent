import os
import copy
import asyncio
import json
import json5
import time
import sys
import pyttsx3
import re
import urllib.parse
from typing import Dict, Iterator, List, Optional, Union

from qwen_agent import Agent
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import ContentItem, Message
from qwen_agent.tools import BaseTool

os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d'
os.environ['GRADIO_SERVER_PORT'] = '12000'

class MyImageGen(BaseTool):
    """图像生成工具类"""
    name = 'my_image_gen'
    description = 'AI绘画服务，输入文本描述，返回基于文本信息绘制的图像URL'
    parameters = [{
        'name': 'prompt',
        'type': 'string',
        'description': '所需图像内容的详细描述（英文）',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        """调用图像生成工具"""
        prompt = json5.loads(params)['prompt']  # 解析JSON参数
        prompt = urllib.parse.quote(prompt)  # URL编码提示词
        # 返回包含图像URL的JSON
        return json.dumps({'image_url': f'https://image.pollinations.ai/prompt/{prompt}'}, ensure_ascii=False)

class TextToSpeech(BaseTool):
    """文本转语音工具类"""
    name = 'text_to_speech'
    description = '将文本转换为语音并保存为WAV文件'
    parameters = [{
        'name': 'text',
        'type': 'string',
        'description': '需要转换为语音的文本内容',
        'required': True
    }, {
        'name': 'filename',
        'type': 'string',
        'description': '保存的语音文件名（可选，默认为当前时间戳）',
        'required': False
    }]

    def call(self, params: str, **kwargs) -> str:
        """调用文本转语音工具"""
        # 解析参数
        params_dict = json5.loads(params)
        text = params_dict['text']
        filename = params_dict.get('filename', f'tts_{int(time.time())}.wav')
        
        try:
            # 初始化语音引擎
            engine = pyttsx3.init()
            
            # 尝试设置中文语音
            voices = engine.getProperty('voices')
            chinese_voice_found = False
            for voice in voices:
                # 检查语音是否支持中文
                if 'zh' in voice.languages or 'chinese' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    print(f"使用语音: {voice.name}")
                    chinese_voice_found = True
                    break
            
            if not chinese_voice_found:
                print("警告: 未找到中文语音，将使用默认语音")
            
            # 设置语音属性
            engine.setProperty('rate', 160)  # 语速 (默认200)
            engine.setProperty('volume', 0.9)  # 音量 (0.0-1.0)
            
            # 保存语音到文件
            engine.save_to_file(text, filename)
            engine.runAndWait()
            
            # 获取文件信息
            file_size = round(os.path.getsize(filename)/1024, 1)
            full_path = os.path.abspath(filename)
            
            # 返回成功信息和文件路径
            return json.dumps({
                'status': 'success',
                'message': f'成功生成语音文件: {filename}',
                'file_path': full_path,
                'file_size': f'{file_size} KB'
            }, ensure_ascii=False)
            
        except Exception as e:
            # 错误处理
            error_msg = f"生成语音失败: {str(e)}"
            print(error_msg, file=sys.stderr)
            
            # 返回错误信息
            return json.dumps({
                'status': 'error',
                'message': error_msg
            }, ensure_ascii=False)

class PhoneCallHandler(BaseTool):
    """电话处理工具类"""
    name = 'phone_call_handler'
    description = '根据电话号码生成相应的语音提示'
    parameters = [{
        'name': 'phone_number',
        'type': 'string',
        'description': '需要处理的电话号码',
        'required': True
    }, {
        'name': 'filename',
        'type': 'string',
        'description': '保存的语音文件名（可选，默认为call_处理结果.wav）',
        'required': False
    }]

    def call(self, params: str, **kwargs) -> str:
        """处理电话号码并生成语音提示"""
        params_dict = json5.loads(params)
        phone_number = params_dict['phone_number']
        filename = params_dict.get('filename', f'call_{int(time.time())}.wav')
        
        # 清理电话号码（移除非数字字符）
        cleaned_number = re.sub(r'\D', '', phone_number)
        
        # 根据规则生成语音文本
        if cleaned_number.startswith('181'):
            message = "黑名单电话，已为您记录并挂断"
        elif len(cleaned_number) < 8:
            message = "骚扰电话，已为您记录并挂断"
        elif cleaned_number.startswith('139'):
            message = "正在为您接通，请稍候"
        else:
            message = "骚扰电话，已为您记录并挂断"
        
        # 使用TextToSpeech工具生成语音
        tts_params = json.dumps({'text': message, 'filename': filename})
        return TextToSpeech().call(tts_params)

class VisualStorytelling(Agent):
    """Customize an agent for analyzing Unicom benefits from pictures with enhanced tools"""

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None):
        super().__init__(llm=llm)
        
        # 定义默认工具集
        default_tools = [
            MyImageGen(),
            TextToSpeech(),
            PhoneCallHandler(),
            'code_interpreter',
            {
                "mcpServers": {
                    "sqlite": {
                        "command": "uvx",
                        "args": [
                            "mcp-server-sqlite",
                            "--db-path",
                            "users.db"
                        ]
                    }
                }
            }
        ]
        
        # 如果用户没有提供工具列表，使用默认工具集
        if function_list is None:
            function_list = default_tools

        self.image_agent = Assistant(llm={'model': 'qwen-vl-max'})

        self.writing_agent = Assistant(
            llm=self.llm,
            function_list=function_list,
            system_message='''
            你是一个联通权益分析助手。请基于图片内容，以友好客服的语气分析并分点总结权益。
            输出格式（使用 Markdown）：
            - **权益1**：描述、条件、有效期。
            - **权益2**：...
            如果图片无权益相关内容，请礼貌说明并建议用户上传其他图片。
            参考知识：联通权益常见类型包括流量包、积分兑换、会员优惠、折扣券等。优先提取图片中的文本和图标信息。
            
            此外，你还可以使用以下工具处理用户请求：
            1. my_image_gen - 生成图像
            2. text_to_speech - 将文本转换为语音
            3. phone_call_handler - 根据电话号码生成语音提示
            4. 数据库查询工具 - 通过mcpServer的sqlite查询用户数据库
            5. code_interpreter - 执行代码解决复杂问题
            '''
        )

        self.description_cache = {}

    def _run(self, messages: List[Message], lang: str = 'zh', **kwargs) -> Iterator[List[Message]]:
        """Define the workflow with error handling and multi-image support"""
        try:
            assert messages and isinstance(messages[-1]['content'], list), 'Invalid message format'
            images = [item.image for item in messages[-1]['content'] if hasattr(item, 'image') and item.image]
            
            # 如果没有图片但有工具调用请求，直接传递给writing_agent
            if not images:
                for rsp in self.writing_agent.run(messages, lang=lang, **kwargs):
                    yield rsp
                return

            new_messages = copy.deepcopy(messages)
            descriptions = []
            for img in images:
                if img in self.description_cache:
                    descriptions.append(self.description_cache[img])
                    continue
                img_msg = copy.deepcopy(new_messages)
                img_msg[-1]['content'] = [ContentItem(image=img), ContentItem(text='请详细描述这张图片的所有细节内容，包括文本、图标和权益相关元素')]
                rsp_list = []
                for rsp in self.image_agent.run(img_msg):
                    rsp_list.extend(rsp)
                desc = rsp_list[-1]['content'] if rsp_list else '图片描述失败'
                descriptions.append(desc)
                self.description_cache[img] = desc  # Cache the description

            combined_desc = '\n'.join([f'图片 {i+1} 描述：{desc}' for i, desc in enumerate(descriptions)])
            new_messages.append(Message('assistant', combined_desc))

            new_messages.append(Message('user', '基于以上图片描述，以客服的语气分点列出图中联通权益的总结，包括权益名称、条件、有效期等'))

            for rsp in self.writing_agent.run(new_messages, lang=lang, **kwargs):
                yield rsp

        except Exception as e:
            error_msg = f"处理失败：{str(e)}。请检查图片路径/URL 或重试。如果问题持续，请提供更多细节。"
            yield [Message('assistant', error_msg)]


def test(query: Optional[str] = '分析这个联通权益图片',
         image: str = r'D:\\CodeField\\Qwen-Agent\\examples\\test.png'):
    if not (os.path.exists(image) or image.startswith('http')):
        print('无效图片路径或 URL！')
        return

    bot = VisualStorytelling(llm={'model': 'qwen-max'})

    messages = [Message('user', [ContentItem(image=image)])]
    if query:
        messages[-1]['content'].append(ContentItem(text=query))

    for response in bot.run(messages):
        print('bot response:', response)


def app_gui():
    bot = VisualStorytelling(llm={'model': 'qwen-max'})
    ui = WebUI(bot)
    ui.run(instructions='上传联通权益图片（支持多张）或使用工具功能：图像生成、语音合成、电话处理、数据库查询！')


if __name__ == '__main__':
    # 测试工具功能
    # print(MyImageGen().call('{"prompt":"A beautiful unicorn in a forest"}'))
    # print(TextToSpeech().call('{"text":"你好，欢迎使用联通服务"}'))
    # print(PhoneCallHandler().call('{"phone_number":"13912345678"}'))
    
    # test()
    app_gui()