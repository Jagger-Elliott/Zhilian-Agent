import copy
import os
from typing import Dict, Iterator, List, Literal, Optional, Union

from qwen_agent.agents import FnCallAgent
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import DEFAULT_SYSTEM_MESSAGE, FUNCTION, Message
from qwen_agent.memory import Memory
from qwen_agent.settings import MAX_LLM_CALL_PER_RUN
from qwen_agent.tools import BaseTool
from qwen_agent.utils.utils import extract_files_from_messages


os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d'
os.environ['GRADIO_SERVER_PORT'] = '12000'

SYSTEM_MESSAGE = """
你是一个智能的旅游规划助手，可以帮助用户规划出行路线、查询航班信息并提供旅行建议。
你可以使用以下工具：
1. 高德地图（amap-maps）：用于路线规划、地理位置查询等
2. Variflight（variflight）：用于航班查询、航班状态追踪等

请始终在生成最终答案前，分析用户需求、调用必要的工具获取信息，并基于结果做出总结。
回答必须准确、简洁、符合用户语言习惯。
"""

TRAVEL_AGENT_PROMPT = """
你是一个旅行规划助手，使用 ReAct 框架与用户互动。
你有两个主要工具：
- amap-maps：用于获取路线规划、地理位置和交通信息
- variflight：用于查询航班信息

当用户提问时，请按照以下步骤：
1. **Thought**：分析用户意图，明确需要使用哪个工具（可能需要多个步骤）。
2. **Action**：调用一个工具，工具名称必须是 ["amap-maps", "variflight"]。
3. **Action Input**：提供调用工具所需的 JSON 参数。
4. **Observation**：等待工具返回结果。
5. 循环执行 Thought → Action → Observation，直到可以给出最终答案。
6. **Final Answer**：整合工具返回的结果，给用户提供完整的答复。

示例 1（查询路线）：
Question: 从北京到上海怎么走？
Thought: 用户需要从北京到上海的路线规划，应使用 amap-maps 工具。
Action: amap-maps
Action Input: {"origin": "北京", "destination": "上海", "mode": "driving"}
Observation: {... 高德返回的路线数据 ...}
Thought: 我已经获得路线信息，现在总结成自然语言。
Final Answer: 从北京到上海自驾大约需要 12 小时，全程约 1200 公里。

示例 2（查询航班）：
Question: 8月20日从广州到成都有哪些航班？
Thought: 用户需要查询航班信息，应使用 variflight 工具。
Action: variflight
Action Input: {"from": "广州", "to": "成都", "date": "2025-08-20"}
Observation: {... 航班信息 ...}
Thought: 我已经获得航班列表，现在为用户整理结果。
Final Answer: 8月20日广州到成都共有 15 个航班，最早 06:30 起飞，最晚 22:10 起飞。

请严格按以上格式生成，并在调用工具前先进行推理说明。
Question: {query}
Thought:
"""

TRAVEL_TOOLS = [{
        "mcpServers": {
            "amap-maps": {
                "command": "npx",
                "args": [
                    "-y",
                    "@amap/amap-maps-mcp-server"
                ],
                "env": {
                    "AMAP_MAPS_API_KEY": "2b5042a60254b76b209a898bc252fdd7"
                }
            },
            "variflight": {
            "command": "npx",
            "args": [
                "-y",
                "@variflight-ai/variflight-mcp"
            ],
            "env": {
                "VARIFLIGHT_API_KEY": "sk-IismzmkAJCKGBnjefAxv7dNMM-bUpt7d2jd7hgLt1zQ"
            }
        }
        }
    }]
class TravelAgent(FnCallAgent):
    """"""

    def __init__(self,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 files: Optional[List[str]] = None,
                 **kwargs):
        super().__init__(function_list=TRAVEL_TOOLS,
                         llm=llm,
                         system_message=SYSTEM_MESSAGE,
                         name="travel agent",
                         description="你是一个旅行规划助手")


    def _run(self, messages: List[Message], lang: Literal['en', 'zh'] = 'en', **kwargs) -> Iterator[List[Message]]:
        return super()._run(messages=messages, lang=lang, **kwargs)

    def _call_tool(self, tool_name: str, tool_args: Union[str, dict] = '{}', **kwargs) -> str:
        if tool_name not in self.function_map:
            return f'Tool {tool_name} does not exists.'
        # Temporary plan: Check if it is necessary to transfer files to the tool
        # Todo: This should be changed to parameter passing, and the file URL should be determined by the model
        if self.function_map[tool_name].file_access:
            assert 'messages' in kwargs
            files = extract_files_from_messages(kwargs['messages'], include_images=True) + self.mem.system_files
            return super()._call_tool(tool_name, tool_args, files=files, **kwargs)
        else:
            return super()._call_tool(tool_name, tool_args, **kwargs)
    
    def plan_trip(self, origin: str, destination: str, date: str, mode: str = "driving") -> dict:
        """
        自动调用高德地图获取路线，再调用 Variflight 查询航班，整合成建议
        """
        # Step 1: 调用高德地图
        route = self._call_tool(
            "amap-maps",
            {"origin": origin, "destination": destination, "mode": mode}
        )

        # Step 2: 调用 Variflight
        flights = self._call_tool(
            "variflight",
            {"from": origin, "to": destination, "date": date}
        )

        return {
            "origin": origin,
            "destination": destination,
            "date": date,
            "recommended_mode": "driving" if "顺畅" in route else "flight",
            "route_info": route,
            "flight_info": flights
        }

    def summarize_trip_plan(self, plan_data: dict, lang: str = "zh") -> str:
        """
        将 plan_trip 返回的字典转成用户可读的旅行建议
        """
        if lang == "zh":
            summary = f"从 {plan_data['origin']} 到 {plan_data['destination']} 的行程：\n"
            summary += f"推荐出行方式：{ '自驾' if plan_data['recommended_mode'] == 'driving' else '飞机' }\n"
            summary += f"路线信息：{plan_data['route_info']}\n"
            summary += f"航班信息：{plan_data['flight_info']}"
        else:
            summary = f"Trip from {plan_data['origin']} to {plan_data['destination']}:\n"
            summary += f"Recommended: { 'Driving' if plan_data['recommended_mode'] == 'driving' else 'Flight' }\n"
            summary += f"Route Info: {plan_data['route_info']}\n"
            summary += f"Flight Info: {plan_data['flight_info']}"
        return summary

def test():
    llm_cfg = {
        'model': 'qwen-max',
        'model_server': 'dashscope',
        'api_key': os.getenv('DASHSCOPE_API_KEY'),
    }
    agent = TravelAgent(llm=llm_cfg)

    # 全套旅游方案
    plan = agent.plan_trip("北京", "上海", "2025-08-20")
    print(agent.summarize_trip_plan(plan, lang="zh"))

if __name__ == "__main__":
    test()


