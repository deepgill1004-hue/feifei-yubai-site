# -*- coding: utf-8 -*-
r"""
indexnow.py -- 把網址通知 IndexNow（Bing／ChatGPT 搜尋／Copilot 等收錄管道）

key 檔放在站台根目錄 <KEY>.txt（內容＝KEY）。2026-10-24 起網站改用自有網域 sophieyubai.com（根目錄），
keyLocation 指到 https://sophieyubai.com/<KEY>.txt，送出的網址都必須在這個網域底下。

被誰呼叫（失敗只記 log、絕不讓上架失敗）：
  * weekly-linkedin-vocus\scripts\site_publish.py   新文章 push 成功後送「該篇＋文章列表＋首頁」
  * affiliate\affiliate_sync.py                      picks 頁 push 成功後送有變動的頁
手動：
  python scripts\indexnow.py --sitemap                 # 把 sitemap.xml 全部網址送出
  python scripts\indexnow.py --url <網址> [--url ...]   # 指定網址

紀錄：站台 clone 的上一層 indexnow.log（在 git 外，不會弄髒工作樹）。
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SITE_URL = "https://sophieyubai.com"
HOST = "sophieyubai.com"
KEY = "b41da6231eadc9ff7e23d34b01a687d1"
KEY_LOCATION = f"{SITE_URL}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
LOG = Path(__file__).resolve().parent.parent.parent / "indexnow.log"
MAX_URLS = 10000


def _log(msg: str) -> None:
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except OSError:
        pass


def submit(urls: list[str]) -> tuple[bool, str]:
    """送出網址。回傳 (成功?, 說明)；200/202 視為成功。任何例外都吞掉並記 log。"""
    try:
        seen: list[str] = []
        for u in urls:
            if u.startswith(SITE_URL + "/") and u not in seen:
                seen.append(u)
        if not seen:
            return False, "沒有可送的網址（必須在 " + SITE_URL + "/ 底下）"
        seen = seen[:MAX_URLS]
        payload = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": seen},
                             ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(ENDPOINT, data=payload, method="POST", headers={
            "Content-Type": "application/json; charset=utf-8", "User-Agent": "yubai-indexnow/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                code, body = r.status, r.read().decode("utf-8", errors="replace")[:200]
        except urllib.error.HTTPError as e:
            code, body = e.code, e.read().decode("utf-8", errors="replace")[:200]
        ok = code in (200, 202)
        msg = f"HTTP {code}｜{len(seen)} 條" + (f"｜{body}" if body.strip() else "")
        _log(("OK " if ok else "FAIL ") + msg + "｜" + ", ".join(seen[:3]) + (" …" if len(seen) > 3 else ""))
        return ok, msg
    except Exception as e:  # noqa: BLE001  IndexNow 掛了不能影響上架
        msg = f"{type(e).__name__}: {e}"
        _log("ERROR " + msg)
        return False, msg


def sitemap_urls(repo: Path) -> list[str]:
    return re.findall(r"<loc>([^<]+)</loc>", (repo / "sitemap.xml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import argparse
    ap = argparse.ArgumentParser(description="IndexNow 送出網址")
    ap.add_argument("--sitemap", action="store_true", help="送 sitemap.xml 全部網址")
    ap.add_argument("--url", action="append", default=[], help="指定網址（可重複）")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    us = list(a.url)
    if a.sitemap:
        us += sitemap_urls(Path(a.repo).resolve())
    ok, m = submit(us)
    print(("OK  " if ok else "FAIL ") + m)
    sys.exit(0 if ok else 1)
