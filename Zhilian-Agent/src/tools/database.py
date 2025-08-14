import json
import json5
import re
from typing import Dict, Any
from qwen_agent.agents import Assistant
from qwen_agent.tools import BaseTool
import os
os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d'

class DatabaseQueryAssistant(Assistant):
    """数据库查询助手，专门处理数据库查询请求"""
    def __init__(self):
        super().__init__(
            llm={'model': 'qwen-max'},
            function_list=[
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
            ],
            system_message='''
            你是一个联通权益分析助手。你可以使用以下工具处理用户请求：
            1. 数据库查询工具 - 通过mcpServer的sqlite查询用户数据库
            '''
        )

class DatabaseQueryTool(BaseTool):
    """数据库访问工具（集成查询助手）"""
    name = 'database_query_tool'
    description = """执行数据库查询并返回结构化结果，该SQLite数据库包含4个数据表，主要用于管理用户信息、VIP权益数据和广告电话记录。以下是精简后的数据库结构：

        1. VIP权益表 (表名vip_benefits)
        主键: id (INTEGER)

        字段:

        vip_level (TEXT, 非空): VIP等级名称(如青铜/白银/黄金)

        package_type (TEXT, 非空): 套餐类型(如"家庭版单宽200M")

        monthly_fee (REAL, 非空): 月费金额(元)

        contract_duration_months (INTEGER, 非空): 合约期限(月)

        includes_phone_plan (BOOLEAN, 非空): 是否包含电话套餐

        2. 用户表 (表名users)
        主键: id (INTEGER)

        字段:

        name (TEXT, 非空): 用户姓名

        phone (TEXT, 非空): 手机号码(格式181xxxxxxx)

        vip_level (TEXT): VIP等级(当前全为"白银")

        package (TEXT): 当前使用套餐(当前全为"无")

        blacklist (TEXT): 屏蔽号码列表(逗号分隔)

        3. 广告电话表 (表名advertising_calls)
        主键: id (INTEGER)

        字段:

        phone_number (TEXT, 非空): 广告电话号码

        4. 系统序列表 (表名sqlite_sequence)
        字段:

        name (TEXT): 表名

        seq (INTEGER): 当前自增ID值
    """
    parameters = [{
        'name': 'query',
        'type': 'string',
        'description': '需要执行的查询请求或SQL语句',
        'required': True
    }]

    def __init__(self):
        super().__init__()
        # 创建数据库查询助手实例
        self.assistant = DatabaseQueryAssistant()

    def call(self, params: str, **kwargs) -> str:
        """执行查询并返回助手处理后的文本结果"""
        params_dict = json5.loads(params)
        user_query = params_dict['query']
        
        # 清理输入（防止SQL注入）
        sanitized_query = re.sub(r'[;\'"\\]', '', user_query)
        
        # 使用助手进行数据库查询
        response = self._execute_database_query(sanitized_query)
        
        # 返回助手的文本输出
        return response

    def _execute_database_query(self, query: str) -> str:
        """使用助手处理查询请求"""
        # 构造符合要求的消息格式
        messages = [{
            'role': 'user',
            'content': f"执行数据库查询：{query}"
        }]
        
        # 调用助手处理（处理生成器输出）
        response_generator = self.assistant.run(messages=messages)
        
        # 收集生成器的所有输出片段
        response_parts = []
        for response_chunk in response_generator:
            # 确保我们只处理文本内容
            if isinstance(response_chunk, dict):
                response_parts.append(response_chunk.get('content', ''))
            else:
                response_parts.append(str(response_chunk))
        
        # 合并所有输出片段
        full_response = ''.join(response_parts)
        
        # 提取助手的文本输出
        try:
            # 尝试解析JSON格式的输出
            if full_response.strip().startswith('{'):
                result_json = json5.loads(full_response)
                return result_json.get('result', full_response)
            return full_response
        except Exception as e:
            return f"查询处理失败: {str(e)}"

# 示例使用
# if __name__ == "__main__":
#     # 创建工具实例
#     db_tool = DatabaseQueryTool()
    
#     # 构造查询参数
#     query_params = json.dumps({
#         "query": "数据库有几张表？请列出所有表名。"
#     })
    
#     # 执行查询
#     result = db_tool.call(query_params)
#     print("数据库查询结果:")
#     print(result)