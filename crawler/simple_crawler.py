#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版同步爬虫
基于原始ocu.py的逻辑，但支持多领域爬取
"""

import json
import sqlite3
import time
import os
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org"
USER_AGENT = "openalex-crawler/1.0 (mailto:research@example.com)"

# 简化的领域配置
SIMPLE_DOMAIN_CONFIG = {
    "人工智能": {
        "keywords": ["artificial intelligence", "machine learning", "deep learning"],
        "max_papers": 10000,
        "year_ranges": [(2015, 2024), (2010, 2014)]
    },
    "计算机科学": {
        "keywords": ["computer science", "algorithms", "software engineering"],
        "max_papers": 8000,
        "year_ranges": [(2015, 2024), (2010, 2014)]
    },
    "电子信息": {
        "keywords": ["electronics", "signal processing", "telecommunications"],
        "max_papers": 5000,
        "year_ranges": [(2015, 2024)]
    }
}

@dataclass
class SimpleProgress:
    """简化进度记录"""
    domain: str
    keyword: str
    year_range: tuple
    current_cursor: str = "*"
    papers_crawled: int = 0
    completed: bool = False

def rate_limited_get(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 6, backoff: float = 1.0) -> Dict[str, Any]:
    """限速请求 - 直接使用ocu.py的逻辑"""
    headers = {"User-Agent": USER_AGENT}
    params = params or {}
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code == 429:
                ra = r.headers.get("Retry-After")
                wait = int(ra) if ra and ra.isdigit() else backoff * (2 ** attempt)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt + 1 == max_retries:
                raise
            time.sleep(backoff * (2 ** attempt))
    raise RuntimeError("unreachable")

def init_simple_db(db_path: str):
    """初始化简化数据库"""
    con = sqlite3.connect(db_path)
    con.executescript("""
        PRAGMA journal_mode=WAL;
        
        CREATE TABLE IF NOT EXISTS works (
            id TEXT PRIMARY KEY,
            short_id TEXT UNIQUE,
            title TEXT,
            authors TEXT,
            year INTEGER,
            journal TEXT,
            abstract TEXT,
            keywords TEXT,
            doi TEXT,
            citation_count INTEGER,
            url TEXT,
            domain TEXT,
            crawl_timestamp REAL
        );
        
        CREATE INDEX IF NOT EXISTS idx_domain ON works(domain);
        CREATE INDEX IF NOT EXISTS idx_year ON works(year);
    """)
    con.commit()
    con.close()

def extract_simple_work_data(obj: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """提取简化的论文数据"""
    full_id = obj.get("id", "")
    short_id = full_id.rsplit("/", 1)[-1] if full_id else ""
    
    # 作者信息
    authors = []
    for au in obj.get("authorships", []):
        author = au.get("author", {})
        if author.get("display_name"):
            authors.append(author.get("display_name"))
    
    # 摘要
    abstract = None
    if obj.get("abstract_inverted_index"):
        try:
            inv_idx = obj["abstract_inverted_index"]
            max_pos = max(pos for positions in inv_idx.values() for pos in positions)
            words = [None] * (max_pos + 1)
            for w, positions in inv_idx.items():
                for p in positions:
                    words[p] = w
            abstract = " ".join(w for w in words if w)
        except:
            abstract = None
    
    # 关键词
    concepts = obj.get("concepts", [])
    keywords = [c.get("display_name") for c in concepts if c.get("display_name")]
    
    # 期刊信息
    primary_location = obj.get("primary_location", {})
    source = primary_location.get("source", {})
    journal = source.get("display_name")
    
    return {
        'id': full_id,
        'short_id': short_id,
        'title': obj.get("display_name"),
        'authors': "; ".join(authors) if authors else None,
        'year': obj.get("publication_year"),
        'journal': journal,
        'abstract': abstract,
        'keywords': json.dumps(keywords, ensure_ascii=False) if keywords else None,
        'doi': obj.get("doi"),
        'citation_count': obj.get("cited_by_count"),
        'url': primary_location.get("landing_page_url") or full_id,
        'domain': domain,
        'crawl_timestamp': time.time()
    }

def save_works_batch(con: sqlite3.Connection, works_data: List[Dict[str, Any]]):
    """批量保存论文数据"""
    if not works_data:
        return
    
    columns = list(works_data[0].keys())
    placeholders = ", ".join("?" * len(columns))
    columns_str = ", ".join(columns)
    
    insert_sql = f"""
        INSERT OR REPLACE INTO works ({columns_str})
        VALUES ({placeholders})
    """
    
    data_tuples = [tuple(work[col] for col in columns) for work in works_data]
    con.executemany(insert_sql, data_tuples)
    con.commit()

def crawl_domain_keyword_simple(con: sqlite3.Connection, domain: str, keyword: str, year_range: tuple, max_papers: int):
    """爬取特定领域的关键词 - 简化版本"""
    from_year, to_year = year_range
    
    # 构建搜索参数
    params = {
        "search": keyword,
        "per_page": 200,
        "cursor": "*",
        "sort": "cited_by_count:desc",
        "filter": f"from_publication_date:{from_year}-01-01,to_publication_date:{to_year}-12-31"
    }
    
    url = f"{BASE_URL}/works"
    papers_crawled = 0
    batch_size = 50
    works_batch = []
    
    logger.info(f"开始爬取: {domain} - {keyword} ({year_range})")
    
    while papers_crawled < max_papers:
        try:
            # 发送请求
            data = rate_limited_get(url, params)
            results = data.get("results", [])
            
            if not results:
                logger.info(f"没有更多结果，任务完成")
                break
            
            # 处理结果
            for obj in results:
                if papers_crawled >= max_papers:
                    break
                
                work_data = extract_simple_work_data(obj, domain)
                works_batch.append(work_data)
                papers_crawled += 1
                
                # 批量保存
                if len(works_batch) >= batch_size:
                    save_works_batch(con, works_batch)
                    works_batch = []
                    logger.info(f"已爬取 {papers_crawled} 篇论文")
            
            # 更新游标
            meta = data.get("meta", {})
            next_cursor = meta.get("next_cursor")
            if not next_cursor:
                break
            params["cursor"] = next_cursor
            
        except Exception as e:
            logger.error(f"爬取失败: {e}")
            break
    
    # 保存剩余数据
    if works_batch:
        save_works_batch(con, works_batch)
    
    logger.info(f"完成爬取: {domain} - {keyword} - {papers_crawled} 篇论文")
    return papers_crawled

def main():
    """主函数"""
    db_path = "simple_openalex.db"
    
    # 初始化数据库
    init_simple_db(db_path)
    
    con = sqlite3.connect(db_path)
    total_papers = 0
    
    try:
        for domain, config in SIMPLE_DOMAIN_CONFIG.items():
            logger.info(f"开始爬取领域: {domain}")
            
            for keyword in config['keywords']:
                for year_range in config['year_ranges']:
                    papers_count = crawl_domain_keyword_simple(
                        con, domain, keyword, year_range, config['max_papers']
                    )
                    total_papers += papers_count
                    
                    # 检查数据库大小
                    db_size = os.path.getsize(db_path) / (1024 * 1024)
                    if db_size > 1000:  # 1GB限制
                        logger.warning(f"数据库大小达到限制 ({db_size:.1f}MB)，停止爬取")
                        break
                
                if db_size > 1000:
                    break
            
            if db_size > 1000:
                break
    
    finally:
        con.close()
    
    logger.info(f"爬取完成，总共 {total_papers} 篇论文")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，正在安全退出...")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)

