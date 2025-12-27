#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: gitsilence
# @Time: 2025/10/29 14:36
from openai import OpenAI

keys = """
apikey1
apikey2
apikey3
"""


keys = [key.strip() for key in keys.splitlines() if key != '']
for key in keys:
    print(key)
    client = OpenAI(api_key=key, base_url="https://api.qnaigc.com/v1")
    try:
        completion = client.chat.completions.create(
            model="claude-4.5-sonnet",
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=100,
        )
        print(completion.choices[0].message.content)
        print("--" * 30)
    except Exception as e:
        print("异常了-", e)
