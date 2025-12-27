#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: gitsilence
# @Time: 2025/10/31
from openai import OpenAI
import time
from datetime import datetime

keys = """
apikey1
apikey2
apikey3
"""

# 测试配置
REQUEST_COUNT = 10  # 每个key发送的请求数
REQUEST_INTERVAL = 0.5  # 请求间隔（秒），可以调整来测试不同速率

keys = [key.strip() for key in keys.splitlines() if key != '']


def rpm_for_key(api_key):
    """测试单个API key的RPM限制"""
    print(f"\n{'='*60}")
    print(f"开始测试 API Key: {api_key[:20]}...")
    print(f"{'='*60}")

    client = OpenAI(api_key=api_key, base_url="https://api.qnaigc.com/v1")

    success_count = 0
    rate_limit_count = 0
    error_count = 0

    start_time = time.time()

    for i in range(REQUEST_COUNT):
        request_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n[{i+1}/{REQUEST_COUNT}] 请求时间: {request_time}")

        try:
            completion = client.chat.completions.create(
                model="claude-4.5-sonnet",
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=10,
            )
            success_count += 1
            print(f"✓ 成功 - 响应: {completion.choices[0].message.content}")

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                rate_limit_count += 1
                print(f"✗ 达到速率限制 - {error_msg}")
            else:
                error_count += 1
                print(f"✗ 其他错误 - {error_msg}")

        # 等待指定时间后发送下一个请求
        if i < REQUEST_COUNT - 1:
            time.sleep(REQUEST_INTERVAL)

    end_time = time.time()
    duration = end_time - start_time
    actual_rpm = (success_count / duration) * 60

    # 打印统计结果
    print(f"\n{'='*60}")
    print(f"测试完成 - API Key: {api_key[:20]}...")
    print(f"{'='*60}")
    print(f"总请求数: {REQUEST_COUNT}")
    print(f"成功请求: {success_count}")
    print(f"速率限制: {rate_limit_count}")
    print(f"其他错误: {error_count}")
    print(f"测试时长: {duration:.2f} 秒")
    print(f"实际速率: {actual_rpm:.2f} RPM (每分钟请求数)")
    print(f"{'='*60}\n")

    return {
        "api_key": api_key[:20] + "...",
        "success": success_count,
        "rate_limited": rate_limit_count,
        "errors": error_count,
        "duration": duration,
        "rpm": actual_rpm
    }


if __name__ == "__main__":
    print("开始测试 API Keys 的 RPM 限制")
    print(f"每个 key 将发送 {REQUEST_COUNT} 个请求")
    print(f"请求间隔: {REQUEST_INTERVAL} 秒")

    results = []
    for key in keys:
        result = rpm_for_key(key)
        results.append(result)
        # 在测试不同key之间添加更长的延迟
        time.sleep(2)

    # 打印汇总结果
    print("\n" + "="*60)
    print("所有测试结果汇总")
    print("="*60)
    for i, result in enumerate(results, 1):
        print(f"\nKey {i}: {result['api_key']}")
        print(f"  成功: {result['success']}, 限流: {result['rate_limited']}, 错误: {result['errors']}")
        print(f"  实际速率: {result['rpm']:.2f} RPM")
