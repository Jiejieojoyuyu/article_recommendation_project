"""
论文和作者相关的Pydantic模型
"""
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class PaperBase(BaseModel):
    """论文基础模型"""
    title: str
    authors: List[str]
    author_names: List[str]
    year: int
    journal: str
    abstract: str
    keywords: List[str]
    doi: Optional[str] = None
    url: Optional[str] = None

class Paper(PaperBase):
    """完整论文模型"""
    id: str
    short_id: Optional[str] = None
    journal_impact_factor: Optional[float] = None
    citation_count: int = 0
    download_count: int = 0
    created_at: str
    references: List[str] = []
    cited_by: List[str] = []
    truth_value_score: Optional[float] = None
    research_field: str
    funding: List[str] = []
    # 来自真实数据库的额外字段
    journal_issn: Optional[str] = None
    host_organization: Optional[str] = None
    fwci: Optional[float] = None
    citation_percentile: Optional[float] = None
    publication_date: Optional[str] = None
    primary_topic: Optional[str] = None
    topics: List[Dict[str, Any]] = []
    keywords_display: Optional[str] = None
    domain: Optional[str] = None

    class Config:
        from_attributes = True

class PaperCreate(PaperBase):
    """创建论文模型"""
    research_field: str
    funding: List[str] = []

class PaperUpdate(BaseModel):
    """更新论文模型"""
    title: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    journal: Optional[str] = None
    url: Optional[str] = None

class PaperSummary(BaseModel):
    """论文摘要模型（用于列表显示）"""
    id: str
    short_id: Optional[str] = None
    title: str
    author_names: List[str]
    year: int
    journal: str
    citation_count: int
    truth_value_score: Optional[float] = None
    research_field: str

class AuthorBase(BaseModel):
    """作者基础模型"""
    name: str
    email: Optional[str] = None
    affiliation: str
    research_areas: List[str]
    bio: Optional[str] = None

class Author(AuthorBase):
    """完整作者模型"""
    id: str
    h_index: int = 0
    citation_count: int = 0
    paper_count: int = 0
    created_at: str
    career_timeline: List[Dict[str, Any]] = []
    collaboration_network: List[str] = []

    class Config:
        from_attributes = True

class AuthorCreate(AuthorBase):
    """创建作者模型"""
    pass

class AuthorUpdate(BaseModel):
    """更新作者模型"""
    name: Optional[str] = None
    affiliation: Optional[str] = None
    research_areas: Optional[List[str]] = None
    bio: Optional[str] = None

class AuthorSummary(BaseModel):
    """作者摘要模型（用于列表显示）"""
    id: str
    name: str
    affiliation: str
    research_areas: List[str]
    h_index: int
    citation_count: int
    paper_count: int

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    search_type: str = "hybrid"  # "hybrid", "semantic", "exact"
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = "relevance"  # "relevance", "date", "citation", "truth_value"
    sort_order: str = "desc"  # "asc", "desc"
    limit: int = 20
    offset: int = 0

class SearchResponse(BaseModel):
    """搜索响应模型"""
    papers: List[PaperSummary]
    total: int
    query: str
    search_type: str
    filters: Optional[Dict[str, Any]] = None
    execution_time: float

class SearchFilters(BaseModel):
    """搜索过滤器模型"""
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    authors: Optional[List[str]] = None
    journals: Optional[List[str]] = None
    research_fields: Optional[List[str]] = None
    min_citations: Optional[int] = None
    min_truth_value: Optional[float] = None

class GraphNode(BaseModel):
    """图节点模型"""
    id: str
    label: str
    type: str  # "paper", "author", "journal"
    size: Optional[float] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class GraphEdge(BaseModel):
    """图边模型"""
    source: str
    target: str
    type: str  # "citation", "collaboration", "authorship"
    weight: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class GraphData(BaseModel):
    """图数据模型"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    center_node: str
    layout: str = "force"

class TruthValueResult(BaseModel):
    """真值计算结果模型"""
    paper_id: str
    total_score: float
    dimensions: Dict[str, float]
    explanation: str
    computed_at: str

class AIAnalysisResult(BaseModel):
    """AI分析结果模型"""
    type: str  # "summary", "comparison", "trend_analysis"
    content: str
    confidence: float
    sources: List[str]
    generated_at: str

class CitationNetwork(BaseModel):
    """引用网络模型"""
    paper_id: str
    direct_citations: List[str]
    indirect_citations: List[str]
    citation_depth: int
    influence_score: float

class CollaborationNetwork(BaseModel):
    """合作网络模型"""
    author_id: str
    direct_collaborators: List[str]
    collaboration_strength: Dict[str, float]
    network_centrality: float

