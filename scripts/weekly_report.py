#!/usr/bin/env python3
# 蘇菲餘白官網週報｜出檔程式（2026-11-24）
# 週報頁（私人連結）：https://claude.ai/artifact/PBp6k3KarEdkM5TVSPcKMv（最上面 6 個數字）
#
# 讀（都在「週報資料夾」，預設是網站 repo 旁邊的「蘇菲餘白週報」，不放進 repo、不公開）：
#   data/<週次>/browser.json   Search Console、Bing、Cloudflare 的數字（每週二排程在蘇菲已登入的 Chrome 讀）
#   data/<週次>/local.json     可省略：LINE 按鈕點擊、IG／FB／LINE 核對結果
#   ai_panel/<YYYY-MM>.json    每月第一個週二的 AI 引用面板結果
#   actions.json               每週 3 件事（行動追蹤）；notes/<週次>.json 可覆寫結論文字
# 另外每次現算網站 repo 本身：網站地圖網址數、robots.txt、上架檢查、結構化資料、文章清單、20 題（data/ai_questions.json）
# 寫：out/dash_<週次>.json（週報頁讀的檔，裡面附本程式原文供查核）
#
# 用法：python -X utf8 scripts/weekly_report.py [--week 2026-W48] [--data ../蘇菲餘白週報] [--repo 網站 repo]
#       不給 --week＝上一個完整的週（週一～週日）。程式放在 repo 外面時用 --repo 指到網站 repo；
#       repo 裡還沒有 data/ai_questions.json 時，改讀跟程式放在一起的 ai_questions.json。
# 規則：收不到的欄位是 null，原因寫在 *_state；不補猜的數字。門檻是起始值，累積 4 週真實數據後調一次並寫進週報。
#
# browser.json 格式：
#   {"collected_at": "2026-12-01 10:20",
#    "gsc": {"state": "ok" 或原因, "through": "2026-11-29", "clicks": 0, "impressions": 0,
#            "queries": [{"query", "clicks", "impressions", "position"}], "rows_capped": false,
#            "pages": [{"page", "clicks", "impressions"}], "daily": [{"date", "clicks", "impressions"}],
#            "index": {"indexed": 0, "not_indexed": 0, "reasons": []}, "sitemap": {"state", "last_read", "discovered"}},
#    "bing": {"state": "ok" 或原因, "clicks": 0, "impressions": 0, "note": ""},
#    "cf":   {"state": "ok" 或原因, "visits": 0, "pageviews": 0, "referers": [{"ref", "visits"}],
#             "referers_complete": true, "pages": [{"path", "visits"}], "note": ""}}
# local.json 格式：{"line": {"state": "ok" 或原因, "clicks": 文末點擊, "total": 全站 LINE 點擊, "by_pos": {"end": 0, "fab": 0, …},
#                           "friends": LINE 官方帳號好友數或 null, "collected_at": "…"},
#                  "channels": [{"item", "value", "state": "ok|wait|bad", "note", "checked"}]}
#   line 的數字來自 LINE 按鈕點擊計數的接收端 /stats（資料週週一～週日加總；pos=end 是文末），見 data/README.md
# ai_panel/<YYYY-MM>.json：{"month": "2026-12", "asked_at": "...", "results": [{"id": "q01", "platform": "chatgpt|perplexity|google_ai|copilot",
#                  "cited": true, "cited_page": "letters/...", "top3": ["...", "...", "..."], "has_ai_answer": true, "skipped": false, "note": ""}]}
import argparse, datetime, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = "https://sophieyubai.com/"
LAUNCH = datetime.date(2026, 10, 24)   # 自有網域上線（成長儀表板記載）
PHASES = [  # (代號, 名稱, 期間文字, 開始, 結束)
    ("1", "先被收錄", "10/24～11/21", datetime.date(2026, 10, 24), datetime.date(2026, 11, 21)),
    ("2", "被看見", "11/22～1 月", datetime.date(2026, 11, 22), datetime.date(2027, 1, 31)),
    ("3", "被點、被引用、帶來 LINE 好友", "2 月～4 月", datetime.date(2027, 2, 1), datetime.date(2027, 4, 30)),
]
R1_MIN_IMPR, R1_POS = 20, (8, 20)               # 臨門一腳：一週曝光 20 次以上、平均名次 8～20
R2_POS_MAX, R2_CTR, R2_MIN_IMPR = 10, 0.02, 20  # 排進前十卻很少人點：名次 1～10、點閱率 < 2%
R4_DROP = 5                                     # 名次掉 5 名以上、連續兩週
R5_UNINDEXED = 0.10                             # 送出的頁超過一成沒收錄
R3_COVER = 0.6                                  # 搜尋詞的字有六成以上出現在某一篇標題裡，才算「有文章」
AI_REF = ("chatgpt.com", "chat.openai.com", "perplexity.ai", "gemini.google.com", "copilot.microsoft.com",
          "edgeservices.bing.com", "claude.ai", "you.com", "phind.com", "poe.com", "chat.deepseek.com", "grok.com", "meta.ai")
PLATFORMS = ("chatgpt", "perplexity", "google_ai", "copilot")
STATUSES = ("待做", "進行中", "已上線", "已讀回", "沒做到", "暫緩")
RULES = {
    "R1": ("臨門一腳的詞", "問句寫成小標或常見問題、第一段直接回答、從欄目頁和相關文章加站內連結、補一個具體數字或對照表"),
    "R2": ("排進前十卻很少人點", "改搜尋標題和描述：問句開頭，把讀者在意的數字或答案放進去"),
    "R3": ("有人搜、我們沒文章", "新題目排進產線的選題"),
    "R4": ("名次掉 5 名以上（連續兩週）", "查原因：內容過時、別人寫得更完整、網頁出錯；先修再觀察"),
    "R5": ("沒被收錄", "看「網頁」報表的原因；「替代頁面（有適當的標準標記）」是正常的，其他原因修好後要求重新收錄"),
    "R6": ("AI 沒引用（連續兩個月）", "對照被引用的那頁：40～60 字就答完、有官方來源與作者資歷；照著補強那篇"),
}


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def week_dates(tag):
    y, w = tag.split("-W")
    mon = datetime.date.fromisocalendar(int(y), int(w), 1)
    return mon, mon + datetime.timedelta(days=6)


def shift_week(tag, n):
    i = (week_dates(tag)[0] + datetime.timedelta(days=7 * n)).isocalendar()
    return f"{i[0]}-W{i[1]:02d}"


def rng(tag):
    mon, sun = week_dates(tag)
    return f"{mon.month}/{mon.day}–{sun.month}/{sun.day}"


def md(s):
    m = re.match(r"^\d{4}-(\d{2})-(\d{2})", str(s or ""))
    return f"{int(m.group(1))}/{int(m.group(2))}" if m else (s or "")


def bigrams(s):
    s = re.sub(r"[\s\W_]+", "", str(s).lower())
    return {s[i:i + 2] for i in range(len(s) - 1)} or ({s} if s else set())


# ---------- 網站本身（每次現算） ----------
def site_facts():
    sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sm)
    robots = (REPO / "robots.txt").read_text(encoding="utf-8")
    allow_all = bool(re.search(r"User-agent:\s*\*\s*\n\s*Allow:\s*/\s*$", robots, re.M)) and "Disallow: /" not in robots
    blocks = ok = 0
    for f in REPO.rglob("*.html"):
        if ".git" in f.parts:
            continue
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', f.read_text(encoding="utf-8", errors="replace"), re.S):
            blocks += 1
            try:
                json.loads(b)
                ok += 1
            except ValueError:
                pass
    arts = load(REPO / "letters" / "articles.json") or []
    line_ok = sum(1 for a in arts if (REPO / "letters" / a["f"]).exists()
                  and "line.me/R/ti/p/" in (REPO / "letters" / a["f"]).read_text(encoding="utf-8"))
    home = (REPO / "index.html").read_text(encoding="utf-8")
    cfg = load(REPO / "data" / "analytics.json") or {}
    run = subprocess.run([sys.executable, "-B", str(REPO / "scripts" / "yubai_site.py"), "check"],
                         capture_output=True, text=True, encoding="utf-8")
    lines = (run.stdout + run.stderr).splitlines()
    warns = [l for l in lines if l.startswith("WARN")]
    errs = [l for l in lines if l.startswith("ERROR")]
    cat = {"標籤只部分出現在內文": sum("標籤" in l for l in warns), "網址含亂碼或 sophie-note": sum("sophie-note" in l for l in warns),
           "缺人臉偵測套件（OpenCV）": sum("OpenCV" in l for l in warns), "還沒裝訪客統計": sum("還沒裝訪客統計" in l for l in warns),
           "還沒接上 LINE 點擊計數": sum("LINE 按鈕點擊計數" in l for l in warns)}
    cat["其他"] = len(warns) - sum(cat.values())
    return {"sitemap_urls": len(locs), "robots_allow_all": allow_all, "ld_blocks": blocks, "ld_ok": ok,
            "articles": len(arts), "line_ok": line_ok, "cf_beacon": "static.cloudflareinsights.com/beacon" in home,
            "line_endpoint": bool(str(cfg.get("line_click_endpoint") or "").strip()), "click_js_live": "yubai-click.js" in home,
            "check_errors": len(errs), "check_warns": len(warns), "warn_cat": cat, "read_on": datetime.date.today().isoformat()}


def page_index():
    """每篇文章與主題頁的標題字，判斷搜尋詞有沒有對應文章"""
    pages = {}
    for a in load(REPO / "letters" / "articles.json") or []:
        pages["letters/" + a["f"]] = bigrams(a.get("t", ""))
    for f in list((REPO / "topics").glob("*.html")) + list((REPO / "columns").glob("*.html")):
        m = re.search(r"<title>(.*?)</title>", f.read_text(encoding="utf-8"), re.S)
        if m:
            pages[f"{f.parent.name}/{f.name}"] = bigrams(m.group(1).split("｜")[0])
    return pages


def best_page(query, pidx):
    qb = bigrams(query)
    best = (0.0, None)
    for p, b in pidx.items():
        s = len(qb & b) / len(qb) if qb else 0
        if s > best[0]:
            best = (s, p)
    return best


# ---------- 各來源 ----------
def gsc_week(br):
    g = (br or {}).get("gsc") or {}
    st = g.get("state") or "沒收到：這週沒有 Search Console 數據檔"
    base = {"state": st, "index": g.get("index") or {}, "sitemap": g.get("sitemap") or {}, "through": g.get("through"),
            "queries": [], "clicks": None, "impressions": None, "rows_capped": False}
    if st != "ok":
        return base
    qs = []
    for q in g.get("queries") or []:
        imp = q.get("impressions") or 0
        if imp <= 0 or q.get("position") in (None, ""):
            continue
        qs.append({"query": q["query"], "clicks": q.get("clicks") or 0, "impressions": imp,
                   "ctr": (q.get("clicks") or 0) / imp, "position": float(q["position"])})
    base.update(clicks=g.get("clicks"), impressions=g.get("impressions"), queries=qs, rows_capped=bool(g.get("rows_capped")))
    return base


def cf_week(br):
    c = (br or {}).get("cf") or {}
    st = c.get("state") or "沒收到：這週沒有 Cloudflare 數據檔"
    out = {"state": st, "visits": c.get("visits"), "ai": None, "ai_min": None, "refs": [], "pages": []}
    if st != "ok":
        return out
    refs = c.get("referers") or []
    complete = bool(c.get("referers_complete")) or sum(r.get("visits") or 0 for r in refs) == (c.get("visits") or 0)
    ai = [r for r in refs if any(d in str(r.get("ref", "")).lower() for d in AI_REF)]
    if complete:
        out["ai"] = sum(r["visits"] for r in ai)
    else:   # 來源清單沒讀完整：看到的才算，畫面寫「至少」
        out["ai_min"] = sum(r["visits"] for r in ai)
    out["refs"] = [{"kind": "ai" if r in ai else "ref", "name": r.get("ref", ""), "visits": r.get("visits")} for r in refs]
    out["pages"] = [{"kind": "page", "name": p.get("path", ""), "visits": p.get("visits")} for p in (c.get("pages") or [])]
    return out


def line_week(local, facts):
    ln = (local or {}).get("line") or {}
    if facts["line_endpoint"]:
        default = "這週沒讀到：LINE 按鈕點擊的接收端 /stats 沒收"
    else:
        default = "還沒接上：data/analytics.json 的 line_click_endpoint 是空的（接收端要在蘇菲電腦上部署）"
    st = ln.get("state") or default
    ok = st == "ok"
    return {"state": st, "clicks": ln.get("clicks") if ok else None, "total": ln.get("total") if ok else None, "friends": ln.get("friends")}


def collected(br, key):
    return md(((br or {}).get(key) or {}).get("collected_at") or (br or {}).get("collected_at") or "")


def week_row(tag, data_dir, facts):
    br = load(data_dir / "data" / tag / "browser.json")
    local = load(data_dir / "data" / tag / "local.json")
    g, c, ln = gsc_week(br), cf_week(br), line_week(local, facts)
    b = (br or {}).get("bing") or {}
    q = g["queries"]
    idx = g["index"]
    row = {"week": tag, "range": rng(tag),
           "search_clicks": g["clicks"], "search_impressions": g["impressions"],
           "top10_terms": sum(1 for x in q if round(x["position"]) <= 10) if g["state"] == "ok" else None,
           "top20_terms": sum(1 for x in q if round(x["position"]) <= 20) if g["state"] == "ok" else None,
           "terms_with_impressions": len(q) if g["state"] == "ok" else None,
           "ai_visitors": c["ai"], "ai_visitors_min": c["ai_min"], "line_clicks": ln["clicks"], "line_total": ln["total"],
           "indexed": idx.get("indexed") if g["state"] == "ok" else None, "submitted": facts["sitemap_urls"],
           "visits": c["visits"] if c["state"] == "ok" else None,
           "gsc_state": g["state"], "bing_state": b.get("state") or "沒收到：這週沒有 Bing 數據檔", "cf_state": c["state"], "line_state": ln["state"],
           "gsc_through": g["through"] if g["state"] == "ok" else None,
           "gsc_collected": collected(br, "gsc"), "cf_collected": collected(br, "cf"),
           "line_collected": md(((local or {}).get("line") or {}).get("collected_at") or ""), "sitemap_read": md(facts["read_on"])}
    return row, {"gsc": g, "cf": c, "line": ln, "bing": b, "local": local, "br": br}


def daily_rows(tag, weeks, data_dir):
    _, sun = week_dates(tag)
    start = sun - datetime.timedelta(days=27)
    gsc = {}
    for t in sorted(weeks):
        for d in (((load(data_dir / "data" / t / "browser.json") or {}).get("gsc") or {}).get("daily") or []):
            gsc[d["date"]] = d
    rows = []
    for i in range(28):
        d = start + datetime.timedelta(days=i)
        g = gsc.get(d.isoformat())
        rows.append({"date": d.isoformat(), "d": f"{d.month}/{d.day}", "mon": d.weekday() == 0,
                     "search_clicks": g.get("clicks") if g else None, "search_impressions": g.get("impressions") if g else None})
    return rows


def rank_dist(g):
    if g["state"] != "ok":
        return []
    buckets = [("前 3 名", 1, 3), ("4～10 名", 4, 10), ("11～20 名", 11, 20), ("21～50 名", 21, 50), ("50 名以後", 51, 10 ** 6)]
    return [{"bucket": n, "terms": sum(1 for q in g["queries"] if lo <= round(q["position"]) <= hi), "order": i + 1}
            for i, (n, lo, hi) in enumerate(buckets)]


def ai_months(data_dir):
    out = []
    for p in sorted((data_dir / "ai_panel").glob("*.json")) if (data_dir / "ai_panel").exists() else []:
        j = load(p)
        if j and j.get("results"):
            out.append((j.get("month", p.stem), j["results"]))
    return out


def rule_hits(tag, weeks, g, row, pidx, months, questions):
    hits = []
    for q in g["queries"]:
        pos, imp = q["position"], q["impressions"]
        s, page = best_page(q["query"], pidx)
        mapped = page if s >= R3_COVER else None
        base = {"query": q["query"], "page": mapped, "position": round(pos, 1), "impressions": imp, "clicks": q["clicks"], "ctr": round(q["ctr"], 4), "extra": ""}
        if imp >= R1_MIN_IMPR and R1_POS[0] <= round(pos) <= R1_POS[1]:
            hits.append(dict(base, rule="R1"))
        if round(pos) <= R2_POS_MAX and imp >= R2_MIN_IMPR and q["ctr"] < R2_CTR:
            hits.append(dict(base, rule="R2"))
        if s < R3_COVER:
            hits.append(dict(base, rule="R3", page=None))
    p1, p2 = weeks.get(shift_week(tag, -1)), weeks.get(shift_week(tag, -2))
    if p1 and p2 and p1["gsc"]["state"] == "ok" and p2["gsc"]["state"] == "ok":
        a = {q["query"]: q["position"] for q in p1["gsc"]["queries"]}
        b = {q["query"]: q["position"] for q in p2["gsc"]["queries"]}
        for q in g["queries"]:
            k = q["query"]
            if k in a and k in b and a[k] - b[k] >= R4_DROP and q["position"] - b[k] >= R4_DROP:
                s, page = best_page(k, pidx)
                hits.append({"rule": "R4", "query": k, "page": page if s >= R3_COVER else None, "position": round(q["position"], 1),
                             "impressions": q["impressions"], "clicks": q["clicks"], "ctr": round(q["ctr"], 4), "extra": f"兩週前第 {b[k]:.1f} 名"})
    if row["indexed"] is not None and row["submitted"]:
        miss = 1 - row["indexed"] / row["submitted"]
        if miss > R5_UNINDEXED:
            reasons = "；".join(g["index"].get("reasons") or [])
            hits.append({"rule": "R5", "query": "", "page": None, "position": None, "impressions": None, "clicks": None, "ctr": None,
                         "extra": f"{row['submitted'] - row['indexed']} 頁沒收錄（{miss:.0%}）" + (f"：{reasons}" if reasons else "")})
    if len(months) >= 2:
        (m1, a), (m0, b) = months[-2], months[-1]
        cited = lambda res, qid: any(r.get("cited") for r in res if r.get("id") == qid)
        for qq in questions:
            if not cited(a, qq["id"]) and not cited(b, qq["id"]):
                hits.append({"rule": "R6", "query": qq["q"], "page": qq["expect"], "position": None, "impressions": None,
                             "clicks": None, "ctr": None, "extra": f"{m1}、{m0} 都沒被引用"})
    order = {"R1": 0, "R2": 1, "R4": 2, "R5": 3, "R6": 4, "R3": 5}
    hits.sort(key=lambda h: (order[h["rule"]], -(h["impressions"] or 0)))
    for h in hits:
        h["rule_name"], h["suggestion"] = RULES[h["rule"]]
    return hits


def plan_actions(tag, hits, acts):
    """排下週（＝蘇菲週二看週報的這一週）的 3 件事；已排過就不重排；上週沒做完的順延"""
    nxt = shift_week(tag, 1)
    if any(a["week"] == nxt for a in acts):
        return []
    new = []
    for a in [a for a in acts if a["week"] == tag and a["status"] in ("待做", "進行中")]:
        if a["status"] == "待做":
            a["status"], a["evidence"] = "沒做到", (a.get("evidence", "") + " 到週二還沒做，順延到下週").strip()
        new.append(dict(a, id=f"{nxt}-{len(new) + 1}", week=nxt, status="待做", evidence="", carried=a["id"]))
    for h in hits:
        if len(new) >= 3:
            break
        if h["rule"] == "R3" and any(x["rule"].startswith("R3") for x in new):
            continue
        item = f"「{h['query']}」" + (f"→ {h['page']}" if h.get("page") else "") if h["query"] else h["rule_name"]
        new.append({"id": f"{nxt}-{len(new) + 1}", "week": nxt, "item": item, "change": h["suggestion"],
                    "rule": f"{h['rule']} {h['rule_name']}", "why": h.get("extra") or (f"第 {h['position']} 名、曝光 {h['impressions']}" if h.get("position") else ""),
                    "owner": "上架產線改稿｜蘇菲先點頭", "status": "待做", "evidence": "", "carried": ""})
    return new


def phases_rows(tag, weeks, row, facts, acts, months, today):
    rows_sorted = [weeks[k]["row"] for k in sorted(weeks)]
    ratio = row["indexed"] / row["submitted"] if row["indexed"] is not None and row["submitted"] else None
    recent = [a for a in acts if shift_week(tag, -4) < a["week"] <= tag and a["status"] != "暫緩"]
    done = sum(1 for a in recent if a["status"] == "已讀回")
    any_ai = [r["ai_visitors"] for r in rows_sorted if r["ai_visitors"] is not None]

    def sum4(field, end, n=4):
        vals = [r[field] for r in rows_sorted if r["week"] <= end][-n:]
        return sum(vals) if len(vals) == n and all(v is not None for v in vals) else None
    c_now, c_prev = sum4("search_clicks", tag), sum4("search_clicks", shift_week(tag, -4))
    l_now, l_prev = sum4("line_clicks", tag), sum4("line_clicks", shift_week(tag, -4))
    growth = lambda now, prev: None if now is None or prev in (None, 0) else round((now - prev) / prev * 100)
    cg, lg = growth(c_now, c_prev), growth(l_now, l_prev)
    ai_cited = len({r["id"] for r in months[-1][1] if r.get("cited")}) if months else None

    def r(ph, crit, target, cur, met, num=None, goal=None, show=None):
        pct = None if num is None or not goal else max(0.0, min(1.0, num / goal))
        return {"phase": ph, "criterion": crit, "target": target, "current": cur, "met": met, "num": num, "goal": goal,
                "pct": None if pct is None else round(pct, 3), "show": show if show is not None else ("—" if num is None else str(num))}
    t = row["terms_with_impressions"]
    return [
        r("1", "送出的頁被收錄", "9 成以上", f"{ratio:.0%}" if ratio is not None else "等 Search Console", None if ratio is None else ratio >= 0.9,
          None if ratio is None else round(ratio * 100), 90, None if ratio is None else f"{ratio:.0%}"),
        r("1", "有曝光的搜尋詞", "超過 100 個", (("至少 " if weeks[tag]["gsc"]["rows_capped"] else "") + str(t)) if t is not None else "等 Search Console",
          None if t is None else t > 100, t, 100),
        r("1", "沒有技術錯誤", "0 個", f"{facts['check_errors']} 個" if facts["check_errors"] else "0 個", facts["check_errors"] == 0,
          1 if facts["check_errors"] == 0 else 0, 1, "0 個" if facts["check_errors"] == 0 else f"{facts['check_errors']} 個"),
        r("2", "進前 20 的詞", "30 個", str(row["top20_terms"]) if row["top20_terms"] is not None else "等 Search Console",
          None if row["top20_terms"] is None else row["top20_terms"] >= 30, row["top20_terms"], 30),
        r("2", "進前 10 的詞", "10 個", str(row["top10_terms"]) if row["top10_terms"] is not None else "等 Search Console",
          None if row["top10_terms"] is None else row["top10_terms"] >= 10, row["top10_terms"], 10),
        r("2", "每週 3 件優化做完、讀回", "近 4 週全部", f"{done}/{len(recent)} 件" if recent else "還沒有行動",
          None if not recent else all(a["status"] == "已讀回" for a in recent), done if recent else None, len(recent) or None, f"{done}/{len(recent)}" if recent else None),
        r("2", "AI 來源的訪客", "開始出現", f"累計 {sum(any_ai)} 人" if any_ai else "等訪客統計", None if not any_ai else sum(any_ai) > 0,
          sum(any_ai) if any_ai else None, 1),
        r("3", "搜尋點擊每月成長", "近 4 週比前 4 週多", f"{c_now} 比 {c_prev}" if c_now is not None and c_prev is not None else "要 8 週數據",
          None if c_now is None or c_prev is None else c_now > c_prev, None if cg is None else max(cg, 0), None if cg is None else 100, None if cg is None else f"{cg:+d}%"),
        r("3", "AI 引用面板", "20 題至少 4 題有引用", f"{ai_cited}/20 題" if ai_cited is not None else "12/1 第一次問", None if ai_cited is None else ai_cited >= 4, ai_cited, 4),
        r("3", "文末 LINE 點擊每月成長", "近 4 週比前 4 週多", f"{l_now} 比 {l_prev}" if l_now is not None and l_prev is not None else "還沒有點擊計數",
          None if l_now is None or l_prev is None else l_now > l_prev, None if lg is None else max(lg, 0), None if lg is None else 100, None if lg is None else f"{lg:+d}%"),
    ]


def ai_panel_rows(questions, months):
    if not months:
        return [{"id": q["id"], "q": q["q"], "expect": q["expect"], **{p: "還沒問" for p in PLATFORMS}, "cited_n": None, "detail": ""} for q in questions], ""
    month, res = months[-1]
    cell, detail = {}, {}
    for r in res:
        v = ("跳過" if r.get("skipped") else "引用" if r.get("cited") else "沒有 AI 回答" if r.get("has_ai_answer") is False else "—")
        cell[(r["id"], r["platform"])] = v
        bits = []
        if r.get("cited") and r.get("cited_page"):
            bits.append("引用 " + r["cited_page"])
        if r.get("top3"):
            bits.append("前三：" + "、".join(r["top3"][:3]))
        if bits:
            detail.setdefault(r["id"], []).append({"chatgpt": "ChatGPT", "perplexity": "Perplexity", "google_ai": "Google", "copilot": "Copilot"}.get(r["platform"], r["platform"]) + "｜" + "；".join(bits))
    rows = []
    for q in questions:
        row = {"id": q["id"], "q": q["q"], "expect": q["expect"]}
        for p in PLATFORMS:
            row[p] = cell.get((q["id"], p), "沒問")
        row["cited_n"] = sum(1 for p in PLATFORMS if row[p] == "引用")
        row["detail"] = "｜｜".join(detail.get(q["id"], []))
        rows.append(row)
    return rows, month


def health_rows(facts, row, w):
    c = facts["warn_cat"]
    sm = w["gsc"]["sitemap"]
    return [
        {"item": "上架檢查", "value": f"{facts['check_errors']} 錯誤、{facts['check_warns']} 則提醒", "state": "ok" if facts["check_errors"] == 0 else "bad",
         "note": "、".join(f"{k} {v}" for k, v in c.items() if v)},
        {"item": "robots.txt", "value": "全開" if facts["robots_allow_all"] else "有擋", "state": "ok" if facts["robots_allow_all"] else "bad",
         "note": "Google、Bing、ChatGPT、Perplexity、Claude 的爬蟲都進得來" if facts["robots_allow_all"] else "檢查 robots.txt"},
        {"item": "網站地圖", "value": f"{facts['sitemap_urls']} 個網址" + (f"；Google 讀取{sm.get('state')}（{md(sm.get('last_read'))}）" if sm.get("state") else ""),
         "state": "ok", "note": f"{md(facts['read_on'])} 讀 repo 的 sitemap.xml"},
        {"item": "結構化資料", "value": f"{facts['ld_blocks']} 段，{'全部讀得懂' if facts['ld_ok'] == facts['ld_blocks'] else str(facts['ld_blocks'] - facts['ld_ok']) + ' 段壞掉'}",
         "state": "ok" if facts["ld_ok"] == facts["ld_blocks"] else "bad", "note": "影片的上架日期都帶台灣時區"},
        {"item": "Google 收錄", "value": f"{row['indexed']} / {row['submitted']}" if row["indexed"] is not None else "等 Search Console",
         "state": "ok" if row["indexed"] is not None else "wait", "note": "；".join(w["gsc"]["index"].get("reasons") or []) or (row["gsc_state"] if row["gsc_state"] != "ok" else "")},
        {"item": "Bing", "value": "有數據" if row["bing_state"] == "ok" else row["bing_state"].split("：")[0], "state": "ok" if row["bing_state"] == "ok" else "wait",
         "note": "" if row["bing_state"] == "ok" else row["bing_state"]},
        {"item": "訪客統計（Cloudflare）", "value": ("已裝" if facts["cf_beacon"] else "還沒裝") + (f"，{row['visits']} 次造訪" if row["visits"] is not None else ""),
         "state": "ok" if facts["cf_beacon"] and row["cf_state"] == "ok" else ("wait" if facts["cf_beacon"] else "bad"), "note": "" if row["cf_state"] == "ok" else row["cf_state"]},
        {"item": "文末加入 LINE 按鈕", "value": f"{facts['line_ok']}/{facts['articles']} 篇有", "state": "ok" if facts["line_ok"] == facts["articles"] else "bad",
         "note": ("點擊計數已接上" if facts["click_js_live"] else "點擊計數：網址已填，等 apply-theme 上線") if facts["line_endpoint"]
                 else "點擊計數還沒接上（接收端要在蘇菲電腦上部署）"},
    ]


def channel_rows(local):
    rows = list((local or {}).get("channels") or [])
    have = {r["item"] for r in rows}
    for item, note in (("IG @sophie.beautylab 個人簡介連結", "應該是 https://sophieyubai.com/"),
                       ("FB 粉專名稱", "只看不改"), ("FB 粉專「網站」欄", "只看不改"),
                       ("LINE 官方帳號好友數", "LINE 官方帳號後台")):
        if item not in have:
            rows.append({"item": item, "value": "還沒核對", "state": "wait", "note": note + "；要在蘇菲已登入的瀏覽器看", "checked": ""})
    return rows


def draft_text(tag, row, prev, facts, hits, need):
    s = []
    if row["gsc_state"] == "ok":
        s.append(f"Google 搜尋點擊 {row['search_clicks']}、曝光 {row['search_impressions']}，進前十的詞 {row['top10_terms']} 個")
    else:
        s.append("搜尋數字這週沒有收到（原因寫在每一格）")
    if row["ai_visitors"] is not None:
        s.append(f"AI 帶來 {row['ai_visitors']} 位訪客")
    s.append(f"網站本身 {facts['check_errors']} 錯誤、送出 {row['submitted']} 頁")
    head = "；".join(s) + "。"
    more = []
    if hits:
        more.append(f"判讀規則抓到 {len(hits)} 筆，前 3 筆排進本週行動。")
    if row["indexed"] is not None:
        more.append(f"已收錄 {row['indexed']} / {row['submitted']} 頁。")
    return head, head + ("" if not more else " " + " ".join(more))


def main():
    global REPO
    ap = argparse.ArgumentParser()
    ap.add_argument("--week")
    ap.add_argument("--data")
    ap.add_argument("--collected", default="")
    ap.add_argument("--repo", default=str(REPO))
    a = ap.parse_args()
    REPO = Path(a.repo).resolve()
    data_dir = Path(a.data).resolve() if a.data else REPO.parent / "蘇菲餘白週報"
    today = datetime.date.today()
    tag = a.week or shift_week(f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}", -1)
    facts = site_facts()
    pidx = page_index()
    questions = (load(REPO / "data" / "ai_questions.json") or load(Path(__file__).resolve().parent / "ai_questions.json") or {}).get("questions") or []
    weeks = {}
    for d in sorted((data_dir / "data").glob("????-W??")) if (data_dir / "data").exists() else []:
        if d.name <= tag:
            r, w = week_row(d.name, data_dir, facts)
            weeks[d.name] = dict(w, row=r)
    if tag not in weeks:
        r, w = week_row(tag, data_dir, facts)
        weeks[tag] = dict(w, row=r)
    keys = sorted(weeks)
    for i, k in enumerate(keys):   # 跟上週比
        cur, prev = weeks[k]["row"], (weeks[keys[i - 1]]["row"] if i and keys[i - 1] == shift_week(k, -1) else None)
        for f in ("search_clicks", "search_impressions", "top10_terms", "ai_visitors", "line_clicks", "indexed"):
            if f in ("search_clicks", "search_impressions"):
                cur[f + "_chg"] = None if not prev or cur[f] is None or not prev[f] else round((cur[f] - prev[f]) / prev[f] * 100)
            else:
                cur[f + "_chg"] = None if not prev or cur[f] is None or prev[f] is None else cur[f] - prev[f]
    w = weeks[tag]
    row = w["row"]
    months = ai_months(data_dir)
    acts = load(data_dir / "actions.json") or []
    hits = rule_hits(tag, weeks, w["gsc"], row, pidx, months, questions)
    new = plan_actions(tag, hits, acts)
    if new:
        acts += new
        (data_dir / "actions.json").parent.mkdir(parents=True, exist_ok=True)
        (data_dir / "actions.json").write_text(json.dumps(acts, ensure_ascii=False, indent=2), encoding="utf-8")
    nxt = shift_week(tag, 1)
    act_rows = [dict(x, when="本週" if x["week"] == nxt else "上週") for x in acts if x["week"] in (tag, nxt)]
    ph = next((p for p in PHASES if today <= p[4]), PHASES[-1])
    notes = load(data_dir / "notes" / f"{tag}.json") or {}
    head, concl = draft_text(tag, row, None, facts, hits, notes.get("need_you"))
    ai_rows, ai_month = ai_panel_rows(questions, months)
    mon_note = load(data_dir / "notes" / f"{today:%Y-%m}.json") or {}
    report = {"week": tag, "range": rng(tag), "plan_week": nxt, "plan_range": rng(nxt),
              "n_week": (week_dates(tag)[0] - (LAUNCH - datetime.timedelta(days=LAUNCH.weekday()))).days // 7 + 1,
              "headline": notes.get("headline") or head, "conclusion": notes.get("conclusion") or concl,
              "need_you": notes.get("need_you") or "無", "phase": ph[0], "phase_name": ph[1], "phase_span": ph[2], "ai_month": ai_month,
              "month_summary": mon_note.get("summary", ""), "month_worked": mon_note.get("worked", ""),
              "month_not_worked": mon_note.get("not_worked", ""), "month_next": mon_note.get("next", ""),
              "collected_at": a.collected or (w["br"] or {}).get("collected_at") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
              "repo_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
    out = {
        "week": tag,
        "weekly": [weeks[k]["row"] for k in sorted(weeks, reverse=True)],
        "daily": daily_rows(tag, weeks, data_dir),
        "report": [report],
        "actions": act_rows,
        "opportunities": [{k: h.get(k) for k in ("rule", "rule_name", "query", "page", "position", "impressions", "clicks", "ctr", "suggestion", "extra")} for h in hits[:30]],
        "rank_dist": rank_dist(w["gsc"]),
        "traffic": sorted(w["cf"]["refs"], key=lambda r: (r["kind"] != "ai", -(r["visits"] or 0))) + w["cf"]["pages"][:10],
        "ai_panel": ai_rows,
        "health": health_rows(facts, row, w),
        "channels": channel_rows(w["local"]),
        "phases": phases_rows(tag, weeks, row, facts, acts, months, today),
        "meta": [{"label": "weekly_report.py", "value": Path(__file__).read_text(encoding="utf-8"), "type": "code", "lang": "python"},
                 {"label": "Input", "value": f"{data_dir.name}/data/{tag}/browser.json、local.json；ai_panel/*.json；actions.json；notes/；"
                                              f"網站 repo（{report['repo_commit']}）的 sitemap.xml、robots.txt、上架檢查、letters/articles.json、data/ai_questions.json"}],
    }
    (data_dir / "out").mkdir(parents=True, exist_ok=True)
    dst = data_dir / "out" / f"dash_{tag}.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    r = row
    print(f"{tag}（{rng(tag)}）→ {dst}")
    print(f"  搜尋點擊 {r['search_clicks']}｜曝光 {r['search_impressions']}｜前十 {r['top10_terms']}｜AI 訪客 {r['ai_visitors']}"
          f"｜LINE 點擊 {r['line_clicks']}｜收錄 {r['indexed']}/{r['submitted']}")
    print(f"  來源：GSC {r['gsc_state']}｜Bing {r['bing_state']}｜Cloudflare {r['cf_state']}｜LINE {r['line_state']}")
    print(f"  網站：{facts['check_errors']} 錯誤、{facts['check_warns']} 提醒｜結構化資料 {facts['ld_ok']}/{facts['ld_blocks']}｜判讀規則 {len(hits)} 筆｜新排行動 {len(new)} 件")


if __name__ == "__main__":
    main()
