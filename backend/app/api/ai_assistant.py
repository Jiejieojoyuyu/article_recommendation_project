"""
AI助手API接口
"""
import random
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from ..models.paper import AIAnalysisResult
from ..models.user import User
from ..api.auth import get_current_user
from ..db.mock_db import db

router = APIRouter(prefix="/ai-assistant", tags=["AI助手"])

@router.post("/summarize/{paper_id}", response_model=AIAnalysisResult, summary="一句话总结论文")
async def summarize_paper(
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    使用AI生成论文的一句话总结
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 模拟AI总结生成
    summaries = [
        f"本文提出了{paper['research_field']}领域的创新方法，通过{random.choice(['深度学习', '机器学习', '统计分析', '实验验证'])}技术实现了重要突破。",
        f"研究者在{paper['research_field']}方面取得进展，{random.choice(['显著提升了性能', '解决了关键问题', '开辟了新方向', '优化了现有方法'])}。",
        f"这项工作在{paper['research_field']}领域具有重要意义，{random.choice(['为后续研究提供了基础', '推动了技术发展', '解决了实际应用问题', '填补了理论空白'])}。"
    ]
    
    summary = random.choice(summaries)
    confidence = random.uniform(0.8, 0.95)
    
    from datetime import datetime
    
    result = AIAnalysisResult(
        type="summary",
        content=summary,
        confidence=confidence,
        sources=[paper_id],
        generated_at=datetime.now().isoformat()
    )
    
    return result

@router.post("/compare", response_model=AIAnalysisResult, summary="跨论文对比分析")
async def compare_papers_ai(
    paper_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    使用AI对比分析多篇论文
    
    - **paper_ids**: 要对比的论文ID列表（2-5篇）
    """
    if len(paper_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要2篇论文进行对比")
    if len(paper_ids) > 5:
        raise HTTPException(status_code=400, detail="最多支持对比5篇论文")
    
    # 验证所有论文都存在
    papers = []
    for paper_id in paper_ids:
        paper = db.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail=f"论文 {paper_id} 不存在")
        papers.append(paper)
    
    # 生成对比分析
    comparison_content = generate_comparison_analysis(papers)
    confidence = random.uniform(0.75, 0.90)
    
    from datetime import datetime
    
    result = AIAnalysisResult(
        type="comparison",
        content=comparison_content,
        confidence=confidence,
        sources=paper_ids,
        generated_at=datetime.now().isoformat()
    )
    
    return result

@router.post("/research-trends", response_model=AIAnalysisResult, summary="研究趋势分析")
async def analyze_research_trends(
    research_field: str,
    current_user: User = Depends(get_current_user)
):
    """
    分析指定研究领域的发展趋势
    
    - **research_field**: 研究领域名称
    """
    # 获取该领域的论文
    field_papers = [
        paper for paper in db.papers 
        if research_field.lower() in paper["research_field"].lower()
    ]
    
    if not field_papers:
        raise HTTPException(status_code=404, detail="未找到该研究领域的相关论文")
    
    # 生成趋势分析
    trends_analysis = generate_trends_analysis(research_field, field_papers)
    confidence = random.uniform(0.70, 0.85)
    
    from datetime import datetime
    
    result = AIAnalysisResult(
        type="trend_analysis",
        content=trends_analysis,
        confidence=confidence,
        sources=[paper["id"] for paper in field_papers[:10]],  # 取前10篇作为来源
        generated_at=datetime.now().isoformat()
    )
    
    return result

@router.post("/explain-paper/{paper_id}", response_model=AIAnalysisResult, summary="论文详细解读")
async def explain_paper(
    paper_id: str,
    aspect: str = "methodology",  # "methodology", "contribution", "significance"
    current_user: User = Depends(get_current_user)
):
    """
    AI详细解读论文的特定方面
    
    - **paper_id**: 论文ID
    - **aspect**: 解读方面 (methodology: 方法论, contribution: 贡献, significance: 意义)
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 根据不同方面生成解读
    explanation = generate_paper_explanation(paper, aspect)
    confidence = random.uniform(0.80, 0.92)
    
    from datetime import datetime
    
    result = AIAnalysisResult(
        type=f"explanation_{aspect}",
        content=explanation,
        confidence=confidence,
        sources=[paper_id],
        generated_at=datetime.now().isoformat()
    )
    
    return result

@router.post("/recommend-readings/{paper_id}", summary="推荐相关阅读")
async def recommend_related_readings(
    paper_id: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    基于指定论文推荐相关阅读材料
    
    - **paper_id**: 基准论文ID
    - **limit**: 推荐数量限制
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 查找相关论文
    related_papers = find_related_papers(paper, limit)
    
    # 生成推荐理由
    recommendations = []
    for related_paper in related_papers:
        reason = generate_recommendation_reason(paper, related_paper)
        recommendations.append({
            "paper_id": related_paper["id"],
            "title": related_paper["title"],
            "authors": related_paper["author_names"],
            "year": related_paper["year"],
            "reason": reason,
            "relevance_score": random.uniform(0.6, 0.9)
        })
    
    return {
        "base_paper_id": paper_id,
        "recommendations": recommendations,
        "total": len(recommendations)
    }

@router.post("/generate-research-ideas/{paper_id}", response_model=AIAnalysisResult, summary="生成研究思路")
async def generate_research_ideas(
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    基于论文生成后续研究思路和方向
    
    - **paper_id**: 论文ID
    """
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 生成研究思路
    research_ideas = generate_research_ideas_content(paper)
    confidence = random.uniform(0.65, 0.80)
    
    from datetime import datetime
    
    result = AIAnalysisResult(
        type="research_ideas",
        content=research_ideas,
        confidence=confidence,
        sources=[paper_id],
        generated_at=datetime.now().isoformat()
    )
    
    return result

@router.get("/capabilities", summary="获取AI助手能力列表")
async def get_ai_capabilities():
    """
    获取AI助手的所有可用功能
    """
    capabilities = [
        {
            "name": "论文总结",
            "endpoint": "/ai-assistant/summarize/{paper_id}",
            "description": "生成论文的简洁总结",
            "input": "论文ID",
            "output": "一句话总结"
        },
        {
            "name": "跨论文对比",
            "endpoint": "/ai-assistant/compare",
            "description": "对比分析多篇论文的异同",
            "input": "2-5篇论文ID",
            "output": "对比分析报告"
        },
        {
            "name": "研究趋势分析",
            "endpoint": "/ai-assistant/research-trends",
            "description": "分析特定领域的研究发展趋势",
            "input": "研究领域名称",
            "output": "趋势分析报告"
        },
        {
            "name": "论文解读",
            "endpoint": "/ai-assistant/explain-paper/{paper_id}",
            "description": "深度解读论文的方法、贡献或意义",
            "input": "论文ID + 解读方面",
            "output": "详细解读"
        },
        {
            "name": "相关阅读推荐",
            "endpoint": "/ai-assistant/recommend-readings/{paper_id}",
            "description": "推荐相关的阅读材料",
            "input": "论文ID",
            "output": "推荐论文列表"
        },
        {
            "name": "研究思路生成",
            "endpoint": "/ai-assistant/generate-research-ideas/{paper_id}",
            "description": "基于论文生成后续研究方向",
            "input": "论文ID",
            "output": "研究思路建议"
        }
    ]
    
    return {
        "capabilities": capabilities,
        "total": len(capabilities),
        "version": "1.0",
        "last_updated": "2023-12-01"
    }

# 辅助函数
def generate_comparison_analysis(papers: List[dict]) -> str:
    """生成论文对比分析"""
    
    # 分析共同点和差异
    research_fields = [paper["research_field"] for paper in papers]
    common_field = max(set(research_fields), key=research_fields.count)
    
    years = [paper["year"] for paper in papers]
    year_span = max(years) - min(years)
    
    # 生成对比内容
    if year_span <= 2:
        time_context = "这些论文发表时间相近，反映了该领域的同期研究焦点。"
    else:
        time_context = f"这些论文跨越了{year_span}年，展现了该领域的发展轨迹。"
    
    comparison_points = [
        f"所选论文主要集中在{common_field}领域。{time_context}",
        f"在方法论上，这些研究采用了不同的技术路径，体现了多元化的解决方案。",
        f"从影响力来看，论文的引用情况反映了不同研究贡献的学术认可度。",
        f"这些工作在理论创新和实际应用方面各有侧重，形成了互补的研究生态。"
    ]
    
    return " ".join(comparison_points)

def generate_trends_analysis(field: str, papers: List[dict]) -> str:
    """生成研究趋势分析"""
    
    # 按年份分组分析
    years = [paper["year"] for paper in papers]
    recent_papers = [paper for paper in papers if paper["year"] >= 2020]
    
    # 关键词分析
    all_keywords = []
    for paper in recent_papers:
        all_keywords.extend(paper["keywords"])
    
    from collections import Counter
    keyword_freq = Counter(all_keywords)
    top_keywords = [kw for kw, _ in keyword_freq.most_common(5)]
    
    trends = [
        f"{field}领域在近年来呈现快速发展态势。",
        f"当前的研究热点主要集中在：{', '.join(top_keywords[:3])}等方向。",
        f"从发表趋势看，该领域的研究活跃度持续上升。",
        f"技术融合趋势明显，跨学科研究成为新的增长点。",
        f"未来发展方向可能包括：{', '.join(top_keywords[3:])}等新兴领域。"
    ]
    
    return " ".join(trends)

def generate_paper_explanation(paper: dict, aspect: str) -> str:
    """生成论文解读"""
    
    if aspect == "methodology":
        explanations = [
            f"本文采用了{paper['research_field']}领域的主流方法，结合创新的技术手段。",
            f"研究方法在{random.choice(['数据处理', '模型设计', '实验设计', '算法优化'])}方面有所突破。",
            f"方法论的核心创新在于{random.choice(['提高了效率', '增强了准确性', '扩大了适用范围', '简化了实现复杂度'])}。"
        ]
    elif aspect == "contribution":
        explanations = [
            f"本文的主要贡献在于{random.choice(['理论创新', '方法改进', '应用拓展', '实证发现'])}。",
            f"研究填补了{paper['research_field']}领域的重要空白。",
            f"所提出的方法为相关问题的解决提供了新的思路。"
        ]
    else:  # significance
        explanations = [
            f"这项工作对{paper['research_field']}领域具有重要的推动作用。",
            f"研究成果为后续相关研究奠定了基础。",
            f"在实际应用方面，该工作具有广阔的应用前景。"
        ]
    
    return " ".join(explanations)

def find_related_papers(base_paper: dict, limit: int) -> List[dict]:
    """查找相关论文"""
    related_papers = []
    
    for paper in db.papers:
        if paper["id"] == base_paper["id"]:
            continue
        
        # 计算相关性分数
        score = 0
        
        # 研究领域相同
        if paper["research_field"] == base_paper["research_field"]:
            score += 3
        
        # 关键词重叠
        common_keywords = set(paper["keywords"]) & set(base_paper["keywords"])
        score += len(common_keywords)
        
        # 作者重叠
        common_authors = set(paper["authors"]) & set(base_paper["authors"])
        score += len(common_authors) * 2
        
        # 引用关系
        if base_paper["id"] in paper.get("references", []):
            score += 4
        if paper["id"] in base_paper.get("references", []):
            score += 3
        
        if score > 0:
            related_papers.append((paper, score))
    
    # 按相关性排序
    related_papers.sort(key=lambda x: x[1], reverse=True)
    
    return [paper for paper, _ in related_papers[:limit]]

def generate_recommendation_reason(base_paper: dict, related_paper: dict) -> str:
    """生成推荐理由"""
    reasons = []
    
    if base_paper["research_field"] == related_paper["research_field"]:
        reasons.append("同一研究领域")
    
    common_keywords = set(base_paper["keywords"]) & set(related_paper["keywords"])
    if common_keywords:
        reasons.append(f"共同关键词：{', '.join(list(common_keywords)[:2])}")
    
    common_authors = set(base_paper["authors"]) & set(related_paper["authors"])
    if common_authors:
        reasons.append("作者相关")
    
    if not reasons:
        reasons.append("内容相关")
    
    return "；".join(reasons)

def generate_research_ideas_content(paper: dict) -> str:
    """生成研究思路"""
    
    ideas = [
        f"基于本文的{paper['research_field']}方法，可以考虑在{random.choice(['不同数据集', '新应用场景', '跨领域问题', '实际部署'])}上进行验证和扩展。",
        f"结合{random.choice(['最新技术趋势', '相关领域进展', '实际需求', '理论发展'])}，可以探索方法的进一步优化。",
        f"考虑到当前的局限性，未来工作可以重点关注{random.choice(['效率提升', '精度改进', '鲁棒性增强', '可解释性提高'])}。",
        f"从产业应用角度，该研究可以向{random.choice(['商业化', '标准化', '规模化', '自动化'])}方向发展。"
    ]
    
    return " ".join(ideas)

