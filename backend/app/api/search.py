"""
搜索API接口
"""
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from ..models.paper import SearchRequest, SearchResponse, PaperSummary, SearchFilters
from ..models.user import User
from ..api.auth import get_current_user, get_current_user_optional
from ..db.database import db, user_manager
from ..algorithms.recommender import rerank_search_results

router = APIRouter(prefix="/search", tags=["搜索"])

@router.post("/", response_model=SearchResponse, summary="论文搜索")
async def search_papers(search_request: SearchRequest, current_user: Optional[User] = Depends(get_current_user_optional)):
    """
    论文搜索API
    
    支持多种搜索模式：
    - **hybrid**: 混合搜索（默认）- 同时匹配标题、作者、关键词等
    - **semantic**: 语义搜索 - 适用于长句或段落查询
    - **exact**: 精确搜索 - 严格匹配查询词
    
    排序选项：
    - **relevance**: 相关度排序（默认）
    - **date**: 发表时间排序
    - **citation**: 引用数排序
    - **truth_value**: 真值分数排序
    """
    start_time = time.time()
    
    # 执行搜索
    results = await perform_search(
        query=search_request.query,
        search_type=search_request.search_type,
        filters=search_request.filters
    )
    
    # 应用排序
    sorted_results = apply_sorting(
        results=results,
        sort_by=search_request.sort_by,
        sort_order=search_request.sort_order
    )
    
    # 如果用户已登录，应用个性化重排序
    if current_user:
        user_data = await user_manager.get_user_by_id(current_user.id)
        if user_data:
            sorted_results = rerank_search_results(
                user_id=current_user.id,
                results=sorted_results,
                user_data=user_data
            )
            
            # 记录搜索历史
            await user_manager.add_search_history(current_user.id, search_request.query)
    
    # 分页
    total = len(sorted_results)
    paginated_results = sorted_results[search_request.offset:search_request.offset + search_request.limit]
    
    # 转换为PaperSummary格式
    paper_summaries = []
    for result in paginated_results:
        summary = PaperSummary(
            id=result["id"],
            short_id=result.get("short_id"),
            title=result["title"],
            author_names=result["author_names"],
            year=result["year"],
            journal=result["journal"],
            citation_count=result["citation_count"],
            truth_value_score=result.get("truth_value_score"),
            research_field=result["research_field"]
        )
        paper_summaries.append(summary)
    
    execution_time = time.time() - start_time
    
    return SearchResponse(
        papers=paper_summaries,
        total=total,
        query=search_request.query,
        search_type=search_request.search_type,
        filters=search_request.filters,
        execution_time=round(execution_time, 3)
    )

@router.get("/suggestions", summary="搜索建议")
async def get_search_suggestions(
    q: str = Query(..., description="查询前缀"),
    limit: int = Query(10, description="建议数量限制")
):
    """
    获取搜索建议/自动补全
    
    - **q**: 用户输入的查询前缀
    - **limit**: 返回建议的最大数量
    """
    suggestions = []
    q_lower = q.lower()
    
    # 从论文标题中提取建议
    papers = await db.get_papers(limit=100)  # 获取一些论文用于建议
    for paper in papers:
        title_words = paper["title"].lower().split()
        for word in title_words:
            if word.startswith(q_lower) and len(word) > len(q):
                suggestions.append(word)
        
        # 从关键词中提取建议
        for keyword in paper["keywords"]:
            if keyword.lower().startswith(q_lower):
                suggestions.append(keyword)
        
        # 从作者名中提取建议
        for author_name in paper["author_names"]:
            if author_name.lower().startswith(q_lower):
                suggestions.append(author_name)
    
    # 去重并限制数量
    unique_suggestions = list(set(suggestions))[:limit]
    
    return {
        "query": q,
        "suggestions": unique_suggestions
    }

@router.get("/filters", summary="获取可用过滤器")
async def get_available_filters():
    """
    获取可用的搜索过滤器选项
    """
    # 从数据库中提取所有可能的过滤器值
    papers = await db.get_papers(limit=1000)  # 获取更多论文用于统计
    years = sorted(set(paper["year"] for paper in papers if paper["year"]), reverse=True)
    journals = sorted(set(paper["journal"] for paper in papers if paper["journal"]))
    research_fields = sorted(set(paper["research_field"] for paper in papers if paper["research_field"]))
    authors = []
    
    for paper in papers:
        if paper["author_names"]:
            authors.extend(paper["author_names"])
    unique_authors = sorted(set(authors))
    
    return {
        "years": {
            "min": min(years),
            "max": max(years),
            "available": years[:10]  # 最近10年
        },
        "journals": journals,
        "research_fields": research_fields,
        "authors": unique_authors[:50]  # 前50个作者
    }

@router.get("/trending", summary="热门搜索")
async def get_trending_searches(limit: int = Query(10, description="热门搜索数量")):
    """
    获取热门搜索词
    """
    # 模拟热门搜索数据
    trending_searches = [
        {"query": "深度学习", "count": 156},
        {"query": "机器学习", "count": 134},
        {"query": "自然语言处理", "count": 98},
        {"query": "计算机视觉", "count": 87},
        {"query": "推荐系统", "count": 76},
        {"query": "图神经网络", "count": 65},
        {"query": "知识图谱", "count": 54},
        {"query": "联邦学习", "count": 43},
        {"query": "强化学习", "count": 38},
        {"query": "预训练模型", "count": 32}
    ]
    
    return {
        "trending": trending_searches[:limit],
        "updated_at": "2023-12-01T10:00:00Z"
    }

@router.get("/history", summary="搜索历史")
async def get_search_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, description="历史记录数量")
):
    """
    获取用户的搜索历史
    """
    history_queries = await user_manager.get_search_history(current_user.id, limit)
    
    return {
        "history": [{"query": query, "timestamp": ""} for query in history_queries],
        "total": len(history_queries)
    }

@router.delete("/history", summary="清除搜索历史")
async def clear_search_history(current_user: User = Depends(get_current_user)):
    """
    清除用户的搜索历史
    """
    success = await user_manager.clear_search_history(current_user.id)
    
    if success:
        return {"message": "搜索历史已清除"}
    else:
        return {"message": "搜索历史已经为空"}

# 辅助函数
async def perform_search(query: str, search_type: str = "hybrid", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    执行搜索逻辑
    """
    # 直接使用数据库的搜索功能
    return await db.search_papers(query, filters)

def hybrid_search(query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    混合搜索：在标题、作者、关键词、摘要中搜索
    """
    results = []
    query_words = query.lower().split()
    
    for paper in db.papers:
        relevance_score = 0.0
        
        # 搜索标题
        title_matches = sum(1 for word in query_words if word in paper["title"].lower())
        relevance_score += title_matches * 3.0  # 标题匹配权重最高
        
        # 搜索作者
        for author_name in paper["author_names"]:
            author_matches = sum(1 for word in query_words if word in author_name.lower())
            relevance_score += author_matches * 2.0
        
        # 搜索关键词
        for keyword in paper["keywords"]:
            keyword_matches = sum(1 for word in query_words if word in keyword.lower())
            relevance_score += keyword_matches * 2.5
        
        # 搜索摘要
        abstract_matches = sum(1 for word in query_words if word in paper["abstract"].lower())
        relevance_score += abstract_matches * 1.0
        
        # 搜索期刊
        journal_matches = sum(1 for word in query_words if word in paper["journal"].lower())
        relevance_score += journal_matches * 1.5
        
        if relevance_score > 0:
            paper_copy = paper.copy()
            paper_copy["relevance_score"] = relevance_score
            results.append(paper_copy)
    
    # 应用过滤器
    if filters:
        results = apply_filters(results, filters)
    
    return results

def semantic_search(query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    语义搜索：处理长句和段落查询
    """
    results = []
    query_lower = query.lower()
    
    for paper in db.papers:
        # 简化的语义匹配 - 检查查询是否作为子串出现在文本中
        semantic_score = 0.0
        
        # 在摘要中寻找语义相关内容
        if query_lower in paper["abstract"].lower():
            semantic_score += 5.0
        
        # 检查标题的语义相关性
        if query_lower in paper["title"].lower():
            semantic_score += 3.0
        
        # 检查关键词组合的语义相关性
        keywords_text = " ".join(paper["keywords"]).lower()
        if query_lower in keywords_text:
            semantic_score += 4.0
        
        if semantic_score > 0:
            paper_copy = paper.copy()
            paper_copy["relevance_score"] = semantic_score
            results.append(paper_copy)
    
    # 应用过滤器
    if filters:
        results = apply_filters(results, filters)
    
    return results

def exact_search(query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    精确搜索：严格匹配查询词
    """
    results = []
    query_lower = query.lower().strip()
    
    for paper in db.papers:
        exact_score = 0.0
        
        # 精确匹配标题
        if query_lower == paper["title"].lower():
            exact_score += 10.0
        elif query_lower in paper["title"].lower():
            exact_score += 5.0
        
        # 精确匹配作者
        for author_name in paper["author_names"]:
            if query_lower == author_name.lower():
                exact_score += 8.0
            elif query_lower in author_name.lower():
                exact_score += 3.0
        
        # 精确匹配关键词
        for keyword in paper["keywords"]:
            if query_lower == keyword.lower():
                exact_score += 7.0
        
        # 精确匹配DOI
        if paper.get("doi") and query_lower == paper["doi"].lower():
            exact_score += 10.0
        
        if exact_score > 0:
            paper_copy = paper.copy()
            paper_copy["relevance_score"] = exact_score
            results.append(paper_copy)
    
    # 应用过滤器
    if filters:
        results = apply_filters(results, filters)
    
    return results

def apply_filters(results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    应用搜索过滤器
    """
    filtered_results = results.copy()
    
    # 年份过滤
    if filters.get("year_min"):
        filtered_results = [r for r in filtered_results if r["year"] >= filters["year_min"]]
    if filters.get("year_max"):
        filtered_results = [r for r in filtered_results if r["year"] <= filters["year_max"]]
    
    # 期刊过滤
    if filters.get("journals"):
        journal_names = [j.lower() for j in filters["journals"]]
        filtered_results = [r for r in filtered_results if r["journal"].lower() in journal_names]
    
    # 研究领域过滤
    if filters.get("research_fields"):
        field_names = [f.lower() for f in filters["research_fields"]]
        filtered_results = [r for r in filtered_results if r["research_field"].lower() in field_names]
    
    # 最小引用数过滤
    if filters.get("min_citations"):
        filtered_results = [r for r in filtered_results if r["citation_count"] >= filters["min_citations"]]
    
    # 最小真值分数过滤
    if filters.get("min_truth_value"):
        filtered_results = [r for r in filtered_results if r.get("truth_value_score", 0) >= filters["min_truth_value"]]
    
    # 作者过滤
    if filters.get("authors"):
        author_names = [a.lower() for a in filters["authors"]]
        filtered_results = [
            r for r in filtered_results 
            if any(author.lower() in author_names for author in r["author_names"])
        ]
    
    return filtered_results

def apply_sorting(results: List[Dict[str, Any]], sort_by: str = "relevance", sort_order: str = "desc") -> List[Dict[str, Any]]:
    """
    应用排序
    """
    reverse = sort_order == "desc"
    
    if sort_by == "date":
        return sorted(results, key=lambda x: x["year"], reverse=reverse)
    elif sort_by == "citation":
        return sorted(results, key=lambda x: x["citation_count"], reverse=reverse)
    elif sort_by == "truth_value":
        return sorted(results, key=lambda x: x.get("truth_value_score", 0), reverse=reverse)
    else:  # relevance
        return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=reverse)
