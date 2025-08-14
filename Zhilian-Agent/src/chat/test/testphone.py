import requests
import json
import time
import base64
def test_phone_call_handle():
    """测试电话呼叫处理接口"""
    # 接口地址
    url = "http://localhost:12000/phonecallhandle"
    
    # 请求头
    headers = {"Content-Type": "application/json"}
    
    # 测试不同电话号码
    test_numbers = [
        "13912345678",   # 正常电话
        "18187654321",   # 黑名单电话
        # "13800138000",   # 骚扰电话（假设数据库中存在的号码）
        # "123-456-7890",  # 带分隔符的电话
        # "这是文本中的电话：400-820-8820",  # 包含电话号码的文本
        # "无效号码"        # 无效号码测试
    ]
    
    for phone in test_numbers:
        print(f"\n测试电话号码: {phone}")
        
        # 构建请求数据
        payload = {"phone_number": phone}
        
        # 发送请求
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        end_time = time.time()
        
        # 打印响应状态
        print(f"响应状态码: {response.status_code}")
        print(f"响应时间: {end_time - start_time:.2f}秒")
        
        # 解析响应
        if response.status_code == 200:
            response_data = response.json()
            
            # 打印结果摘要
            result = response_data.get('result', {})
            print(f"处理结果:")
            print(f"  电话号码: {result.get('phone_number', '')}")
            print(f"  电话类型: {result.get('call_type', '')}")
            print(f"  提示信息: {result.get('message', '')}")
            print(f"  音频文件: {result.get('audiopath', '')}")
            print(f"  音频数据长度: {len(result.get('audio', ''))} 字符")
            
            # 保存音频文件（可选）
            save_audio = input("是否保存音频文件？(y/n): ").lower() == 'y'
            if save_audio and 'audio' in result and result['audio']:
                filename = f"call_{result['phone_number']}_{int(time.time())}.wav"
                with open(filename, "wb") as audio_file:
                    audio_file.write(base64.b64decode(result['audio']))
                print(f"音频已保存为: {filename}")
        else:
            print(f"错误响应: {response.text}")
        
        print("-" * 50)

if __name__ == "__main__":
    # 测试单个电话号码处理
    test_phone_call_handle()