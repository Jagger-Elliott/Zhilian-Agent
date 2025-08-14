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
                    {"username": "李四"},
                    # {"text": "数据库查看李四用户的所有信息。"},
                    # {"text": "我的vip等级是什么？"}
                    {"text": "为我领取权益“家庭版单宽月均47元，即如果权益所需vip等级匹配用户vip等级后修改数据库中用户信息”"}
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
    # 测试图片请求
    # test_image_query("D:\\CodeField\\Zhilian-Agent\\Zhilian-Agent\\src\\chat\\qtbenefit.png")