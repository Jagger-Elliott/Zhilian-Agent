import json
import json5
import urllib.parse
from qwen_agent.tools import BaseTool

class MyImageGen(BaseTool):
    """图像生成工具类"""
    name = 'my_image_gen'
    description = 'AI绘画服务，输入文本描述，返回基于文本信息绘制的图像URL'
    parameters = [{
        'name': 'prompt',
        'type': 'string',
        'description': '所需图像内容的详细描述（英文）',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        """调用图像生成工具"""
        prompt = json5.loads(params)['prompt']  # 解析JSON参数
        prompt = urllib.parse.quote(prompt)  # URL编码提示词
        # 返回包含图像URL的JSON
        return json.dumps({'image_url': f'https://image.pollinations.ai/prompt/{prompt}'}, ensure_ascii=False)
