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
                    {"username": "张三"},
                    {"text": "请问联通公司的业务主要是什么"}
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
                    {"username": "张三"},
                    {"text": "请描述这张图片的内容"},
                    {"image": f"{encoded_image}"}
                ]
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("\nImage Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_final_answer():
    """
    测试带有 Final Answer 的回复
    """
    url = "http://localhost:12000/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"username": "张三"},
                    {"text":"什么是狗？要给出多个相关图片"}
                    # {"text": "生成含有权益信息的英文海报图片，图片主题颜色是红色，图片主要内容是“You've successfully claimed the “200M Home Edition Single Broadband” package, with an average monthly cost of RMB 47. The benefit has now taken effect in your account.”"}
                ]
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("\nTest Final Answer Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # 测试纯文本请求
    # test_text_query()
    test_final_answer()