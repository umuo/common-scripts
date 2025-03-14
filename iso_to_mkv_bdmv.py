import subprocess
import os
import sys
import re
import time

# 配置
ISO_PATH = "/Volumes/Nas/emby/qbit_download/动漫/DB/DB/龙珠 Disc 01 (001-008).ISO"  # 替换为你的 ISO 路径
OUTPUT_DIR = "/Volumes/Nas/emby/resource/动漫/动漫/DB"          # 替换为输出目录

def mount_iso(iso_path):
    """挂载 ISO 文件，返回挂载路径"""
    if sys.platform == 'darwin':
        mount_cmd = ['hdiutil', 'mount', iso_path]
    elif sys.platform.startswith('linux'):
        mount_point = f"/mnt/iso_{time.strftime('%Y%m%d%H%M%S')}"
        os.makedirs(mount_point, exist_ok=True)
        mount_cmd = ['sudo', 'mount', '-o', 'loop', iso_path, mount_point]
    else:
        raise NotImplementedError("仅支持 macOS 和 Linux")

    result = subprocess.run(mount_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"挂载失败: {result.stderr}")
        sys.exit(1)

    # 解析挂载路径
    if sys.platform == 'darwin':
        mount_path = re.search(r'/Volumes/.+', result.stdout).group()
    else:
        mount_path = mount_point

    return mount_path

def find_main_m2ts(mount_path):
    """在挂载目录中查找最大的 .m2ts 文件（通常为主视频）"""
    stream_dir = os.path.join(mount_path, 'BDMV', 'STREAM')
    if not os.path.exists(stream_dir):
        print(f"未找到 STREAM 目录: {stream_dir}")
        sys.exit(1)

    # 按大小排序 .m2ts 文件
    m2ts_files = []
    for root, _, files in os.walk(stream_dir):
        for file in files:
            if file.endswith('.m2ts'):
                path = os.path.join(root, file)
                m2ts_files.append((path, os.path.getsize(path)))

    if not m2ts_files:
        print("未找到 .m2ts 文件")
        sys.exit(1)

    # 选择最大的文件
    m2ts_files.sort(key=lambda x: x[1], reverse=True)
    return m2ts_files[0][0]

def convert_with_ffmpeg(input_path, output_dir):
    """使用 FFmpeg 转换视频为 MKV（无损拷贝流）"""
    output_path = os.path.join(output_dir, os.path.basename(input_path).replace('.m2ts', '.mkv'))
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c', 'copy',  # 无损复制
        '-y',           # 覆盖输出文件
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"转换失败: {result.stderr}")
        sys.exit(1)
    print(f"转换完成: {output_path}")

def unmount(path):
    """卸载 ISO"""
    if sys.platform == 'darwin':
        cmd = ['hdiutil', 'unmount', path]
    else:
        cmd = ['sudo', 'umount', path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"卸载失败: {result.stderr}")
        sys.exit(1)
    print(f"已卸载: {path}")

if __name__ == '__main__':
    # 挂载 ISO
    mount_path = mount_iso(ISO_PATH)
    print(f"已挂载到: {mount_path}")

    # 定位主视频文件
    main_m2ts = find_main_m2ts(mount_path)
    print(f"找到主视频文件: {main_m2ts}")

    # 转换
    convert_with_ffmpeg(main_m2ts, OUTPUT_DIR)

    # 卸载
    unmount(mount_path)
