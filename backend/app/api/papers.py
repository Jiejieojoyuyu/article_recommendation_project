"""
论文相关API接口 - 更新版本
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from ..models.paper import Paper, PaperSummary, GraphData, GraphNode, GraphEdge, TruthValueResult, CitationNetwork
from ..models.user import User
from ..api.auth import get_current_user
from ..db.database import db, user_manager
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
    # 获取数据时就进行分页
    papers = await db.get_papers(limit=limit, offset=offset)
    
    # 转换为PaperSummary格式
    paper_summaries = []
    for paper in papers:
        if not paper:
            continue
        summary = PaperSummary(
            id=paper["id"],
            short_id=paper.get("short_id"),
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

@router.get("/detail", response_model=Paper, summary="获取论文详情")
async def get_paper_detail(paper_id: str = Query(..., description="论文ID")):
    """
    获取论文详细信息
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    return Paper(**paper)

@router.get("/truth-value", response_model=TruthValueResult, summary="计算论文真值分数")
async def calculate_paper_truth_value(paper_id: str = Query(..., description="论文ID")):
    """
    计算论文的真值分数
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    truth_value_result = calculate_truth_value(paper)
    return TruthValueResult(**truth_value_result)

@router.get("/references", response_model=List[PaperSummary], summary="获取参考文献")
async def get_paper_references(paper_id: str = Query(..., description="论文ID")):
    """
    获取论文的参考文献列表
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    references = []
    for ref_id in paper.get("references", []):
        ref_paper = await db.get_paper_by_id(ref_id)
        if ref_paper:
            summary = PaperSummary(
                id=ref_paper["id"],
                short_id=ref_paper.get("short_id"),
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

@router.get("/citations", response_model=List[PaperSummary], summary="获取被引文献")
async def get_paper_citations(paper_id: str = Query(..., description="论文ID")):
    """
    获取引用该论文的文献列表
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    citations = []
    for cite_id in paper.get("cited_by", []):
        cite_paper = await db.get_paper_by_id(cite_id)
        if cite_paper:
            summary = PaperSummary(
                id=cite_paper["id"],
                short_id=cite_paper.get("short_id"),
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

@router.get("/similar", response_model=List[PaperSummary], summary="获取相似论文")
async def get_similar_papers(
    paper_id: str = Query(..., description="论文ID"),
    limit: int = Query(10, description="返回数量")
):
    """
    获取与指定论文相似的论文
    
    - **paper_id**: 论文ID（作为查询参数）
    - **limit**: 返回的相似论文数量
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 基于研究领域搜索相似论文
    filters = {"research_field": paper["research_field"]}
    similar_papers = await db.search_papers("", filters)
    
    # 移除当前论文并限制数量
    filtered_papers = [p for p in similar_papers if p["id"] != paper_id][:limit]
    
    # 转换为PaperSummary格式
    result = []
    for paper_data in filtered_papers:
        summary = PaperSummary(
            id=paper_data["id"],
            short_id=paper_data.get("short_id"),
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

@router.post("/bookmark", summary="收藏论文")
async def bookmark_paper(
    paper_id: str = Query(..., description="论文ID"),
    current_user: User = Depends(get_current_user)
):
    """
    收藏论文到用户收藏夹
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    success = await user_manager.add_bookmark(current_user.id, paper_id)
    if not success:
        raise HTTPException(status_code=400, detail="论文已在收藏夹中")
    
    return {"message": "论文收藏成功"}

@router.delete("/bookmark", summary="取消收藏论文")
async def unbookmark_paper(
    paper_id: str = Query(..., description="论文ID"),
    current_user: User = Depends(get_current_user)
):
    """
    从收藏夹中移除论文
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    success = await user_manager.remove_bookmark(current_user.id, paper_id)
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
    paper1 = await db.get_paper_by_id(paper_id1)
    paper2 = await db.get_paper_by_id(paper_id2)
    
    if not paper1:
        raise HTTPException(status_code=404, detail="第一篇论文不存在")
    if not paper2:
        raise HTTPException(status_code=404, detail="第二篇论文不存在")
    
    comparison_result = compare_papers_truth_value(paper1, paper2)
    return comparison_result

@router.get("/citation-network", response_model=CitationNetwork, summary="获取引用网络分析")
async def get_citation_network(paper_id: str = Query(..., description="论文ID")):
    """
    获取论文的引用网络分析
    
    - **paper_id**: 论文ID（作为查询参数）
    """
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 计算直接和间接引用
    direct_citations = paper.get("cited_by", [])
    indirect_citations = []
    
    # 计算二级引用（引用该论文的论文又被哪些论文引用）
    for cite_id in direct_citations:
        cite_paper = await db.get_paper_by_id(cite_id)
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
