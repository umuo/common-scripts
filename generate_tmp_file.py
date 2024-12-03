# --coding: utf-8--
"""
批量生成临时文件用的脚本
"""
import os
import random
import string


def generate_random_filename(extension):
    """生成一个随机文件名，带有指定扩展名"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + f".{extension}"


def generate_random_content(size):
    """生成指定大小的随机内容"""
    return os.urandom(size)


def create_files_in_directory(directory, total_size, total_count, extensions):
    """
    在指定目录中生成临时文件。
    参数：
        directory: 目标目录
        total_size: 文件总大小（字节）
        total_count: 文件总数量
        extensions: 文件扩展名列表
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 平均每个文件大小
    avg_size = total_size // total_count
    remaining_size = total_size % total_count

    for i in range(total_count):
        # 随机选择文件扩展名
        extension = random.choice(extensions)
        # 如果是最后一个文件，增加剩余的大小
        size = avg_size + (remaining_size if i == total_count - 1 else 0)
        # 生成随机文件名和内容
        filename = generate_random_filename(extension)
        filepath = os.path.join(directory, filename)
        content = generate_random_content(size)
        # 写入文件
        with open(filepath, 'wb') as f:
            f.write(content)
        print(f"Generated: {filename} ({size} bytes)")


# 配置参数
output_directory = r"E:\DeskTop\tmp\Att"  # 目标目录
total_size_in_mb = 1024 * 10  # 文件总大小（MB）
total_count = 10000  # 文件总数量
file_extensions = ["jpg", "mp4", "avi", "jpeg", "png"]  # 支持的文件格式

# 转换大小到字节
total_size_in_bytes = total_size_in_mb * 1024 * 1024

# 调用生成函数
create_files_in_directory(output_directory, total_size_in_bytes, total_count, file_extensions)

