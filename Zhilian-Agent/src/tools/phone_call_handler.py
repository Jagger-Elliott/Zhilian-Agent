import json
import json5
import time
import re
from qwen_agent.tools import BaseTool
from .text_to_speech import TextToSpeech

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