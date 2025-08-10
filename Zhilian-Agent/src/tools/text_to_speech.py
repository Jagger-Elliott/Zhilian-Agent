import json
import json5
import time
import sys
import pyttsx3
from qwen_agent.tools import BaseTool

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
