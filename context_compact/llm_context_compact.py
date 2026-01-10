from openai import OpenAI
from dotenv import load_dotenv
import httpx
import os
from tools import tools, mock_tool_executor
from token_compute import Token
import json
load_dotenv()

# 预留的输出空间, 32K, 精确值为32768, 保守取值 32000
reserved_output_space = 32000
# 模型最大上下文 128K
# model_max_context_space = 128000
model_max_context_space = 35000


# 定义拦截器函数
def log_request(request):
    print("\n--- [DEBUG] Raw Request Body ---")
    # request.content 是字节流，需要 decode
    body = request.content.decode("utf-8")
    try:
        # 格式化 JSON 方便阅读
        print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
    except:
        print(body)
    print("--- [DEBUG] End Request ---\n")


class LlmRequest:
    def __init__(self):
        self.client = OpenAI(base_url=os.environ['base_url'], api_key=os.environ['api_key'],
                             http_client=httpx.Client(event_hooks={'request': [log_request]}))
        self.messages = [
            {
                "role": "system",
                "content": "你是一个乐于助人的助手."
            }
        ]
        # 上次 token 消耗
        self.last_usage = {}
        pass

    def ask(self, query: str = None):
        """
        正常问AI
        :param query:
        :return:
        """
        if query:
            self.messages.append(
                {
                    "role": "user",
                    "content": query
                }
            )
        stream_completion = self.client.chat.completions.create(
            model=os.environ['model'],
            tools=tools,
            tool_choice="auto",  # 让AI决定是否调用
            stream_options={"include_usage": True},  # 想要看到消耗的token，需要加这个参数
            stream=True,
            messages=self.messages
        )
        full_content = ""
        tool_calls_buffer = {}  # 用于暂存工具调用的分片数据

        print("AI: ", end="", flush=True)
        for chunk in stream_completion:
            # 1. 提取 Token 使用量 (通常在最后一个 chunk)
            # 处理 Token 统计
            if chunk.usage:
                u = chunk.usage
                # 这里可以存起来或者打印
                self.last_usage = {
                    "prompt": u.prompt_tokens,
                    "completion": u.completion_tokens,
                    "total": u.total_tokens
                }
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            # 1. 处理文本内容
            if delta.content:
                full_content += delta.content
                print(delta.content, end="", flush=True)

            # 2. 处理工具调用 (Tool Calls)
            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    index = tool_call.index
                    if index not in tool_calls_buffer:
                        tool_calls_buffer[index] = {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        }

                    if tool_call.function.name:
                        tool_calls_buffer[index]["function"]["name"] += tool_call.function.name
                    if tool_call.function.arguments:
                        tool_calls_buffer[index]["function"]["arguments"] += tool_call.function.arguments

        print("\n")  # 换行
        if hasattr(self, 'last_usage'):
            print(f"\n(消耗: {self.last_usage['total']} tokens)")
        # 将完整的文本回复存入上下文
        if full_content:
            self.messages.append({"role": "assistant", "content": full_content})
        # 每轮都会进行工具裁剪
        self.tool_compact()
        # 如果有工具调用，处理逻辑
        if tool_calls_buffer:
            tool_calls = list(tool_calls_buffer.values())
            # 1. 把 AI 的工具请求存入上下文
            self.messages.append({"role": "assistant", "tool_calls": tool_calls})

            # 2. 执行 Mock 调用
            tool_results = mock_tool_executor(tool_calls)

            # 3. 把工具执行结果存入上下文
            self.messages.extend(tool_results)

            # 4. 再次发起请求，让 AI 根据工具结果说话
            print("AI 思考中...")
            self.ask(None)
            return

        # 打印本次消耗
        if hasattr(self, 'last_usage'):
            # 如果消耗的token数+预留数量大于最大上下文，就需要开始上下文压缩
            if self.last_usage['total'] + reserved_output_space > model_max_context_space:
                self.summary()
                pass
        pass

    def tool_compact(self):
        """
        工具调用裁剪
                1. 保护最近消息20K的工具输出不被裁剪
                2. 至少要裁掉10K的工具输出才执行
        :return:
        """
        prune_protect = 5_000  # 这里只保证最近的5K不被裁剪
        prune_minium = 1_000  # 只有达到1K才裁剪
        # 获取所有的工具调用结果
        tool_messages = [message for message in self.messages if message['role'] == 'tool']
        total = 0
        cut_tool_messages = []  # 需要裁剪的tool message
        cut_tool_total = 0  # 需要裁剪的tool 总token数
        # 从最新的tool 开始遍历
        for message in reversed(tool_messages):
            single_tool_count = Token.estimate(message['content'])
            total += single_tool_count
            # 大于 保护的token数之外的就需要裁剪了
            if total > prune_protect:
                cut_tool_total += single_tool_count
                cut_tool_messages.append(message)

        # 只有需要裁剪的量 大于 prune_minium 才开始裁剪
        if cut_tool_total > prune_minium:
            print("开始进行工具裁剪......")
            for message in cut_tool_messages:
                message['content'] = '[Old tool result content cleared]'

        pass

    def summary(self):
        """
        总结压缩
        :return:
        """
        print("开始进行总结压缩.......")
        system_prompt = """
        You are a helpful AI assistant tasked with summarizing conversations.

        When asked to summarize, provide a detailed but concise summary of the conversation. 
        Focus on information that would be helpful for continuing the conversation, including:
        - What was done
        - What is currently being worked on
        - Which files are being modified
        - What needs to be done next
        - Key user requests, constraints, or preferences that should persist
        - Important technical decisions and why they were made
        
        Your summary should be comprehensive enough to provide context but concise enough to be quickly understood.
        """
        summary_messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            *self.messages[1:],
            {
                "role": "user",
                # Provide a detailed prompt
                # for continuing our conversation above.
                # Focus on information that would be helpful for continuing the conversation,
                # including what we did, what we're doing, which files we're working on,
                # and what we're going to do next considering new session will not have access to our conversation.
                "content": """
                    请提供详细的提示，以便我们继续上述对话。 
                    关注有助于继续对话的信息，
                    包括我们做了什么，正在做什么，正在处理哪些文件，
                    考虑到新的会议，我们接下来要做的事情将无法进入我们的对话。
                """
            }
        ]
        resp = self.client.chat.completions.create(
            model=os.environ['model'],
            messages=summary_messages,
            stream=False
        )
        print(resp)
        summary = resp.choices[0].message.content
        self.messages = [self.messages[0], {"role": "user", "content": "What did we do so far?"},
                         {"role": "assistant", "content": summary}]
        pass


if __name__ == '__main__':
    llm = LlmRequest()
    print("=== 欢迎使用 AI 助手 (输入 'exit' 或 'quit' 退出) ===")

    while True:
        try:
            user_input = input("User >>> ").strip()

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            llm.ask(user_input)

        except KeyboardInterrupt:
            print("\n强制退出")
            break
    pass
