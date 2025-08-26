"""
真值算法模块
计算论文的真值分数，包含多个维度的评估
"""
import random
import math
from typing import Dict, Any
from datetime import datetime

def calculate_truth_value(paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算论文的真值分数
    
    Args:
        paper_data: 包含论文信息的字典
    
    Returns:
        包含总分和各维度分数的字典
    """
    # 获取论文基础信息
    citation_count = paper_data.get("citation_count", 0)
    year = paper_data.get("year", 2020)
    journal_if = paper_data.get("journal_impact_factor", 1.0)
    author_count = len(paper_data.get("authors", []))
    references_count = len(paper_data.get("references", []))
    
    # 计算各维度分数
    dimensions = {}
    
    # 1. 引用影响力 (Citation Impact) - 30%权重
    # 使用对数函数避免极端值影响
    citation_score = min(10.0, math.log(citation_count + 1) * 2.0)
    dimensions["citation_impact"] = round(citation_score, 2)
    
    # 2. 期刊质量 (Journal Quality) - 25%权重
    # 基于期刊影响因子计算
    journal_score = min(10.0, math.log(journal_if + 1) * 3.0)
    dimensions["journal_quality"] = round(journal_score, 2)
    
    # 3. 时效性 (Recency) - 15%权重
    # 越新的论文得分越高
    current_year = datetime.now().year
    years_old = current_year - year
    recency_score = max(0, 10.0 - years_old * 0.5)
    dimensions["recency"] = round(recency_score, 2)
    
    # 4. 研究协作度 (Collaboration) - 10%权重
    # 基于作者数量计算协作度
    collaboration_score = min(10.0, math.log(author_count) * 2.5 + 2.0)
    dimensions["collaboration"] = round(collaboration_score, 2)
    
    # 5. 参考文献质量 (Reference Quality) - 10%权重
    # 基于参考文献数量计算
    reference_score = min(10.0, math.log(references_count + 1) * 1.5)
    dimensions["reference_quality"] = round(reference_score, 2)
    
    # 6. 创新性指标 (Innovation) - 10%权重
    # 模拟创新性评估（实际应用中可能基于关键词新颖度、跨领域性等）
    innovation_base = random.uniform(4.0, 9.0)
    # 如果引用数很高但论文较新，可能有创新性
    if citation_count > 50 and years_old < 3:
        innovation_base += 1.0
    innovation_score = min(10.0, innovation_base)
    dimensions["innovation"] = round(innovation_score, 2)
    
    # 计算加权总分
    weights = {
        "citation_impact": 0.30,
        "journal_quality": 0.25, 
        "recency": 0.15,
        "collaboration": 0.10,
        "reference_quality": 0.10,
        "innovation": 0.10
    }
    
    total_score = sum(dimensions[dim] * weights[dim] for dim in dimensions)
    total_score = round(total_score, 2)
    
    # 生成解释说明
    explanation = generate_explanation(dimensions, total_score)
    
    return {
        "paper_id": paper_data.get("id", "unknown"),
        "total_score": total_score,
        "dimensions": dimensions,
        "explanation": explanation,
        "computed_at": datetime.now().isoformat()
    }

def generate_explanation(dimensions: Dict[str, float], total_score: float) -> str:
    """
    生成真值分数的解释说明
    
    Args:
        dimensions: 各维度分数
        total_score: 总分
    
    Returns:
        解释说明文本
    """
    explanations = []
    
    # 找出最高和最低的维度
    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
    highest_dim = sorted_dims[0]
    lowest_dim = sorted_dims[-1]
    
    # 总体评价
    if total_score >= 8.0:
        explanations.append("这是一篇高质量的研究论文")
    elif total_score >= 6.0:
        explanations.append("这是一篇质量良好的研究论文")
    elif total_score >= 4.0:
        explanations.append("这是一篇质量中等的研究论文")
    else:
        explanations.append("这篇论文的质量有待提升")
    
    # 突出优势
    dim_names = {
        "citation_impact": "引用影响力",
        "journal_quality": "期刊质量",
        "recency": "时效性",
        "collaboration": "研究协作度",
        "reference_quality": "参考文献质量",
        "innovation": "创新性"
    }
    
    if highest_dim[1] >= 7.0:
        explanations.append(f"在{dim_names[highest_dim[0]]}方面表现突出")
    
    # 指出不足
    if lowest_dim[1] <= 3.0:
        explanations.append(f"在{dim_names[lowest_dim[0]]}方面有提升空间")
    
    return "，".join(explanations) + "。"

def batch_calculate_truth_values(papers: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    批量计算多篇论文的真值分数
    
    Args:
        papers: 论文列表
    
    Returns:
        真值分数结果列表
    """
    results = []
    for paper in papers:
        result = calculate_truth_value(paper)
        results.append(result)
    
    return results

def get_truth_value_distribution(papers: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    获取论文真值分数的分布统计
    
    Args:
        papers: 论文列表
    
    Returns:
        包含分布统计的字典
    """
    if not papers:
        return {"total": 0, "distribution": {}}
    
    results = batch_calculate_truth_values(papers)
    scores = [r["total_score"] for r in results]
    
    # 分数段统计
    distribution = {
        "excellent": len([s for s in scores if s >= 8.0]),
        "good": len([s for s in scores if 6.0 <= s < 8.0]),
        "average": len([s for s in scores if 4.0 <= s < 6.0]),
        "poor": len([s for s in scores if s < 4.0])
    }
    
    return {
        "total": len(scores),
        "distribution": distribution,
        "average_score": round(sum(scores) / len(scores), 2),
        "max_score": max(scores),
        "min_score": min(scores)
    }

def compare_papers_truth_value(paper1: Dict[str, Any], paper2: Dict[str, Any]) -> Dict[str, Any]:
    """
    比较两篇论文的真值分数
    
    Args:
        paper1: 第一篇论文
        paper2: 第二篇论文
    
    Returns:
        比较结果
    """
    result1 = calculate_truth_value(paper1)
    result2 = calculate_truth_value(paper2)
    
    comparison = {
        "paper1": {
            "id": paper1.get("id"),
            "title": paper1.get("title"),
            "score": result1["total_score"],
            "dimensions": result1["dimensions"]
        },
        "paper2": {
            "id": paper2.get("id"),
            "title": paper2.get("title"),
            "score": result2["total_score"],
            "dimensions": result2["dimensions"]
        },
        "winner": "paper1" if result1["total_score"] > result2["total_score"] else "paper2",
        "score_difference": abs(result1["total_score"] - result2["total_score"])
    }
    
    # 维度对比
    dimension_comparison = {}
    for dim in result1["dimensions"]:
        dimension_comparison[dim] = {
            "paper1": result1["dimensions"][dim],
            "paper2": result2["dimensions"][dim],
            "difference": result1["dimensions"][dim] - result2["dimensions"][dim]
        }
    
    comparison["dimension_comparison"] = dimension_comparison
    
    return comparison

