# --coding: utf-8--
import os
import m3u8
import requests
import ffmpeg


# 下载 m3u8 文件并解析
def download_m3u8(m3u8_url):
    # 获取 m3u8 文件内容
    response = requests.get(m3u8_url)
    playlist = m3u8.loads(response.text)
    return playlist


# 下载 TS 文件
def download_ts_files(playlist, download_dir):
    ts_urls = []
    for segment in playlist.segments:
        ts_url = segment.uri
        if not ts_url.startswith("http"):
            ts_url = os.path.join(os.path.dirname(playlist.base_uri), ts_url)


        # 下载 TS 文件
        ts_filename = os.path.join(download_dir, os.path.basename(ts_url))
        if not os.path.exists(ts_filename):
            print(f"Downloading {ts_filename}...")
            ts_response = requests.get(ts_url, stream=True)
            with open(ts_filename, 'wb') as f:
                for chunk in ts_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        ts_urls.append(ts_filename)
    return ts_urls


# 合并 TS 文件并转换为 MP4
def merge_and_convert_to_mp4(ts_files, output_mp4):
    # 使用 ffmpeg 合并并转换
    ts_list_file = "ts_list.txt"
    with open(ts_list_file, 'w') as f:
        for ts_file in ts_files:
            f.write(f"file '{ts_file}'\n")

    print("Merging and converting to MP4...")
    output = ffmpeg.input(ts_list_file, format='concat', safe=0).output(output_mp4, vcodec='libx264', acodec='aac')
    command = output.compile()
    print(" ".join(command))
    output.run()

    # 删除中间文件
    os.remove(ts_list_file)
    for ts_file in ts_files:
        os.remove(ts_file)


def main(m3u8_url, output_mp4):
    # 创建临时下载目录
    download_dir = "downloaded_ts"
    os.makedirs(download_dir, exist_ok=True)

    # 下载并解析 m3u8 文件
    print("Parsing M3U8...")
    playlist = download_m3u8(m3u8_url)

    # 下载 TS 文件
    ts_files = download_ts_files(playlist, download_dir)

    # 合并 TS 文件并转换为 MP4
    merge_and_convert_to_mp4(ts_files, output_mp4)

    print(f"Video saved as {output_mp4}")


if __name__ == "__main__":
    # 输入 M3U8 URL 和输出的 MP4 文件名
    m3u8_url = 'https://s3plus.sankuai.com/annualbill-private/m3u8/4c1b993b-82b7-4700-aa9e-372e6c6ebe49.m3u8?AWSAccessKeyId=SRV_u80fSKXwuNYN7Dt3y7nT5T2QhtZVtM7P&Expires=1735109263&Signature=bB6Q%2FFvLsFk49TsC4UU1c6IE2Vk%3D'  # 替换为你的 M3U8 文件地址
    output_mp4 = 'output_video.mp4'
    # ffmpeg_path = r'D:\Downloads\aaa\ffmpeg.exe'
    # ffmpeg下载地址：https://github.com/BtbN/FFmpeg-Builds/releases

    main(m3u8_url, output_mp4)


