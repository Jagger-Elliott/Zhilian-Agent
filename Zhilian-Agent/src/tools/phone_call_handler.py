import json
import json5
import time
import re
import os
import base64
from typing import Dict, Any, List
from qwen_agent.agents import Assistant
from qwen_agent.tools import BaseTool
from .text_to_speech import TextToSpeech 

class CallAnalysisAgent(Assistant):
    """电话分析助手（号码提取、数据库查询、欺诈检测）"""
    def __init__(self):
        super().__init__(
            llm={'model': 'qwen-max'},
            function_list=[{
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
            }],
            system_message='''
            你是一个电话分析专家，负责处理任意位数的来电号码。请按以下步骤工作：
            1. 号码提取：从用户输入中提取完整的电话号码
            2. 数据库查询：使用mcpServers工具查询号码对应的用户信息
            3. 欺诈检测：根据以下规则判断号码类型：
               - 号码存在于数据库的advertising_calls表中：骚扰电话
               - 以181开头：黑名单电话
               - 以139开头：正常电话
               - 其他号码：正常电话
            
            输出格式要求（JSON）：
            {
                "phone_number": "提取的电话号码",
                "user_info": "数据库查询结果",
                "call_type": "黑名单/骚扰/正常"
            }
            '''
        )

class PhoneCallHandler(BaseTool):
    """电话处理工具类（集成电话识别助手）"""
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

    def __init__(self):
        super().__init__()
        # 创建电话分析助手实例
        self.assistant = CallAnalysisAgent()

    def call(self, params: str, **kwargs) -> str:
        """处理电话号码并生成语音提示"""
        params_dict = json5.loads(params)
        phone_number = params_dict['phone_number']
        filename = params_dict.get('filename', f'call_{int(time.time())}.wav')
        
        # 清理电话号码（移除非数字字符）
        cleaned_number = re.sub(r'\D', '', phone_number)
        
        # 使用助手进行电话分析
        analysis_result = self._analyze_phone_number(cleaned_number)
        
        # 根据分析结果生成语音文本
        call_type = analysis_result.get('call_type', '未知')
        if call_type == '黑名单':
            message = f"警告！{cleaned_number}是黑名单电话，请勿接听。"
        elif call_type == '骚扰':
            message = f"注意！{cleaned_number}是骚扰电话，建议谨慎接听。"
        else:
            message = f"{cleaned_number}是正常来电，请接听。"
        
        # 使用TextToSpeech工具生成语音
        tts_params = json.dumps({'text': message, 'filename': filename})
        tts_response = TextToSpeech().call(tts_params)
        tts_result = json.loads(tts_response)
        audio_path = tts_result.get('file_path', '')
        audio_base64 = ""
        try:
            with open(audio_path, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        except Exception as e:
            print(f"音频文件读取失败: {str(e)}")
        result = {
            "phone_number": cleaned_number,
            "call_type": call_type,
            "message": message,
            "audiopath": audio_path,  # 音频文件路径
            "audio": audio_base64     # 音频的base64编码数据
        }
        
        return json.dumps(result, ensure_ascii=False)

    def _analyze_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """使用助手分析电话号码"""
        # 构造输入（模拟用户消息）
        user_input = f"分析电话号码：{phone_number}"
        
        # 调用助手处理
        response = self.assistant.run(user_input)
        
        try:
            # 从助手响应中提取JSON数据
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json5.loads(json_str)
        except Exception as e:
            return {
                'phone_number': phone_number,
                'user_info': '分析失败',
                'call_type': '未知'
            }