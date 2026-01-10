import random
import uuid
from datetime import datetime


def mock_tool_executor(tool_calls):
    """
    模拟执行工具调用并返回结果
    """
    results = []

    for tool in tool_calls:
        func_name = tool['function']['name']
        # tool_id 必须传回给 AI，以便它匹配哪个结果对应哪个调用
        call_id = tool['id']

        print(f"🛠️  Mock 执行工具: {func_name}...")

        if func_name == "read_file":
            # 模拟随机的文件内容
            mock_contents = [
                "User log: Success at 200 OK",
                "Config: { 'debug': True, 'version': '1.0.2' }",
                "Hello World! This is a mock file content.",
                f"Secret_Key: {uuid.uuid4().hex[:12]}"
            ]
            output = random.choice(mock_contents)

        elif func_name == "execute_bash":
            # 模拟随机的终端输出
            mock_outputs = [
                f"Total: 124 files, Date: {datetime.now().strftime('%Y-%m-%d')}",
                "Process PID 4502 started successfully.",
                "Error: Permission denied (just kidding, it's a mock)",
                "root  pts/0  2024-05-20 10:00 (192.168.1.1)"
            ]
            output = random.choice(mock_outputs)

        else:
            output = "Error: Tool not found."

        # 构造符合 OpenAI 格式的工具返回消息
        results.append({
            "tool_call_id": call_id,
            "role": "tool",
            "name": func_name,
            "content": output
        })

        print(f"✅ Mock 结果: {output}")

    return results


tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文件系统中的文件内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件的完整路径或相对路径。"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码，默认为 utf-8。",
                        "default": "utf-8"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "在本地终端执行 bash 命令并获取输出结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "需要执行的 bash 命令字符串。"
                    }
                },
                "required": ["command"]
            }
        }
    }
]
