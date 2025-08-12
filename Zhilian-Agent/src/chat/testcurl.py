import requests
import base64
import json

# 测试文本请求
def test_text_query():
    url = "http://localhost:12000/chat"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "你好，请介绍一下你自己"}
                ]
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("Text Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 测试图片请求
def test_image_query(image_path):
    # 读取图片并转换为base64
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    url = "http://localhost:12000/chat"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "请描述这张图片的内容"},
                    {"image": f"data:image/png;base64,{encoded_image}"}
                ]
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("\nImage Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 测试多模态请求
def test_multimodal_query():
    url = "http://localhost:12000/chat"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "请生成一张日落的图片并描述它"}
                ]
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("\nMultimodal Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # 测试纯文本请求
    test_text_query()
    
    # 测试图片请求（替换为你的图片路径）
    # test_image_query("path/to/your/image.jpg")
    
    # 测试多模态请求
    test_multimodal_query()