from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from rich.console import Console
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from rich.panel import Panel
import sys
import logging

load_dotenv()
# 1. 配置基础日志
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)  # 全局设为 WARNING 防止其他库刷屏

# 2. 专门开启 openai 和 httpx 的调试日志
# 这将打印出: HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
logging.getLogger("openai").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)
console = Console()
model = init_chat_model(
    # 1. 模型名称 (你的自定义模型名)
    os.environ['OPENAI_MODEL'],

    # 2. 提供商 (对于兼容 OpenAI 接口的服务，这里通常填 "openai")
    model_provider="openai",

    # 3. 自定义参数
    api_key=os.environ['OPENAI_API_KEY'],  # 你的 API Key
    base_url=os.environ['OPENAI_BASE_URL'],  # 你的 Base URL
)

agent = create_deep_agent(
    skills=['./.skills'],
    backend=FilesystemBackend(root_dir=r"E:\PythonProject\PycharmProjects\common-scripts\skills_use"),
    subagents=[],
    model=model
)
question = input("Question: ")
# Display the question
console.print(Panel(
    f"[bold cyan]Question:[/bold cyan] {question}",
    border_style="cyan"
))
console.print()
try:
    result = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })

    # Extract and display the final answer
    final_message = result["messages"][-1]
    answer = final_message.content if hasattr(final_message, 'content') else str(final_message)

    console.print(Panel(
        f"[bold green]Answer:[/bold green]\n\n{answer}",
        border_style="green"
    ))

except Exception as e:
    console.print(Panel(
        f"[bold red]Error:[/bold red]\n\n{str(e)}",
        border_style="red"
    ))
    sys.exit(1)
