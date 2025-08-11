import os
import copy
import json
import re
from typing import Dict, Iterator, List, Optional, Union
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import ContentItem, Message

os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d' 
os.environ['GRADIO_SERVER_PORT'] = '12000'


class IntentRecognition():
    """意图识别 + 槽位填充 Agent（带槽位配置 + JSON 校验）"""
    # name = '意图识别'
    # description = '根据根据用户输入进行意图识别'
    # parameters = [{
    #     'name': 'prompt',
    #     'type': 'string',
    #     'description': '据用户输入',
    #     'required': True
    # }]

    def __init__(self, llm: Optional[Union[Dict, BaseChatModel]] = None):
        super().__init__()
        self.llm = llm
        # 槽位配置
        slot_config = {
            "图像分析": {
                "image_count": "用户上传的图片数量",
                "analysis_target": "需要分析的具体内容（如文字、物体、场景等）"
            },
            "图像生成": {
                "prompt": "生成图片的文本描述",
                "style": "图片风格（如卡通、写实、油画等）",
                "size": "图片尺寸（如1024x1024）"
            },
            "语音合成": {
                "text": "需要转换为语音的文本",
                "voice_type": "声音类型（如男声、女声）",
                "speed": "语速（如慢速、正常、快速）"
            },
            "电话处理": {
                "phone_number": "电话号码",
                "call_action": "通话操作类型（如拨打、挂断、查询）",
                "context": "通话上下文（如通话内容、通话时间、通话地点等）"
            },
            "数据库查询": {
                "query": "SQL 查询语句",
                "database": "数据库名称",
                "table": "表名"
            },
            "代码执行": {
                "language": "编程语言",
                "code": "需要执行的代码内容"
            },
            "一般对话": {
                "topic": "对话主题（如天气、闲聊、新闻等）"
            },
            "权益分析": {
                "benefit_type": "权益类型（如流量包、会员、积分等）",
                "valid_period": "有效期",
                "conditions": "使用条件"
            }
        }

        # 意图识别+槽位填充 LLM
        self.intent_agent = Assistant(
            llm=self.llm,
            system_message=f'''
你是一个智能意图识别助手，任务是从用户输入中识别意图并提取对应槽位（slot filling）。

意图类型：
{list(slot_config.keys())}

各意图需要提取的槽位：
{slot_config}

要求：
1. 必须先判断用户的意图（intent），再提取该意图对应的所有槽位。
2. 如果槽位无法确定，请返回 null，不要猜测。
3. 必须以 JSON 格式返回：
{{
    "intent": "意图类型",
    "confidence": 0.0~1.0,
    "slots": {{
        "slot_name": "value 或 null"
    }}
}}
4. 不要输出除 JSON 外的任何内容。
            '''
        )

    def _extract_json(self, text: str) -> Optional[dict]:
        """用正则提取 JSON，并解析为 dict"""
        try:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        return None

    def call(self, messages: List[Message], lang: str = 'zh', **kwargs) -> Iterator[List[Message]]:
        """直接调用 LLM 进行意图识别和槽位填充，并提取 JSON"""
        try:
            assert messages and isinstance(messages[-1]['content'], list), '无效的消息格式'

            # 合并用户文本和图片提示
            images = [item.image for item in messages[-1]['content'] if hasattr(item, 'image') and item.image]
            text_content = [item.text for item in messages[-1]['content'] if hasattr(item, 'text') and item.text]
            user_text = ' '.join(text_content) if text_content else ''
            
            intent_message = copy.deepcopy(messages)
            if images:
                intent_message[-1]['content'] = [ContentItem(text=f'用户输入：{user_text}，上传了{len(images)}张图片')]
            else:
                intent_message[-1]['content'] = [ContentItem(text=f'用户输入：{user_text}')]

            # 调用 LLM
            for rsp in self.intent_agent.run(intent_message, lang=lang, **kwargs):
                if rsp and isinstance(rsp[-1]['content'], str):
                    parsed = self._extract_json(rsp[-1]['content'])
                    if parsed:
                        rsp[-1]['content'] = json.dumps(parsed, ensure_ascii=False)
                yield rsp

        except Exception as e:
            yield [Message('assistant', f"处理失败：{str(e)}")]


def parse(query: Optional[str] = '帮我打电话给13912345678') -> str:
    bot = IntentRecognition(llm={'model': 'qwen-max'})
    messages = [Message('user', [ContentItem(text=query)])]
    result = ""
    for response in bot.run(messages):
        print('bot response:', response)
        result += response + " "
    return result
    


def app_gui():
    bot = IntentRecognition(llm={'model': 'qwen-max'})
    ui = WebUI(bot)
    ui.run(instructions='意图识别 + 槽位填充助手（带槽位配置 + JSON 校验）')


if __name__ == '__main__':
    # test()
    app_gui()
