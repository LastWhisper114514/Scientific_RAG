# src/ingestion/load_pwc.py
import gzip, json
from pathlib import Path
from typing import Dict, Iterable, List, Any
from src.utils.pretty import log, ok, warn, section, timer

# ---- ??:????????(?? JSON ??) ----
def _peek_first_nonspace_char_gz(path: str, max_read=8192) -> str:
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            buf = f.read(max_read)
        for ch in buf:
            if not ch.isspace():
                return ch
    except Exception:
        pass
    return ""

# ---- ??:????? ----
def _iter_jsonl_gz(path: str):
    log(f"reading(jsonl): {path}")
    scanned = parsed = yielded = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            scanned += 1
            try:
                obj = json.loads(line)
                parsed += 1
            except Exception:
                continue
            if isinstance(obj, dict):
                yielded += 1
                yield obj
    ok(f"scanned: {scanned:,} | parsed: {parsed:,} | yielded dicts: {yielded:,} from {Path(path).name}")

def _iter_json_array_gz(path: str):
    log(f"reading(array via ijson): {path}")
    try:
        import ijson
    except Exception:
        raise RuntimeError("??? JSON ??,???? ijson??? `pip install ijson`?")
    yielded = 0
    # ijson ?????????
    with gzip.open(path, "rb") as f:
        for obj in ijson.items(f, "item"):
            if isinstance(obj, dict):
                yielded += 1
                yield obj
    ok(f"yielded dicts: {yielded:,} from {Path(path).name}")

# ---- ??:???????? ----
def _read_any_json_gz(path: str) -> Iterable[Dict]:
    p = Path(path)
    if not p.exists():
        warn(f"missing file: {p}")
        return []
    first = _peek_first_nonspace_char_gz(str(p))
    if first == "[":
        return _iter_json_array_gz(str(p))
    else:
        return _iter_jsonl_gz(str(p))

def load_papers(raw_paths: Dict[str, str]) -> List[Dict[str, Any]]:
    section("Step 1/4  Load raw PWC JSON")

    # 1) ??:abstracts(????? sample ??)
    with timer("merge abstracts & metadata"):
        papers: List[Dict[str, Any]] = []

        def _title(x):    return (x.get("title") or "").strip()
        def _abstract(x): return (x.get("abstract") or "").strip()
        # URL:?? paper_url,?? url_abs/url_pdf
        def _url(x):      return (x.get("paper_url") or x.get("url_abs") or x.get("url_pdf") or "").strip()
        # ID:?? arxiv_id,?? openreview/nips
        def _pid(x):      return x.get("arxiv_id") or x.get("openreview_id") or x.get("nips_id") or ""

        for x in _read_any_json_gz(raw_paths.get("abstracts", "")):
            if not isinstance(x, dict):
                continue
            t, a = _title(x), _abstract(x)
            if not (t or a):
                continue
            papers.append({
                "title": t,
                "abstract": a,
                "url": _url(x),
                "tasks": x.get("tasks") or [],
                "methods": x.get("methods") or [],
                "datasets": x.get("datasets") or [],
                "code": "",  # ???,?? links ??
                "source_id": _pid(x),
            })
        ok(f"abstract records kept: {len(papers):,}")

    # 2) links-between-papers-and-code:? repository
    links_path = raw_paths.get("links", "")
    if links_path:
        with timer("merge code repos from links"):
            # ??????:{paper_url, repo_url} ??? paper/url, repository/url
            linkmap = {}
            for l in _read_any_json_gz(links_path):
                if not isinstance(l, dict):
                    continue
                purl = l.get("paper_url") or (l.get("paper") or {}).get("url")
                rurl = l.get("repo_url")  or (l.get("repository") or {}).get("url") or l.get("code")
                if purl and rurl:
                    linkmap.setdefault(purl, set()).add(rurl)
            hit = 0
            for rec in papers:
                if rec["url"] in linkmap and not rec["code"]:
                    rec["code"] = sorted(list(linkmap[rec["url"]]))[0]
                    hit += 1
            ok(f"code repo linked for {hit:,} papers")

    # 3) ????(methods/datasets/eval)?????????,????
    for name in ("methods", "datasets", "eval"):
        p = raw_paths.get(name, "")
        if p:
            _ = list(_read_any_json_gz(p))  # ??????,????
    return papers
