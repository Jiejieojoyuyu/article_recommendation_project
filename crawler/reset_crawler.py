#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫重置工具
用于清空数据库、重置进度、删除日志文件等
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path

def reset_database(db_path: str):
    """重置数据库"""
    if os.path.exists(db_path):
        try:
            # 删除数据库文件
            os.remove(db_path)
            print(f"✅ 已删除数据库文件: {db_path}")
        except Exception as e:
            print(f"❌ 删除数据库文件失败: {e}")
    else:
        print(f"ℹ️  数据库文件不存在: {db_path}")

def reset_progress(progress_file: str = "crawl_progress.json"):
    """重置进度文件"""
    if os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print(f"✅ 已删除进度文件: {progress_file}")
        except Exception as e:
            print(f"❌ 删除进度文件失败: {e}")
    else:
        print(f"ℹ️  进度文件不存在: {progress_file}")

def reset_logs(log_file: str = "crawler.log"):
    """重置日志文件"""
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
            print(f"✅ 已删除日志文件: {log_file}")
        except Exception as e:
            print(f"❌ 删除日志文件失败: {e}")
    else:
        print(f"ℹ️  日志文件不存在: {log_file}")

def reset_all():
    """重置所有文件"""
    print("🔄 开始重置爬虫...")
    
    # 重置数据库
    reset_database("openalex_advanced.db")
    reset_database("openalex.db")
    reset_database("test_db.db")
    
    # 重置进度文件
    reset_progress("crawl_progress.json")
    reset_progress("test_progress.json")
    
    # 重置日志文件
    reset_logs("crawler.log")
    
    print("🎉 重置完成！")

def show_status():
    """显示当前状态"""
    print("📊 当前爬虫状态:")
    
    # 检查数据库文件
    db_files = ["openalex_advanced.db", "openalex.db", "test_db.db"]
    for db_file in db_files:
        if os.path.exists(db_file):
            size_mb = os.path.getsize(db_file) / (1024 * 1024)
            print(f"   数据库: {db_file} ({size_mb:.1f} MB)")
            
            # 显示论文数量
            try:
                con = sqlite3.connect(db_file)
                count = con.execute("SELECT COUNT(*) FROM works").fetchone()[0]
                con.close()
                print(f"     论文数量: {count:,}")
            except:
                print(f"     无法读取论文数量")
        else:
            print(f"   数据库: {db_file} (不存在)")
    
    # 检查进度文件
    progress_files = ["crawl_progress.json", "test_progress.json"]
    for progress_file in progress_files:
        if os.path.exists(progress_file):
            size_kb = os.path.getsize(progress_file) / 1024
            print(f"   进度文件: {progress_file} ({size_kb:.1f} KB)")
        else:
            print(f"   进度文件: {progress_file} (不存在)")
    
    # 检查日志文件
    log_files = ["crawler.log"]
    for log_file in log_files:
        if os.path.exists(log_file):
            size_kb = os.path.getsize(log_file) / 1024
            print(f"   日志文件: {log_file} ({size_kb:.1f} KB)")
        else:
            print(f"   日志文件: {log_file} (不存在)")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="爬虫重置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python reset_crawler.py --all                    # 重置所有文件
  python reset_crawler.py --db openalex.db         # 只重置指定数据库
  python reset_crawler.py --progress               # 只重置进度文件
  python reset_crawler.py --logs                   # 只重置日志文件
  python reset_crawler.py --status                 # 显示当前状态
        """
    )
    
    parser.add_argument("--all", action="store_true", help="重置所有文件")
    parser.add_argument("--db", help="重置指定数据库文件")
    parser.add_argument("--progress", action="store_true", help="重置进度文件")
    parser.add_argument("--logs", action="store_true", help="重置日志文件")
    parser.add_argument("--status", action="store_true", help="显示当前状态")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.all:
        reset_all()
        return
    
    if args.db:
        reset_database(args.db)
    
    if args.progress:
        reset_progress()
    
    if args.logs:
        reset_logs()
    
    if not any([args.all, args.db, args.progress, args.logs]):
        print("请指定要执行的操作，使用 --help 查看帮助")
        show_status()

if __name__ == "__main__":
    main()

