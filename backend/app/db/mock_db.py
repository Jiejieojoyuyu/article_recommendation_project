"""
模拟数据库和测试数据
包含论文、作者、用户等完整的测试数据集
"""
from datetime import datetime
from typing import Dict, List, Any

# 模拟作者数据
AUTHORS = [
    {
        "id": "author_001",
        "name": "张三",
        "email": "zhangsan@university.edu",
        "affiliation": "清华大学计算机科学与技术系",
        "research_areas": ["机器学习", "深度学习", "计算机视觉"],
        "h_index": 25,
        "citation_count": 1250,
        "paper_count": 45,
        "bio": "专注于深度学习和计算机视觉研究的教授，在顶级会议发表多篇论文。",
        "created_at": "2020-01-15",
        "career_timeline": [
            {"year": 2015, "event": "博士毕业", "institution": "斯坦福大学"},
            {"year": 2016, "event": "加入清华大学", "position": "助理教授"},
            {"year": 2019, "event": "晋升副教授", "institution": "清华大学"},
            {"year": 2022, "event": "晋升教授", "institution": "清华大学"}
        ],
        "collaboration_network": ["author_002", "author_003"]
    },
    {
        "id": "author_002", 
        "name": "李四",
        "email": "lisi@mit.edu",
        "affiliation": "MIT计算机科学与人工智能实验室",
        "research_areas": ["自然语言处理", "知识图谱", "机器学习"],
        "h_index": 30,
        "citation_count": 1800,
        "paper_count": 52,
        "bio": "自然语言处理领域的专家，在语言模型和知识图谱方面有重要贡献。",
        "created_at": "2018-09-20",
        "career_timeline": [
            {"year": 2013, "event": "博士毕业", "institution": "CMU"},
            {"year": 2014, "event": "加入MIT", "position": "博士后研究员"},
            {"year": 2016, "event": "晋升助理教授", "institution": "MIT"},
            {"year": 2021, "event": "晋升副教授", "institution": "MIT"}
        ],
        "collaboration_network": ["author_001", "author_003"]
    },
    {
        "id": "author_003",
        "name": "王五",
        "email": "wangwu@berkeley.edu", 
        "affiliation": "UC Berkeley电气工程与计算机科学系",
        "research_areas": ["推荐系统", "信息检索", "数据挖掘"],
        "h_index": 22,
        "citation_count": 980,
        "paper_count": 38,
        "bio": "推荐系统和信息检索领域的研究者，致力于个性化推荐算法的创新。",
        "created_at": "2019-03-10",
        "career_timeline": [
            {"year": 2017, "event": "博士毕业", "institution": "华盛顿大学"},
            {"year": 2018, "event": "加入UC Berkeley", "position": "助理教授"},
            {"year": 2023, "event": "晋升副教授", "institution": "UC Berkeley"}
        ],
        "collaboration_network": ["author_001", "author_002"]
    }
]

# 模拟论文数据
PAPERS = [
    {
        "id": "paper_001",
        "title": "深度学习在计算机视觉中的应用与挑战",
        "authors": ["author_001", "author_002"],
        "author_names": ["张三", "李四"],
        "year": 2023,
        "journal": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
        "journal_impact_factor": 17.86,
        "abstract": "本文系统性地回顾了深度学习在计算机视觉领域的最新进展，分析了当前面临的主要挑战，包括数据偏差、模型可解释性和计算效率等问题。我们提出了一个统一的框架来理解这些挑战，并展望了未来的研究方向。",
        "keywords": ["深度学习", "计算机视觉", "神经网络", "图像识别"],
        "doi": "10.1109/TPAMI.2023.001",
        "citation_count": 156,
        "download_count": 2340,
        "created_at": "2023-05-15",
        "url": "https://ieeexplore.ieee.org/document/001",
        "references": ["paper_003", "paper_004"],
        "cited_by": ["paper_002"],
        "truth_value_score": 8.7,
        "research_field": "计算机视觉",
        "funding": ["国家自然科学基金", "清华大学创新基金"]
    },
    {
        "id": "paper_002",
        "title": "基于Transformer的多模态融合推荐系统",
        "authors": ["author_003", "author_001"],
        "author_names": ["王五", "张三"],
        "year": 2023,
        "journal": "ACM Transactions on Information Systems",
        "journal_impact_factor": 5.43,
        "abstract": "我们提出了一种新颖的基于Transformer架构的多模态融合推荐系统，能够同时处理文本、图像和用户行为数据。实验结果表明，该方法在多个基准数据集上显著优于现有的推荐算法，提升了推荐准确性和用户满意度。",
        "keywords": ["推荐系统", "Transformer", "多模态融合", "深度学习"],
        "doi": "10.1145/TOIS.2023.002",
        "citation_count": 89,
        "download_count": 1560,
        "created_at": "2023-08-20",
        "url": "https://dl.acm.org/doi/002",
        "references": ["paper_001", "paper_004"],
        "cited_by": [],
        "truth_value_score": 7.9,
        "research_field": "推荐系统",
        "funding": ["NSF", "UC Berkeley研究基金"]
    },
    {
        "id": "paper_003",
        "title": "知识图谱增强的自然语言理解模型",
        "authors": ["author_002"],
        "author_names": ["李四"],
        "year": 2022,
        "journal": "Nature Machine Intelligence", 
        "journal_impact_factor": 25.89,
        "abstract": "本研究提出了一种将知识图谱与预训练语言模型深度融合的方法，显著提升了模型在常识推理和实体关系理解方面的能力。我们的方法在多个NLU任务上取得了SOTA性能，为知识增强的语言理解开辟了新路径。",
        "keywords": ["知识图谱", "自然语言理解", "预训练模型", "常识推理"],
        "doi": "10.1038/s42256-022-003",
        "citation_count": 234,
        "download_count": 3420,
        "created_at": "2022-11-10",
        "url": "https://nature.com/articles/003",
        "references": ["paper_005"],
        "cited_by": ["paper_001", "paper_004"],
        "truth_value_score": 9.2,
        "research_field": "自然语言处理",
        "funding": ["MIT研究基金", "Google AI资助"]
    },
    {
        "id": "paper_004",
        "title": "联邦学习中的隐私保护机制研究",
        "authors": ["author_001", "author_003"],
        "author_names": ["张三", "王五"],
        "year": 2022,
        "journal": "Proceedings of Machine Learning Research",
        "journal_impact_factor": 4.16,
        "abstract": "随着数据隐私保护需求的增长，联邦学习成为了机器学习的重要发展方向。本文深入分析了联邦学习中的隐私泄露风险，提出了一种基于差分隐私的保护机制，在保护隐私的同时保持了模型性能。",
        "keywords": ["联邦学习", "隐私保护", "差分隐私", "机器学习"],
        "doi": "10.48550/arXiv.2022.004",
        "citation_count": 127,
        "download_count": 2100,
        "created_at": "2022-07-25",
        "url": "https://proceedings.mlr.press/004",
        "references": ["paper_003"],
        "cited_by": ["paper_001", "paper_002"],
        "truth_value_score": 8.1,
        "research_field": "机器学习",
        "funding": ["清华大学-伯克利深圳学院合作基金"]
    },
    {
        "id": "paper_005",
        "title": "大规模图神经网络的分布式训练方法",
        "authors": ["author_002", "author_003"],
        "author_names": ["李四", "王五"],
        "year": 2021,
        "journal": "Journal of Machine Learning Research",
        "journal_impact_factor": 4.09,
        "abstract": "图神经网络在处理大规模图数据时面临着计算和内存的双重挑战。本文提出了一种高效的分布式训练框架，通过图分割和梯度聚合优化，实现了在大规模图数据上的高效训练，为图学习的实际应用奠定了基础。",
        "keywords": ["图神经网络", "分布式训练", "图分割", "大规模图数据"],
        "doi": "10.5555/JMLR.2021.005",
        "citation_count": 178,
        "download_count": 2890,
        "created_at": "2021-09-15",
        "url": "https://jmlr.org/papers/005",
        "references": [],
        "cited_by": ["paper_003"],
        "truth_value_score": 8.4,
        "research_field": "图神经网络",
        "funding": ["MIT-IBM Watson AI Lab"]
    }
]

# 模拟用户数据
USERS = [
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
        "followed_authors": ["author_001", "author_002"],
        "bookmarked_papers": ["paper_001", "paper_003"],
        "reading_history": ["paper_001", "paper_002", "paper_003"],
        "folders": [
            {
                "id": "folder_001",
                "name": "深度学习论文",
                "parent_id": None,
                "papers": ["paper_001"],
                "created_at": "2023-02-01"
            },
            {
                "id": "folder_002", 
                "name": "视觉相关",
                "parent_id": "folder_001",
                "papers": ["paper_001"],
                "created_at": "2023-02-15"
            }
        ]
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
        "followed_authors": ["author_002", "author_003"],
        "bookmarked_papers": ["paper_002", "paper_003", "paper_005"],
        "reading_history": ["paper_003", "paper_005"],
        "folders": [
            {
                "id": "folder_003",
                "name": "NLP研究",
                "parent_id": None,
                "papers": ["paper_003"],
                "created_at": "2023-04-01"
            }
        ]
    }
]

# 搜索历史和推荐数据
SEARCH_HISTORY = [
    {
        "user_id": "user_001",
        "query": "深度学习 计算机视觉",
        "timestamp": "2023-11-30T10:30:00",
        "results_clicked": ["paper_001"]
    },
    {
        "user_id": "user_001", 
        "query": "推荐系统 算法",
        "timestamp": "2023-11-29T15:20:00",
        "results_clicked": ["paper_002"]
    }
]

# 推荐记录
RECOMMENDATIONS = [
    {
        "user_id": "user_001",
        "paper_id": "paper_004",
        "score": 0.85,
        "reason": "基于你对深度学习和隐私保护的兴趣",
        "created_at": "2023-12-01T09:00:00"
    },
    {
        "user_id": "user_001",
        "paper_id": "paper_005", 
        "score": 0.78,
        "reason": "基于你关注的作者的最新研究",
        "created_at": "2023-12-01T09:00:00"
    }
]

# 数据库操作函数
class MockDatabase:
    """模拟数据库操作类"""
    
    def __init__(self):
        self.papers = PAPERS.copy()
        self.authors = AUTHORS.copy()
        self.users = USERS.copy()
        self.search_history = SEARCH_HISTORY.copy()
        self.recommendations = RECOMMENDATIONS.copy()
    
    # 论文相关操作
    def get_papers(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取论文列表"""
        return self.papers[offset:offset + limit]
    
    def get_paper_by_id(self, paper_id: str) -> Dict[str, Any] | None:
        """根据ID获取论文"""
        for paper in self.papers:
            if paper["id"] == paper_id:
                return paper
        return None
    
    def search_papers(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """搜索论文"""
        results = []
        query_lower = query.lower()
        
        for paper in self.papers:
            # 简单的文本匹配搜索
            if (query_lower in paper["title"].lower() or 
                query_lower in paper["abstract"].lower() or
                any(query_lower in keyword.lower() for keyword in paper["keywords"]) or
                any(query_lower in author.lower() for author in paper["author_names"])):
                results.append(paper)
        
        # 应用过滤器
        if filters:
            if "year_min" in filters and filters["year_min"]:
                results = [p for p in results if p["year"] >= filters["year_min"]]
            if "year_max" in filters and filters["year_max"]:
                results = [p for p in results if p["year"] <= filters["year_max"]]
            if "journal" in filters and filters["journal"]:
                results = [p for p in results if filters["journal"].lower() in p["journal"].lower()]
        
        return results
    
    # 作者相关操作
    def get_authors(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取作者列表"""
        return self.authors[offset:offset + limit]
    
    def get_author_by_id(self, author_id: str) -> Dict[str, Any] | None:
        """根据ID获取作者"""
        for author in self.authors:
            if author["id"] == author_id:
                return author
        return None
    
    def get_papers_by_author(self, author_id: str) -> List[Dict[str, Any]]:
        """获取作者的论文"""
        return [paper for paper in self.papers if author_id in paper["authors"]]
    
    # 用户相关操作
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
    
    # 收藏和关注操作
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
    
    # 文件夹操作
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
    
    # 推荐相关
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
db = MockDatabase()

