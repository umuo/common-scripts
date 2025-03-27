#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import argparse
import sqlite3
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DirectoryMapping:
    def __init__(self, source_dir, target_dir, content_prefix=None):
        """
        初始化目录映射
        
        Args:
            source_dir: 源目录
            target_dir: 目标目录
            content_prefix: STRM文件内容前缀，如果为None则使用源目录
        """
        self.source_dir = os.path.abspath(source_dir)
        self.target_dir = os.path.abspath(target_dir)
        self.content_prefix = content_prefix if content_prefix else self.source_dir

class CloudDriveHandler(FileSystemEventHandler):
    def __init__(self, dir_mappings, db_path):
        """
        初始化处理器
        
        Args:
            dir_mappings: 目录映射列表
            db_path: SQLite数据库路径
        """
        self.dir_mappings = dir_mappings
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建文件同步记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS synced_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT UNIQUE,
            target_path TEXT,
            sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建目录同步记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS synced_dirs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dir_path TEXT UNIQUE,
            sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def on_created(self, event):
        """当检测到新文件创建时触发"""
        if event.is_directory:
            return
            
        # 获取文件路径
        file_path = event.src_path
        
        # 检查文件扩展名，只处理视频文件
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.3gp']
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in video_extensions:
            self.create_strm_file(file_path)
    
    def is_file_synced(self, file_path):
        """
        检查文件是否已经同步过
        
        Args:
            file_path: 原始文件的完整路径
            
        Returns:
            bool: 是否已同步
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM synced_files WHERE source_path = ?", (file_path,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def is_dir_synced(self, dir_path):
        """
        检查目录是否已经同步过
        
        Args:
            dir_path: 目录的完整路径
            
        Returns:
            bool: 是否已同步
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM synced_dirs WHERE dir_path = ?", (dir_path,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def record_synced_file(self, source_path, target_path):
        """
        记录已同步的文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标STRM文件路径
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO synced_files (source_path, target_path) VALUES (?, ?)",
            (source_path, target_path)
        )
        
        conn.commit()
        conn.close()
    
    def record_synced_dir(self, dir_path):
        """
        记录已同步的目录
        
        Args:
            dir_path: 目录路径
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO synced_dirs (dir_path) VALUES (?)",
            (dir_path,)
        )
        
        conn.commit()
        conn.close()
    
    def find_mapping_for_file(self, file_path):
        """
        查找文件对应的目录映射
        
        Args:
            file_path: 文件路径
            
        Returns:
            DirectoryMapping: 匹配的目录映射，如果没有找到则返回None
        """
        for mapping in self.dir_mappings:
            if file_path.startswith(mapping.source_dir):
                return mapping
        return None
    
    def create_strm_file(self, file_path):
        """
        为指定文件创建STRM文件
        
        Args:
            file_path: 原始文件的完整路径
        """
        # 检查文件是否已经同步过
        if self.is_file_synced(file_path):
            print(f"文件已同步过，跳过: {file_path}")
            return
        
        # 查找对应的目录映射
        mapping = self.find_mapping_for_file(file_path)
        if not mapping:
            print(f"找不到文件的目录映射，跳过: {file_path}")
            return
            
        # 获取相对路径
        rel_path = os.path.relpath(file_path, mapping.source_dir)
        
        # 构建目标STRM文件路径
        strm_path = os.path.join(mapping.target_dir, os.path.splitext(rel_path)[0] + '.strm')
        
        # 检查STRM文件是否已存在
        if os.path.exists(strm_path):
            print(f"STRM文件已存在，跳过: {strm_path}")
            # 记录到数据库
            self.record_synced_file(file_path, strm_path)
            return
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(strm_path), exist_ok=True)
        
        # 构建STRM文件内容
        content_path = os.path.join(mapping.content_prefix, rel_path)
        
        # 写入STRM文件
        with open(strm_path, 'w', encoding='utf-8') as f:
            f.write(content_path)
            
        # 记录到数据库
        self.record_synced_file(file_path, strm_path)
        
        print(f"已创建STRM文件: {strm_path} -> {content_path}")

def scan_existing_files(dir_mappings, db_path):
    """
    扫描现有文件并创建STRM文件
    
    Args:
        dir_mappings: 目录映射列表
        db_path: SQLite数据库路径
    """
    handler = CloudDriveHandler(dir_mappings, db_path)
    
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.3gp']
    
    for mapping in dir_mappings:
        source_dir = mapping.source_dir
        print(f"扫描目录: {source_dir}")
        for root, dirs, files in os.walk(source_dir):
            # 检查当前目录是否已同步过
            if handler.is_dir_synced(root):
                print(f"目录已同步过，跳过: {root}")
                dirs[:] = []  # 清空dirs列表，阻止os.walk继续遍历子目录
                continue
            
            # 处理当前目录中的文件
            has_video_files = False
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in video_extensions:
                    has_video_files = True
                    file_path = os.path.join(root, file)
                    handler.create_strm_file(file_path)
            
            # 如果当前目录包含视频文件，标记为已同步
            if has_video_files:
                handler.record_synced_dir(root)

def notify_emby_scan(emby_url, api_key, library_name=None):
    """
    通知Emby服务器扫描媒体库
    
    Args:
        emby_url: Emby服务器URL，例如 http://localhost:8096
        api_key: Emby API密钥
        library_name: 要扫描的媒体库名称，如果为None则扫描所有媒体库
        
    Returns:
        bool: 是否成功通知
    """
    if not emby_url or not api_key:
        print("未提供Emby服务器URL或API密钥，跳过通知")
        return False
    
    # 移除URL末尾的斜杠
    emby_url = emby_url.rstrip('/')
    
    try:
        # 如果指定了媒体库名称，先获取媒体库ID
        if library_name:
            # 获取所有媒体库
            libraries_url = f"{emby_url}/emby/Library/VirtualFolders?api_key={api_key}"
            response = requests.get(libraries_url, timeout=10)
            response.raise_for_status()
            
            libraries = response.json()
            library_id = None
            
            # 查找指定名称的媒体库
            for library in libraries:
                if library.get('Name') == library_name:
                    library_id = library.get('ItemId')
                    break
            
            if not library_id:
                print(f"找不到名为 '{library_name}' 的媒体库，将扫描所有媒体库")
                library_name = None
        
        # 构建扫描URL
        if library_name and library_id:
            # 扫描指定媒体库
            scan_url = f"{emby_url}/emby/Library/VirtualFolders/LibraryScan?api_key={api_key}&ItemId={library_id}"
            print(f"正在通知Emby扫描媒体库: {library_name}")
        else:
            # 扫描所有媒体库
            scan_url = f"{emby_url}/emby/Library/Refresh?api_key={api_key}"
            print("正在通知Emby扫描所有媒体库")
        
        # 发送扫描请求
        response = requests.post(scan_url, timeout=10)
        response.raise_for_status()
        
        print("已成功通知Emby开始扫描")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"通知Emby扫描失败: {str(e)}")
        return False

def parse_directory_mappings(mappings_str):
    """
    解析目录映射字符串
    
    Args:
        mappings_str: 格式为 "源目录#目标目录#内容前缀" 的字符串列表
        
    Returns:
        list: DirectoryMapping对象列表
    """
    mappings = []
    
    for mapping_str in mappings_str:
        parts = mapping_str.split('#')
        
        if len(parts) < 2:
            print(f"错误: 映射格式不正确: {mapping_str}")
            print("正确格式: 源目录#目标目录#[内容前缀]")
            continue
            
        source_dir = parts[0]
        target_dir = parts[1]
        content_prefix = parts[2] if len(parts) > 2 else None
        
        mappings.append(DirectoryMapping(source_dir, target_dir, content_prefix))
        
    return mappings

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='监控云盘目录并生成STRM文件')
    parser.add_argument('--mappings', '-m', required=True, nargs='+', 
                        help='目录映射，格式: "源目录#目标目录#[内容前缀]"')
    parser.add_argument('--scan', '-c', action='store_true', help='启动时扫描现有文件')
    parser.add_argument('--db', '-d', default='strm_monitor.db', help='SQLite数据库文件路径')
    parser.add_argument('--no-monitor', '-n', default=True, action='store_true', help='扫描后不启动监控')
    
    # parser.add_argument('--emby-url', '-e', help='Emby服务器URL，例如 http://localhost:8096')
    # parser.add_argument('--api-key', '-k', help='Emby API密钥')
    # parser.add_argument('--library', '-l', help='要扫描的Emby媒体库名称，不指定则扫描所有媒体库')
    
    
    args = parser.parse_args()
    
    # 解析目录映射
    dir_mappings = parse_directory_mappings(args.mappings)
    if not dir_mappings:
        print("错误: 没有有效的目录映射")
        return
        
    db_path = os.path.abspath(args.db)
    
    # 检查源目录是否存在
    for mapping in dir_mappings:
        if not os.path.exists(mapping.source_dir):
            print(f"错误: 源目录 '{mapping.source_dir}' 不存在")
            return
        
        # 确保目标目录存在
        os.makedirs(mapping.target_dir, exist_ok=True)
    
    # 如果需要，扫描现有文件
    if args.scan:
        print(f"扫描现有文件...")
        scan_existing_files(dir_mappings, db_path)
        
        # 扫描完成后通知Emby
        emby_url = "http://192.168.0.210:8096"
        api_key = "1aeb2181561440a796ff1649c591a825"
        notify_emby_scan(emby_url, api_key)
    
    # 如果指定了不监控，则直接返回
    if args.no_monitor:
        print("扫描完成，不启动监控")
        return
    
    # 设置监控
    event_handler = CloudDriveHandler(dir_mappings, db_path)
    observer = Observer()
    
    # 为每个源目录设置监控
    for mapping in dir_mappings:
        observer.schedule(event_handler, mapping.source_dir, recursive=True)
        print(f"已设置监控: {mapping.source_dir} -> {mapping.target_dir}")
        if mapping.content_prefix != mapping.source_dir:
            print(f"  STRM内容前缀: {mapping.content_prefix}")
    
    # 启动监控
    observer.start()
    print(f"同步记录保存到: {db_path}")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()
