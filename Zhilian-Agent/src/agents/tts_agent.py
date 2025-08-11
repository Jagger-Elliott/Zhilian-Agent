from qwen_agent.agents import Assistant
from tools.text_to_speech import TextToSpeech  # 导入文本转语音工具

class TTSAgent(Assistant):
    """TTS语音生成Agent"""
    def __init__(self):
        super().__init__(
            llm={'model': 'qwen-max'},
            function_list=[TextToSpeech()],
            system_message='''
            你是一个TTS语音生成专家，根据响应文本生成语音文件：
            1. 接收响应文本和文件名
            2. 调用text_to_speech工具生成语音
            3. 返回语音文件路径信息
            
            输出格式要求（JSON）：
            {
                "status": "success/error",
                "message": "结果描述",
                "file_path": "生成的语音文件路径"
            }
            '''
        )