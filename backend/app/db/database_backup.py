"""
真实数据库连接和操作模块 - 修复版本
连接到项目根目录的openalex_v1.db SQLite数据库
"""
import sqlite3
import aiosqlite
import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path

# 数据库文件路径（项目根目录）
DB_PATH = Path(__file__).parent.parent.parent.parent / "openalex_v1.db"

class DatabaseConnection:
    """数据库连接管理类"""
    
    def __init__(self):
        self.db_path = str(DB_PATH)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
    
    async def get_connection(self):
        """获取异步数据库连接 - 每次都创建新连接"""
        return await aiosqlite.connect(self.db_path)
    
    def get_sync_connection(self):
        """获取同步数据库连接"""
        return sqlite3.connect(self.db_path)

class RealDatabase:
    """真实数据库操作类"""
    
    def __init__(self):
        self.connection = DatabaseConnection()
    
    def _parse_json_field(self, field_value: str) -> List[Dict] | List[str] | None:
        """解析JSON字段"""
        if not field_value:
            return []
        try:
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _format_paper_data(self, row: tuple) -> Dict[str, Any]:
        """格式化论文数据"""
        if not row:
            return None
            
        # 解析数据库行数据
        (id_val, short_id, title, authors_json, author_names_json, year, journal, 
         abstract, keywords_json, doi, citation_count, download_count, url, 
         reference_ids_json, cited_by, research_field, funding_json, journal_issn,
         host_organization_name, author_orcids_json, author_institutions_json,
         author_countries_json, fwci, citation_percentile, publication_date,
         primary_topic, topics_json, keywords_display, domain, crawl_timestamp) = row
        
        # 解析JSON字段
        authors_list = self._parse_json_field(authors_json)
        author_names_list = self._parse_json_field(author_names_json)
        keywords_list = self._parse_json_field(keywords_json)
        funding_list = self._parse_json_field(funding_json)
        reference_ids_list = self._parse_json_field(reference_ids_json)
        topics_list = self._parse_json_field(topics_json)
        
        # 确保topics是字典列表
        if isinstance(topics_list, list):
            formatted_topics = []
            for topic in topics_list:
                if isinstance(topic, str):
                    formatted_topics.append({"display_name": topic})
                elif isinstance(topic, dict):
                    formatted_topics.append(topic)
            topics_list = formatted_topics
        
        # 提取作者ID和姓名
        author_ids = []
        author_names = []
        
        if isinstance(authors_list, list):
            for author in authors_list:
                if isinstance(author, dict):
                    if 'author_id' in author:
                        author_ids.append(author['author_id'])
                    if 'name' in author:
                        author_names.append(author['name'])
        
        # 如果没有解析出作者姓名，使用备用字段
        if not author_names and isinstance(author_names_list, list):
            author_names = author_names_list
        
        # 格式化数据
        return {
            "id": id_val,
            "short_id": short_id,
            "title": title or "",
            "authors": author_ids,
            "author_names": author_names,
            "year": year or 0,
            "journal": journal or "",
            "journal_impact_factor": None,  # 这个字段在真实数据库中可能不存在
            "abstract": abstract or "",
            "keywords": keywords_list if isinstance(keywords_list, list) else [],
            "doi": doi,
            "citation_count": citation_count or 0,
            "download_count": download_count or 0,
            "created_at": publication_date or "",
            "url": url,
            "references": reference_ids_list if isinstance(reference_ids_list, list) else [],
            "cited_by": [],  # 需要单独查询
            "truth_value_score": fwci,  # 使用Field-Weighted Citation Impact作为真值分数
            "research_field": research_field or primary_topic or domain or "",
            "funding": funding_list if isinstance(funding_list, list) else [],
            "journal_issn": journal_issn,
            "host_organization": host_organization_name,
            "fwci": fwci,
            "citation_percentile": citation_percentile,
            "publication_date": publication_date,
            "primary_topic": primary_topic,
            "topics": topics_list if isinstance(topics_list, list) else [],
            "keywords_display": keywords_display,
            "domain": domain
        }
    
    async def get_papers(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取论文列表"""
        db = await self.connection.get_connection()
        try:
            query = """
                SELECT id, short_id, title, authors, author_names, year, journal, abstract, keywords, doi,
                       citation_count, download_count, url, reference_ids, cited_by, research_field, funding,
                       journal_issn, host_organization_name, author_orcids, author_institutions, author_countries,
                       fwci, citation_percentile, publication_date, primary_topic, topics, keywords_display, domain, crawl_timestamp
                FROM works 
                ORDER BY citation_count DESC, year DESC
                LIMIT ? OFFSET ?
            """
            async with db.execute(query, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [self._format_paper_data(row) for row in rows if row]
        finally:
            await db.close()
    
    async def get_paper_by_id(self, paper_id: str) -> Dict[str, Any] | None:
        """根据ID获取论文"""
        db = await self.connection.get_connection()
        try:
            query = """
                SELECT id, short_id, title, authors, author_names, year, journal, abstract, keywords, doi,
                       citation_count, download_count, url, reference_ids, cited_by, research_field, funding,
                       journal_issn, host_organization_name, author_orcids, author_institutions, author_countries,
                       fwci, citation_percentile, publication_date, primary_topic, topics, keywords_display, domain, crawl_timestamp
                FROM works 
                WHERE id = ? OR short_id = ?
            """
            async with db.execute(query, (paper_id, paper_id)) as cursor:
                row = await cursor.fetchone()
                return self._format_paper_data(row) if row else None
        finally:
            await db.close()
    
    async def search_papers(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """搜索论文"""
        db = await self.connection.get_connection()
        try:
            # 构建搜索SQL
            search_conditions = []
            params = []
            
            if query:
                search_conditions.append("""
                    (title LIKE ? OR abstract LIKE ? OR keywords LIKE ? 
                     OR author_names LIKE ? OR research_field LIKE ? 
                     OR primary_topic LIKE ? OR domain LIKE ?)
                """)
                search_term = f"%{query}%"
                params.extend([search_term] * 7)
            
            # 添加过滤条件
            if filters:
                if "year_min" in filters and filters["year_min"]:
                    search_conditions.append("year >= ?")
                    params.append(filters["year_min"])
                
                if "year_max" in filters and filters["year_max"]:
                    search_conditions.append("year <= ?")
                    params.append(filters["year_max"])
                
                if "journal" in filters and filters["journal"]:
                    search_conditions.append("journal LIKE ?")
                    params.append(f"%{filters['journal']}%")
                
                if "research_field" in filters and filters["research_field"]:
                    search_conditions.append("(research_field LIKE ? OR primary_topic LIKE ? OR domain LIKE ?)")
                    field_term = f"%{filters['research_field']}%"
                    params.extend([field_term, field_term, field_term])
                
                if "min_citations" in filters and filters["min_citations"]:
                    search_conditions.append("citation_count >= ?")
                    params.append(filters["min_citations"])
            
            where_clause = " AND ".join(search_conditions) if search_conditions else "1=1"
            
            sql_query = f"""
                SELECT id, short_id, title, authors, author_names, year, journal, abstract, keywords, doi,
                       citation_count, download_count, url, reference_ids, cited_by, research_field, funding,
                       journal_issn, host_organization_name, author_orcids, author_institutions, author_countries,
                       fwci, citation_percentile, publication_date, primary_topic, topics, keywords_display, domain, crawl_timestamp
                FROM works 
                WHERE {where_clause}
                ORDER BY citation_count DESC, year DESC
                LIMIT 100
            """
            
            async with db.execute(sql_query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._format_paper_data(row) for row in rows if row]
        finally:
            await db.close()
    
    async def get_papers_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        """根据作者姓名获取论文"""
        db = await self.connection.get_connection()
        try:
            query = """
                SELECT id, short_id, title, authors, author_names, year, journal, abstract, keywords, doi,
                       citation_count, download_count, url, reference_ids, cited_by, research_field, funding,
                       journal_issn, host_organization_name, author_orcids, author_institutions, author_countries,
                       fwci, citation_percentile, publication_date, primary_topic, topics, keywords_display, domain, crawl_timestamp
                FROM works 
                WHERE author_names LIKE ?
                ORDER BY year DESC, citation_count DESC
            """
            async with db.execute(query, (f"%{author_name}%",)) as cursor:
                rows = await cursor.fetchall()
                return [self._format_paper_data(row) for row in rows if row]
        finally:
            await db.close()
    
    async def get_author_info(self, author_name: str) -> Dict[str, Any] | None:
        """根据作者姓名获取作者信息（从论文数据中聚合）"""
        papers = await self.get_papers_by_author(author_name)
        if not papers:
            return None
        
        # 聚合作者信息
        total_citations = sum(p.get("citation_count", 0) for p in papers)
        affiliations = []
        research_areas = set()
        
        for paper in papers:
            if paper.get("host_organization"):
                affiliations.append(paper["host_organization"])
            if paper.get("research_field"):
                research_areas.add(paper["research_field"])
            if paper.get("primary_topic"):
                research_areas.add(paper["primary_topic"])
            if paper.get("domain"):
                research_areas.add(paper["domain"])
        
        # 计算h-index的简化版本
        citations_list = sorted([p.get("citation_count", 0) for p in papers], reverse=True)
        h_index = 0
        for i, citations in enumerate(citations_list, 1):
            if citations >= i:
                h_index = i
            else:
                break
        
        return {
            "id": f"author_{author_name.replace(' ', '_')}",
            "name": author_name,
            "email": None,
            "affiliation": affiliations[0] if affiliations else "",
            "research_areas": list(research_areas),
            "h_index": h_index,
            "citation_count": total_citations,
            "paper_count": len(papers),
            "bio": f"{author_name}是一位研究者，专注于{', '.join(list(research_areas)[:3])}等领域。",
            "created_at": "",
            "career_timeline": [],
            "collaboration_network": []
        }
    
    async def get_research_fields_stats(self) -> Dict[str, int]:
        """获取研究领域统计"""
        db = await self.connection.get_connection()
        try:
            query = """
                SELECT 
                    COALESCE(research_field, primary_topic, domain, '未分类') as field,
                    COUNT(*) as count
                FROM works 
                WHERE field IS NOT NULL AND field != ''
                GROUP BY field
                ORDER BY count DESC
                LIMIT 20
            """
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}
        finally:
            await db.close()
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        db = await self.connection.get_connection()
        try:
            # 总论文数
            async with db.execute("SELECT COUNT(*) FROM works") as cursor:
                total_papers = (await cursor.fetchone())[0]
            
            # 总引用数
            async with db.execute("SELECT SUM(citation_count) FROM works WHERE citation_count IS NOT NULL") as cursor:
                total_citations = (await cursor.fetchone())[0] or 0
            
            # 平均引用数
            avg_citations = total_citations / total_papers if total_papers > 0 else 0
            
            # 年份分布
            async with db.execute("""
                SELECT year, COUNT(*) 
                FROM works 
                WHERE year IS NOT NULL AND year > 1900 
                GROUP BY year 
                ORDER BY year DESC 
                LIMIT 10
            """) as cursor:
                year_stats = await cursor.fetchall()
            
            return {
                "total_papers": total_papers,
                "total_citations": total_citations,
                "average_citations": round(avg_citations, 2),
                "year_distribution": {str(year): count for year, count in year_stats}
            }
        finally:
            await db.close()

# 用户数据管理（继续使用内存存储，因为真实数据库主要是论文数据）
class UserManager:
    """用户数据管理（使用内存存储）"""
    
    def __init__(self):
        self.users = [
            {
                "id": "user_001",
                "username": "student_zhang",
                "email": "student@example.com",
                "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
                "full_name": "张学生",
                "affiliation": "北京大学",
                "research_interests": ["机器学习", "深度学习"],
                "created_at": "2023-01-15",
                "last_login": "2023-12-01",
                "followed_authors": [],
                "bookmarked_papers": [],
                "reading_history": [],
                "folders": []
            },
            {
                "id": "user_002",
                "username": "researcher_li",
                "email": "researcher@example.com", 
                "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "full_name": "李研究员",
                "affiliation": "中科院计算所",
                "research_interests": ["自然语言处理", "知识图谱"],
                "created_at": "2023-03-20",
                "last_login": "2023-11-28",
                "followed_authors": [],
                "bookmarked_papers": [],
                "reading_history": [],
                "folders": []
            }
        ]
        self.search_history = []
        self.recommendations = []
    
    def get_user_by_username(self, username: str) -> Dict[str, Any] | None:
        """根据用户名获取用户"""
        for user in self.users:
            if user["username"] == username:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Dict[str, Any] | None:
        """根据ID获取用户"""
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        user_data["id"] = f"user_{len(self.users) + 1:03d}"
        user_data["created_at"] = datetime.now().isoformat()
        user_data["folders"] = []
        user_data["followed_authors"] = []
        user_data["bookmarked_papers"] = []
        user_data["reading_history"] = []
        self.users.append(user_data)
        return user_data
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any] | None:
        """更新用户信息"""
        for i, user in enumerate(self.users):
            if user["id"] == user_id:
                self.users[i].update(update_data)
                return self.users[i]
        return None
    
    def add_bookmark(self, user_id: str, paper_id: str) -> bool:
        """添加论文收藏"""
        user = self.get_user_by_id(user_id)
        if user and paper_id not in user["bookmarked_papers"]:
            user["bookmarked_papers"].append(paper_id)
            return True
        return False
    
    def remove_bookmark(self, user_id: str, paper_id: str) -> bool:
        """移除论文收藏"""
        user = self.get_user_by_id(user_id)
        if user and paper_id in user["bookmarked_papers"]:
            user["bookmarked_papers"].remove(paper_id)
            return True
        return False
    
    def follow_author(self, user_id: str, author_id: str) -> bool:
        """关注作者"""
        user = self.get_user_by_id(user_id)
        if user and author_id not in user["followed_authors"]:
            user["followed_authors"].append(author_id)
            return True
        return False
    
    def unfollow_author(self, user_id: str, author_id: str) -> bool:
        """取消关注作者"""
        user = self.get_user_by_id(user_id)
        if user and author_id in user["followed_authors"]:
            user["followed_authors"].remove(author_id)
            return True
        return False
    
    def create_folder(self, user_id: str, folder_data: Dict[str, Any]) -> Dict[str, Any] | None:
        """创建收藏夹"""
        user = self.get_user_by_id(user_id)
        if user:
            folder_data["id"] = f"folder_{len([f for u in self.users for f in u['folders']]) + 1:03d}"
            folder_data["created_at"] = datetime.now().isoformat()
            folder_data["papers"] = []
            user["folders"].append(folder_data)
            return folder_data
        return None
    
    def get_user_folders(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的收藏夹"""
        user = self.get_user_by_id(user_id)
        return user["folders"] if user else []
    
    def get_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户推荐"""
        user_recs = [rec for rec in self.recommendations if rec["user_id"] == user_id]
        return user_recs[:limit]
    
    def add_search_history(self, user_id: str, query: str, results_clicked: List[str] = None):
        """添加搜索历史"""
        self.search_history.append({
            "user_id": user_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results_clicked": results_clicked or []
        })

# 全局数据库实例
db = RealDatabase()
user_manager = UserManager()
