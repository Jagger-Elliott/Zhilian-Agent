import os, sys
from pprint import pprint
from typing import Optional
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
from agents import ReActAgent
from qwen_agent.gui import WebUI
from recognition import parse
from planner import TaskDecomposer
from tools import MyImageGen, PhoneCallHandler, TextToSpeech

ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')

os.environ['DASHSCOPE_API_KEY'] = 'sk-45d286a145b7486d940d9c1e90d4061d'
os.environ['GRADIO_SERVER_PORT'] = '12000'
def init_agent_service():
    llm_cfg = {
        'model': 'qwen-max',
        'model_server': 'dashscope',
        'api_key': os.getenv('DASHSCOPE_API_KEY'),
    }
    tools = [
        # TaskDecomposer(),
        MyImageGen(),
        # TextToSpeech(),
        # PhoneCallHandler(),
    ]
    bot = ReActAgent(llm=llm_cfg,
                    name='general agent',
                    description='This agent can solve the problem',
                    function_list=tools)
    return bot


def test(query: str = 'pd.head the file first and then help me draw a line chart to show the changes in stock prices',
         file: Optional[str] = os.path.join(ROOT_RESOURCE, 'stock_prices.csv')):
    # Define the agent
    bot = init_agent_service()

    # Chat
    messages = []

    if not file:
        messages.append({'role': 'user', 'content': query})
    else:
        messages.append({'role': 'user', 'content': [{'text': query}, {'file': file}]})

    for response in bot.run(messages):
        pprint(response, indent=2)


def app_tui():
    # Define the agent
    bot = init_agent_service()


    # Chat
    messages = []
    while True:
        # Query example: pd.head the file first and then help me draw a line chart to show the changes in stock prices
        query = input('user question: ')
        # File example: resource/stock_prices.csv
        file = input('file url (press enter if no file): ').strip()
        if not query:
            print('user question cannot be empty！')
            continue
        intent = parse(query)
        if not file:
            messages.append({'role': 'user', 'content': intent})
        else:
            messages.append({'role': 'user', 'content': [{'text': intent}, {'file': file}]})

        response = []
        for response in bot.run(messages):
            print('bot response:', response)
        messages.extend(response)


def app_gui():
    bot = init_agent_service()
    chatbot_config = {
    }
    WebUI(bot, chatbot_config=chatbot_config).run()


if __name__ == '__main__':
    app_gui()
