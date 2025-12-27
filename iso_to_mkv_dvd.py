import subprocess
import os
import sys
import time
import re

# 可配置指定的iso文件绝对路径，或者配置指定的目录，扫描iso文件
ISO_ITEM_LIST = [
    "/Volumes/Nas/emby/qbit_download/动漫/DB/DBZ"
]
EXCLUDE_ISO_LIST = [
    "龙珠二世 Disc 18 (137-144).ISO"
]
# 输出的目录名
OUTPUT_DIR = "/Volumes/Nas/emby/qbit_download/动漫/DB/db_mkv"  # 替换为输出目录    # 替换为输出目录


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
        # VTS_01_8.VOB
        if (file.upper().startswith("VTS_") and
                file.upper().endswith(".VOB") and
                not file.upper().startswith("VTS_00") and
                #  排除第一个视频文件
                not file.upper() != 'VTS_00_0.VOB'):
            path = os.path.join(video_ts_dir, file)
            vob_files.append((path, os.path.getsize(path)))

    if not vob_files:
        print("未找到主 VOB 文件")
        sys.exit(1)

    # 按大小排序，选择最大的（通常为主影片）
    vob_files.sort(key=lambda x: x[1], reverse=True)
    return [vob[0] for vob in vob_files]


def convert_with_ffmpeg(input_path, output_dir):
    """转换 VOB 为 MKV（简单模式，转换所有流）"""
    output_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{output_name}.mkv")
    cmd = [
        'ffmpeg',
        '-fflags', '+genpts',
        '-i', input_path,
        '-map', '0:v',
        '-map', '0:a',
        '-map', '0:s?',
        '-map', '-0:d',
        '-c', 'copy',  # 完全无损复制
        '-f', 'matroska',
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


def process_iso(iso_path, output_dir):
    """处理单个ISO文件"""
    mount_path = mount_iso(iso_path)
    try:
        print(f"已挂载到: {mount_path}")

        # 定位主 VOB 文件
        main_vobs = find_main_vts(mount_path)
        print(f"找到主视频文件: {main_vobs}")

        # 转换
        output_files = []
        for vob in main_vobs:
            convert_with_ffmpeg(vob, output_dir)
            output_name = os.path.splitext(os.path.basename(vob))[0]
            output_files.append(os.path.join(output_dir, f"{output_name}.mkv"))

        # 按文件名排序后合并
        output_files.sort()
        # 从ISO_PATH提取文件名(不带扩展名)
        iso_name = os.path.splitext(os.path.basename(iso_path))[0]
        merged_output = os.path.join(OUTPUT_DIR, f"{iso_name}.mkv")  # 使用ISO文件名
        list_file = os.path.join(OUTPUT_DIR, "file_list.txt")

        with open(list_file, "w") as f:
            for file in output_files:
                f.write(f"file '{file}'\n")

        # 合并命令基本参数
        merge_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-map', '0',      # 映射所有流
            '-c', 'copy',    # 复制所有流
            '-y',
            merged_output
        ]

        # 检测是否有字幕流
        has_subtitle = any('srt' in file for file in output_files)
        if has_subtitle:
            merge_cmd.extend([
                '-map', '0:s',
                '-c:s', 'copy'
            ])

        merge_cmd.append(merged_output)

        subprocess.run(merge_cmd)
        print(f"合并完成: {merged_output}")

        # 清理临时文件
        for file in output_files:
            os.remove(file)
        os.remove(list_file)
        print("已清理临时文件")

    finally:
        # 卸载
        unmount(mount_path)


if __name__ == '__main__':
    # 判断输入是文件还是目录
    for iso_item in ISO_ITEM_LIST:
        if os.path.isdir(iso_item):
            # 遍历目录中的ISO文件
            for file in os.listdir(iso_item):
                if file in EXCLUDE_ISO_LIST:
                    print("跳过: ", file, " 因为在排除列表中")
                    continue
                if file.lower().endswith('.iso'):
                    iso_file = os.path.join(iso_item, file)
                    print(f"\n开始处理: {iso_file}")
                    process_iso(iso_file, OUTPUT_DIR)
        elif os.path.isfile(iso_item) and iso_item.lower().endswith('.iso'):
            # 处理单个ISO文件
            process_iso(iso_item, OUTPUT_DIR)
        else:
            print("错误: 输入路径必须是ISO文件或包含ISO文件的目录")
            sys.exit(1)
