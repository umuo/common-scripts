#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: gitsilence
# @Time: 2025/4/13 23:12
"""
Github 仓库备份脚本
1、创建 .env 文件，配置 GITHUB_USERNAME 和 GITHUB_TOKEN
`
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_token
`
2、运行脚本
"""
import os
import subprocess
import requests
from typing import List
from dotenv import load_dotenv
# 加载 .env 文件中的环境变量
load_dotenv()

# ========= 配置区 =========
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # 注意不要泄露
BACKUP_DIR = "/Users/gitsilence/remote_github_bak"  # 本地备份的主目录
EXCLUDE_REPOS = ["xxx"]  # 要排除的仓库名称


# ==========================

def get_all_repos(username: str, token: str) -> List[dict]:
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner"
        response = requests.get(url, auth=(username, token))
        if response.status_code != 200:
            raise Exception(f"获取仓库失败: {response.status_code} - {response.text}")
        page_repos = response.json()
        if not page_repos:
            break
        repos.extend(page_repos)
        page += 1
    return repos


def run_git_command(args: List[str], cwd: str = None):
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"命令失败: {' '.join(args)}\n{result.stderr}")
    else:
        print(result.stdout)


def clone_or_update_repo(repo: dict, base_dir: str, token: str):
    repo_name = repo["name"]
    if repo_name in EXCLUDE_REPOS:
        print(f"跳过仓库: {repo_name}")
        return

    clone_url = repo["clone_url"]
    # 替换成带 token 的 URL（避免交互式登录）
    clone_url_with_auth = clone_url.replace("https://", f"https://{GITHUB_USERNAME}:{token}@")

    repo_path = os.path.join(base_dir, repo_name)
    if os.path.exists(repo_path):
        print(f"\n更新仓库: {repo_name}")
        run_git_command(["git", "pull"], cwd=repo_path)
    else:
        print(f"\n克隆仓库: {repo_name}")
        run_git_command(["git", "clone", clone_url_with_auth, repo_path])


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print("正在获取仓库列表...")
    repos = get_all_repos(GITHUB_USERNAME, GITHUB_TOKEN)
    print(f"共找到 {len(repos)} 个仓库")

    for repo in repos:
        clone_or_update_repo(repo, BACKUP_DIR, GITHUB_TOKEN)

    print("\n✅ 所有仓库处理完成。")


if __name__ == "__main__":
    main()
