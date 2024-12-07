
import re
import os
from openai import OpenAI

# ######手动配置项#######
API_KEY = "xxxx"
BASE_URL = "https://newapi.lacknb.com/v1"
MODEL = "grok-beta"
# #####################

# 初始化 OpenAI 客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def get_file_list(root_folder):
    """
    遍历目录，获取最深层次的所有文件路径列表
    :param root_folder: 需要遍历的根目录
    :return: 文件路径列表
    """
    file_list = []
    for root, _, files in os.walk(root_folder):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

def split_list(data, chunk_size):
    """
    将列表分割成指定大小的子列表
    :param data: 原列表
    :param chunk_size: 每个子列表的大小
    :return: 分割后的列表
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def extract_json_from_response(response):
    """
    从 ChatGPT 响应中提取 JSON 数据
    :param response: ChatGPT 返回的文本
    :return: 提取到的 JSON 数据（字典）
    """
    try:
        # 使用正则表达式查找 JSON 数据块
        json_match = re.search(r"{.*}", response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return eval(json_str)  # 将字符串转为字典
        else:
            print("未找到有效的 JSON 数据")
            return {}
    except Exception as e:
        print(f"JSON 提取失败: {e}")
        return {}


def generate_new_paths(file_paths, context_name):
    """
    使用 ChatGPT 生成符合 Emby 标准的新路径
    :param file_paths: 文件绝对路径列表
    :param context_name: 当前目录名（影视名称）
    :return: 一个字典，{原路径: 新路径}
    """
    movie_dir_name = "电影"
    tv_dir_name = "电视剧"
    anime_dir_name = "动漫"
    prompt = f"""
我有一个名为 '{context_name}' 的影视资源目录，里面存放着电影、电视剧和动漫。请根据以下 Emby 命名规范，为每个文件生成符合规范的新文件绝对路径。

**Emby 命名规范：**

*   **电影：**
    *   格式：`电影目录/电影名称 (年份).扩展名`
    *   电影目录名称：`{movie_dir_name}` (默认为"电影")
    *   电影名称和年份之间用空格和半角括号分隔。
    *   如果文件名中已包含年份，请尽量使用原有年份。
    *   如果存在多个版本（如导演剪辑版），请在年份后添加版本信息，例如：`电影名称 (年份) 导演剪辑版.扩展名`
*   **电视剧：**
    *   格式：`电视剧目录/剧集名称/Season 季号/剧集名称 - S季号E集号 - 集标题(可选).扩展名`
    *   电视剧目录名称：`{tv_dir_name}` (默认为"电视剧")
    *   季号和集号必须为两位数，不足两位前面补零。例如：`S01E01`
    *   剧集名称、季号、集号之间用空格和半角短横线 `-` 分隔。
    *   如果文件名中已包含季号和集号，请尽量使用原有信息。
    *   特殊剧集（如SP、OVA）放在 `Specials` 文件夹中，并使用 `S00E集号` 的格式。
*   **动漫：**
    *   格式：`动漫目录/动漫名称/Season 季号/动漫名称 - Ep 集号.扩展名`
    *   动漫目录名称：`{anime_dir_name}` (默认为"动漫")
    *   季号为两位数，不足两位前面补零。集号可以是一位或多位。
    *   动漫名称、季号、集号之间用空格和半角短横线 `-` 分隔。
    *   如果文件名中已包含季号和集号，请尽量使用原有信息。
    *   特殊剧集（如SP、OVA）放在 `Specials` 文件夹中，并使用 `Ep 特殊集号` 的格式,例如：`Ep01`。

**文件列表：**

{file_paths}

**要求：**

1. 请根据文件路径和名称，推断其属于电影、电视剧还是动漫。
2. 如果`{context_name}`下还有子文件夹，请递归的向下遍历。
3. 返回一个 **纯净的** JSON 格式字典，**不要包含任何其他字符**，例如说明文字、换行符等。字典格式如下：

{{
    "旧文件绝对路径": "新文件绝对路径",
    ...
}}
"""
    print(file_paths)
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL,
        )
        print(response.choices)
        result = response.choices[0].message.content.strip()
        return extract_json_from_response(result)  # 将返回的 JSON 字符串转换为 Python 字典
    except Exception as e:
        print(f"ChatGPT 调用失败: {e}")
        return {}

def rename_files(file_map):
    """
    根据文件映射字典重命名文件
    :param file_map: {原路径: 新路径} 的映射
    """
    for old_path, new_path in file_map.items():
        new_dir = os.path.dirname(new_path)
        # os.makedirs(new_dir, exist_ok=True)  # 确保新目录存在
        try:
            # os.rename(old_path, new_path)
            print(f"重命名成功: {old_path} -> {new_path}")
        except Exception as e:
            print(f"重命名失败: {old_path} -> {new_path}, 错误: {e}")

if __name__ == "__main__":
    # 获取根目录路径
    root_folder = input("请输入媒体文件夹路径: ").strip()
    context_name = os.path.basename(os.path.abspath(root_folder))  # 获取当前目录名作为影视名称
    
    # 获取文件列表
    file_paths = get_file_list(root_folder)
    if not file_paths:
        print("未找到任何文件，程序退出。")
        exit(0)
    for paths in split_list(file_paths, 20):

        # 使用 ChatGPT 生成新路径
        file_map = generate_new_paths(paths, context_name)
        if not file_map:
            print("ChatGPT 未返回有效结果，程序退出。")
            continue

        # 执行重命名
        rename_files(file_map)
