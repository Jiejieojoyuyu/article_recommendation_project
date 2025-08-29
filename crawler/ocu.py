#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全修正版 OpenAlex 爬虫脚本（ocu.py）
- 子命令：init-db, topic, year-range, author, work, recurse
- 注意：把 --db 放在子命令之后，例如：
    python ocu.py init-db --db openalex.db
    python ocu.py topic --db openalex.db --query "graph neural network" --from-year 2019 --to-year 2024 --max-records 200
    python ocu.py recurse --db openalex.db --seed-work-id W2755950973 --depth 2 --max-nodes 500 --time-limit 300
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
import requests

BASE_URL = "https://api.openalex.org"
USER_AGENT = "openalex-crawler/1.0 (mailto:you@example.com)"

# -----------------------------
# Utilities
# -----------------------------
def _rate_limited_get(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 6, backoff: float = 1.0) -> Dict[str, Any]:
    headers = {"User-Agent": USER_AGENT}
    params = params or {}
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code == 429:
                # respect Retry-After if provided
                ra = r.headers.get("Retry-After")
                wait = int(ra) if ra and ra.isdigit() else backoff * (2 ** attempt)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt + 1 == max_retries:
                raise
            time.sleep(backoff * (2 ** attempt))
    raise RuntimeError("unreachable")

def _flatten_abstract(inv_idx: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """将 OpenAlex 的 abstract_inverted_index 转为文本（若为空返回 None）"""
    if not inv_idx:
        #print("inv_idx is None")
        return None
    try:
        # 找出最大位置
        max_pos = max(pos for positions in inv_idx.values() for pos in positions)
        words = [None] * (max_pos + 1)
        for w, positions in inv_idx.items():
            for p in positions:
                words[p] = w
        #print(words)
        return " ".join(w for w in words if w)
    except Exception:
        # 回退到 None
        return None

def _norm_work_id(work_id: str) -> Tuple[str, str]:
    """把输入的 work_id 规范化，返回 (full_url, short_id)"""
    work_id = work_id.strip()
    if work_id.startswith("http"):
        short = work_id.rsplit("/", 1)[-1]
        return work_id, short
    if work_id.startswith("W"):
        short = work_id
        full = f"{BASE_URL}/works/{short}"
        return full, short
    # 如果用户可能传入带前缀的 openalex url
    if work_id.startswith("https://openalex.org/"):
        short = work_id.rsplit("/", 1)[-1]
        return work_id, short
    # 最后兜底
    short = work_id
    full = f"{BASE_URL}/works/{short}"
    return full, short

# -----------------------------
# Database schema & helpers
# -----------------------------
SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS works (
    id TEXT PRIMARY KEY,
    short_id TEXT UNIQUE,
    title TEXT,
    authors TEXT,
    author_names TEXT,
    year INTEGER,
    journal TEXT,
    abstract TEXT,
    keywords TEXT,
    doi TEXT,
    citation_count INTEGER,
    download_count INTEGER,
    url TEXT,
    reference_ids TEXT,   -- JSON 列表（短 id，如 W...）
    cited_by INTEGER,
    research_field TEXT,
    funding TEXT,
    -- 新增字段
    journal_issn TEXT,
    host_organization_name TEXT,
    author_orcids TEXT,   -- JSON 列表
    author_institutions TEXT,  -- JSON 列表
    author_countries TEXT,     -- JSON 列表
    fwci REAL,
    citation_percentile REAL,
    publication_date TEXT,
    primary_topic TEXT,
    topics TEXT,          -- JSON 列表
    keywords_display TEXT -- JSON 列表
);

CREATE TABLE IF NOT EXISTS relations (
    from_short_id TEXT,
    to_short_id TEXT,
    relation_type TEXT CHECK(relation_type IN ('references','cited_by')),
    PRIMARY KEY (from_short_id, to_short_id, relation_type)
);
"""

def init_db(db_path: str):
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_SQL)
    con.commit()
    con.close()

@dataclass
class WorkRecord:
    id: str
    short_id: str
    title: Optional[str]
    authors: str
    author_names: Optional[str]
    year: Optional[int]
    journal: Optional[str]
    abstract: Optional[str]
    keywords: Optional[str]
    doi: Optional[str]
    citation_count: Optional[int]
    download_count: Optional[int]
    url: Optional[str]
    reference_ids: Optional[str]
    cited_by: Optional[int]
    research_field: Optional[str]
    funding: Optional[str]
    # 新增字段
    journal_issn: Optional[str]
    host_organization_name: Optional[str]
    author_orcids: Optional[str]
    author_institutions: Optional[str]
    author_countries: Optional[str]
    fwci: Optional[float]
    citation_percentile: Optional[float]
    publication_date: Optional[str]
    primary_topic: Optional[str]
    topics: Optional[str]
    keywords_display: Optional[str]

def upsert_work(con: sqlite3.Connection, rec: WorkRecord):
    con.execute(
        """
        INSERT INTO works (id, short_id, title, authors, author_names, year, journal, abstract, keywords,
                           doi, citation_count, download_count, url, reference_ids, cited_by, research_field, funding,
                           journal_issn, host_organization_name, author_orcids, author_institutions, author_countries,
                           fwci, citation_percentile, publication_date, primary_topic, topics, keywords_display)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            authors=excluded.authors,
            author_names=excluded.author_names,
            year=excluded.year,
            journal=excluded.journal,
            abstract=excluded.abstract,
            keywords=excluded.keywords,
            doi=excluded.doi,
            citation_count=excluded.citation_count,
            download_count=excluded.download_count,
            url=excluded.url,
            reference_ids=excluded.reference_ids,
            cited_by=excluded.cited_by,
            research_field=excluded.research_field,
            funding=excluded.funding,
            journal_issn=excluded.journal_issn,
            host_organization_name=excluded.host_organization_name,
            author_orcids=excluded.author_orcids,
            author_institutions=excluded.author_institutions,
            author_countries=excluded.author_countries,
            fwci=excluded.fwci,
            citation_percentile=excluded.citation_percentile,
            publication_date=excluded.publication_date,
            primary_topic=excluded.primary_topic,
            topics=excluded.topics,
            keywords_display=excluded.keywords_display
        """,
        (
            rec.id, rec.short_id, rec.title, rec.authors, rec.author_names, rec.year, rec.journal, rec.abstract,
            rec.keywords, rec.doi, rec.citation_count, rec.download_count, rec.url, rec.reference_ids, rec.cited_by,
            rec.research_field, rec.funding, rec.journal_issn, rec.host_organization_name, rec.author_orcids,
            rec.author_institutions, rec.author_countries, rec.fwci, rec.citation_percentile, rec.publication_date,
            rec.primary_topic, rec.topics, rec.keywords_display
        )
    )

def upsert_relation(con: sqlite3.Connection, from_short_id: str, to_short_id: str, relation_type: str):
    con.execute(
        "INSERT OR IGNORE INTO relations (from_short_id, to_short_id, relation_type) VALUES (?, ?, ?)",
        (from_short_id, to_short_id, relation_type)
    )

# -----------------------------
# Extract work fields from OpenAlex object
# -----------------------------
def _extract_work(obj: Dict[str, Any]) -> WorkRecord:
    full_id = obj.get("id") or ""
    short_id = full_id.rsplit("/", 1)[-1] if full_id else (obj.get("id") or "")
    
    # authors
    auths_list = []
    author_names = []
    author_orcids = []
    author_institutions = []
    author_countries = []
    
    for au in obj.get("authorships", []) or []:
        author = au.get("author") or {}
        aid = author.get("id")
        aname = author.get("display_name")
        orcid = author.get("orcid")
        
        auths_list.append({"author_id": (aid.rsplit("/", 1)[-1] if aid else None), "name": aname})
        if aname:
            author_names.append(aname)
        if orcid:
            author_orcids.append(orcid)
        
        # 提取机构信息
        institutions = au.get("institutions", []) or []
        for inst in institutions:
            inst_name = inst.get("display_name")
            if inst_name:
                author_institutions.append(inst_name)
        
        # 提取国家信息
        countries = au.get("countries", []) or []
        for country in countries:
            if isinstance(country, dict):
                country_name = country.get("display_name")
            else:
                country_name = str(country) if country else None
            if country_name:
                author_countries.append(country_name)
    
    # abstract
    abstract = _flatten_abstract(obj.get("abstract_inverted_index"))
    
    # concepts -> keywords / research field
    concepts = obj.get("concepts") or []
    concept_simple = [c.get("display_name") for c in concepts if c.get("display_name")]
    research_field = [
        {"id": (c.get("id").rsplit("/", 1)[-1] if c.get("id") else None),
         "display_name": c.get("display_name"),
         "level": c.get("level")}
        for c in concepts
    ]
    
    # funding/grants
    grants = obj.get("grants") or []
    funding_list = []
    for g in grants:
        funding_list.append({
            "funder": g.get("funder", {}).get("display_name") if isinstance(g.get("funder"), dict) else g.get("funder"),
            "award_id": g.get("award_id") or g.get("grant_id"),
            "url": g.get("url")
        })
    
    # venue and urls
    primary_location = obj.get("primary_location") or {}
    source = primary_location.get("source", {}) or {}
    journal = source.get("display_name")
    issn_list = source.get("issn", []) or []
    journal_issn = json.dumps(issn_list, ensure_ascii=False) if issn_list else None
    host_organization_name = source.get("host_organization_name")
    
    primary_landing = primary_location.get("landing_page_url")
    best_oa = (obj.get("best_oa_location") or {}).get("landing_page_url")
    url = primary_landing or best_oa or full_id
    
    # references
    references = obj.get("referenced_works") or []
    
    # 提取新字段
    fwci = obj.get("fwci")
    if fwci is not None and not isinstance(fwci, (int, float)):
        fwci = None
    
    citation_percentile = None
    if obj.get("citation_normalized_percentile"):
        citation_percentile = obj.get("citation_normalized_percentile", {}).get("value")
        if citation_percentile is not None and not isinstance(citation_percentile, (int, float)):
            citation_percentile = None
    
    publication_date = obj.get("publication_date")
    
    # 提取主题信息
    primary_topic = None
    if obj.get("primary_topic"):
        primary_topic = obj.get("primary_topic", {}).get("display_name")
    
    # 提取所有主题
    topics = obj.get("topics", []) or []
    topic_names = [t.get("display_name") for t in topics if t.get("display_name")]
    
    # 提取关键词
    keywords_list = obj.get("keywords", []) or []
    keyword_names = [k.get("display_name") for k in keywords_list if k.get("display_name")]

    rec = WorkRecord(
        id=full_id,
        short_id=short_id or "",
        title=obj.get("display_name"),
        authors=json.dumps(auths_list, ensure_ascii=False) if auths_list else "",
        author_names=("; ".join(author_names) if author_names else None),
        year=obj.get("publication_year"),
        journal=journal,
        abstract=abstract,
        keywords=(json.dumps(concept_simple, ensure_ascii=False) if concept_simple else None),
        doi=obj.get("doi"),
        citation_count=obj.get("cited_by_count"),
        download_count=obj.get("download_count") if obj.get("download_count") is not None else None,
        url=url,
        reference_ids=(json.dumps([rid.rsplit("/", 1)[-1] for rid in references], ensure_ascii=False) if references else None),
        cited_by=obj.get("cited_by_count"),
        research_field=(json.dumps(research_field, ensure_ascii=False) if research_field else None),
        funding=(json.dumps(funding_list, ensure_ascii=False) if funding_list else None),
        # 新增字段
        journal_issn=journal_issn,
        host_organization_name=host_organization_name,
        author_orcids=(json.dumps(author_orcids, ensure_ascii=False) if author_orcids else None),
        author_institutions=(json.dumps(author_institutions, ensure_ascii=False) if author_institutions else None),
        author_countries=(json.dumps(author_countries, ensure_ascii=False) if author_countries else None),
        fwci=fwci,
        citation_percentile=citation_percentile,
        publication_date=publication_date,
        primary_topic=primary_topic,
        topics=(json.dumps(topic_names, ensure_ascii=False) if topic_names else None),
        keywords_display=(json.dumps(keyword_names, ensure_ascii=False) if keyword_names else None)
    )
    return rec

# -----------------------------
# OpenAlex client (分页)
# -----------------------------
class OpenAlexClient:
    def __init__(self, per_page: int = 200):
        self.per_page = max(1, min(per_page, 200))

    def _paginate(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
                  max_records: Optional[int] = None, time_limit: Optional[int] = None) -> Iterable[Dict[str, Any]]:
        url = f"{BASE_URL}/{endpoint}"
        params = dict(params or {})
        params.update({"per_page": self.per_page, "cursor": "*"})
        total = 0
        start = time.time()
        while True:
            if time_limit and (time.time() - start) > time_limit:
                return
            data = _rate_limited_get(url, params=params)
            for item in data.get("results", []):
                yield item
                total += 1
                if max_records and total >= max_records:
                    return
            meta = data.get("meta", {}) or {}
            next_c = meta.get("next_cursor")
            if not next_c:
                return
            params["cursor"] = next_c

    def search_topic(self, query: str, from_year: Optional[int] = None, to_year: Optional[int] = None,
                     max_records: Optional[int] = None, time_limit: Optional[int] = None):
        flt = []
        if from_year:
            flt.append(f"from_publication_date:{from_year}-01-01")
        if to_year:
            flt.append(f"to_publication_date:{to_year}-12-31")
        params = {"search": query}
        if flt:
            params["filter"] = ",".join(flt)
        params["sort"] = "cited_by_count:desc"
        return self._paginate("works", params, max_records, time_limit)

    def year_range(self, from_year: int, to_year: int, max_records: Optional[int] = None, time_limit: Optional[int] = None):
        params = {"filter": f"from_publication_date:{from_year}-01-01,to_publication_date:{to_year}-12-31", "sort": "cited_by_count:desc"}
        return self._paginate("works", params, max_records, time_limit)

    def by_author(self, author_id: str, max_records: Optional[int] = None, time_limit: Optional[int] = None):
        # 支持短 id 或完整 url
        aid = author_id.rsplit("/", 1)[-1]
        params = {"filter": f"authorships.author.id:https://openalex.org/{aid}", "sort": "publication_year:desc"}
        return self._paginate("works", params, max_records, time_limit)

    def by_work_id(self, work_id: str) -> Dict[str, Any]:
        full, short = _norm_work_id(work_id)
        return _rate_limited_get(full)

    def citing_works(self, work_id: str, max_records: Optional[int] = None, time_limit: Optional[int] = None):
        full, _ = _norm_work_id(work_id)
        params = {"filter": f"cites:{full}", "sort": "cited_by_count:desc"}
        return self._paginate("works", params, max_records, time_limit)

# -----------------------------
# Save iterator results to DB
# -----------------------------
def save_iter_to_db(con: sqlite3.Connection, it: Iterable[Dict[str, Any]],
                    add_relations_from: Optional[str] = None, relation_type: Optional[str] = None) -> int:
    cnt = 0
    for obj in it:
        rec = _extract_work(obj)
        upsert_work(con, rec)
        if add_relations_from and relation_type:
            if relation_type == "references" and rec.reference_ids:
                to_ids = json.loads(rec.reference_ids)
                for to in to_ids:
                    upsert_relation(con, rec.short_id, to, "references")
            elif relation_type == "cited_by":
                upsert_relation(con, add_relations_from, rec.short_id, "cited_by")
        cnt += 1
    con.commit()
    return cnt

# -----------------------------
# BFS / 递归抓取
# -----------------------------
def recurse_from_seed(con: sqlite3.Connection, client: OpenAlexClient, seed_work_id: str,
                      depth: int = 1, max_nodes: int = 1000, time_limit: Optional[int] = None):
    """
    从 seed_work_id 出发做 BFS（广度优先），按层次抓取 reference 与 cited_by。
    depth: BFS 最深层数（>=1）。depth=1 表示抓取起点及起点的第一层邻居。
    """
    start_time = time.time()
    full_seed, seed_short = _norm_work_id(seed_work_id)

    # 把种子入库（若 API 返回失败会抛错）
    seed_obj = client.by_work_id(seed_work_id)
    seed_rec = _extract_work(seed_obj)
    upsert_work(con, seed_rec)
    con.commit()

    visited = {seed_short}
    frontier = [seed_short]
    total_nodes = 1

    for layer in range(depth):
        if time_limit and (time.time() - start_time) > time_limit:
            break
        new_frontier: List[str] = []
        for short in list(frontier):
            if time_limit and (time.time() - start_time) > time_limit:
                break
            # 获取当前论文（直接从 API 拉取，因为不再存储 raw 数据）
            obj = client.by_work_id(short)
            rec = _extract_work(obj)
            upsert_work(con, rec)
            con.commit()
            cur_obj = obj

            # 1) references（当前 -> 参考文献）
            referenced = cur_obj.get("referenced_works") or []
            for ref_full in referenced:
                ref_short = ref_full.rsplit("/", 1)[-1]
                upsert_relation(con, short, ref_short, "references")
                if ref_short not in visited:
                    try:
                        robj = client.by_work_id(ref_short)
                        rrec = _extract_work(robj)
                        upsert_work(con, rrec)
                        total_nodes += 1
                        visited.add(ref_short)
                        new_frontier.append(ref_short)
                        if total_nodes >= max_nodes:
                            con.commit()
                            return
                    except Exception:
                        # 忽略拉不下来的个别项
                        pass

            # 2) cited_by：哪些论文引用了当前论文
            citing_iter = client.citing_works(short, max_records=None, time_limit=time_limit)
            for cobj in citing_iter:
                crec = _extract_work(cobj)
                upsert_work(con, crec)
                upsert_relation(con, crec.short_id, short, "cited_by")
                if crec.short_id not in visited:
                    visited.add(crec.short_id)
                    new_frontier.append(crec.short_id)
                    total_nodes += 1
                    if total_nodes >= max_nodes:
                        con.commit()
                        return
            con.commit()
        frontier = new_frontier
        if not frontier:
            break

# -----------------------------
# CLI (argparse)
# -----------------------------
def build_parser() -> argparse.ArgumentParser:
    # 父 parser：把 --db 放到每个子命令
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--db", required=False, default="openalex.db", help="SQLite 数据库文件路径（传到子命令）")

    p = argparse.ArgumentParser(description="OpenAlex 爬虫（修正版）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init-db", parents=[parent], help="初始化数据库")
    sp.set_defaults(func=cmd_init_db)

    sp = sub.add_parser("topic", parents=[parent], help="按主题搜索抓取")
    sp.add_argument("--query", required=True, help="搜索关键词（search）")
    sp.add_argument("--from-year", type=int, help="起始年份")
    sp.add_argument("--to-year", type=int, help="结束年份")
    sp.add_argument("--max-records", type=int, default=500, help="最多抓取数量")
    sp.add_argument("--time-limit", type=int, help="时间上限（秒）")
    sp.set_defaults(func=cmd_topic)

    sp = sub.add_parser("year-range", parents=[parent], help="按年份范围抓取")
    sp.add_argument("--from-year", type=int, required=True)
    sp.add_argument("--to-year", type=int, required=True)
    sp.add_argument("--max-records", type=int, default=500)
    sp.add_argument("--time-limit", type=int)
    sp.set_defaults(func=cmd_year_range)

    sp = sub.add_parser("author", parents=[parent], help="按作者抓取")
    sp.add_argument("--author-id", required=True, help="作者短 id（A...）或完整 URL")
    sp.add_argument("--max-records", type=int, default=500)
    sp.add_argument("--time-limit", type=int)
    sp.set_defaults(func=cmd_author)

    sp = sub.add_parser("work", parents=[parent], help="抓取单篇论文")
    sp.add_argument("--work-id", required=True, help="论文短 id（W...）或完整 URL")
    sp.set_defaults(func=cmd_work)

    sp = sub.add_parser("recurse", parents=[parent], help="递归抓取（引用 + 被引，BFS）")
    sp.add_argument("--seed-work-id", required=True, help="起始论文短 id（W...）或完整 URL")
    sp.add_argument("--depth", type=int, default=1, help="BFS 层数（>=1）")
    sp.add_argument("--max-nodes", type=int, default=1000, help="最大节点数（包含起始论文）")
    sp.add_argument("--time-limit", type=int, help="时间上限（秒）")
    sp.set_defaults(func=cmd_recurse)

    return p

# -----------------------------
# Command implementations
# -----------------------------
def cmd_init_db(args):
    db = args.db
    init_db(db)
    print(f"Initialized DB at: {db}")

def cmd_topic(args):
    db = args.db
    con = sqlite3.connect(db)
    client = OpenAlexClient()
    it = client.search_topic(args.query, args.from_year, args.to_year, max_records=args.max_records, time_limit=args.time_limit)
    n = save_iter_to_db(con, it)
    print(f"Saved {n} works for topic '{args.query}' into {db}")
    con.close()

def cmd_year_range(args):
    db = args.db
    con = sqlite3.connect(db)
    client = OpenAlexClient()
    it = client.year_range(args.from_year, args.to_year, max_records=args.max_records, time_limit=args.time_limit)
    n = save_iter_to_db(con, it)
    print(f"Saved {n} works for years {args.from_year}-{args.to_year} into {db}")
    con.close()

def cmd_author(args):
    db = args.db
    con = sqlite3.connect(db)
    client = OpenAlexClient()
    it = client.by_author(args.author_id, max_records=args.max_records, time_limit=args.time_limit)
    n = save_iter_to_db(con, it)
    print(f"Saved {n} works for author {args.author_id} into {db}")
    con.close()

def cmd_work(args):
    db = args.db
    con = sqlite3.connect(db)
    client = OpenAlexClient()
    obj = client.by_work_id(args.work_id)
    rec = _extract_work(obj)
    upsert_work(con, rec)
    con.commit()
    print(f"Saved work {rec.short_id} into {db}")
    con.close()

def cmd_recurse(args):
    db = args.db
    con = sqlite3.connect(db)
    client = OpenAlexClient()
    recurse_from_seed(con, client, args.seed_work_id, depth=args.depth, max_nodes=args.max_nodes, time_limit=args.time_limit)
    print("Recursion finished.")
    con.close()

# -----------------------------
# Entrypoint
# -----------------------------
def main():
    parser = build_parser()
    args = parser.parse_args()
    # args has .db because parent added it to each subparser
    args.func(args)

if __name__ == "__main__":
    main()
