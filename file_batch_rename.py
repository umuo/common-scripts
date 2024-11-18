import os


def rename_mp4_to_dat(directory):
    # 使用 os.walk 遍历目录及子目录
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # 检查文件是否是 MP4 格式
            if filename.endswith(".mp4"):
                old_file_path = os.path.join(root, filename)
                new_file_path = os.path.join(root, filename[:-4] + ".dat")
                # 重命名文件
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {old_file_path} -> {new_file_path}")


# 指定要遍历的根目录路径
directory_path = r'I:\resource\local'

# 调用函数
rename_mp4_to_dat(directory_path)
