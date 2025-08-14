import requests
import base64
import json

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
                    {"text": "帮我查一下当前微博热搜前5条？"}
                    # {"text":"帮我查一下故宫到颐和园怎么走，周边有什么美食推荐嘛？生成美食相关图片"}
                    # {"text":"帮我查一下北京到颐和园怎么走。根据最终路线生成二维平面地图"}
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