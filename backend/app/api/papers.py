"""
论文相关API接口
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from ..models.paper import Paper, PaperSummary, GraphData, GraphNode, GraphEdge, TruthValueResult, CitationNetwork
from ..models.user import User
from ..api.auth import get_current_user
from ..db.mock_db import db
from ..algorithms.truth_value import calculate_truth_value, compare_papers_truth_value

router = APIRouter(prefix="/papers", tags=["论文"])

@router.get("/", response_model=List[PaperSummary], summary="获取论文列表")
async def get_papers(
    limit: int = Query(20, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
    sort_by: str = Query("date", description="排序方式: date, citation, truth_value"),
    order: str = Query("desc", description="排序顺序: asc, desc")
):
    """
    获取论文列表
    
    - **limit**: 返回的论文数量限制
    - **offset**: 分页偏移量
    - **sort_by**: 排序方式（date: 发表时间, citation: 引用数, truth_value: 真值分数）
    - **order**: 排序顺序（asc: 升序, desc: 降序）
    """
    papers = db.get_papers()
    
    # 排序
    reverse = order == "desc"
    if sort_by == "citation":
        papers = sorted(papers, key=lambda x: x["citation_count"], reverse=reverse)
    elif sort_by == "truth_value":
        papers = sorted(papers, key=lambda x: x.get("truth_value_score", 0), reverse=reverse)
    else:  # date
        papers = sorted(papers, key=lambda x: x["year"], reverse=reverse)
    
    # 分页
    paginated_papers = papers[offset:offset + limit]
    
    # 转换为PaperSummary格式
    paper_summaries = []
    for paper in paginated_papers:
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

@router.get("/{paper_id}", response_model=Paper, summary="获取论文详情")
async def get_paper_detail(paper_id: str):
    """
    获取论文详细信息
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    return Paper(**paper)

@router.get("/{paper_id}/truth-value", response_model=TruthValueResult, summary="计算论文真值分数")
async def calculate_paper_truth_value(paper_id: str):
    """
    计算论文的真值分数
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    truth_value_result = calculate_truth_value(paper)
    return TruthValueResult(**truth_value_result)

@router.get("/{paper_id}/references", response_model=List[PaperSummary], summary="获取参考文献")
async def get_paper_references(paper_id: str):
    """
    获取论文的参考文献列表
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    references = []
    for ref_id in paper.get("references", []):
        ref_paper = db.get_paper_by_id(ref_id)
        if ref_paper:
            summary = PaperSummary(
                id=ref_paper["id"],
                title=ref_paper["title"],
                author_names=ref_paper["author_names"],
                year=ref_paper["year"],
                journal=ref_paper["journal"],
                citation_count=ref_paper["citation_count"],
                truth_value_score=ref_paper.get("truth_value_score"),
                research_field=ref_paper["research_field"]
            )
            references.append(summary)
    
    return references

@router.get("/{paper_id}/citations", response_model=List[PaperSummary], summary="获取被引文献")
async def get_paper_citations(paper_id: str):
    """
    获取引用该论文的文献列表
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    citations = []
    for cite_id in paper.get("cited_by", []):
        cite_paper = db.get_paper_by_id(cite_id)
        if cite_paper:
            summary = PaperSummary(
                id=cite_paper["id"],
                title=cite_paper["title"],
                author_names=cite_paper["author_names"],
                year=cite_paper["year"],
                journal=cite_paper["journal"],
                citation_count=cite_paper["citation_count"],
                truth_value_score=cite_paper.get("truth_value_score"),
                research_field=cite_paper["research_field"]
            )
            citations.append(summary)
    
    return citations

@router.get("/{paper_id}/graph", response_model=GraphData, summary="获取论文引用关系图")
async def get_paper_citation_graph(
    paper_id: str,
    depth: int = Query(2, description="图的深度"),
    max_nodes: int = Query(50, description="最大节点数")
):
    """
    获取论文的引用关系图数据
    
    - **paper_id**: 中心论文ID
    - **depth**: 引用关系的深度（1-3）
    - **max_nodes**: 最大节点数量限制
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    nodes = []
    edges = []
    visited = set()
    
    # 添加中心节点
    center_node = GraphNode(
        id=paper["id"],
        label=paper["title"][:50] + "..." if len(paper["title"]) > 50 else paper["title"],
        type="paper",
        size=3.0,
        color="#ff6b6b",
        metadata={
            "year": paper["year"],
            "citation_count": paper["citation_count"],
            "is_center": True
        }
    )
    nodes.append(center_node)
    visited.add(paper["id"])
    
    # 递归构建图
    def build_graph(current_paper_id: str, current_depth: int):
        if current_depth <= 0 or len(nodes) >= max_nodes:
            return
        
        current_paper = db.get_paper_by_id(current_paper_id)
        if not current_paper:
            return
        
        # 添加参考文献
        for ref_id in current_paper.get("references", []):
            if ref_id not in visited and len(nodes) < max_nodes:
                ref_paper = db.get_paper_by_id(ref_id)
                if ref_paper:
                    node = GraphNode(
                        id=ref_paper["id"],
                        label=ref_paper["title"][:30] + "..." if len(ref_paper["title"]) > 30 else ref_paper["title"],
                        type="paper",
                        size=2.0,
                        color="#4ecdc4",
                        metadata={
                            "year": ref_paper["year"],
                            "citation_count": ref_paper["citation_count"]
                        }
                    )
                    nodes.append(node)
                    visited.add(ref_id)
                    
                    # 添加边
                    edge = GraphEdge(
                        source=current_paper_id,
                        target=ref_id,
                        type="citation",
                        weight=1.0,
                        metadata={"direction": "references"}
                    )
                    edges.append(edge)
                    
                    # 递归
                    build_graph(ref_id, current_depth - 1)
        
        # 添加被引文献
        for cite_id in current_paper.get("cited_by", []):
            if cite_id not in visited and len(nodes) < max_nodes:
                cite_paper = db.get_paper_by_id(cite_id)
                if cite_paper:
                    node = GraphNode(
                        id=cite_paper["id"],
                        label=cite_paper["title"][:30] + "..." if len(cite_paper["title"]) > 30 else cite_paper["title"],
                        type="paper",
                        size=2.0,
                        color="#45b7d1",
                        metadata={
                            "year": cite_paper["year"],
                            "citation_count": cite_paper["citation_count"]
                        }
                    )
                    nodes.append(node)
                    visited.add(cite_id)
                    
                    # 添加边
                    edge = GraphEdge(
                        source=cite_id,
                        target=current_paper_id,
                        type="citation",
                        weight=1.0,
                        metadata={"direction": "cited_by"}
                    )
                    edges.append(edge)
                    
                    # 递归
                    build_graph(cite_id, current_depth - 1)
    
    # 构建图
    build_graph(paper_id, depth)
    
    return GraphData(
        nodes=nodes,
        edges=edges,
        center_node=paper_id,
        layout="force"
    )

@router.get("/{paper_id}/similar", response_model=List[PaperSummary], summary="获取相似论文")
async def get_similar_papers(
    paper_id: str,
    limit: int = Query(10, description="返回数量")
):
    """
    获取与指定论文相似的论文
    
    - **paper_id**: 论文ID
    - **limit**: 返回的相似论文数量
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    similar_papers = []
    paper_keywords = set(paper["keywords"])
    paper_field = paper["research_field"]
    
    for other_paper in db.papers:
        if other_paper["id"] == paper_id:
            continue
        
        # 计算相似度
        similarity_score = 0.0
        
        # 基于关键词相似度
        other_keywords = set(other_paper["keywords"])
        common_keywords = paper_keywords & other_keywords
        if paper_keywords and other_keywords:
            keyword_similarity = len(common_keywords) / len(paper_keywords | other_keywords)
            similarity_score += keyword_similarity * 0.6
        
        # 基于研究领域相似度
        if paper_field == other_paper["research_field"]:
            similarity_score += 0.3
        
        # 基于作者相似度
        paper_authors = set(paper["authors"])
        other_authors = set(other_paper["authors"])
        common_authors = paper_authors & other_authors
        if common_authors:
            similarity_score += len(common_authors) * 0.1
        
        if similarity_score > 0.2:  # 相似度阈值
            similar_papers.append({
                "paper": other_paper,
                "similarity": similarity_score
            })
    
    # 按相似度排序
    similar_papers.sort(key=lambda x: x["similarity"], reverse=True)
    
    # 转换为PaperSummary格式
    result = []
    for item in similar_papers[:limit]:
        paper_data = item["paper"]
        summary = PaperSummary(
            id=paper_data["id"],
            title=paper_data["title"],
            author_names=paper_data["author_names"],
            year=paper_data["year"],
            journal=paper_data["journal"],
            citation_count=paper_data["citation_count"],
            truth_value_score=paper_data.get("truth_value_score"),
            research_field=paper_data["research_field"]
        )
        result.append(summary)
    
    return result

@router.post("/{paper_id}/bookmark", summary="收藏论文")
async def bookmark_paper(
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    收藏论文到用户收藏夹
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    success = db.add_bookmark(current_user.id, paper_id)
    if not success:
        raise HTTPException(status_code=400, detail="论文已在收藏夹中")
    
    return {"message": "论文收藏成功"}

@router.delete("/{paper_id}/bookmark", summary="取消收藏论文")
async def unbookmark_paper(
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    从收藏夹中移除论文
    
    - **paper_id**: 论文ID
    """
    success = db.remove_bookmark(current_user.id, paper_id)
    if not success:
        raise HTTPException(status_code=400, detail="论文不在收藏夹中")
    
    return {"message": "已取消收藏"}

@router.post("/compare", summary="比较论文真值分数")
async def compare_papers(paper_id1: str, paper_id2: str):
    """
    比较两篇论文的真值分数
    
    - **paper_id1**: 第一篇论文ID
    - **paper_id2**: 第二篇论文ID
    """
    paper1 = db.get_paper_by_id(paper_id1)
    paper2 = db.get_paper_by_id(paper_id2)
    
    if not paper1:
        raise HTTPException(status_code=404, detail="第一篇论文不存在")
    if not paper2:
        raise HTTPException(status_code=404, detail="第二篇论文不存在")
    
    comparison_result = compare_papers_truth_value(paper1, paper2)
    return comparison_result

@router.get("/{paper_id}/citation-network", response_model=CitationNetwork, summary="获取引用网络分析")
async def get_citation_network(paper_id: str):
    """
    获取论文的引用网络分析
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 计算直接和间接引用
    direct_citations = paper.get("cited_by", [])
    indirect_citations = []
    
    # 计算二级引用（引用该论文的论文又被哪些论文引用）
    for cite_id in direct_citations:
        cite_paper = db.get_paper_by_id(cite_id)
        if cite_paper:
            indirect_citations.extend(cite_paper.get("cited_by", []))
    
    # 去重
    indirect_citations = list(set(indirect_citations) - set(direct_citations) - {paper_id})
    
    # 计算影响力分数（简化版本）
    influence_score = len(direct_citations) * 1.0 + len(indirect_citations) * 0.5
    
    return CitationNetwork(
        paper_id=paper_id,
        direct_citations=direct_citations,
        indirect_citations=indirect_citations,
        citation_depth=2,
        influence_score=influence_score
    )

