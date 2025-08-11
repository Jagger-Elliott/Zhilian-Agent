# IntentRecognitionAgent 使用说明

## 概述

`IntentRecognitionAgent` 是一个智能意图识别代理，能够自动识别用户输入的意图类型，并路由到相应的处理流程。它基于 `VisualStorytelling` 类的架构设计，提供了更智能的用户交互体验。

## 功能特性

### 支持的意图类型

1. **图像分析** - 分析用户上传的图片内容
2. **权益分析** - 专门分析联通权益相关内容
3. **图像生成** - 根据用户描述生成图片
4. **语音合成** - 将文本转换为语音
5. **电话处理** - 处理电话号码相关功能
6. **数据库查询** - 查询和操作数据库
7. **代码执行** - 执行代码或解决技术问题
8. **一般对话** - 普通聊天或问答

### 核心组件

- **意图识别代理** (`intent_agent`) - 分析用户输入并识别意图
- **图像分析代理** (`image_analysis_agent`) - 使用视觉模型分析图片
- **权益分析代理** (`benefit_analysis_agent`) - 专门处理联通权益分析
- **工具处理代理** (`tool_agent`) - 处理各种工具调用
- **一般对话代理** (`chat_agent`) - 处理普通对话

## 安装和使用

### 1. 环境要求

```bash
# 确保已安装必要的依赖
pip install qwen-agent
```

### 2. 基本使用

```python
from agent.intent_recognition import IntentRecognitionAgent
from qwen_agent.llm.schema import Message, ContentItem

# 创建代理实例
bot = IntentRecognitionAgent(llm={'model': 'qwen-max'})

# 发送消息
messages = [Message('user', [ContentItem(text='请帮我生成一张美丽的风景图片')])]
for response in bot.run(messages):
    print(response)
```

### 3. 图像分析示例

```python
# 分析图片中的权益内容
messages = [Message('user', [
    ContentItem(image='path/to/image.jpg'),
    ContentItem(text='分析这张图片中的权益内容')
])]

for response in bot.run(messages):
    print(response)
```

### 4. 工具调用示例

```python
# 语音合成
messages = [Message('user', [ContentItem(text='请将"你好，欢迎使用联通服务"转换为语音')])]

# 电话处理
messages = [Message('user', [ContentItem(text='请处理电话号码13912345678')])]

# 数据库查询
messages = [Message('user', [ContentItem(text='查询用户数据库中的所有用户信息')])]
```

## 运行测试

### 命令行测试

```bash
cd Zhilian-Agent
python test_intent_agent.py
```

### GUI 界面

```python
from agent.intent_recognition import app_gui

# 启动Web界面
app_gui()
```

## 配置选项

### 自定义工具集

```python
from tools import MyImageGen, TextToSpeech, PhoneCallHandler

custom_tools = [
    MyImageGen(),
    TextToSpeech(),
    PhoneCallHandler(),
    'code_interpreter'
]

bot = IntentRecognitionAgent(
    llm={'model': 'qwen-max'},
    function_list=custom_tools
)
```

### 自定义LLM模型

```python
# 使用不同的模型
bot = IntentRecognitionAgent(llm={'model': 'qwen-vl-max'})
```

## 工作流程

1. **意图识别**: 分析用户输入，识别意图类型
2. **路由决策**: 根据意图类型选择相应的处理代理
3. **内容处理**: 执行具体的处理逻辑
4. **结果返回**: 返回处理结果给用户

## 错误处理

代理包含完善的错误处理机制：

- 输入格式验证
- 图片路径检查
- 工具调用异常处理
- 友好的错误提示

## 扩展开发

### 添加新的意图类型

1. 在 `intent_agent` 的系统消息中添加新的意图类型
2. 在 `_run` 方法中添加相应的路由逻辑
3. 创建对应的处理代理（如需要）

### 添加新的工具

1. 在 `default_tools` 列表中添加新工具
2. 在相应的代理中更新系统消息
3. 确保工具正确导入和配置

## 注意事项

1. 确保API密钥正确配置
2. 图片路径需要是有效的本地路径或URL
3. 数据库文件路径需要正确设置
4. 网络连接正常以访问外部服务

## 故障排除

### 常见问题

1. **导入错误**: 检查路径配置和依赖安装
2. **API错误**: 验证API密钥和网络连接
3. **图片处理失败**: 检查图片格式和路径
4. **工具调用失败**: 确认工具配置和权限

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 运行代理时会显示详细的调试信息
```

## 更新日志

- **v1.0.0**: 初始版本，支持基本的意图识别和路由功能
- 基于 `VisualStorytelling` 架构设计
- 支持多种意图类型和工具集成 