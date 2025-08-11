import json
from typing import Dict, Iterator, List, Literal, Optional, Tuple, Union

from qwen_agent.agents.fncall_agent import FnCallAgent
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import ASSISTANT, DEFAULT_SYSTEM_MESSAGE, Message
from qwen_agent.settings import MAX_LLM_CALL_PER_RUN
from qwen_agent.tools import BaseTool
from qwen_agent.utils.utils import format_as_text_message, merge_generate_cfgs
TOOL_DESC = (
    '{name_for_model}：这是 {name_for_human} API。'
    '作用：{description_for_model}。'
    '所需参数：{parameters}。'
    '调用示例：{args_format}'
)

PROMPT_REACT = """
你是一个智能助手，使用 ReAct 框架完成任务。你可以访问以下工具：
{tool_descs}

当前用户输入：
{query}

你的输出必须严格遵循以下格式，每一步都必须包含 Thought 或 Action 或 Observation：
1. **Thought**：详细推理过程，至少包含：
   - 用户的目标
   - 我已知的信息
   - 还缺的信息
   - 下一步计划
2. **Action**：选择一个工具（名称必须在[{tool_names}]中）
3. **Action Input**：JSON 格式的工具参数
4. **Observation**：工具返回结果
5. 循环思考并调用工具，直到可以给出最终答案
6. **Final Answer**：最终回答用户

示例：
Question: 我想拨打 13912345678
Thought: 用户想打电话到 13912345678。
已知：我有 validate_phone_number 工具可以校验号码，phone_call_handler 工具可以拨号。
缺少：需要确认号码是否合法。
计划：先调用 validate_phone_number 检查号码。
Action: validate_phone_number
Action Input: {{"phone_number": "13912345678"}}
Observation: {{"valid": true}}
Thought: 号码合法，可以拨打。
Action: phone_call_handler
Action Input: {{"phone_number": "13912345678"}}
Observation: {{"status": "success", "detail": "电话已拨打"}}
Thought: 电话拨打成功。
Final Answer: 已拨打 13912345678

Question: {query}
Thought:
"""


class ReActAgent(FnCallAgent):
    """This agent use ReAct format to call tools"""

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None,
                 **kwargs):
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message=system_message,
                         name=name,
                         description=description,
                         files=files,
                         **kwargs)
        self.extra_generate_cfg = merge_generate_cfgs(
            base_generate_cfg=self.extra_generate_cfg,
            new_generate_cfg={'stop': ['Observation:', 'Observation:\n']},
        )

    def _run(self, messages: List[Message], lang: Literal['en', 'zh'] = 'en', **kwargs) -> Iterator[List[Message]]:
        text_messages = self._prepend_react_prompt(messages, lang=lang)

        num_llm_calls_available = MAX_LLM_CALL_PER_RUN
        response: str = 'Thought: '
        while num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            # Display the streaming response
            output = []
            for output in self._call_llm(messages=text_messages):
                if output:
                    yield [Message(role=ASSISTANT, content=response + output[-1].content)]

            # Accumulate the current response
            if output:
                response += output[-1].content

            has_action, action, action_input, thought = self._detect_tool(output[-1].content)
            if not has_action:
                break

            # Add the tool result
            observation = self._call_tool(action, action_input, messages=messages, **kwargs)
            observation = f'\nObservation: {observation}\nThought: '
            response += observation
            yield [Message(role=ASSISTANT, content=response)]

            if (not text_messages[-1].content.endswith('\nThought: ')) and (not thought.startswith('\n')):
                # Add the '\n' between '\nQuestion:' and the first 'Thought:'
                text_messages[-1].content += '\n'
            if action_input.startswith('```'):
                # Add a newline for proper markdown rendering of code
                action_input = '\n' + action_input
            text_messages[-1].content += thought + f'\nAction: {action}\nAction Input: {action_input}' + observation

    def _prepend_react_prompt(self, messages: List[Message], lang: Literal['en', 'zh']) -> List[Message]:
        tool_descs = []
        for f in self.function_map.values():
            function = f.function
            name = function.get('name', None)
            name_for_human = function.get('name_for_human', name)
            name_for_model = function.get('name_for_model', name)
            assert name_for_human and name_for_model
            args_format = function.get('args_format', '')
            tool_descs.append(
                TOOL_DESC.format(name_for_human=name_for_human,
                                 name_for_model=name_for_model,
                                 description_for_model=function['description'],
                                 parameters=json.dumps(function['parameters'], ensure_ascii=False),
                                 args_format=args_format).rstrip())
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool.name for tool in self.function_map.values())
        text_messages = [format_as_text_message(m, add_upload_info=True, lang=lang) for m in messages]
        text_messages[-1].content = PROMPT_REACT.format(
            tool_descs=tool_descs,
            tool_names=tool_names,
            query=text_messages[-1].content,
        )
        return text_messages

    def _detect_tool(self, text: str) -> Tuple[bool, str, str, str]:
        special_func_token = '\nAction:'
        special_args_token = '\nAction Input:'
        special_obs_token = '\nObservation:'
        func_name, func_args = None, None
        i = text.rfind(special_func_token)
        j = text.rfind(special_args_token)
        k = text.rfind(special_obs_token)
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                # then it is likely that `Observation` is ommited by the LLM,
                # because the output text may have discarded the stop word.
                text = text.rstrip() + special_obs_token  # Add it back.
            k = text.rfind(special_obs_token)
            func_name = text[i + len(special_func_token):j].strip()
            func_args = text[j + len(special_args_token):k].strip()
            text = text[:i]  # Return the response before tool call, i.e., `Thought`
        return (func_name is not None), func_name, func_args, text
