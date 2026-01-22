import os
import asyncio
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import os
import re
from dotenv import load_dotenv
load_dotenv()

# --- 配置部分 ---
SKILLS_DIR = "./.skills"


# --- 1. 动态生成符合 XML 结构的描述 ---
def generate_skill_description(directory: str) -> str:
    """
    仿照 JS 逻辑生成 XML 格式的技能描述。
    结构:
    <available_skills>
      <skill>
        <name>...</name>
        <description>...</description>
      </skill>
    </available_skills>
    """
    # 确保目录存在
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 获取文件列表
    files = [f for f in os.listdir(directory) if not f.startswith('.')]

    # 逻辑分支 1：没有技能时的描述
    if not files:
        return "Load a skill to get detailed instructions for a specific task. No skills are currently available."

    # 逻辑分支 2：构建 XML 列表
    # 注意：这里我们将文件名作为 name，简单描述作为 description
    # 如果你的文件内容里有专门的描述字段，也可以在这里通过读取文件头获取
    xml_parts = []
    xml_parts.append("<available_skills>")

    for filename in files:
        xml_parts.append("  <skill>")
        xml_parts.append(f"    <name>{filename}</name>")
        # 简单将文件名作为描述，或者你可以根据文件扩展名做区分
        xml_parts.append(f"    <description>Contains instructions for {filename}</description>")
        xml_parts.append("  </skill>")

    xml_parts.append("</available_skills>")

    # 头部引导语
    header_parts = [
        "Load a skill to get detailed instructions for a specific task.",
        "Skills provide specialized knowledge and step-by-step guidance.",
        "Use this when a task matches an available skill's description.",
    ]

    # 组合所有部分 (使用换行符比空格更利于 LLM 理解 XML 结构)
    return "\n".join(header_parts + xml_parts)


# --- 1. 解析 Frontmatter 的辅助函数 ---
def parse_frontmatter(content: str):
    """
    解析类似 Jekyll/Hugo 的 YAML Frontmatter。
    返回一个字典 (metadata) 和剩余的正文 (body)。
    """
    # 匹配以 --- 开头，中间包裹内容的结构
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)

    metadata = {}
    body = content

    if match:
        yaml_text = match.group(1)
        body = match.group(2)

        # 简单解析 YAML 行： key: value
        for line in yaml_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, body


# --- 3. 定义工具 ---
@tool
def skill(skill_name: str) -> str:
    """
    Load a skill to get detailed instructions.
    Use the skill 'name' found in the description.
    """
    # 假设 skill_name 就是目录名或者 Frontmatter 中的 name
    # 这里我们简化处理：假设 skill_name == 目录名
    # 如果用户传的是 Frontmatter 里的 name (例如 html-to-pdf)，我们需要反向查找目录

    target_path = None
    target_dir_name = None

    # 1. 尝试直接拼接目录 (假设输入是目录名)
    potential_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    if os.path.exists(potential_path):
        target_path = potential_path
        target_dir_name = skill_name

    # 2. 如果找不到，遍历所有 SKILL.md 匹配 Frontmatter 中的 name
    else:
        for d in os.listdir(SKILLS_DIR):
            d_path = os.path.join(SKILLS_DIR, d)
            if os.path.isdir(d_path):
                s_file = os.path.join(d_path, "SKILL.md")
                if os.path.exists(s_file):
                    try:
                        with open(s_file, 'r', encoding='utf-8') as f:
                            cnt = f.read()
                        meta, _ = parse_frontmatter(cnt)
                        if meta.get("name") == skill_name:
                            target_path = s_file
                            target_dir_name = d
                            break
                    except:
                        continue

    if not target_path:
        return f"Error: Skill '{skill_name}' not found."

    try:
        with open(target_path, "r", encoding='utf-8') as f:
            raw_content = f.read()

        # 解析 Metadata 和 Body
        meta, body = parse_frontmatter(raw_content)
        name = meta.get("name", skill_name)

        # --- 构建符合 Plugin Pattern 的输出 ---
        output_parts = [
            f"## Skill: {name}",
            "",
            f"**Base directory**: {os.path.abspath(os.path.join(SKILLS_DIR, target_dir_name))}",
            "",
            body.strip()  # 去掉 YAML 头后的正文
        ]

        return "\n".join(output_parts)

    except Exception as e:
        return f"Error loading skill: {str(e)}"

# 【注入描述】
# 将生成的 XML 描述注入到工具中
current_description = generate_skill_description(SKILLS_DIR)
skill.description = current_description

# --- 3. 初始化 Agent ---
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
    model=model,
    debug=True,
    tools=[skill]
)


# --- 4. 主循环 ---
async def main():
    print(f"System: Skills loaded from {SKILLS_DIR}")
    print("System: Tool description updated with XML structure.")
    # 打印一下当前的 description 方便调试，确认 XML 结构正确
    # print(f"DEBUG Description:\n{skill.description}\n")
    print("--------------------------------------------------")

    chat_history = []

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            chat_history.append({"role": "user", "content": user_input})

            print("Agent: ", end="", flush=True)

            async for chunk in agent.astream({"messages": chat_history}):
                # print(chunk)
                if "model" in chunk:
                    model = chunk["model"]
                    if "messages" in model:
                        new_messages = model["messages"]
                        last_msg = new_messages[-1]
                        last_msg.pretty_print()

                        # 维护历史记录
                        for msg in new_messages:
                            if msg not in chat_history:
                                chat_history.append(msg)

        except KeyboardInterrupt:
            print("\nConversation ended.")
            break


if __name__ == '__main__':
    asyncio.run(main())
