from qwen_agent.tools import BaseTool
from qwen_agent.agents import Assistant
from qwen_agent.llm.schema import ContentItem, Message
import json5
import json
import base64
import os

os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d'
os.environ['GRADIO_SERVER_PORT'] = '12000'

class ImageUnderstanding(BaseTool):
    """图像理解工具类（修复版）"""
    name = 'image_understanding'
    description = '分析图片内容，返回详细的文本描述。支持识别图片中的文字、物体、场景等。'
    parameters = [{
        'name': 'image_path',
        'type': 'string',
        'description': '图片路径',
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
            image_data = params_dict['image_path']
            query = params_dict.get('query', '请详细描述这张图片的内容')
            
            # 创建VL Agent处理图片
            vl_agent = Assistant(llm={'model': 'qwen-vl-max'})
            
            # 构建消息
            content = [
                ContentItem(image=f"{image_data}"),
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

def main():
    # 设置测试图片路径
    # image_path = r"D:\\CodeField\\Zhilian-Agent\\Zhilian-Agent\\src\\chat\\test\\qtbenefit.png"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, 'qtbenefit.png')
    # 验证文件存在
    if not os.path.exists(image_path):
        print(f"错误：图片文件不存在 - {image_path}")
        return
    
    # 创建ImageUnderstanding实例
    image_understanding = ImageUnderstanding()
    
    # 准备参数
    params = {
        'image_path': image_path,
        'query': '请详细描述这张图片的内容'
    }
    params_str = json5.dumps(params)
    
    print("\n调用图像理解工具...")
    result = image_understanding.call(params_str)
    
    # 解析并打印结果
    print("\n工具返回结果:")
    try:
        result_dict = json5.loads(result)
        if result_dict['status'] == 'success':
            print("分析成功:")
            print(result_dict['description'])
        else:
            print(f"分析失败: {result_dict['message']}")
    except Exception as e:
        print(f"结果解析失败: {str(e)}")
        print("原始返回:")
        print(result)

if __name__ == '__main__':
    main()