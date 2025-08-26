"""
OpenAlex API爬虫程序
用于从OpenAlex API获取学术论文和作者数据

注意：此文件仅生成代码，不在运行指令中执行
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openalex_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Paper:
    """论文数据结构"""
    id: str
    title: str
    authors: List[str]
    author_names: List[str]
    year: int
    journal: str
    abstract: str
    keywords: List[str]
    doi: Optional[str]
    citation_count: int
    download_count: int
    url: Optional[str]
    references: List[str]
    cited_by: List[str]
    research_field: str
    funding: List[str]

@dataclass
class Author:
    """作者数据结构"""
    id: str
    name: str
    email: Optional[str]
    affiliation: str
    research_areas: List[str]
    h_index: int
    citation_count: int
    paper_count: int
    bio: Optional[str]

class OpenAlexCrawler:
    """OpenAlex API爬虫类"""
    
    def __init__(self, email: str = None, rate_limit: float = 1.0):
        """
        初始化爬虫
        
        Args:
            email: 联系邮箱（可选，用于更高的API限额）
            rate_limit: 请求间隔（秒）
        """
        self.base_url = "https://api.openalex.org"
        self.email = email
        self.rate_limit = rate_limit
        self.session = requests.Session()
        
        # 设置请求头
        headers = {
            'User-Agent': 'Academic Recommendation System Crawler',
            'Accept': 'application/json'
        }
        if email:
            headers['From'] = email
        
        self.session.headers.update(headers)
        
        # 创建数据目录
        self.data_dir = Path('crawled_data')
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"OpenAlex爬虫初始化完成，数据目录: {self.data_dir}")

    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        发送API请求
        
        Args:
            url: 请求URL
            params: 查询参数
            
        Returns:
            API响应数据
        """
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # 遵守速率限制
            time.sleep(self.rate_limit)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None

    def search_papers(self, 
                     query: str = None,
                     research_fields: List[str] = None,
                     year_range: tuple = None,
                     limit: int = 100,
                     offset: int = 0) -> List[Dict]:
        """
        搜索论文
        
        Args:
            query: 搜索关键词
            research_fields: 研究领域列表
            year_range: 年份范围 (start_year, end_year)
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            论文数据列表
        """
        logger.info(f"开始搜索论文: query={query}, limit={limit}")
        
        url = f"{self.base_url}/works"
        params = {
            'per-page': min(limit, 200),  # OpenAlex最大200
            'page': offset // 200 + 1
        }
        
        # 构建过滤条件
        filters = []
        
        if query:
            params['search'] = query
        
        if research_fields:
            # 根据研究领域过滤
            concept_filters = []
            for field in research_fields:
                concept_filters.append(f"concepts.display_name:{field}")
            if concept_filters:
                filters.append(f"({' OR '.join(concept_filters)})")
        
        if year_range:
            start_year, end_year = year_range
            filters.append(f"publication_year:{start_year}-{end_year}")
        
        if filters:
            params['filter'] = ','.join(filters)
        
        # 排序：按引用数降序
        params['sort'] = 'cited_by_count:desc'
        
        data = self._make_request(url, params)
        if not data:
            return []
        
        papers = []
        for work in data.get('results', []):
            paper = self._parse_paper(work)
            if paper:
                papers.append(paper)
        
        logger.info(f"搜索完成，获得 {len(papers)} 篇论文")
        return papers

    def get_author_info(self, author_id: str) -> Optional[Dict]:
        """
        获取作者信息
        
        Args:
            author_id: OpenAlex作者ID
            
        Returns:
            作者信息
        """
        url = f"{self.base_url}/authors/{author_id}"
        data = self._make_request(url)
        
        if not data:
            return None
        
        return self._parse_author(data)

    def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """
        获取论文详细信息
        
        Args:
            paper_id: OpenAlex论文ID
            
        Returns:
            论文详细信息
        """
        url = f"{self.base_url}/works/{paper_id}"
        data = self._make_request(url)
        
        if not data:
            return None
        
        return self._parse_paper(data)

    def _parse_paper(self, work_data: Dict) -> Optional[Dict]:
        """
        解析论文数据
        
        Args:
            work_data: OpenAlex API返回的论文数据
            
        Returns:
            标准化的论文数据
        """
        try:
            # 提取基本信息
            paper_id = work_data.get('id', '').replace('https://openalex.org/', '')
            title = work_data.get('title', '')
            
            if not title:
                return None
            
            # 作者信息
            authors = []
            author_names = []
            for authorship in work_data.get('authorships', []):
                author = authorship.get('author', {})
                if author:
                    author_id = author.get('id', '').replace('https://openalex.org/', '')
                    author_name = author.get('display_name', '')
                    if author_id and author_name:
                        authors.append(author_id)
                        author_names.append(author_name)
            
            # 发表信息
            publication_year = work_data.get('publication_year', 0)
            
            # 期刊信息
            host_venue = work_data.get('host_venue', {}) or work_data.get('primary_location', {})
            journal = host_venue.get('display_name', 'Unknown Journal')
            
            # 摘要
            abstract_inverted = work_data.get('abstract_inverted_index', {})
            abstract = self._reconstruct_abstract(abstract_inverted) if abstract_inverted else ''
            
            # 关键词（从概念中提取）
            keywords = []
            for concept in work_data.get('concepts', []):
                if concept.get('level', 0) <= 2:  # 只取前两级概念
                    keywords.append(concept.get('display_name', ''))
            
            # DOI
            doi = work_data.get('doi')
            if doi and doi.startswith('https://doi.org/'):
                doi = doi.replace('https://doi.org/', '')
            
            # 引用数
            citation_count = work_data.get('cited_by_count', 0)
            
            # URL
            url = work_data.get('doi') or work_data.get('id')
            
            # 参考文献
            references = []
            for ref in work_data.get('referenced_works', [])[:50]:  # 限制数量
                ref_id = ref.replace('https://openalex.org/', '')
                references.append(ref_id)
            
            # 被引文献
            cited_by = []
            for citation in work_data.get('related_works', [])[:50]:  # 限制数量
                cite_id = citation.replace('https://openalex.org/', '')
                cited_by.append(cite_id)
            
            # 研究领域（取主要概念）
            research_field = 'Computer Science'  # 默认值
            if work_data.get('concepts'):
                main_concept = work_data['concepts'][0]
                research_field = main_concept.get('display_name', research_field)
            
            # 资助信息
            funding = []
            for grant in work_data.get('grants', []):
                funder = grant.get('funder_display_name')
                if funder:
                    funding.append(funder)
            
            return {
                'id': paper_id,
                'title': title,
                'authors': authors,
                'author_names': author_names,
                'year': publication_year,
                'journal': journal,
                'abstract': abstract,
                'keywords': keywords[:10],  # 限制关键词数量
                'doi': doi,
                'citation_count': citation_count,
                'download_count': 0,  # OpenAlex不提供下载数
                'url': url,
                'references': references,
                'cited_by': cited_by,
                'research_field': research_field,
                'funding': funding,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"解析论文数据失败: {e}")
            return None

    def _parse_author(self, author_data: Dict) -> Optional[Dict]:
        """
        解析作者数据
        
        Args:
            author_data: OpenAlex API返回的作者数据
            
        Returns:
            标准化的作者数据
        """
        try:
            author_id = author_data.get('id', '').replace('https://openalex.org/', '')
            name = author_data.get('display_name', '')
            
            if not name:
                return None
            
            # 机构信息
            affiliation = 'Unknown'
            if author_data.get('last_known_institution'):
                affiliation = author_data['last_known_institution'].get('display_name', affiliation)
            
            # 研究领域
            research_areas = []
            for concept in author_data.get('x_concepts', [])[:10]:  # 前10个概念
                research_areas.append(concept.get('display_name', ''))
            
            # 统计数据
            h_index = author_data.get('h_index', 0)
            citation_count = author_data.get('cited_by_count', 0)
            paper_count = author_data.get('works_count', 0)
            
            return {
                'id': author_id,
                'name': name,
                'email': None,  # OpenAlex不提供邮箱
                'affiliation': affiliation,
                'research_areas': research_areas,
                'h_index': h_index,
                'citation_count': citation_count,
                'paper_count': paper_count,
                'bio': None,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"解析作者数据失败: {e}")
            return None

    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """
        从倒排索引重构摘要
        
        Args:
            inverted_index: OpenAlex的倒排索引格式摘要
            
        Returns:
            重构的摘要文本
        """
        if not inverted_index:
            return ''
        
        # 创建位置到单词的映射
        position_word = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                position_word[pos] = word
        
        # 按位置排序并连接
        sorted_positions = sorted(position_word.keys())
        words = [position_word[pos] for pos in sorted_positions]
        
        return ' '.join(words)

    def crawl_by_field(self, field: str, limit: int = 1000) -> List[Dict]:
        """
        按研究领域爬取论文
        
        Args:
            field: 研究领域名称
            limit: 爬取数量限制
            
        Returns:
            论文数据列表
        """
        logger.info(f"开始爬取领域 '{field}' 的论文，限制 {limit} 篇")
        
        papers = []
        batch_size = 200
        offset = 0
        
        while len(papers) < limit:
            batch_limit = min(batch_size, limit - len(papers))
            batch_papers = self.search_papers(
                research_fields=[field],
                limit=batch_limit,
                offset=offset
            )
            
            if not batch_papers:
                logger.info("没有更多数据，停止爬取")
                break
            
            papers.extend(batch_papers)
            offset += batch_size
            
            logger.info(f"已爬取 {len(papers)} 篇论文")
            
            # 避免过快请求
            time.sleep(2)
        
        return papers[:limit]

    def save_to_json(self, data: List[Dict], filename: str):
        """
        保存数据到JSON文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
        """
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到 {filepath}")

    def save_to_csv(self, papers: List[Dict], filename: str):
        """
        保存论文数据到CSV文件
        
        Args:
            papers: 论文数据列表
            filename: 文件名
        """
        if not papers:
            return
        
        filepath = self.data_dir / filename
        
        # 定义CSV字段
        fieldnames = [
            'id', 'title', 'author_names', 'year', 'journal',
            'abstract', 'keywords', 'doi', 'citation_count',
            'research_field', 'url'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                # 处理列表字段
                row = paper.copy()
                row['author_names'] = '; '.join(paper.get('author_names', []))
                row['keywords'] = '; '.join(paper.get('keywords', []))
                
                # 只保留需要的字段
                filtered_row = {k: row.get(k, '') for k in fieldnames}
                writer.writerow(filtered_row)
        
        logger.info(f"CSV数据已保存到 {filepath}")

    def crawl_trending_papers(self, days: int = 30, limit: int = 500) -> List[Dict]:
        """
        爬取近期热门论文
        
        Args:
            days: 天数范围
            limit: 数量限制
            
        Returns:
            热门论文列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        year_range = (start_date.year, end_date.year)
        
        logger.info(f"爬取近 {days} 天的热门论文，限制 {limit} 篇")
        
        return self.search_papers(
            year_range=year_range,
            limit=limit
        )


def main():
    """
    主函数 - 示例用法
    """
    # 初始化爬虫
    crawler = OpenAlexCrawler(
        email="your-email@example.com",  # 替换为实际邮箱
        rate_limit=1.0
    )
    
    # 示例1: 爬取计算机科学领域的论文
    papers = crawler.crawl_by_field("Computer Science", limit=100)
    crawler.save_to_json(papers, "computer_science_papers.json")
    crawler.save_to_csv(papers, "computer_science_papers.csv")
    
    # 示例2: 爬取机器学习相关论文
    ml_papers = crawler.search_papers(
        query="machine learning",
        year_range=(2020, 2023),
        limit=50
    )
    crawler.save_to_json(ml_papers, "machine_learning_papers.json")
    
    # 示例3: 爬取热门论文
    trending = crawler.crawl_trending_papers(days=90, limit=100)
    crawler.save_to_json(trending, "trending_papers.json")
    
    logger.info("爬虫任务完成！")


if __name__ == "__main__":
    main()

