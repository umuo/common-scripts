import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}


def get_start_load_param(html_content):
    """从HTML内容中提取start_load参数"""
    match = re.search(r'start_load\("([a-fA-F0-9]+)"\)', html_content)
    if match:
        return match.group(1)
    return None


def encrypt_and_md5(value, key, iv):
    """对字符串进行AES加密并生成MD5"""
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    encrypted_data = cipher.encrypt(pad(value.encode('utf-8'), AES.block_size))
    return encrypted_data.hex()


def main(url):
    # Step 1: 获取网页内容
    response = requests.get(url, headers=HEADERS)
    html_content = response.text

    # 提取start_load参数
    param = get_start_load_param(html_content)
    if not param:
        print("未能提取到start_load参数")
        return

    print(f"提取的参数: {param}")

    # Step 2: 对提取的参数进行AES加密并生成MD5
    key = "1234567812345678"
    iv = "1234567812345678"
    encrypted_md5 = encrypt_and_md5(param, key, iv)
    print(f"加密后的hex: {encrypted_md5}")

    # Step 3: 设置请求头
    HEADERS["Cookie"] = f"ck_ml_sea_={encrypted_md5}"

    # Step 4: 请求API
    api_url = "https://www.alipansou.com/active"
    data = {
        "code": "5678"
    }
    session = requests.Session()
    session.headers = HEADERS
    api_response = session.post(api_url, data=data)
    # print(api_response.cookies.get("_egg"))
    HEADERS["Cookie"] = f"{HEADERS['Cookie']};_egg={api_response.cookies.get('_egg')}"
    if api_response.status_code == 200:
        print("API请求成功")
    else:
        print(f"API请求失败，状态码: {api_response.status_code}")
    print(HEADERS)

    # Step 5: 再次请求目标URL

    final_response = session.get(url, allow_redirects=False)
    print(final_response.headers)
    location = final_response.headers.get("Location")
    if location:
        print(f"响应头中的Location字段: {location}")
    else:
        print("未能找到Location字段")


if __name__ == "__main__":
    target_url = "https://www.alipansou.com/cv/UdQ3H9VE0fL34Bao8cuwCtbSXAvkz"
    HEADERS["referer"] = target_url
    main(target_url)
