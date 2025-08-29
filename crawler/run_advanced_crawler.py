#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级爬虫运行脚本
提供简单的命令行接口来运行多领域爬虫
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from advanced_crawler import AsyncOpenAlexCrawler, ProgressManager, DatabaseManager

def print_banner():
    """打印启动横幅"""
    print("="*70)
    print("🚀 高级多领域 OpenAlex 爬虫")
    print("="*70)
    print("功能特点:")
    print("• 多领域覆盖：AI、计算机、电子信息、文学、教育等14个领域")
    print("• 异步爬取：高效并发处理")
    print("• 进度保存：支持断点续传")
    print("• 大小控制：自动控制数据库在50GB以下")
    print("• 智能调度：优先爬取AI/计算机领域")
    print("="*70)

def print_status(db_path: str):
    """打印当前状态"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 数据库信息
    db_manager = DatabaseManager(db_path)
    total_papers = db_manager.get_paper_count()
    db_size = db_manager.get_db_size_mb()
    
    print(f"\n📊 数据库状态:")
    print(f"   文件: {db_path}")
    print(f"   大小: {db_size:.1f} MB")
    print(f"   论文数: {total_papers:,}")
    
    # 进度信息
    progress_manager = ProgressManager()
    if progress_manager.progress:
        completed_tasks = sum(1 for p in progress_manager.progress.values() if p.completed)
        total_tasks = len(progress_manager.progress)
        
        print(f"\n📈 爬取进度:")
        print(f"   已完成任务: {completed_tasks}/{total_tasks}")
        print(f"   完成率: {(completed_tasks/total_tasks)*100:.1f}%")
        
        print(f"\n🏷️  各领域进度:")
        for domain in ["人工智能", "计算机科学", "电子信息", "文学", "教育学"]:
            domain_stats = progress_manager.get_domain_stats(domain)
            max_papers = 500000 if domain == "人工智能" else 400000 if domain == "计算机科学" else 300000 if domain == "电子信息" else 100000
            progress_pct = (domain_stats['total_papers'] / max_papers) * 100
            print(f"   {domain}: {domain_stats['total_papers']:,}/{max_papers:,} ({progress_pct:.1f}%)")

async def run_crawler(db_path: str, max_concurrent: int = 2):
    """运行爬虫"""
    print(f"\n🚀 启动爬虫...")
    print(f"   数据库: {db_path}")
    print(f"   并发数: {max_concurrent}")
    print(f"   按 Ctrl+C 可安全停止")
    
    try:
        async with AsyncOpenAlexCrawler(db_path, max_concurrent) as crawler:
            await crawler.run_crawler()
    except KeyboardInterrupt:
        print("\n⏹️  用户停止爬虫")
    except Exception as e:
        print(f"\n❌ 爬虫运行出错: {e}")
        raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="高级多领域 OpenAlex 爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_advanced_crawler.py                    # 使用默认设置运行
  python run_advanced_crawler.py --db my_db.db     # 指定数据库文件
  python run_advanced_crawler.py --status          # 查看当前状态
  python run_advanced_crawler.py --concurrent 5    # 设置并发数为5
        """
    )
    
    parser.add_argument(
        "--db", 
        default="openalex_advanced.db",
        help="数据库文件路径 (默认: openalex_advanced.db)"
    )
    
    parser.add_argument(
        "--concurrent", 
        type=int, 
        default=2,
        help="最大并发请求数 (默认: 2)"
    )
    
    parser.add_argument(
        "--status", 
        action="store_true",
        help="显示当前爬取状态"
    )
    
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="静默模式，不显示横幅"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    if args.status:
        print_status(args.db)
        return
    
    # 检查依赖
    try:
        import aiohttp
    except ImportError:
        print("❌ 缺少依赖包 aiohttp")
        print("请运行: pip install aiohttp")
        sys.exit(1)
    
    # 运行爬虫
    try:
        asyncio.run(run_crawler(args.db, args.concurrent))
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
