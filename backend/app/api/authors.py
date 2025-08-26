"""
作者相关API接口
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from ..models.paper import Author, AuthorSummary, PaperSummary, GraphData, GraphNode, GraphEdge, CollaborationNetwork
from ..models.user import User
from ..api.auth import get_current_user
from ..db.mock_db import db

router = APIRouter(prefix="/authors", tags=["作者"])

@router.get("/", response_model=List[AuthorSummary], summary="获取作者列表")
async def get_authors(
    limit: int = Query(20, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
    sort_by: str = Query("h_index", description="排序方式: h_index, citation_count, paper_count"),
    order: str = Query("desc", description="排序顺序: asc, desc")
):
    """
    获取作者列表
    
    - **limit**: 返回的作者数量限制
    - **offset**: 分页偏移量
    - **sort_by**: 排序方式（h_index: H指数, citation_count: 引用数, paper_count: 论文数量）
    - **order**: 排序顺序（asc: 升序, desc: 降序）
    """
    authors = db.get_authors()
    
    # 排序
    reverse = order == "desc"
    if sort_by == "citation_count":
        authors = sorted(authors, key=lambda x: x["citation_count"], reverse=reverse)
    elif sort_by == "paper_count":
        authors = sorted(authors, key=lambda x: x["paper_count"], reverse=reverse)
    else:  # h_index
        authors = sorted(authors, key=lambda x: x["h_index"], reverse=reverse)
    
    # 分页
    paginated_authors = authors[offset:offset + limit]
    
    # 转换为AuthorSummary格式
    author_summaries = []
    for author in paginated_authors:
        summary = AuthorSummary(
            id=author["id"],
            name=author["name"],
            affiliation=author["affiliation"],
            research_areas=author["research_areas"],
            h_index=author["h_index"],
            citation_count=author["citation_count"],
            paper_count=author["paper_count"]
        )
        author_summaries.append(summary)
    
    return author_summaries

@router.get("/{author_id}", response_model=Author, summary="获取作者详情")
async def get_author_detail(author_id: str):
    """
    获取作者详细信息
    
    - **author_id**: 作者ID
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    return Author(**author)

@router.get("/{author_id}/papers", response_model=List[PaperSummary], summary="获取作者论文")
async def get_author_papers(
    author_id: str,
    limit: int = Query(20, description="返回数量限制"),
    sort_by: str = Query("year", description="排序方式: year, citation"),
    order: str = Query("desc", description="排序顺序: asc, desc")
):
    """
    获取作者发表的论文列表
    
    - **author_id**: 作者ID
    - **limit**: 返回的论文数量限制
    - **sort_by**: 排序方式（year: 发表年份, citation: 引用数）
    - **order**: 排序顺序（asc: 升序, desc: 降序）
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    papers = db.get_papers_by_author(author_id)
    
    # 排序
    reverse = order == "desc"
    if sort_by == "citation":
        papers = sorted(papers, key=lambda x: x["citation_count"], reverse=reverse)
    else:  # year
        papers = sorted(papers, key=lambda x: x["year"], reverse=reverse)
    
    # 限制数量
    papers = papers[:limit]
    
    # 转换为PaperSummary格式
    paper_summaries = []
    for paper in papers:
        summary = PaperSummary(
            id=paper["id"],
            title=paper["title"],
            author_names=paper["author_names"],
            year=paper["year"],
            journal=paper["journal"],
            citation_count=paper["citation_count"],
            truth_value_score=paper.get("truth_value_score"),
            research_field=paper["research_field"]
        )
        paper_summaries.append(summary)
    
    return paper_summaries

@router.get("/{author_id}/statistics", summary="获取作者统计信息")
async def get_author_statistics(author_id: str):
    """
    获取作者的详细统计信息
    
    - **author_id**: 作者ID
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    papers = db.get_papers_by_author(author_id)
    
    # 计算统计信息
    years = [paper["year"] for paper in papers]
    citations_per_year = {}
    papers_per_year = {}
    total_citations = 0
    
    for paper in papers:
        year = paper["year"]
        citations = paper["citation_count"]
        
        papers_per_year[year] = papers_per_year.get(year, 0) + 1
        citations_per_year[year] = citations_per_year.get(year, 0) + citations
        total_citations += citations
    
    # 研究领域分布
    research_fields = {}
    for paper in papers:
        field = paper["research_field"]
        research_fields[field] = research_fields.get(field, 0) + 1
    
    # 合作者统计
    collaborators = set()
    for paper in papers:
        for author_id_in_paper in paper["authors"]:
            if author_id_in_paper != author_id:
                collaborators.add(author_id_in_paper)
    
    # 期刊分布
    journals = {}
    for paper in papers:
        journal = paper["journal"]
        journals[journal] = journals.get(journal, 0) + 1
    
    return {
        "author_id": author_id,
        "total_papers": len(papers),
        "total_citations": total_citations,
        "average_citations_per_paper": round(total_citations / len(papers), 2) if papers else 0,
        "active_years": max(years) - min(years) + 1 if years else 0,
        "first_publication_year": min(years) if years else None,
        "latest_publication_year": max(years) if years else None,
        "h_index": author["h_index"],
        "papers_per_year": papers_per_year,
        "citations_per_year": citations_per_year,
        "research_fields": research_fields,
        "total_collaborators": len(collaborators),
        "journal_distribution": journals
    }

@router.get("/{author_id}/career-timeline", summary="获取作者学术生涯轨迹")
async def get_author_career_timeline(author_id: str):
    """
    获取作者的学术生涯轨迹数据（用于图表展示）
    
    - **author_id**: 作者ID
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    papers = db.get_papers_by_author(author_id)
    
    # 按年份组织数据
    timeline_data = {}
    for paper in papers:
        year = paper["year"]
        if year not in timeline_data:
            timeline_data[year] = {
                "year": year,
                "papers_count": 0,
                "total_citations": 0,
                "papers": []
            }
        
        timeline_data[year]["papers_count"] += 1
        timeline_data[year]["total_citations"] += paper["citation_count"]
        timeline_data[year]["papers"].append({
            "id": paper["id"],
            "title": paper["title"],
            "journal": paper["journal"],
            "citations": paper["citation_count"]
        })
    
    # 转换为列表并排序
    timeline = sorted(timeline_data.values(), key=lambda x: x["year"])
    
    # 添加作者生涯里程碑
    career_events = author.get("career_timeline", [])
    
    return {
        "author_id": author_id,
        "academic_timeline": timeline,
        "career_milestones": career_events,
        "total_active_years": len(timeline)
    }

@router.get("/{author_id}/research-evolution", summary="获取研究焦点变迁")
async def get_research_evolution(author_id: str):
    """
    获取作者研究焦点的变迁分析
    
    - **author_id**: 作者ID
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    papers = db.get_papers_by_author(author_id)
    
    # 按时间段分析关键词变化
    time_periods = {}
    for paper in papers:
        year = paper["year"]
        period = f"{(year // 5) * 5}-{(year // 5) * 5 + 4}"  # 5年为一个时期
        
        if period not in time_periods:
            time_periods[period] = {
                "period": period,
                "keywords": {},
                "research_fields": {},
                "papers_count": 0
            }
        
        time_periods[period]["papers_count"] += 1
        
        # 统计关键词
        for keyword in paper["keywords"]:
            time_periods[period]["keywords"][keyword] = time_periods[period]["keywords"].get(keyword, 0) + 1
        
        # 统计研究领域
        field = paper["research_field"]
        time_periods[period]["research_fields"][field] = time_periods[period]["research_fields"].get(field, 0) + 1
    
    # 转换为列表
    evolution_data = sorted(time_periods.values(), key=lambda x: x["period"])
    
    # 识别主要研究主题的变化
    research_trends = []
    for period_data in evolution_data:
        # 获取前5个最频繁的关键词
        top_keywords = sorted(period_data["keywords"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_fields = sorted(period_data["research_fields"].items(), key=lambda x: x[1], reverse=True)[:3]
        
        research_trends.append({
            "period": period_data["period"],
            "papers_count": period_data["papers_count"],
            "main_keywords": [kw[0] for kw in top_keywords],
            "keyword_frequencies": dict(top_keywords),
            "research_fields": dict(top_fields)
        })
    
    return {
        "author_id": author_id,
        "research_evolution": research_trends,
        "total_periods": len(research_trends)
    }

@router.get("/{author_id}/collaboration-network", response_model=CollaborationNetwork, summary="获取合作网络")
async def get_collaboration_network(author_id: str):
    """
    获取作者的合作网络分析
    
    - **author_id**: 作者ID
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    papers = db.get_papers_by_author(author_id)
    
    # 统计合作者和合作强度
    collaborators = {}
    
    for paper in papers:
        for coauthor_id in paper["authors"]:
            if coauthor_id != author_id:
                if coauthor_id not in collaborators:
                    collaborators[coauthor_id] = 0
                collaborators[coauthor_id] += 1
    
    # 计算网络中心性（简化版本：基于合作次数）
    total_collaborations = sum(collaborators.values())
    network_centrality = len(collaborators) / max(1, len(db.authors) - 1)  # 连接比例
    
    # 转换合作强度为比例
    collaboration_strength = {}
    for collaborator_id, count in collaborators.items():
        collaboration_strength[collaborator_id] = count / max(1, total_collaborations)
    
    return CollaborationNetwork(
        author_id=author_id,
        direct_collaborators=list(collaborators.keys()),
        collaboration_strength=collaboration_strength,
        network_centrality=network_centrality
    )

@router.get("/{author_id}/graph", response_model=GraphData, summary="获取作者合作关系图")
async def get_author_collaboration_graph(
    author_id: str,
    max_nodes: int = Query(30, description="最大节点数")
):
    """
    获取作者的合作关系图数据
    
    - **author_id**: 中心作者ID
    - **max_nodes**: 最大节点数量限制
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    nodes = []
    edges = []
    
    # 添加中心作者节点
    center_node = GraphNode(
        id=author["id"],
        label=author["name"],
        type="author",
        size=4.0,
        color="#ff6b6b",
        metadata={
            "affiliation": author["affiliation"],
            "h_index": author["h_index"],
            "is_center": True
        }
    )
    nodes.append(center_node)
    
    # 获取合作网络
    papers = db.get_papers_by_author(author_id)
    collaborators = {}
    
    for paper in papers:
        for coauthor_id in paper["authors"]:
            if coauthor_id != author_id:
                if coauthor_id not in collaborators:
                    collaborators[coauthor_id] = []
                collaborators[coauthor_id].append(paper["id"])
    
    # 按合作次数排序，取前N个合作者
    sorted_collaborators = sorted(collaborators.items(), key=lambda x: len(x[1]), reverse=True)
    top_collaborators = sorted_collaborators[:max_nodes-1]
    
    # 添加合作者节点和边
    for coauthor_id, shared_papers in top_collaborators:
        coauthor = db.get_author_by_id(coauthor_id)
        if coauthor:
            # 添加合作者节点
            collaboration_count = len(shared_papers)
            node_size = min(3.0, 1.5 + collaboration_count * 0.3)
            
            coauthor_node = GraphNode(
                id=coauthor["id"],
                label=coauthor["name"],
                type="author",
                size=node_size,
                color="#4ecdc4",
                metadata={
                    "affiliation": coauthor["affiliation"],
                    "h_index": coauthor["h_index"],
                    "collaboration_count": collaboration_count
                }
            )
            nodes.append(coauthor_node)
            
            # 添加合作关系边
            edge_weight = min(5.0, collaboration_count)
            collaboration_edge = GraphEdge(
                source=author_id,
                target=coauthor_id,
                type="collaboration",
                weight=edge_weight,
                metadata={
                    "shared_papers": shared_papers,
                    "collaboration_count": collaboration_count
                }
            )
            edges.append(collaboration_edge)
    
    # 添加合作者之间的关系（如果存在）
    for i, (author1_id, _) in enumerate(top_collaborators):
        for j, (author2_id, _) in enumerate(top_collaborators[i+1:], i+1):
            # 检查这两个作者是否有共同论文
            author1_papers = set(db.get_papers_by_author(author1_id))
            author2_papers = set(db.get_papers_by_author(author2_id))
            
            shared_papers_ids = []
            for paper1 in author1_papers:
                for paper2 in author2_papers:
                    if paper1["id"] == paper2["id"]:
                        shared_papers_ids.append(paper1["id"])
            
            if shared_papers_ids:
                collaboration_edge = GraphEdge(
                    source=author1_id,
                    target=author2_id,
                    type="collaboration",
                    weight=len(shared_papers_ids),
                    metadata={
                        "shared_papers": shared_papers_ids,
                        "collaboration_count": len(shared_papers_ids)
                    }
                )
                edges.append(collaboration_edge)
    
    return GraphData(
        nodes=nodes,
        edges=edges,
        center_node=author_id,
        layout="force"
    )

@router.post("/{author_id}/follow", summary="关注作者")
async def follow_author(
    author_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    关注作者
    
    - **author_id**: 作者ID
    """
    author = db.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    success = db.follow_author(current_user.id, author_id)
    if not success:
        raise HTTPException(status_code=400, detail="已经关注该作者")
    
    return {"message": "关注成功"}

@router.delete("/{author_id}/follow", summary="取消关注作者")
async def unfollow_author(
    author_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消关注作者
    
    - **author_id**: 作者ID
    """
    success = db.unfollow_author(current_user.id, author_id)
    if not success:
        raise HTTPException(status_code=400, detail="未关注该作者")
    
    return {"message": "已取消关注"}

