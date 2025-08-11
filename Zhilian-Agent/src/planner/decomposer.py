from typing import Dict, List

from qwen_agent.tools import BaseTool

class TaskDecomposer(BaseTool):
    """任务分解模块：根据意图和槽位拆解成具体子任务"""

    def __init__(self):
        pass

    def call(self, intent_result: Dict) -> List[Dict]:
        """
        输入示例：
        {
            "intent": "电话处理",
            "confidence": 0.98,
            "slots": {
                "phone_number": "13912345678",
                "call_action": "拨打",
                "context": null
            }
        }

        输出示例：
        [
            {"task": "validate_phone_number", "params": {"phone_number": "13912345678"}, "desc": "校验电话号码格式"},
            {"task": "make_call", "params": {"phone_number": "13912345678"}, "desc": "发起拨打电话"},
        ]
        """
        tasks = []
        intent = intent_result.get("intent", "")
        slots = intent_result.get("slots", {})

        if intent == "电话处理":
            phone = slots.get("phone_number")
            action = slots.get("call_action")
            if phone:
                tasks.append({"task": "validate_phone_number", "params": {"phone_number": phone}, "desc": "校验电话号码格式"})
                if action == "拨打":
                    tasks.append({"task": "make_call", "params": {"phone_number": phone}, "desc": "发起拨打电话"})
                elif action == "挂断":
                    tasks.append({"task": "hangup_call", "params": {"phone_number": phone}, "desc": "挂断电话"})
                else:
                    tasks.append({"task": "unknown_call_action", "params": {}, "desc": "未知的通话操作"})
            else:
                tasks.append({"task": "error", "params": {}, "desc": "缺少电话号码"})

        elif intent == "图像生成":
            prompt = slots.get("prompt")
            style = slots.get("style")
            size = slots.get("size")
            if prompt:
                params = {"prompt": prompt}
                if style:
                    params["style"] = style
                if size:
                    params["size"] = size
                tasks.append({"task": "generate_image", "params": params, "desc": "根据提示生成图片"})
            else:
                tasks.append({"task": "error", "params": {}, "desc": "缺少生成提示语"})

        elif intent == "语音合成":
            text = slots.get("text")
            voice_type = slots.get("voice_type", "默认")
            speed = slots.get("speed", "正常")
            if text:
                tasks.append({"task": "text_to_speech", "params": {"text": text, "voice_type": voice_type, "speed": speed}, "desc": "文本转语音"})
            else:
                tasks.append({"task": "error", "params": {}, "desc": "缺少文本内容"})

        elif intent == "数据库查询":
            query = slots.get("query")
            database = slots.get("database")
            table = slots.get("table")
            if query:
                tasks.append({"task": "db_query", "params": {"query": query, "database": database, "table": table}, "desc": "执行数据库查询"})
            else:
                tasks.append({"task": "error", "params": {}, "desc": "缺少查询语句"})

        elif intent == "代码执行":
            language = slots.get("language")
            code = slots.get("code")
            if language and code:
                tasks.append({"task": "execute_code", "params": {"language": language, "code": code}, "desc": "执行代码"})
            else:
                tasks.append({"task": "error", "params": {}, "desc": "缺少语言或代码内容"})

        elif intent == "权益分析":
            benefit_type = slots.get("benefit_type")
            valid_period = slots.get("valid_period")
            conditions = slots.get("conditions")
            tasks.append({
                "task": "analyze_benefit",
                "params": {
                    "benefit_type": benefit_type,
                    "valid_period": valid_period,
                    "conditions": conditions,
                },
                "desc": "分析联通权益信息"
            })

        elif intent == "一般对话":
            topic = slots.get("topic")
            tasks.append({
                "task": "general_chat",
                "params": {"topic": topic},
                "desc": "处理一般对话"
            })

        else:
            tasks.append({"task": "unknown_intent", "params": {}, "desc": "未识别的意图"})

        return tasks


# 简单测试
if __name__ == "__main__":
    decomposer = TaskDecomposer()
    sample_intent = {
        "intent": "电话处理",
        "confidence": 0.98,
        "slots": {
            "phone_number": "13912345678",
            "call_action": "拨打",
            "context": None
        }
    }
    tasks = decomposer.call(sample_intent)
    for t in tasks:
        print(t)
