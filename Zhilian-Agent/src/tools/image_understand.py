from qwen_agent.tools import BaseTool
from qwen_agent.agents import Assistant
from qwen_agent.llm.schema import ContentItem, Message
import json5
import json

class ImageUnderstanding(BaseTool):
    """图像理解工具类"""
    name = 'image_understanding'
    description = '分析图片内容，返回详细的文本描述。支持识别图片中的文字、物体、场景等。'
    parameters = [{
        'name': 'image_path',
        'type': 'string',
        'description': '图片路径(D:\\CodeField\\Zhilian-Agent\\Zhilian-Agent\\src\\chat\\images目录啊下的png)',
        'required': True
    }, {
        'name': 'query',
        'type': 'string',
        'description': '关于图片的具体问题（可选）',
        'required': False
    }]

    def call(self, params: str, **kwargs) -> str:
        """调用图像理解工具（支持base64图片）"""
        try:
            params_dict = json5.loads(params)
            image_path = params_dict['image_path']
            query = params_dict.get('query', '请详细描述这张图片的内容')
            
            # 创建VL Agent处理图片
            vl_agent = Assistant(llm={'model': 'qwen-vl-max'})
            
            # 构建消息（直接使用base64数据）
            content = [
                ContentItem(image=f"{image_path}"),
                ContentItem(text=query) if query else None
            ]
            # 过滤掉None值
            content = [item for item in content if item is not None]
            
            messages = [Message('user', content)]
            
            # 获取响应
            response = list(vl_agent.run(messages))
            if response:
                last_response = response[-1][-1]['content']
                return json.dumps({
                    'status': 'success',
                    'description': last_response
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'status': 'error',
                    'message': '未能获取图片描述'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'status': 'error',
                'message': f'图片分析失败: {str(e)}'
            }, ensure_ascii=False)