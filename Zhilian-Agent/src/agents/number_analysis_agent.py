from qwen_agent.agents import Assistant
from qwen_agent.tools import BaseTool

class CallAnalysisAgent(Assistant):
    """电话分析Agent（包含号码提取、数据库查询、欺诈检测）"""
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
            你是一个电话分析专家，负责处理来电号码。请按以下步骤工作：
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