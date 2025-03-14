import subprocess
import os
import sys
import time
import re

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

def find_main_vts(mount_path):
    """定位 DVD 主视频（通常为最大的 VTS_XX_X.VOB 文件）"""
    video_ts_dir = os.path.join(mount_path, 'VIDEO_TS')
    if not os.path.exists(video_ts_dir):
        print(f"未找到 VIDEO_TS 目录: {video_ts_dir}")
        sys.exit(1)

    # 收集所有 VOB 文件（排除 VIDEO_TS.VOB 等菜单文件）
    vob_files = []
    for file in os.listdir(video_ts_dir):
        if file.upper().startswith("VTS_") and file.upper().endswith(".VOB") and not file.upper().startswith("VTS_00"):
            path = os.path.join(video_ts_dir, file)
            vob_files.append((path, os.path.getsize(path)))

    if not vob_files:
        print("未找到主 VOB 文件")
        sys.exit(1)

    # 按大小排序，选择最大的（通常为主影片）
    vob_files.sort(key=lambda x: x[1], reverse=True)
    return [vob[0] for vob in vob_files ]

def convert_with_ffmpeg(input_path, output_dir):
    """转换 VOB 为 MP4/MKV（示例为 H.264 编码）"""
    output_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{output_name}.mp4")
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',  # 使用 H.264 编码
        '-crf', '23',       # 质量参数（0-51，值越小质量越高）
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
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
    try:
        print(f"已挂载到: {mount_path}")

        # 定位主 VOB 文件
        main_vobs = find_main_vts(mount_path)
        print(f"找到主视频文件: {main_vobs}")

        # 转换
        for vob in main_vobs:
            convert_with_ffmpeg(vob, OUTPUT_DIR)
    finally:
        # 卸载
        unmount(mount_path)
