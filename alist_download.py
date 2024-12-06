"""
alist 下载
"""
import requests
import hashlib
import json
import os
from tqdm import tqdm

# ########## 手动配置项 start #######
# 本地下载目录
DOWNLOAD_PATH = r"I:\emby\动漫"
# 远程的目录
REMOTE_PATH = r"/影视合集/动漫/【九龙珠】（风雷剑传奇、剑勇传说）国语中字"
alist_ip_port = "192.168.0.196:5244"
USERNAME = "xxx"
PASSWORD = "xxx"
# ########## 手动配置项 end #######

base_url = f"http://{alist_ip_port}"
url_dic = {
    "loginUrl": f"{base_url}/api/auth/login/hash",
    "listFile": f"{base_url}/api/fs/list",
    "downFile": f"{base_url}/d"
}
session = requests.session()
session.headers = {
    "content-type": "application/json;charset=UTF-8"
}


def get_sha256_hash(input_string: str) -> str:
    # 创建 sha256 哈希对象
    sha256_hash = hashlib.sha256()
    # 更新哈希对象
    sha256_hash.update(input_string.encode('utf-8'))
    # 获取十六进制的哈希值
    return sha256_hash.hexdigest()


def login_token():
    enc_password = PASSWORD + "-https://github.com/alist-org/alist"
    sha_password = get_sha256_hash(enc_password)
    data = {
        "username": USERNAME,
        "password": sha_password,
        "otp_code": ""
    }
    res = session.post(url_dic['loginUrl'], data=json.dumps(data))
    # print(res.json())
    print(res.json()['data']['token'])
    return res.json()['data']['token']
    pass


def list_files(path: str):
    data = {"path": path, "password": "", "page": 1, "per_page": 0, "refresh": False}
    res = session.post(url_dic['listFile'], data=json.dumps(data))
    print(res.json())
    pass


# 递归下载文件的函数
def download_files(path, password="", page=1, per_page=0, refresh=False):
    # 构建请求数据
    data = {
        "path": path,
        "password": password,
        "page": page,
        "per_page": per_page,
        "refresh": refresh
    }

    # 发送请求获取目录内容
    response = session.post(url_dic['listFile'], json=data)
    if response.status_code != 200:
        print(f"请求失败: {response.status_code}")
        return

    result = response.json()

    # 如果返回的代码不是200，说明请求失败
    if result.get("code") != 200:
        print(f"API 错误: {result.get('message')}")
        return

    # 获取文件夹内容
    content = result["data"]["content"]
    if content is None:
        return

    for item in content:
        item_name = item["name"]
        item_path = path + "/" + item_name # 当前项的路径
        path_part = [DOWNLOAD_PATH] + path.lstrip("/").split("/") + [item_name]
        local_item_path = os.path.join(*path_part)  # 本地保存路径

        if item["is_dir"]:  # 如果是目录，递归调用
            os.makedirs(local_item_path, exist_ok=True)  # 创建本地目录
            download_files(item_path, password, page, per_page, refresh)  # 递归处理子目录
        else:  # 如果是文件，下载文件
            download_file(item_path, local_item_path, item['sign'])


# 下载单个文件
def download_file(remote_file_path, download_item_path, sign):
    # 获取文件内容
    data = {
        "path": remote_file_path,
        "password": "",
        "page": 1,
        "per_page": 0,
        "refresh": False
    }
    print(remote_file_path, download_item_path, sign)
    if os.path.exists(download_item_path):
        print(f"{download_item_path} 已存在，跳过下载")
        return

    # 发送GET请求下载文件
    file_url = f"{url_dic['downFile']}{remote_file_path}?sign={sign}"
    file_response = session.get(file_url, stream=True)
    if file_response.status_code == 200:
        total_size = int(file_response.headers.get('content-length', 0))  # 获取文件总大小
        # 确保本地目录存在
        os.makedirs(os.path.dirname(download_item_path), exist_ok=True)
        with open(download_item_path, "wb") as f, tqdm(
            total=total_size, unit=' B', unit_scale=True, desc=download_item_path
        ) as bar:
            for chunk in file_response.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))  # 更新进度条
        print(f"已下载: {download_item_path}")
    else:
        print(f"文件下载失败: {file_url}")


if __name__ == '__main__':
    token = login_token()
    session.headers['authorization'] = token
    download_files(REMOTE_PATH)
    pass
