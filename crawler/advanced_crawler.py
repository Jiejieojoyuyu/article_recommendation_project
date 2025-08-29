#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级多领域 OpenAlex 爬虫
- 支持多领域异步爬取
- 进度保存和断点续传
- 数据库大小控制
- 智能调度和负载均衡
"""

import asyncio
import aiohttp
import json
import sqlite3
import time
import os
import signal
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org"
USER_AGENT = "openalex-crawler/1.0 (mailto:research@example.com)"  # 使用与ocu.py相同的User-Agent

# 领域配置 - 包含搜索关键词、权重和最大论文数
DOMAIN_CONFIG = {
    "人工智能": {
        "keywords": [
            "artificial intelligence", "machine learning", "deep learning", "neural networks",
            "computer vision", "natural language processing", "reinforcement learning",
            "transformer", "BERT", "GPT", "CNN", "RNN", "LSTM", "attention mechanism"
        ],
        "weight": 3.0,  # 高权重，优先爬取
        "max_papers": 500000,  # 大幅增加论文数量
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009), (2000, 2004)]
    },
    "计算机科学": {
        "keywords": [
            "computer science", "algorithms", "data structures", "software engineering",
            "distributed systems", "database", "operating systems", "computer networks",
            "cybersecurity", "blockchain", "cloud computing", "big data"
        ],
        "weight": 2.5,
        "max_papers": 400000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009), (2000, 2004)]
    },
    "电子信息": {
        "keywords": [
            "electronics", "signal processing", "telecommunications", "wireless communication",
            "digital signal processing", "embedded systems", "microelectronics", "circuit design",
            "antenna", "RF", "microwave", "optical communication"
        ],
        "weight": 2.0,
        "max_papers": 300000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009)]
    },
    "数学": {
        "keywords": [
            "mathematics", "statistics", "probability", "linear algebra", "calculus",
            "optimization", "numerical analysis", "topology", "algebra", "geometry"
        ],
        "weight": 1.5,
        "max_papers": 250000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009)]
    },
    "物理学": {
        "keywords": [
            "physics", "quantum mechanics", "thermodynamics", "electromagnetism",
            "optics", "solid state physics", "particle physics", "astrophysics"
        ],
        "weight": 1.5,
        "max_papers": 200000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009)]
    },
    "生物学": {
        "keywords": [
            "biology", "genetics", "molecular biology", "cell biology", "biochemistry",
            "bioinformatics", "genomics", "proteomics", "synthetic biology"
        ],
        "weight": 1.5,
        "max_papers": 200000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009)]
    },
    "化学": {
        "keywords": [
            "chemistry", "organic chemistry", "inorganic chemistry", "physical chemistry",
            "analytical chemistry", "materials chemistry", "catalysis", "polymer chemistry"
        ],
        "weight": 1.5,
        "max_papers": 150000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009)]
    },
    "医学": {
        "keywords": [
            "medicine", "medical research", "clinical trials", "pharmacology", "pathology",
            "immunology", "oncology", "cardiology", "neurology", "public health"
        ],
        "weight": 1.5,
        "max_papers": 200000,
        "year_ranges": [(2015, 2024), (2010, 2014), (2005, 2009)]
    },
    "文学": {
        "keywords": [
            "literature", "literary criticism", "comparative literature", "creative writing",
            "poetry", "novel", "drama", "literary theory", "world literature"
        ],
        "weight": 1.0,
        "max_papers": 100000,
        "year_ranges": [(2010, 2024), (2005, 2009), (2000, 2004)]
    },
    "教育学": {
        "keywords": [
            "education", "educational research", "pedagogy", "curriculum", "learning",
            "teaching methods", "educational psychology", "educational technology"
        ],
        "weight": 1.0,
        "max_papers": 100000,
        "year_ranges": [(2010, 2024), (2005, 2009), (2000, 2004)]
    },
    "语言学": {
        "keywords": [
            "linguistics", "language acquisition", "syntax", "semantics", "phonetics",
            "sociolinguistics", "psycholinguistics", "computational linguistics"
        ],
        "weight": 1.0,
        "max_papers": 80000,
        "year_ranges": [(2010, 2024), (2005, 2009), (2000, 2004)]
    },
    "哲学": {
        "keywords": [
            "philosophy", "ethics", "epistemology", "metaphysics", "logic",
            "political philosophy", "philosophy of mind", "philosophy of science"
        ],
        "weight": 1.0,
        "max_papers": 60000,
        "year_ranges": [(2010, 2024), (2005, 2009), (2000, 2004)]
    },
    "心理学": {
        "keywords": [
            "psychology", "cognitive psychology", "social psychology", "developmental psychology",
            "clinical psychology", "behavioral psychology", "neuroscience"
        ],
        "weight": 1.2,
        "max_papers": 100000,
        "year_ranges": [(2010, 2024), (2005, 2009), (2000, 2004)]
    },
    "经济学": {
        "keywords": [
            "economics", "microeconomics", "macroeconomics", "econometrics", "financial economics",
            "behavioral economics", "development economics", "international economics"
        ],
        "weight": 1.2,
        "max_papers": 100000,
        "year_ranges": [(2010, 2024), (2005, 2009), (2000, 2004)]
    }
}

@dataclass
class CrawlProgress:
    """爬取进度记录"""
    domain: str
    keyword: str
    year_range: tuple
    current_cursor: str = "*"
    papers_crawled: int = 0
    last_update: float = 0.0
    completed: bool = False

@dataclass
class CrawlStats:
    """爬取统计信息"""
    total_papers: int = 0
    total_size_mb: float = 0.0
    domains_completed: int = 0
    start_time: float = 0.0
    last_checkpoint: float = 0.0

class ProgressManager:
    """进度管理器"""
    
    def __init__(self, progress_file: str = "crawl_progress.json"):
        self.progress_file = progress_file
        self.progress: Dict[str, CrawlProgress] = {}
        self.stats = CrawlStats()
        self.load_progress()
    
    def load_progress(self):
        """加载进度文件"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = CrawlStats(**data.get('stats', {}))
                    for key, progress_data in data.get('progress', {}).items():
                        self.progress[key] = CrawlProgress(**progress_data)
                logger.info(f"加载进度文件: {len(self.progress)} 个任务")
            except Exception as e:
                logger.error(f"加载进度文件失败: {e}")
                self._init_progress()
        else:
            self._init_progress()
    
    def _init_progress(self):
        """初始化进度"""
        self.progress = {}
        for domain, config in DOMAIN_CONFIG.items():
            for keyword in config['keywords']:
                for year_range in config['year_ranges']:
                    key = f"{domain}_{keyword}_{year_range[0]}_{year_range[1]}"
                    self.progress[key] = CrawlProgress(
                        domain=domain,
                        keyword=keyword,
                        year_range=year_range
                    )
        self.stats = CrawlStats(start_time=time.time())
        self.save_progress()
    
    def save_progress(self):
        """保存进度"""
        try:
            data = {
                'stats': asdict(self.stats),
                'progress': {k: asdict(v) for k, v in self.progress.items()}
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
    
    def get_next_task(self) -> Optional[CrawlProgress]:
        """获取下一个待处理任务"""
        # 按权重排序，优先处理高权重任务
        sorted_tasks = sorted(
            [p for p in self.progress.values() if not p.completed],
            key=lambda x: (DOMAIN_CONFIG[x.domain]['weight'], -x.papers_crawled),
            reverse=True
        )
        return sorted_tasks[0] if sorted_tasks else None
    
    def update_task(self, task_key: str, cursor: str, papers_count: int, completed: bool = False):
        """更新任务进度"""
        if task_key in self.progress:
            self.progress[task_key].current_cursor = cursor
            self.progress[task_key].papers_crawled += papers_count
            self.progress[task_key].last_update = time.time()
            self.progress[task_key].completed = completed
            self.save_progress()
    
    def get_domain_stats(self, domain: str) -> Dict[str, int]:
        """获取领域统计信息"""
        domain_tasks = [p for p in self.progress.values() if p.domain == domain]
        total_papers = sum(p.papers_crawled for p in domain_tasks)
        completed_tasks = sum(1 for p in domain_tasks if p.completed)
        return {
            'total_papers': total_papers,
            'completed_tasks': completed_tasks,
            'total_tasks': len(domain_tasks)
        }

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        con = sqlite3.connect(self.db_path)
        con.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA cache_size=10000;
            PRAGMA temp_store=MEMORY;
            
            CREATE TABLE IF NOT EXISTS works (
                id TEXT PRIMARY KEY,
                short_id TEXT UNIQUE,
                title TEXT,
                authors TEXT,
                author_names TEXT,
                year INTEGER,
                journal TEXT,
                abstract TEXT,
                keywords TEXT,
                doi TEXT,
                citation_count INTEGER,
                download_count INTEGER,
                url TEXT,
                reference_ids TEXT,
                cited_by INTEGER,
                research_field TEXT,
                funding TEXT,
                journal_issn TEXT,
                host_organization_name TEXT,
                author_orcids TEXT,
                author_institutions TEXT,
                author_countries TEXT,
                fwci REAL,
                citation_percentile REAL,
                publication_date TEXT,
                primary_topic TEXT,
                topics TEXT,
                keywords_display TEXT,
                domain TEXT,
                crawl_timestamp REAL
            );
            
            CREATE INDEX IF NOT EXISTS idx_domain ON works(domain);
            CREATE INDEX IF NOT EXISTS idx_year ON works(year);
            CREATE INDEX IF NOT EXISTS idx_citation_count ON works(citation_count);
        """)
        con.commit()
        con.close()
    
    def get_db_size_mb(self) -> float:
        """获取数据库大小（MB）"""
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path) / (1024 * 1024)
        return 0.0
    
    def get_paper_count(self) -> int:
        """获取论文总数"""
        con = sqlite3.connect(self.db_path)
        count = con.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        con.close()
        return count
    
    def get_domain_paper_count(self, domain: str) -> int:
        """获取特定领域的论文数"""
        con = sqlite3.connect(self.db_path)
        count = con.execute("SELECT COUNT(*) FROM works WHERE domain = ?", (domain,)).fetchone()[0]
        con.close()
        return count

class AsyncOpenAlexCrawler:
    """异步OpenAlex爬虫"""
    
    def __init__(self, db_path: str, max_concurrent: int = 2):  # 降低默认并发数
        self.db_path = db_path
        self.max_concurrent = max_concurrent
        self.progress_manager = ProgressManager()
        self.db_manager = DatabaseManager(db_path)
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，正在安全停止...")
        self.running = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)  # 降低并发限制
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _rate_limited_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """限速请求"""
        async with self.semaphore:
            # 添加请求间隔，模拟原始版本的限速
            await asyncio.sleep(1.0)
            
            for attempt in range(6):
                try:
                    async with self.session.get(url, params=params) as response:
                        if response.status == 429:
                            retry_after = response.headers.get('Retry-After', '60')
                            wait_time = int(retry_after) if retry_after.isdigit() else 60
                            logger.warning(f"遇到限流，等待 {wait_time} 秒")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        data = await response.json()
                        
                        # 检查返回的数据是否有效
                        if not isinstance(data, dict):
                            logger.warning(f"API返回无效数据格式: {type(data)}")
                            return None
                        
                        return data
                        
                except asyncio.TimeoutError:
                    if attempt < 5:
                        wait_time = 2 ** attempt
                        logger.warning(f"请求超时，{wait_time}秒后重试")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"请求超时，跳过: {url}")
                        return None
                        
                except Exception as e:
                    if attempt < 5:
                        wait_time = 2 ** attempt
                        logger.warning(f"请求失败: {e}，{wait_time}秒后重试")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"请求失败，跳过: {url} - {e}")
                        return None
            
            return None
    
    def _extract_work_data(self, obj: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """提取论文数据"""
        # 检查输入数据
        if not isinstance(obj, dict):
            logger.warning(f"论文数据格式错误: {type(obj)}")
            return None
        
        # 简化的数据提取，基于原ocu.py的逻辑
        full_id = obj.get("id", "")
        short_id = full_id.rsplit("/", 1)[-1] if full_id else ""
        
        # 作者信息
        authors = []
        author_names = []
        authorships = obj.get("authorships", [])
        if isinstance(authorships, list):
            for au in authorships:
                if isinstance(au, dict):
                    author = au.get("author", {})
                    if isinstance(author, dict):
                        authors.append({
                            "author_id": author.get("id", "").rsplit("/", 1)[-1] if author.get("id") else "",
                            "name": author.get("display_name", "")
                        })
                        if author.get("display_name"):
                            author_names.append(author.get("display_name"))
        
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
        
        # 概念/关键词
        concepts = obj.get("concepts", [])
        keywords = [c.get("display_name") for c in concepts if c.get("display_name")]
        
        # 期刊信息
        primary_location = obj.get("primary_location", {})
        source = primary_location.get("source", {})
        journal = source.get("display_name")
        
        # 引用信息
        references = obj.get("referenced_works", [])
        reference_ids = [rid.rsplit("/", 1)[-1] for rid in references]
        
        return {
            'id': full_id,
            'short_id': short_id,
            'title': obj.get("display_name"),
            'authors': json.dumps(authors, ensure_ascii=False),
            'author_names': "; ".join(author_names) if author_names else None,
            'year': obj.get("publication_year"),
            'journal': journal,
            'abstract': abstract,
            'keywords': json.dumps(keywords, ensure_ascii=False) if keywords else None,
            'doi': obj.get("doi"),
            'citation_count': obj.get("cited_by_count"),
            'download_count': obj.get("download_count"),
            'url': primary_location.get("landing_page_url") or full_id,
            'reference_ids': json.dumps(reference_ids, ensure_ascii=False) if reference_ids else None,
            'cited_by': obj.get("cited_by_count"),
            'research_field': json.dumps(concepts, ensure_ascii=False) if concepts else None,
            'funding': None,  # 简化处理
            'journal_issn': json.dumps(source.get("issn", []), ensure_ascii=False) if source.get("issn") else None,
            'host_organization_name': source.get("host_organization_name"),
            'author_orcids': None,  # 简化处理
            'author_institutions': None,  # 简化处理
            'author_countries': None,  # 简化处理
            'fwci': obj.get("fwci"),
            'citation_percentile': obj.get("citation_normalized_percentile", {}).get("value") if obj.get("citation_normalized_percentile") else None,
            'publication_date': obj.get("publication_date"),
            'primary_topic': obj.get("primary_topic", {}).get("display_name") if obj.get("primary_topic") else None,
            'topics': json.dumps([t.get("display_name") for t in obj.get("topics", [])], ensure_ascii=False) if obj.get("topics") else None,
            'keywords_display': None,  # 简化处理
            'domain': domain,
            'crawl_timestamp': time.time()
        }
    
    async def _save_papers_batch(self, papers_data: List[Dict[str, Any]]):
        """批量保存论文数据"""
        if not papers_data:
            return
        
        con = sqlite3.connect(self.db_path)
        try:
            # 准备插入语句
            columns = list(papers_data[0].keys())
            placeholders = ", ".join("?" * len(columns))
            columns_str = ", ".join(columns)
            
            insert_sql = f"""
                INSERT OR REPLACE INTO works ({columns_str})
                VALUES ({placeholders})
            """
            
            # 批量插入
            data_tuples = [tuple(paper[col] for col in columns) for paper in papers_data]
            con.executemany(insert_sql, data_tuples)
            con.commit()
            
        except Exception as e:
            logger.error(f"保存论文数据失败: {e}")
            con.rollback()
        finally:
            con.close()
    
    async def crawl_domain_keyword(self, progress: CrawlProgress) -> bool:
        """爬取特定领域的关键词"""
        domain_config = DOMAIN_CONFIG[progress.domain]
        max_papers = domain_config['max_papers']
        
        # 检查是否已达到该领域的最大论文数
        current_count = self.db_manager.get_domain_paper_count(progress.domain)
        if current_count >= max_papers:
            logger.info(f"领域 {progress.domain} 已达到最大论文数 {max_papers}")
            return True
        
        # 构建搜索参数
        params = {
            "search": progress.keyword,
            "per_page": 200,
            "cursor": progress.current_cursor,
            "sort": "cited_by_count:desc"
        }
        
        # 添加年份过滤
        from_year, to_year = progress.year_range
        params["filter"] = f"from_publication_date:{from_year}-01-01,to_publication_date:{to_year}-12-31"
        
        url = f"{BASE_URL}/works"
        papers_batch = []
        batch_size = 50
        papers_crawled = 0
        
        while self.running and papers_crawled < 1000:  # 每次最多爬取1000篇
            # 检查数据库大小
            db_size = self.db_manager.get_db_size_mb()
            if db_size > 48000:  # 接近50GB时停止
                logger.warning(f"数据库大小接近限制 ({db_size:.1f}MB)，停止爬取")
                break
            
            # 检查领域论文数
            current_count = self.db_manager.get_domain_paper_count(progress.domain)
            if current_count >= max_papers:
                logger.info(f"领域 {progress.domain} 已达到最大论文数")
                break
            
            # 发送请求
            data = await self._rate_limited_request(url, params)
            if not data:
                logger.warning(f"API请求失败，跳过当前批次")
                break
            
            # 检查数据格式
            if not isinstance(data, dict):
                logger.warning(f"API返回数据格式错误: {type(data)}")
                break
            
            results = data.get("results", [])
            if not results:
                logger.info(f"没有更多结果，任务完成")
                break
            
            # 处理结果
            for obj in results:
                if not self.running:
                    break
                
                try:
                    paper_data = self._extract_work_data(obj, progress.domain)
                    if paper_data:  # 只有成功提取的数据才添加
                        papers_batch.append(paper_data)
                        papers_crawled += 1
                except Exception as e:
                    logger.warning(f"提取论文数据失败: {e}")
                    continue
                
                # 批量保存
                if len(papers_batch) >= batch_size:
                    await self._save_papers_batch(papers_batch)
                    papers_batch = []
                    
                    # 更新进度
                    task_key = f"{progress.domain}_{progress.keyword}_{progress.year_range[0]}_{progress.year_range[1]}"
                    self.progress_manager.update_task(task_key, params["cursor"], batch_size)
            
            # 更新游标
            meta = data.get("meta", {})
            next_cursor = meta.get("next_cursor")
            if not next_cursor:
                break
            params["cursor"] = next_cursor
            
            # 短暂休息
            await asyncio.sleep(0.1)
        
        # 保存剩余数据
        if papers_batch:
            await self._save_papers_batch(papers_batch)
        
        # 更新最终进度
        task_key = f"{progress.domain}_{progress.keyword}_{progress.year_range[0]}_{progress.year_range[1]}"
        self.progress_manager.update_task(task_key, params["cursor"], papers_crawled, completed=True)
        
        logger.info(f"完成爬取: {progress.domain} - {progress.keyword} ({progress.year_range}) - {papers_crawled} 篇论文")
        return True
    
    async def run_crawler(self):
        """运行爬虫主循环"""
        logger.info("开始多领域异步爬虫")
        self.progress_manager.stats.start_time = time.time()
        
        while self.running:
            # 获取下一个任务
            task = self.progress_manager.get_next_task()
            if not task:
                logger.info("所有任务已完成")
                break
            
            # 检查数据库大小
            db_size = self.db_manager.get_db_size_mb()
            if db_size > 48000:
                logger.warning(f"数据库大小接近限制 ({db_size:.1f}MB)，停止爬取")
                break
            
            logger.info(f"开始爬取: {task.domain} - {task.keyword} ({task.year_range})")
            
            try:
                await self.crawl_domain_keyword(task)
            except Exception as e:
                logger.error(f"爬取任务失败: {e}")
                continue
            
            # 更新统计信息
            self.progress_manager.stats.total_papers = self.db_manager.get_paper_count()
            self.progress_manager.stats.total_size_mb = self.db_manager.get_db_size_mb()
            self.progress_manager.stats.last_checkpoint = time.time()
            self.progress_manager.save_progress()
            
            # 打印进度报告
            self._print_progress_report()
            
            # 短暂休息
            await asyncio.sleep(1)
        
        logger.info("爬虫已停止")
    
    def _print_progress_report(self):
        """打印进度报告"""
        stats = self.progress_manager.stats
        elapsed = time.time() - stats.start_time
        
        print("\n" + "="*60)
        print("爬取进度报告")
        print("="*60)
        print(f"总论文数: {stats.total_papers:,}")
        print(f"数据库大小: {stats.total_size_mb:.1f} MB")
        print(f"运行时间: {elapsed/3600:.1f} 小时")
        print(f"平均速度: {stats.total_papers/(elapsed/60):.1f} 篇/分钟")
        
        print("\n各领域进度:")
        for domain in DOMAIN_CONFIG.keys():
            domain_stats = self.progress_manager.get_domain_stats(domain)
            max_papers = DOMAIN_CONFIG[domain]['max_papers']
            progress_pct = (domain_stats['total_papers'] / max_papers) * 100
            print(f"  {domain}: {domain_stats['total_papers']:,}/{max_papers:,} ({progress_pct:.1f}%)")
        
        print("="*60)

async def main():
    """主函数"""
    db_path = "openalex_advanced.db"
    
    async with AsyncOpenAlexCrawler(db_path, max_concurrent=3) as crawler:
        await crawler.run_crawler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断，正在安全退出...")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)
