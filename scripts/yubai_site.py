# -*- coding: utf-8 -*-
r"""
yubai_site.py -- 蘇菲餘白網站版型的唯一來源（C 版：雜誌底＋電影章節，2026-10-12 起）

負責：
  * 每一頁的 <head> 樣式、頁首、頁尾、動態腳本（theme_page）
  * 首頁 index.html 與文章列表 letters/index.html：每次從 letters/*.html 文章頁重新產生（build_indexes）
  * 文章主視覺自動轉 WebP（ensure_webp）
  * 機器可讀層：JSON-LD（文章 BlogPosting／首頁 WebSite+Organization／關於頁 AboutPage+Person，包在
    <!--yubai:ld--> 區塊內，theme_page 每次重產）與 llms.txt（render_llms_txt）
  * YouTube 短影片（2026-10-24 起）：資料只讀 data/videos.json；有對應文章的頁面嵌入影片＋VideoObject，
    另產影片總覽 videos.html 並確保它在 sitemap.xml 裡。改了 videos.json 要再跑一次 apply-theme

被誰呼叫：
  * weekly-linkedin-vocus\scripts\site_publish.py（每篇新文章上架）
  * 手動：python scripts\yubai_site.py apply-theme [--repo <站台 clone>]   # 全站重套版型＋JSON-LD＋llms.txt（可重複執行）
  * 手動：python scripts\yubai_site.py llms [--repo <站台 clone>]          # 只重產 llms.txt

改版型只改這支＋assets/yubai.css／yubai-home.css／yubai.js，不要回頭改各頁 HTML。
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
from datetime import date
from pathlib import Path

SITE_URL = "https://deepgill1004-hue.github.io/feifei-yubai-site"
LINE_URL = "https://line.me/R/ti/p/@371arhqu"
YT_CHANNEL = "https://www.youtube.com/channel/UCq-gFBlAjGaeJ6UAzMXzuyw"
FB_PAGE = "https://www.facebook.com/profile.php?id=100080504551842"
BRAND = "蘇菲餘白"
# 對外定位句：首頁、關於頁、llms.txt 三處用字完全一致（2026-10-20 協調員指定）；FB／YouTube 簡介第一句請貼同一句
POSITIONING = ("蘇菲餘白專注大健康與自費醫美，由護理師、心臟醫材、醫美營運出身的蘇菲，"
               "把複雜的健康與療程資訊翻成一般人看得懂的判斷。")
ASSET_VER = "20261024c"
FOOTER_NOTE = "內容僅供衛教與消費判斷參考，不取代醫師診療或個別法律意見。"
# 文章列表的主題篩選鈕：（顯示文字, 關鍵字以 | 分隔，比對標題＋摘要）
CHIPS = [
    ("玻尿酸", "玻尿酸|填充|Filler|filler"),
    ("肉毒", "肉毒|Botox"),
    ("電波・音波", "電波|音波|鳳凰|海芙|Thermage|Ultherapy|Morpheus"),
    ("雷射・皮秒", "雷射|皮秒|斑|ILIB"),
    ("再生・膠原", "再生|PN|PRP|外泌體|膠原|舒顏萃|洢蓮絲|Profhilo|晶亮瓷|微晶瓷"),
    ("減重・GLP-1", "GLP|減重|瘦瘦針|體重|肥胖"),
    ("抗老・長壽", "抗老|長壽|老化|更年期|停經|荷爾蒙|骨質|疲勞"),
    ("手術・整形", "手術|隆乳|隆鼻|鼻|拉皮|整形|埋線|麻醉"),
    ("法規・消費", "法規|廣告|合約|預付|分期|消保|話術|價格|低價|個資|偷拍|病歷|同意書|規範"),
]

HOME_CARDS = 6            # 首頁「最新文章」除主打外再列幾篇
WEBP_MAX = 1600

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com" />'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,400;1,500'
         '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=Noto+Serif+TC:wght@500;700;900&amp;display=swap" rel="stylesheet" />')

esc = lambda s: html.escape(s, quote=True)  # noqa: E731

# 右下角浮動「加入 LINE」：全站每頁都有，跟著捲動（放在 footer 內，重套版型時一起換掉，不會重複）
LINE_FAB = ('<a class="y-line-fab" href="' + LINE_URL + '" rel="noopener" aria-label="加入蘇菲餘白官方 LINE">'
            '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="currentColor" d="M24 5C12.1 5 2.5 12.8 2.5 22.4c0 8.6 7.6 15.8 17.9 17.2.7.2 1.7.5 1.9 1.1.2.6.1 1.4.1 1.9l-.3 1.8c-.1.6-.4 2.2 1.9 1.2 2.3-1 12.3-7.3 16.8-12.4 3.1-3.4 4.6-6.9 4.6-10.8C45.5 12.8 35.9 5 24 5z"/>'
            '<text x="24" y="26.6" text-anchor="middle" font-size="10" font-weight="700" font-family="Arial, Helvetica, sans-serif" fill="#06C755">LINE</text></svg>'
            '<span>加入 LINE</span></a>')


# ---------------------------------------------------------------- 共用區塊

def head_block(p: str, home: bool = False) -> str:
    css = (f'<link rel="stylesheet" href="{p}assets/yubai.css?v={ASSET_VER}" />'
           f'<link rel="stylesheet" href="{p}assets/yubai-home.css?v={ASSET_VER}" />' if home else
           f'<link rel="stylesheet" href="{p}assets/styles-v2.css?v=20260503-2" />'
           f'<link rel="stylesheet" href="{p}assets/yubai.css?v={ASSET_VER}" />')
    icons = (f'<link rel="icon" href="{p}favicon.ico" sizes="any" />'
             f'<link rel="icon" type="image/png" href="{p}assets/icon-512.png" />'
             f'<link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png" />')
    return f"<!--yubai:head-->\n    {icons}\n    {FONTS}\n    {css}\n    <!--/yubai:head-->"


def header_block(p: str) -> str:
    # 手機版（≤900px、有 JS）：連結收進「選單」，LINE 鈕留在頁首；沒有 JS 時維持原本只露療程主題／文章的樣子
    return (f'<header class="site-header" aria-label="主要導覽">\n'
            f'      <a class="brand" href="{p}index.html" aria-label="回到首頁">{BRAND}</a>\n'
            f'      <div class="y-head-r"><nav id="y-nav"><a class="m-hide" href="{p}about.html">關於</a><a href="{p}treatments.html">療程主題</a>'
            f'<a href="{p}letters/index.html">文章</a><a class="m-hide" href="{p}videos.html">影片</a>'
            f'<a class="m-hide" href="{p}faq.html">FAQ</a>'
            f'<a class="m-hide" href="{p}consult.html">諮詢</a></nav>'
            f'<button class="y-menu-btn" type="button" aria-expanded="false" aria-controls="y-nav">選單</button>'
            f'<a class="nav-cta" href="{LINE_URL}" rel="noopener">加入 LINE</a></div>\n'
            f'    </header>')


def footer_block(p: str) -> str:
    return (f'<footer class="site-footer y-footer">\n'
            f'      <p class="footer-brand">{BRAND}</p>\n'
            f'      <nav class="footer-nav" aria-label="網站導覽"><a href="{p}about.html">關於</a><a href="{p}treatments.html">療程主題</a>'
            f'<a href="{p}letters/index.html">文章</a><a href="{p}videos.html">影片</a><a href="{p}faq.html">FAQ</a>'
            f'<a href="{p}consult.html">諮詢</a></nav>\n'
            f'      <p class="footer-links"><a href="{LINE_URL}" rel="noopener">官方 LINE</a>'
            f'<a href="{YT_CHANNEL}" rel="noopener">YouTube</a><a href="{FB_PAGE}" rel="noopener">Facebook</a>'
            f'<a href="{p}feed.xml">RSS</a></p>\n'
            f'      <p class="fine">{BRAND}｜{FOOTER_NOTE}</p>\n'
            f'      {LINE_FAB}\n'
            f'    </footer>')


def script_block(p: str) -> str:
    return f'<script src="{p}assets/yubai.js?v={ASSET_VER}" defer></script>'


# ---------------------------------------------------------------- 機器可讀層：JSON-LD

LD_RE = re.compile(r"\s*<!--yubai:ld-->.*?<!--/yubai:ld-->", re.S)
LOGO_URL = SITE_URL + "/assets/icon-512.png"
ABOUT_URL = SITE_URL + "/about.html"
AUTHOR_NAME = "蘇菲"
PERSON_ID = ABOUT_URL + "#sophie"
# 只能用 about.html 已經寫出來的事實；不加頭銜、年資、學歷、真名
ABOUT_PERSON_DESC = ("蘇菲的內容來自醫療、護理、醫療器材銷售與醫美營運現場的長期觀察，"
                     "把醫美療程原理、諮詢流程、常見話術、風險與預算拆開，讓消費者知道下一步該問什麼。")
SITE_DESC = "醫美判斷力與療程諮詢筆記：整理醫美療程、抗老選擇、診所諮詢與消費判斷。"


def _org() -> dict:
    return {"@type": "Organization", "name": BRAND, "url": SITE_URL + "/", "logo": LOGO_URL}


def _person_ref() -> dict:
    return {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR_NAME, "alternateName": BRAND, "url": ABOUT_URL}


def ld_block(objs: list[dict]) -> str:
    """把 JSON-LD 物件包進 <!--yubai:ld--> 標記區塊（小於符號一律轉 unicode 跳脫，不可能提早結束 script 標籤）。"""
    scripts = []
    for o in objs:
        js = json.dumps({"@context": "https://schema.org", **o}, ensure_ascii=False, separators=(",", ":"))
        scripts.append(f'<script type="application/ld+json">{js.replace("<", chr(92) + "u003c")}</script>')
    return "<!--yubai:ld-->\n    " + "\n    ".join(scripts) + "\n    <!--/yubai:ld-->"


def home_ld() -> str:
    return ld_block([
        {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/", "inLanguage": "zh-Hant",
         "description": SITE_DESC, "publisher": _org()},
        {**_org(), "description": POSITIONING, "sameAs": [LINE_URL, YT_CHANNEL, FB_PAGE]},
    ])


def _meta_content(text: str, attr: str, name: str) -> str:
    m = re.search(r'<meta\s+' + attr + r'="' + re.escape(name) + r'"\s+content="([^"]*)"', text)
    return html.unescape(m.group(1)).strip() if m else ""


_SITEMAP_CACHE: dict = {}


def _sitemap_lastmod(site_root: Path, url: str) -> str:
    sm = site_root / "sitemap.xml"
    if not sm.exists():
        return ""
    key = (str(sm), sm.stat().st_mtime_ns)
    if key not in _SITEMAP_CACHE:
        t = sm.read_text(encoding="utf-8")
        _SITEMAP_CACHE.clear()
        _SITEMAP_CACHE[key] = dict(re.findall(r"<loc>([^<]*)</loc>\s*<lastmod>([^<]*)</lastmod>", t))
    return _SITEMAP_CACHE[key].get(url, "")


def article_ld(text: str, page_path: Path, site_root: Path) -> list[dict]:
    meta = article_meta(page_path.name, text, site_root)
    if not meta:
        return []
    url = f"{SITE_URL}/letters/{page_path.name}"
    headline = meta["title"] or re.sub(r"[｜|]\s*" + BRAND + r"\s*$", "", _meta_content(text, "property", "og:title"))
    obj = {"@type": "BlogPosting", "headline": headline}
    desc = _meta_content(text, "name", "description")
    if desc:
        obj["description"] = desc
    # 日期只用頁面自己已有的（article:published_time／檔名日期／頁面顯示日期＝article_meta 同一套）；
    # 都沒有就不放 datePublished，dateModified 退而用 sitemap.xml 的 lastmod，再沒有就整個不放，不編
    pub = meta["date"]
    if pub:
        obj["datePublished"] = pub
        obj["dateModified"] = pub
    else:
        lm = _sitemap_lastmod(site_root, url)
        if lm:
            obj["dateModified"] = lm
    img = _meta_content(text, "property", "og:image")
    if img:
        obj["image"] = img if img.startswith("http") else f"{SITE_URL}/{img.lstrip('./')}"
    obj.update({"inLanguage": "zh-Hant", "mainEntityOfPage": {"@type": "WebPage", "@id": url}, "url": url,
                "author": _person_ref(), "publisher": _org()})
    return [obj]


def about_ld(text: str) -> list[dict]:
    desc = _meta_content(text, "name", "description")
    page = {"@type": "AboutPage", "name": "關於蘇菲", "url": ABOUT_URL, "inLanguage": "zh-Hant",
            "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"},
            "mainEntity": {"@id": PERSON_ID}}
    if desc:
        page["description"] = desc
    person = {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR_NAME, "alternateName": BRAND, "url": ABOUT_URL,
              "description": ABOUT_PERSON_DESC}
    return [page, person]


def ld_for_page(text: str, page_path: Path) -> str:
    """回傳該頁該有的 <!--yubai:ld--> 區塊；不需要的頁（列表、主題、轉址…）回空字串。"""
    parent = page_path.parent
    in_sub = parent.name in ("letters", "topics")
    root = parent.parent if in_sub else parent
    if not in_sub and page_path.name == "about.html":
        return ld_block(about_ld(text))
    if parent.name == "letters" and re.match(r"\d{3}", page_path.name):
        objs = article_ld(text, page_path, root)
        if objs:
            objs += [video_ld(v) for v in videos_for(root, f"letters/{page_path.name}")]
        return ld_block(objs) if objs else ""
    return ""


# ---------------------------------------------------------------- 圖片

def ensure_webp(src: Path) -> Path | None:
    """png/jpg 旁邊產生同名 .webp（長邊 ≤1600）；已存在且較新就沿用。沒有 Pillow 就回 None。"""
    if src.suffix.lower() == ".webp":
        return src if src.exists() else None
    if src.suffix.lower() not in (".png", ".jpg", ".jpeg") or not src.exists():
        return None
    dest = src.with_suffix(".webp")
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return dest
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(src).convert("RGB")
    im.thumbnail((WEBP_MAX, WEBP_MAX))
    im.save(dest, "WEBP", quality=80, method=6)
    return dest


IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")')


def swap_webp(text: str, page_dir: Path, make: bool) -> str:
    def repl(m: re.Match) -> str:
        src = m.group(2)
        if src.startswith(("http:", "https:", "data:")) or not re.search(r"\.(png|jpe?g)$", src, re.I):
            return m.group(0)
        target = (page_dir / urllib.parse.unquote(src)).resolve()
        webp = target.with_suffix(".webp")
        if make:
            ensure_webp(target)
        if webp.exists():
            return m.group(1) + re.sub(r"\.(png|jpe?g)$", ".webp", src, flags=re.I) + m.group(3)
        return m.group(0)
    return IMG_RE.sub(repl, text)


# ---------------------------------------------------------------- 套版型

def theme_page(text: str, p: str, page_path: Path | None = None, make_webp: bool = False,
               metas: list[dict] | None = None) -> str:
    """把任一頁換成新版型（可重複執行，結果不變）。沒有 site-header 的頁（轉址頁）原樣返回。"""
    if '<header class="site-header"' not in text:
        return text
    # head：拿掉舊樣式連結與上次套的區塊，再放新的
    text = re.sub(r"\s*<!--yubai:head-->.*?<!--/yubai:head-->", "", text, flags=re.S)
    text = re.sub(r'\s*<link rel="stylesheet" href="[^"]*assets/styles(?:-v2)?\.css[^"]*"\s*/?>', "", text)
    text = text.replace("</head>", f"    {head_block(p)}\n  </head>", 1)
    # 頁首、頁尾
    text = re.sub(r'<header class="site-header".*?</header>', lambda _: header_block(p), text, count=1, flags=re.S)
    text = re.sub(r'<footer class="site-footer.*?</footer>', lambda _: footer_block(p), text, count=1, flags=re.S)
    # 動態腳本
    text = re.sub(r'\s*<script src="[^"]*assets/yubai\.js[^"]*" defer></script>', "", text)
    text = text.replace("</body>", f"    {script_block(p)}\n  </body>", 1)
    # 文章／主題頁有電影感頁首：頁首透明
    dark = 'class="letter-masthead' in text

    def body_tag(m: re.Match) -> str:
        cls = re.search(r'class="([^"]*)"', m.group(0))
        classes = [c for c in (cls.group(1).split() if cls else []) if c != "y-dark-top"]
        if dark:
            classes.append("y-dark-top")
        return f'<body class="{" ".join(classes)}">' if classes else "<body>"
    text = re.sub(r"<body[^>]*>", body_tag, text, count=1)
    if page_path is not None:
        text = swap_webp(text, page_path.parent, make_webp)
        text = absolute_og(text, page_path)
        text = enhance_page(text, page_path, metas)
        # 機器可讀層：先拿掉上次的區塊再放新的（og:image 已是絕對網址之後才產，才抓得到正確圖址）
        text = LD_RE.sub("", text)
        block = ld_for_page(text, page_path)
        if block:
            text = text.replace("</head>", f"    {block}\n  </head>", 1)
    return text


def absolute_og(text: str, page_path: Path) -> str:
    """og:image 用相對路徑時，社群爬蟲抓不到縮圖：一律改成絕對網址。"""
    def repl(m: re.Match) -> str:
        src = m.group(2)
        if src.startswith(("http:", "https:")):
            return m.group(0)
        site_root = page_path.parent if page_path.parent.name not in ("letters", "topics") else page_path.parent.parent
        rel = (page_path.parent / src).resolve().relative_to(site_root.resolve()).as_posix()
        return m.group(1) + f"{SITE_URL}/{rel}" + m.group(3)
    return re.sub(r'(<meta property="og:image" content=")([^"]+)(")', repl, text)


# ---------------------------------------------------------------- 文章資料

def _strip(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def article_meta(name: str, text: str, repo: Path) -> dict | None:
    m = re.match(r"^(\d{3})", name)
    h1 = re.search(r"<h1>(.*?)</h1>", text, re.S)
    if not m or not h1 or name == "index.html":
        return None
    desc = DESC_RE.search(text)
    date = re.search(r'<meta property="article:published_time" content="(\d{4}-\d{2}-\d{2})', text)
    if not date:
        d2 = re.search(r"(20\d{2})(\d{2})(\d{2})\.html$", name) or re.search(
            r'<span>(20\d{2})\.(\d{2})\.(\d{2})</span>', text)
        date_s = f"{d2.group(1)}-{d2.group(2)}-{d2.group(3)}" if d2 else ""
    else:
        date_s = date.group(1)
    main = text[text.find("<main"):] if "<main" in text else text
    img = re.search(r'<figure class="letter-portrait">\s*<img src="([^"]+)"', main) or re.search(
        r'<img src="([^"]+)"', main)
    img_rel = None
    if img:
        target = (repo / "letters" / urllib.parse.unquote(img.group(1))).resolve()
        webp = target.with_suffix(".webp")
        use = webp if webp.exists() else target
        try:
            img_rel = urllib.parse.quote(use.relative_to(repo.resolve()).as_posix())
        except ValueError:
            img_rel = None
    title = _strip(h1.group(1))
    body = _strip(_body_region(text))
    cats = _score_cats(title, body)
    return {
        "file": name, "issue": m.group(1), "title": title,
        "desc": html.unescape(desc.group(1)) if desc else "", "date": date_s, "img": img_rel,
        "tags": _tags_of(text), "cats": cats, "col": _column_of(title, body),
    }


_META_CACHE: dict = {}


def collect(repo: Path, extra: dict[str, str] | None = None) -> list[dict]:
    metas = []
    for f in (repo / "letters").glob("*.html"):
        if extra and f.name in extra:
            continue
        st = f.stat()
        key = (str(f), st.st_mtime_ns, st.st_size)
        if key not in _META_CACHE:
            _META_CACHE[key] = article_meta(f.name, f.read_text(encoding="utf-8"), repo)
        if _META_CACHE[key]:
            metas.append(_META_CACHE[key])
    for k, v in (extra or {}).items():
        if a := article_meta(k, v, repo):
            metas.append(a)
    metas.sort(key=lambda a: (a["issue"], a["date"], a["file"]), reverse=True)
    return metas


# ---------------------------------------------------------------- 文章列表

def render_letters_index(metas: list[dict]) -> str:
    cards = []
    for a in metas:
        img = (f'<figure><img src="../{a["img"]}" alt="" loading="lazy" decoding="async" /></figure>'
               if a["img"] else "")
        date = a["date"].replace("-", ".")
        cards.append(
            f'            <article class="letter-item y-card">\n'
            f'              <a href="./{a["file"]}" aria-label="閱讀 {esc(a["title"])}">{img}\n'
            f'                <p class="y-meta">No.{a["issue"]}{" · " + date if date else ""}</p>'
            f'<h3>{html.escape(a["title"], quote=False)}</h3><p class="y-dek">{html.escape(a["desc"], quote=False)}</p>\n'
            f'              </a>\n'
            f'            </article>')
    n = len(metas)
    chips = '<button type="button" data-k="" aria-pressed="true">全部</button>' + "".join(
        f'<button type="button" data-k="{esc(k)}" aria-pressed="false">{label}</button>' for label, k in CHIPS)
    return f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>《蘇菲餘白》文章｜醫美判斷力筆記</title>
    <meta name="description" content="蘇菲餘白文章庫：每篇只拆一個醫美判斷題，從療程、預算、風險到診所話術，幫你把問題問對。" />
    <meta property="og:title" content="《蘇菲餘白》文章｜醫美判斷力筆記" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="{SITE_URL}/assets/sophie-lib/consult-listen-cup.jpg" />
    <link rel="canonical" href="{SITE_URL}/letters/" />
    <link rel="alternate" type="application/rss+xml" title="{BRAND}" href="../feed.xml" />
    {head_block("../")}
  </head>
  <body class="y-dark-top">
    {header_block("../")}
    <main>
      <section class="letter-masthead">
        <div class="section-inner letter-masthead-grid">
          <div>
            <p class="eyebrow">Sophie Yubai Journal</p>
            <h1>《蘇菲餘白》</h1>
            <p class="letter-dek">寫給醫美消費者的判斷力文章。每篇只拆一個問題：療程、預算、風險、診所話術，或進諮詢室前該問出口的那句話。</p>
            <div class="hero-actions">
              <a class="button primary" href="{LINE_URL}" rel="noopener">加入官方 LINE</a>
              <a class="button secondary" href="#letters">看全部 {n} 篇</a>
            </div>
          </div>
          <figure class="letter-portrait y-hide-m"><img src="../assets/sophie-lib/consult-listen-cup.webp" alt="蘇菲端著咖啡，坐在諮詢室裡聽諮詢者說話" /></figure>
        </div>
      </section>

      <section id="letters" class="section">
        <div class="section-inner">
          <div class="letters-heading">
            <h2>已發佈文章</h2>
            <p>共 {n} 篇，由新到舊排列。慢慢讀，<span class="nowrap">把醫美選擇從焦慮裡拿回來。</span></p>
          </div>
          <div class="y-toolbar">
            <label class="y-search"><span class="sr-only">搜尋文章</span><input type="search" placeholder="搜尋：玻尿酸、電波、價格…" autocomplete="off" /></label>
            <div class="y-chips" role="group" aria-label="主題篩選">{chips}</div>
            <div class="y-view" role="group" aria-label="版面"><button type="button" data-view="list" aria-pressed="false">小圖</button><button type="button" data-view="grid" aria-pressed="false">大圖</button></div>
            <p class="y-count" aria-live="polite"></p>
          </div>
          <div class="letter-list y-cards">
{chr(10).join(cards)}
          </div>
        </div>
      </section>
    </main>
    {footer_block("../")}
    {script_block("../")}
  </body>
</html>
"""


# ---------------------------------------------------------------- 首頁

TOPICS = [
    ("01", "鳳凰電波", "會緊，跟會拉不是同一件事。", "t-rf", "topics/thermage.html"),
    ("02", "音波拉提", "先問自己是鬆、凹、脂肪，還是骨架。", "t-hifu", "topics/ultherapy.html"),
    ("03", "玻尿酸填充", "臉不是牆壁，哪裡凹補哪裡，常是變腫的開始。", "t-ha", "topics/hyaluronic-acid.html"),
    ("04", "肉毒桿菌", "不是把表情關掉，是讓太用力的肌肉小聲一點。", "t-botox", "topics/botox.html"),
    ("05", "水光與膚質", "都叫水光，成分、層次與目的可能差很多。", "t-skin", "topics/skinbooster.html"),
]
VIDEOS = [
    ("v1", "四十歲一到臉就得送修？"),
    ("v2", "展示品很軟，放進去就一定自然？"),
    ("v3", "拉提還沒做，先被叫去減重？"),
    ("v4", "想要小臉，別連飽滿都刪掉"),
    ("v5", "做局部減脂，卻拿體重計驗收？"),
    ("v6", "今天能做，不等於今天要做"),
]
PATHS = [
    ("p-first", "第一次接觸醫美", "先建立判斷力，再決定要不要做", [
        ("做醫美前，先把判斷力找回來", "letters/001.html"),
        ("黑眼圈分三型，90 秒先自檢", "letters/002-dark-circles-three-types.html"),
        ("常見問題與諮詢前提醒", "faq.html")]),
    ("p-compare", "正在比較療程", "把療程拆成問題、期待、風險", [
        ("五大療程主題", "treatments.html"),
        ("玻尿酸不是補土", "topics/hyaluronic-acid.html"),
        ("音波不是小臉神器", "topics/ultherapy.html")]),
    ("p-help", "想有人幫忙整理", "把疑問變成帶得進診間的問題", [
        ("諮詢整理方式", "consult.html"),
        ("加入官方 LINE", LINE_URL),
        ("蘇菲餘白文章庫", "letters/index.html")]),
]
QUESTIONS = [
    "我真正想改善的是皮膚、輪廓、比例，還是疲態？",
    "這個療程改善的是質地、支撐、容量，還是肌肉動態？",
    "如果效果不如預期，有沒有修正或等待方案？",
    "恢復期、風險與術後照護，我真的能配合嗎？",
]
HERO_SLIDES = ["hero-clinic", "hero-window", "hero-night", "hero-city"]


def render_home(metas: list[dict]) -> str:
    h = lambda k: f"assets/home/{k}.webp"  # noqa: E731
    n = len(metas)
    feat, rest = (metas[0], metas[1:1 + HOME_CARDS]) if metas else (None, [])

    def jimg(a):
        return f'<figure><img src="{a["img"]}" alt="" loading="lazy" decoding="async" /></figure>' if a["img"] else "<figure></figure>"

    feature = ""
    if feat:
        feature = (f'<a class="feature reveal" href="letters/{feat["file"]}">\n      {jimg(feat)}\n'
                   f'      <div class="feature-body">\n'
                   f'        <p class="meta">No.{feat["issue"]} · {feat["date"].replace("-", ".")} · 最新</p>\n'
                   f'        <h3>{html.escape(feat["title"], quote=False)}</h3>\n'
                   f'        <span class="more">閱讀全文</span>\n      </div>\n    </a>')
    cards = "\n      ".join(
        f'<a class="card reveal" style="--d:{(i % 3) * 80}ms" href="letters/{a["file"]}">\n'
        f'        {jimg(a)}\n        <p class="meta">No.{a["issue"]} · {a["date"].replace("-", ".")}</p>\n'
        f'        <h3>{html.escape(a["title"], quote=False)}</h3>\n      </a>' for i, a in enumerate(rest))
    slides = "\n      ".join(
        f'<img class="slide{" on" if i == 0 else ""}" src="{h(k)}" alt="" '
        f'{"fetchpriority=" + chr(34) + "high" + chr(34) if i == 0 else "loading=" + chr(34) + "lazy" + chr(34)} />'
        for i, k in enumerate(HERO_SLIDES))
    topics = "\n      ".join(
        f'<a class="topic reveal" style="--d:{i * 80}ms" href="{href}">\n'
        f'        <figure><img src="{h(k)}" alt="{t}" loading="lazy" /></figure>\n'
        f'        <div class="topic-body"><span class="num">{num}</span><h3>{t}</h3><p>{d}</p><span class="more">看判斷重點</span></div>\n      </a>'
        for i, (num, t, d, k, href) in enumerate(TOPICS))
    videos = "\n      ".join(
        f'<button class="video reveal" style="--d:{i * 70}ms" data-src="assets/video/{k}.mp4" aria-label="播放：{t}">\n'
        f'        <img src="{h(k + "-poster")}" alt="" loading="lazy" />\n'
        f'        <span class="play" aria-hidden="true"></span>\n        <span class="video-title">{t}</span>\n      </button>'
        for i, (k, t) in enumerate(VIDEOS))
    paths = "\n      ".join(
        f'<article class="path reveal" style="--d:{i * 90}ms">\n'
        f'        <figure><img src="{h(k)}" alt="" loading="lazy" /></figure>\n'
        f'        <p class="path-label">{label}</p>\n        <h3>{t}</h3>\n'
        f'        <ul>{"".join(f"<li><a href={chr(34)}{u}{chr(34)}{" rel=" + chr(34) + "noopener" + chr(34) if u.startswith("http") else ""}>{x}</a></li>" for x, u in links)}</ul>\n      </article>'
        for i, (k, label, t, links) in enumerate(PATHS))
    qs = "\n        ".join(
        f'<li class="reveal" style="--d:{i * 80}ms"><span>{i + 1:02d}</span>{q}</li>' for i, q in enumerate(QUESTIONS))

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>蘇菲餘白｜醫美判斷力與療程諮詢筆記</title>
<meta name="description" content="蘇菲餘白整理醫美療程、抗老選擇、診所諮詢與消費判斷。用 15 年醫療與醫美營運經驗，把複雜療程變成問得出口的問題。" />
<meta property="og:title" content="蘇菲餘白｜醫美判斷力與療程諮詢筆記" />
<meta property="og:description" content="做醫美前，先把療程、預算、風險與診所話術看懂。" />
<meta property="og:type" content="website" />
<meta property="og:image" content="{SITE_URL}/assets/sophie-lib/formal-seated.jpg" />
<link rel="canonical" href="{SITE_URL}/" />
<link rel="alternate" type="application/rss+xml" title="{BRAND}" href="feed.xml" />
<link rel="sitemap" type="application/xml" href="sitemap.xml" />
{head_block("", home=True)}
{home_ld()}
</head>
<body class="home y-dark-top">
{header_block("")}

<main>
  <section class="hero" aria-label="{BRAND}">
    <div class="hero-media">
      {slides}
    </div>
    <div class="hero-veil"></div>
    <div class="hero-text">
      <p class="eyebrow">Aesthetic Judgment Notes</p>
      <h1>{BRAND}</h1>
      <p class="hero-line">不是叫你跟風變美，<br />而是先看懂療程、預算、風險與診所現場邏輯。</p>
      <div class="actions">
        <a class="btn primary" href="consult.html">整理我的諮詢問題</a>
        <a class="btn ghost" href="#topics">認識療程主題</a>
      </div>
    </div>
    <div class="hero-foot">
      <div><b>15 年</b><span>醫療、器材與醫美營運</span></div>
      <div><b>{n} 篇</b><span>醫美判斷長文</span></div>
      <div><b>不取代診療</b><span>只幫你把問題問對</span></div>
    </div>
  </section>

  <section class="manifesto" aria-label="品牌主張">
    <div class="manifesto-media"><img data-parallax src="{h("door")}" alt="蘇菲站在診所門口" loading="lazy" /></div>
    <div class="manifesto-text reveal">
      <p class="eyebrow">Why</p>
      <h2>醫美最貴的成本，<br />不一定是價格，<br />而是期待值錯置。</h2>
      <p class="y-position">{POSITIONING}</p>
      <p>這裡不診斷、不替你決定。只把療程邏輯、風險、預算和恢復期拆開，讓你進診間前就知道該問什麼。</p>
    </div>
  </section>

  <section class="section topics" id="topics" aria-label="療程主題">
    <div class="head reveal">
      <p class="eyebrow">Treatment Map</p>
      <h2>先分清楚問題，再談療程。</h2>
    </div>
    <div class="topic-rail">
      {topics}
    </div>
  </section>

  <section class="section videos" aria-label="短影片">
    <div class="head reveal">
      <p class="eyebrow">Video Notes</p>
      <h2>一支短片，只拆一個判斷題。</h2>
    </div>
    <div class="video-rail">
      {videos}
    </div>
    <div class="center reveal"><a class="btn ghost" href="videos.html">看全部 YouTube 短影片</a></div>
  </section>

  <section class="section paths" aria-label="閱讀路徑">
    <div class="head reveal">
      <p class="eyebrow">Start Here</p>
      <h2>照你現在的狀態開始。</h2>
    </div>
    <div class="path-grid">
      {paths}
    </div>
  </section>

  <section class="checklist" aria-label="諮詢前問題清單">
    <figure class="check-media"><img data-parallax src="{h("checklist")}" alt="蘇菲在諮詢室看資料" loading="lazy" /></figure>
    <div class="check-body">
      <p class="eyebrow reveal">Consultation Checklist</p>
      <h2 class="reveal">醫美消費前<br />必問的 7 個問題</h2>
      <ol class="qs">
        {qs}
        <li class="locked reveal" style="--d:340ms"><span>05–07</span><div>後 3 題在 LINE：預算怎麼抓、哪些話術聽起來很美其實要小心。<a href="{LINE_URL}" rel="noopener">加 LINE 領完整清單</a></div></li>
      </ol>
    </div>
  </section>

  <section class="section journal" aria-label="最新文章">
    <div class="head reveal">
      <p class="eyebrow">Journal</p>
      <h2>每篇文章，只拆一個醫美判斷題。</h2>
    </div>
    {feature}
    <div class="card-grid journal-rail">
      {cards}
    </div>
    <div class="center reveal"><a class="btn ghost" href="letters/index.html">看全部 {n} 篇文章</a></div>
  </section>

  <section class="consult" aria-label="諮詢">
    <div class="consult-media"><img data-parallax src="{h("consult")}" alt="" loading="lazy" /></div>
    <div class="consult-veil"></div>
    <div class="consult-body reveal">
      <p class="eyebrow">Next Step</p>
      <h2>把想做的療程，<br />先整理成問得出口的問題。</h2>
      <p class="consult-items"><span>療程期待校準</span><span>諮詢問題整理</span><span>文章與知識地圖</span></p>
      <div class="actions">
        <a class="btn primary" href="{LINE_URL}" rel="noopener">加入官方 LINE</a>
        <a class="btn ghost" href="consult.html">查看諮詢方式</a>
      </div>
    </div>
  </section>
</main>

{footer_block("")}
{script_block("")}
</body>
</html>
"""


def build_indexes(repo: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """回傳 {"letters/index.html": ..., "index.html": ...}；extra＝尚未寫檔的新文章 {檔名: html}。"""
    metas = collect(repo, extra)
    return {"letters/index.html": render_letters_index(metas), "index.html": render_home(metas),
            "letters/articles.json": render_articles_json(metas),
            "videos.html": render_videos_page(load_videos(repo), metas),
            "checklist.html": render_checklist_page()}


def render_articles_json(metas: list[dict]) -> str:
    """文章頁底部「繼續看」由 yubai.js 讀這份清單產生；新文章上架只更新這一檔，舊文章頁不用動。"""
    import json
    rows = [{"f": a["file"], "n": a["issue"], "t": a["title"], "d": a["date"], "i": a["img"] or ""} for a in metas]
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"


# ---------------------------------------------------------------- llms.txt

LLMS_SUMMARY = (POSITIONING + "網站以醫美判斷力為核心：蘇菲以醫療、護理、醫療器材銷售與醫美營運現場的長期觀察為底，"
                "把醫美療程原理、診所諮詢流程、常見話術、風險與預算拆開，讓消費者知道下一步該問什麼。"
                "這裡不做診斷，也不取代醫師；內容僅供衛教與消費判斷參考。")
LLMS_NOTE = "網站語言為繁體中文（台灣）。每篇文章只拆一個醫美判斷題；引用請以各頁標示的日期與參考資料為準。"


def _clip(s: str, n: int = 100) -> str:
    s = " ".join(s.split())
    if len(s) <= n:
        return s
    cut = max((s.rfind(c, 0, n) for c in "。！？"), default=-1)
    return s[: cut + 1] if cut >= 30 else s[: n - 2].rstrip("，、；：") + "…"


def _md_text(s: str) -> str:
    return " ".join(s.split()).replace("[", "［").replace("]", "］")


def _page_info(f: Path) -> tuple[str, str]:
    t = f.read_text(encoding="utf-8")
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    title = html.unescape(m.group(1)).strip() if m else f.stem
    title = re.sub(r"\s*[｜|]\s*" + BRAND + r"\s*$", "", title)
    return title, _meta_content(t, "name", "description")


def _llms_line(rel: str, title: str, desc: str) -> str:
    d = _clip(desc)
    return f"- [{_md_text(title)}]({SITE_URL}/{rel})" + (f": {d}" if d else "")


def render_llms_txt(repo: Path, extra: dict[str, str] | None = None) -> str:
    """依 llmstxt.org 格式產 llms.txt。文章清單與 letters/articles.json 同一來源（collect）；extra＝尚未寫檔的新文章。"""
    out = [f"# {BRAND}", "", f"> {LLMS_SUMMARY}", "", LLMS_NOTE, "", "## 文章", ""]
    for a in collect(repo, extra):
        out.append(_llms_line(f"letters/{a['file']}", a["title"], a["desc"]))

    def section(head: str, files: list[Path]) -> None:
        rows = [(f.relative_to(repo).as_posix(), *_page_info(f)) for f in files if f.exists()]
        if rows:
            out.extend(["", f"## {head}", ""] + [_llms_line(*r) for r in rows])

    section("療程主題", [repo / "treatments.html"] + sorted((repo / "topics").glob("*.html")))
    section("影片", [repo / "videos.html"])
    out.append(f"- [YouTube 頻道]({YT_CHANNEL}): {BRAND}短影片，每支只講一個判斷題")
    section("好物清單", [repo / "picks.html"] + sorted((repo / "picks").glob("*.html")))
    section("關於", [repo / "about.html", repo / "faq.html", repo / "consult.html", repo / "letters" / "index.html"])
    out += [f"- [RSS 訂閱]({SITE_URL}/feed.xml): 文章更新的 RSS feed",
            f"- [Sitemap]({SITE_URL}/sitemap.xml): 全站網址清單", ""]
    return "\n".join(out)


def write_llms(repo: Path, extra: dict[str, str] | None = None) -> bool:
    f = repo / "llms.txt"
    text = render_llms_txt(repo, extra)
    if f.exists() and f.read_text(encoding="utf-8") == text:
        return False
    f.write_text(text, encoding="utf-8", newline="\n")
    return True


# ---------------------------------------------------------------- 2026-10-20：AEO／內部連結／欄目／補洞
# 全部放在 theme_page 裡自動套用：每篇新文章（site_publish 呼叫 theme_page）與全站重套（apply-theme）都會帶，不是單頁手改。

DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"')
CANON_RE = re.compile(r'<link\s+rel="canonical"')
AEO_RE = re.compile(r"\s*<!--yubai:aeo-->.*?<!--/yubai:aeo-->", re.S)
POS_RE = re.compile(r"\s*<!--yubai:pos-->.*?<!--/yubai:pos-->", re.S)

AUTHOR_BIO = "專注大健康與自費醫美，護理師、心臟醫材、醫美營運出身。內容僅供衛教與消費判斷參考，不取代醫師診療。"

# 沒有 meta description 的固定頁（主題頁優先用自己的 og:description）
PAGE_DESC = {
    "about.html": "蘇菲餘白不是診所官網，也不是療程銷售頁，而是醫美判斷力網站：把療程原理、諮詢流程、常見話術、風險與預算拆開，讓你知道下一步該問什麼。",
    "treatments.html": "鳳凰電波、音波拉提、玻尿酸、肉毒、水光五個療程主題：每個都從常見誤解開始拆，先問它改善什麼、誰容易失望、諮詢時該問什麼。",
    "faq.html": "蘇菲餘白常見問題：網站定位、諮詢界線、諮詢前要準備什麼，以及療程資訊很多時怎麼不被話術帶走。真正的治療仍需合格醫師面診評估。",
    "consult.html": "諮詢前先整理四件事：真正困擾、療程期待、風險與限制、診間問句，另附傳訊息前可以先準備的照片與資料清單。",
}

# 五個療程主題頁（網址不動）：（顯示名, 檔案, 關鍵字）
TOPIC_PAGES = [
    ("鳳凰電波", "topics/thermage.html", "電波|Thermage|鳳凰"),
    ("音波拉提", "topics/ultherapy.html", "音波|Ultherapy|Ulthera"),
    ("玻尿酸", "topics/hyaluronic-acid.html", "玻尿酸|填充|Filler"),
    ("肉毒", "topics/botox.html", "肉毒|Botox"),
    ("水光", "topics/skinbooster.html", "水光|PN|PDRN|Skinbooster|skin booster"),
]

# 三個欄目（2026-10-20 蘇菲拍板；來源 sophie-agent\topics\columns.json）。
# 歸屬規則：優先讀 sophie-agent\topics\column_keywords.json（另一位 agent 維護；尚未建立時用下面這組標題／內文關鍵字）。
COLUMNS = [
    ("A", "自費醫美怎麼選、術後怎麼顧", "醫美|療程|診所|玻尿酸|肉毒|電波|音波|雷射|皮秒|術後|防曬|填充|拉提|水光|隆乳|隆鼻|整形|預付|合約|廣告|同意書|消保|價格"),
    ("B", "瘦瘦針與身形臉部變化", "GLP|瘦瘦針|減重|減肥|體重|猛健樂|司美|週纜|肥胖|停藥|臉垮|臉凹"),
    ("C", "預防醫學與日常健康數字", "血壓|血糖|代謝|抗衰|抗老|骨質|更年期|荷爾蒙|預防|健檢|膽固醇|心血管|睡眠|長壽|失智|疫苗|NAD|健康數字"),
]


def _load_columns() -> list[tuple[str, str, re.Pattern]]:
    names = {c[0]: c[1] for c in COLUMNS}
    kws = {c[0]: c[2] for c in COLUMNS}
    topics_dir = Path(__file__).resolve().parent.parent.parent.parent / "topics"
    try:
        cj = json.loads((topics_dir / "columns.json").read_text(encoding="utf-8"))
        for c in cj.get("columns", []):
            if c.get("id") in names and c.get("name"):
                names[c["id"]] = c["name"]
    except (OSError, ValueError):
        pass
    try:
        kj = json.loads((topics_dir / "column_keywords.json").read_text(encoding="utf-8"))
        kj = kj.get("columns", kj) if isinstance(kj, dict) else {}
        for cid, v in kj.items():
            words = v.get("keywords", []) if isinstance(v, dict) else v
            if cid in kws and isinstance(words, list) and words:
                kws[cid] = "|".join(re.escape(w) for w in words if isinstance(w, str) and w)
    except (OSError, ValueError, AttributeError):
        pass
    return [(cid, names[cid], re.compile(kws[cid], re.I)) for cid, *_ in COLUMNS]


_COLS = _load_columns()
_CAT_RX = [(label, re.compile(kw, re.I)) for label, kw in CHIPS] + [(l, re.compile(k, re.I)) for l, _, k in TOPIC_PAGES]
GENERIC_TAGS = {"蘇菲餘白", "醫美", "醫美判斷力", "知情選擇"}


def _body_region(text: str) -> str:
    """文章正文（不含我們自己加的延伸閱讀／署名／結尾 CTA），評分與摘要都只看這一段。"""
    i = text.find('<article class="letter-body">')
    if i < 0:
        return ""
    ends = [x for x in (text.find(m, i) for m in ('<!--yubai:aeo-->', '<p class="hashtag-line">',
                                                   '<section class="letter-cta">', "</article>")) if x >= 0]
    return VIDEO_RE.sub("", text[i:min(ends)])


def _tags_of(text: str) -> list[str]:
    m = re.search(r'<p class="hashtag-line">(.*?)</p>', text, re.S)
    return [t for t in re.findall(r"#([^\s#<]+)", m.group(1)) if t not in GENERIC_TAGS] if m else []


def _score_cats(title: str, body: str) -> dict:
    out = {}
    for label, rx in _CAT_RX:
        s = 4 * len(rx.findall(title)) + min(len(rx.findall(body)), 6)
        if s >= 3:
            out[label] = max(out.get(label, 0), s)
    return out


def _column_of(title: str, body: str) -> str:
    best, best_s = "A", 0
    for cid, _, rx in _COLS:
        s = 4 * len(rx.findall(title)) + min(len(rx.findall(body)), 8)
        if s > best_s:
            best, best_s = cid, s
    return best


def col_name(cid: str) -> str:
    return next((n for c, n, _ in _COLS if c == cid), "")


def _bigrams(s: str) -> set:
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def related_for(me: dict, metas: list[dict], n: int = 3) -> list[dict]:
    """延伸閱讀：同欄目優先；欄目內依（共同標籤、共同主題分類、標題用字重疊）排序，不夠 n 篇再從其他欄目補。"""
    tb = _bigrams(me["title"])
    scored = []
    for o in metas:
        if o["file"] == me["file"]:
            continue
        ob = _bigrams(o["title"])
        jac = len(tb & ob) / max(1, len(tb | ob))
        s = 4 * len(set(me["tags"]) & set(o["tags"])) + 3 * len(set(me["cats"]) & set(o["cats"])) + 6 * jac
        scored.append((o["col"] != me["col"], -round(s, 4), abs(int(o["issue"]) - int(me["issue"])), o["issue"], o))
    scored.sort(key=lambda x: x[:4])
    return [x[4] for x in scored[:n]]


def _site_root(page_path: Path) -> Path:
    return page_path.parent.parent if page_path.parent.name in ("letters", "topics") else page_path.parent


def make_desc(paras: list[str]) -> str:
    buf = ""
    for p in paras:
        buf += p
        if len(buf) >= 45:
            break
    buf = " ".join(buf.split())
    if len(buf) <= 100:
        return buf
    cut = max((buf.rfind(c, 0, 100) for c in "。！？"), default=-1)
    return buf[: cut + 1] if cut >= 30 else buf[:98].rstrip("，、；：") + "…"


def _body_paras(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"<p>(.*?)</p>", _body_region(text), re.S):
        s = _strip(m.group(1))
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s).replace("**", "")
        if len(s) >= 6 and not s.startswith("["):
            out.append(s)
    return out


def ensure_seo_head(text: str, page_path: Path, root: Path) -> str:
    """補 canonical 與 meta description（缺才補；已有的不動）。"""
    rel = page_path.resolve().relative_to(root.resolve()).as_posix()
    add = []
    if not CANON_RE.search(text):
        add.append(f'<link rel="canonical" href="{SITE_URL}/{rel}" />')
    if not DESC_RE.search(text):
        desc = PAGE_DESC.get(rel) or _meta_content(text, "property", "og:description")
        if not desc and page_path.parent.name == "letters":
            desc = make_desc(_body_paras(text))
        if desc:
            add.append(f'<meta name="description" content="{esc(desc)}" />')
    if not add:
        return text
    return re.sub(r"(</title>)", lambda m: m.group(1) + "".join("\n    " + a for a in add), text, count=1)


def fix_md_leftovers(text: str) -> str:
    """正文裡漏出的 markdown：[文字](網址) 轉成可點連結、**粗體** 轉 <strong>、落單的 ** 刪掉。"""
    i = text.find('<article class="letter-body">')
    if i < 0:
        return text
    ends = [x for x in (text.find(m, i) for m in ('<!--yubai:aeo-->', '<section class="letter-cta">', "</article>")) if x >= 0]
    j = min(ends)
    seg = text[i:j]
    seg = re.sub(r'\[([^\[\]<>]+)\]\((https?://[^\s)<>"]+)\)', r'<a href="\2" rel="noopener">\1</a>', seg)
    seg = re.sub(r"\*\*((?:(?!\*\*|</?p>).)+?)\*\*", r"<strong>\1</strong>", seg, flags=re.S)
    seg = seg.replace("**", "")
    return text[:i] + seg + text[j:]


def cta_section() -> str:
    return ('<section class="letter-cta"><h2>延伸整理</h2><p>我會在 LINE 裡用更白話的方式拆，完整文章與延伸整理留在蘇菲餘白網站。</p>\n'
            f'            <ul class="letter-checks"><li>官方 LINE：<a href="{LINE_URL}" rel="noopener">{LINE_URL}</a></li>'
            f'<li>蘇菲餘白網站：<a href="{SITE_URL}/" rel="noopener">{SITE_URL}/</a></li></ul>\n          </section>')


def ensure_cta_links(text: str) -> str:
    """文末 CTA 區塊必須有兩個明文連結（LINE／網站）；2026-10-21 起不放電子報；缺的補在清單最後。"""
    m = re.search(r'<section class="letter-cta">.*?</section>', text, re.S)
    if not m:
        return text
    sec = m.group(0)
    need = [("官方 LINE", LINE_URL), ("蘇菲餘白網站", SITE_URL + "/")]
    add = "".join(f'<li>{lab}：<a href="{u}" rel="noopener">{u}</a></li>' for lab, u in need if f">{u}</a>" not in sec)
    if not add:
        return text
    if "</ul>" in sec:
        sec2 = sec.replace("</ul>", add + "</ul>", 1)
    else:
        # 舊版型（「蘇菲的話」只有一段話加按鈕、沒有連結清單）：正文不動，在按鈕列前插入跟新文章一致的承接句加兩連結清單
        lead = '' if "我會在 LINE" in sec else '<p>我會在 LINE 裡用更白話的方式拆，完整文章與延伸整理留在蘇菲餘白網站。</p>\n              '
        block = (lead + '<ul class="letter-checks">' + add + '</ul>\n              ')
        if '<div class="panel-actions">' in sec:
            sec2 = sec.replace('<div class="panel-actions">', block + '<div class="panel-actions">', 1)
        else:
            sec2 = sec.replace("</section>", block + "</section>", 1)
    return text[:m.start()] + sec2 + text[m.end():]


CTA_LINE_RE = re.compile(r"<!--yubai:ctaline-->.*?<!--/yubai:ctaline-->", re.S)
# 官方 LINE「加入好友的歡迎訊息」已放 checklist.html 圖文訊息（2026-10-24 蘇菲確認）；歡迎訊息若拿掉清單，這行要改回「加入官方 LINE」
CTA_LINE_TEXT = "加入 LINE，領諮詢前必問清單"


def ensure_cta_line_button(text: str) -> str:
    """文末 CTA 是讀完全文、最想行動的位置：沒有 LINE 按鈕就補一顆放在按鈕列最前面（明文連結清單照舊保留）。"""
    text = CTA_LINE_RE.sub("", text)
    m = re.search(r'<section class="letter-cta">.*?</section>', text, re.S)
    if not m:
        return text
    sec = m.group(0)
    if re.search(r'<a class="button[^"]*" href="' + re.escape(LINE_URL), sec):
        return text
    btn = f'<a class="button y-cta-line" href="{LINE_URL}" rel="noopener">{CTA_LINE_TEXT}</a>'
    if '<div class="panel-actions">' in sec:
        sec2 = sec.replace('<div class="panel-actions">', '<div class="panel-actions"><!--yubai:ctaline-->' + btn + "<!--/yubai:ctaline-->", 1)
    else:
        sec2 = sec[:-len("</section>")] + '<!--yubai:ctaline--><div class="panel-actions">' + btn + "</div><!--/yubai:ctaline--></section>"
    return text[:m.start()] + sec2 + text[m.end():]


def _li(href: str, title: str, tail: str = "") -> str:
    return f'<li><a href="{href}">{html.escape(title, quote=False)}</a>{tail}</li>'


def article_aeo_block(me: dict, metas: list[dict], with_cta: bool) -> str:
    order = sorted(metas, key=lambda a: a["issue"])
    idx = next((k for k, a in enumerate(order) if a["file"] == me["file"]), -1)
    prev_a = order[idx - 1] if idx > 0 else None
    next_a = order[idx + 1] if 0 <= idx < len(order) - 1 else None
    skip = {a["file"] for a in (prev_a, next_a) if a}
    rel = related_for(me, [a for a in metas if a["file"] not in skip], 3)   # 上下篇另外有位置，延伸閱讀不重複
    topics = [(l, f) for l, f, _ in TOPIC_PAGES if l in me["cats"]]
    topics.sort(key=lambda x: -me["cats"][x[0]])
    topic_line = "".join(f'<a href="../{f}">{l}</a>' for l, f in topics[:2])
    meta_line = (f'<p class="y-col">所屬欄目：<b>{html.escape(col_name(me["col"]), quote=False)}</b>'
                 + (f'<span>相關療程主題：{topic_line}</span>' if topic_line else "") + "</p>")
    pn = ""
    if prev_a or next_a:
        pn = ('<nav class="y-pn-static" aria-label="上一篇與下一篇">'
              + (f'<a class="prev" href="./{prev_a["file"]}"><small>← 上一篇</small><b>{html.escape(prev_a["title"], quote=False)}</b></a>' if prev_a else "<span></span>")
              + (f'<a class="next" href="./{next_a["file"]}"><small>下一篇 →</small><b>{html.escape(next_a["title"], quote=False)}</b></a>' if next_a else "<span></span>")
              + "</nav>")
    out = ('<!--yubai:aeo-->\n          '
           f'<aside class="y-author" aria-label="作者"><p class="y-author-name"><span>作者</span><a rel="author" href="../about.html">{BRAND}</a></p>'
           f'<p>{AUTHOR_BIO}</p></aside>\n          '
           '<nav class="y-related" aria-label="延伸閱讀"><p class="y-h">延伸閱讀</p><ul>'
           + "".join(_li(f"./{a['file']}", a["title"], f"<small>No.{a['issue']}</small>") for a in rel)
           + f'</ul>{meta_line}</nav>\n          {pn}')
    if with_cta:
        out += "\n          " + cta_section()
    return out + "\n          <!--/yubai:aeo-->"


def _cols_html(metas: list[dict], prefix: str) -> str:
    cols = []
    for cid, name, _ in _COLS:
        latest = [a for a in metas if a["col"] == cid][:2]
        cols.append(f'<div><h3>{cid}｜{html.escape(name, quote=False)}</h3><ul>'
                    + "".join(_li(f"{prefix}letters/{a['file']}", a["title"]) for a in latest) + "</ul></div>")
    return '<p class="y-h">欄目導覽</p><div class="y-cols">' + "".join(cols) + "</div>"


def topic_aeo_block(label: str, metas: list[dict]) -> str:
    mine = sorted((a for a in metas if label in a["cats"]), key=lambda a: (-a["cats"][label], -int(a["issue"])))[:4]
    rel = ""
    if mine:
        rel = ('<p class="y-h">這個主題的延伸文章</p><ul class="y-list">'
               + "".join(_li(f"../letters/{a['file']}", a["title"], f"<small>No.{a['issue']}</small>") for a in mine) + "</ul>")
    return ('<!--yubai:aeo-->\n      <section class="section y-topic-more"><div class="section-inner">' + rel
            + _cols_html(metas, "../") + '<p class="y-all"><a href="../letters/index.html">看全部文章 →</a></p></div></section>\n      <!--/yubai:aeo-->')


def columns_nav_block(metas: list[dict]) -> str:
    return ('<!--yubai:aeo-->\n      <section class="section y-topic-more"><div class="section-inner">' + _cols_html(metas, "")
            + '<p class="y-all"><a href="letters/index.html">看全部文章 →</a></p></div></section>\n      <!--/yubai:aeo-->')


def enhance_page(text: str, page_path: Path, metas: list[dict] | None) -> str:
    root = _site_root(page_path)
    name = page_path.name
    in_letters = page_path.parent.name == "letters" and re.match(r"\d{3}", name)
    text = AEO_RE.sub("", text)
    text = VIDEO_RE.sub("", text)
    if in_letters:
        text = fix_md_leftovers(text)
        vids = videos_for(root, f"letters/{name}")
        if vids:
            text = insert_article_video(text, article_video_block(vids))
    text = ensure_seo_head(text, page_path, root)
    if not (in_letters or page_path.parent.name == "topics" or name in ("about.html", "treatments.html")):
        return text
    if metas is None:
        metas = collect(root, {name: text} if in_letters else None)
    if in_letters:
        me = next((a for a in metas if a["file"] == name), None)
        if not me:
            return text
        if '<section class="letter-cta">' in text:
            text = re.sub(r'\s*<section class="letter-cta">',
                          lambda _: "\n          " + article_aeo_block(me, metas, False) + '\n          <section class="letter-cta">',
                          text, count=1)
            text = ensure_cta_links(text)
        elif "</article>" in text:
            text = re.sub(r"\s*</article>", lambda _: "\n        " + article_aeo_block(me, metas, True) + "\n      </article>",
                          text, count=1)
        text = ensure_cta_line_button(text)
    elif page_path.parent.name == "topics":
        label = next((l for l, f, _ in TOPIC_PAGES if f == f"topics/{name}"), None)
        if label and "</main>" in text:
            text = re.sub(r"\s*</main>", lambda _: "\n      " + topic_aeo_block(label, metas) + "\n    </main>", text, count=1)
    elif name == "treatments.html" and "</main>" in text:
        text = re.sub(r"\s*</main>", lambda _: "\n      " + columns_nav_block(metas) + "\n    </main>", text, count=1)
    elif name == "about.html":
        text = POS_RE.sub("", text)
        text = re.sub(r'(<p class="letter-dek">.*?</p>)',
                      lambda m: m.group(1) + f'\n            <!--yubai:pos--><p class="y-position">{POSITIONING}</p><!--/yubai:pos-->',
                      text, count=1, flags=re.S)
    return text


# ---------------------------------------------------------------- 2026-10-24：YouTube 短影片（網站 ↔ 頻道互相導流）
# 資料唯一來源＝data/videos.json（本機上架產線往後追加；欄位說明見 data/README.md）。
# 播放器一律「先放縮圖、點了才換成 youtube-nocookie iframe」（yubai.js），不拖慢首屏、不先載入 YouTube 的追蹤碼。

VIDEO_RE = re.compile(r"[ \t]*<!--yubai:video-->.*?<!--/yubai:video-->\n", re.S)   # 整行插入、整行拿掉，重套結果不變
YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_VIDEOS_CACHE: dict = {}


def load_videos(root: Path) -> list[dict]:
    """讀 data/videos.json；格式不對的筆數跳過並在 stderr 提醒，不讓整站重套失敗。"""
    f = root / "data" / "videos.json"
    if not f.exists():
        return []
    key = (str(f), f.stat().st_mtime_ns)
    if key not in _VIDEOS_CACHE:
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"[videos] data/videos.json 不是合法 JSON，先略過影片：{e}", file=sys.stderr)
            rows = []
        out = []
        for v in rows if isinstance(rows, list) else []:
            if not (isinstance(v, dict) and YT_ID_RE.match(str(v.get("id", ""))) and str(v.get("title", "")).strip()):
                print(f"[videos] 略過格式不對的一筆：{v!r}", file=sys.stderr)
                continue
            art = v.get("article") or None
            if art and not (root / art).exists():
                print(f"[videos] {v['id']} 的 article 找不到檔案（{art}），先當作沒有對應文章", file=sys.stderr)
                art = None
            out.append({**v, "title": v["title"].strip(), "article": art,
                        "description": (v.get("description") or "").strip() or v["title"].strip()})
        _VIDEOS_CACHE.clear()
        _VIDEOS_CACHE[key] = out
    return _VIDEOS_CACHE[key]


def videos_for(root: Path, article_rel: str) -> list[dict]:
    return [v for v in load_videos(root) if v["article"] == article_rel]


def yt_watch(vid: str) -> str:
    return f"https://www.youtube.com/shorts/{vid}"


def yt_thumb(vid: str) -> str:
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


def video_ld(v: dict) -> dict:
    """VideoObject；uploadDate 只用 videos.json 的 publishedDate，沒填就不放（不編日期）。"""
    vid = v["id"]
    o = {"@type": "VideoObject", "name": v["title"], "description": v["description"], "thumbnailUrl": yt_thumb(vid)}
    if v.get("publishedDate"):
        o["uploadDate"] = v["publishedDate"]
    o.update({"embedUrl": f"https://www.youtube.com/embed/{vid}", "contentUrl": yt_watch(vid),
              "inLanguage": "zh-Hant", "publisher": _org()})
    return o


def yt_player(v: dict) -> str:
    """沒有 JS 時就是一個連到 YouTube 的縮圖連結；有 JS 時點了才在原地載入播放器。"""
    vid = v["id"]
    return (f'<a class="y-yt" href="{yt_watch(vid)}" data-yt="{vid}" rel="noopener" aria-label="播放影片：{esc(v["title"])}">'
            f'<img loading="lazy" decoding="async" src="{yt_thumb(vid)}" alt="" width="480" height="360" />'
            f'<span class="y-yt-play" aria-hidden="true"></span></a>')


def article_video_block(vids: list[dict]) -> str:
    cards = "".join(
        f'<aside class="y-yt-card" aria-label="這篇的短影片">{yt_player(v)}<div class="y-yt-text">'
        f'<p class="y-yt-label">這篇有短影片版</p><p class="y-yt-title">{html.escape(v["title"], quote=False)}</p>'
        f'<p>先花一點時間看影片，再往下讀完整整理。</p>'
        f'<p class="y-yt-links"><a href="../videos.html">看全部短影片</a><a href="{YT_CHANNEL}" rel="noopener">到 YouTube 頻道</a></p>'
        f'</div></aside>' for v in vids)
    return f"<!--yubai:video-->{cards}<!--/yubai:video-->\n"


def insert_article_video(text: str, block: str) -> str:
    """放在正文第一個小標題（h2／h3）前：開場幾段讀完、正式進入重點之前；正文沒有小標題就放在正文最後。"""
    i = text.find('<article class="letter-body">')
    if i < 0:
        return text
    ends = [x for x in (text.find(m, i) for m in ('<!--yubai:aeo-->', '<p class="hashtag-line">',
                                                   '<section class="letter-cta">', "</article>")) if x >= 0]
    j = min(ends) if ends else len(text)
    hs = [x for x in (text.find(h, i, j) for h in ("<h2", "<h3")) if x >= 0]
    pos = min(hs) if hs else j
    ls = text.rfind("\n", 0, pos) + 1
    if text[ls:pos].strip():
        ls = pos            # 目標不在行首：直接貼在它前面
    return text[:ls] + text[ls:pos] + block + text[ls:]


def _topic_for(topic: str) -> tuple[str, str] | None:
    return next(((l, f) for l, f, kw in TOPIC_PAGES if topic and re.search(kw, topic, re.I)), None)


def _videos_sorted(videos: list[dict]) -> list[dict]:
    # 有上架日期的新到舊；日期相同或都沒填時維持 videos.json 的順序
    return sorted(videos, key=lambda v: v.get("publishedDate") or "", reverse=True)


def render_videos_page(videos: list[dict], metas: list[dict]) -> str:
    titles = {f"letters/{a['file']}": a["title"] for a in metas}
    page_url = f"{SITE_URL}/videos.html"
    cards = []
    for v in _videos_sorted(videos):
        links = []
        if v["article"] and v["article"] in titles:
            links.append(f'<a href="{esc(v["article"])}">完整文章：{html.escape(titles[v["article"]], quote=False)}</a>')
        elif tp := _topic_for(v.get("topic", "")):
            links.append(f'<a href="{tp[1]}">相關療程主題：{tp[0]}</a>')
        links.append(f'<a href="{yt_watch(v["id"])}" rel="noopener">在 YouTube 看</a>')
        cards.append(f'            <article class="y-vid">\n              {yt_player(v)}\n'
                     f'              <h2>{html.escape(v["title"], quote=False)}</h2>\n'
                     f'              <p>{html.escape(v["description"], quote=False)}</p>\n'
                     f'              <p class="y-yt-links">{"".join(links)}</p>\n            </article>')
    desc = "蘇菲餘白的 YouTube 短影片總覽：一支影片只講一個醫美或健康判斷題，有寫成文章的，影片下面直接附上完整文章。"
    ld = ld_block([{
        "@type": "CollectionPage", "name": f"{BRAND}短影片", "url": page_url, "inLanguage": "zh-Hant", "description": desc,
        "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"},
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": k + 1, "item": video_ld(v)} for k, v in enumerate(_videos_sorted(videos))]},
    }]) if videos else ""
    return f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>短影片｜{BRAND}</title>
    <meta name="description" content="{esc(desc)}" />
    <meta property="og:title" content="短影片｜{BRAND}" />
    <meta property="og:description" content="{esc(desc)}" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="{SITE_URL}/assets/sophie-lib/formal-seated.jpg" />
    <link rel="canonical" href="{page_url}" />
    {head_block("")}
    {ld}
  </head>
  <body>
    {header_block("")}
    <main>
      <section class="page-hero">
        <div class="section-inner page-hero-narrow">
          <p class="eyebrow">Video Notes</p>
          <h1>短影片</h1>
          <p class="letter-dek">一支短片只講一個問題。想看來龍去脈，影片下面有完整文章可以接著讀；新影片會先上 YouTube 頻道。</p>
          <div class="hero-actions">
            <a class="button primary" href="{YT_CHANNEL}" rel="noopener">到 YouTube 頻道</a>
            <a class="button secondary" href="letters/index.html">看全部文章</a>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-inner">
          <div class="y-vids">
{chr(10).join(cards)}
          </div>
        </div>
      </section>
    </main>
    {footer_block("")}
    {script_block("")}
  </body>
</html>
"""


# 後 3 題：內容只取自站上已發表的文章（020、059、077、078、079、068、081），不另外加料、不寫價格
CHECKLIST_MORE = [
    ("預算怎麼抓？", "先問這個報價是單次，還是整個療程。總共要做幾次、每次隔多久、之後多久要補一次、回診和術後用品另外算不算錢，全部加起來才是真正的預算。",
     "如果要預付一大筆錢，先看契約寫了什麼：適用範圍、履約保障、退費期限，還有每次做完的消費紀錄。",
     [("醫美諮詢不要先問多少錢，先問這五件事", "letters/020-consultation-questions-before-price.html"),
      ("美容療程預付超過 5 萬，簽約前先問這 3 件事", "letters/077-beauty-prepaid-contract-protection-20260824.html")]),
    ("哪些話聽起來很美，其實要先停下來？", "「今天簽才有這個優惠」、「無息分期、低自備款就能開始」、「唯一、保證、永不復發」。聽到這幾句，先不要當天決定，回家把總價和必要性想清楚再說。",
     "醫療廣告用這些字眼本身就是紅旗；平台上有藍勾勾，也不代表內容合法或有證據。",
     [("診所用「無息分期」招攬病人，可能踩法規紅線", "letters/078-interest-free-installment-medical-solicitation-20260825.html"),
      ("醫療廣告出現「唯一、保證、永不復發」，先停", "letters/079-medical-advertising-red-flags-20260826.html")]),
    ("萬一不如預期，誰負責、怎麼處理？", "付款前先問：術後多久會追蹤、晚上或假日出狀況打給誰、出現不良反應時診所怎麼處理、後續費用誰付。",
     "同時自己先留好三樣東西：病歷與同意書、逐項收費明細、同角度拍的術前術後照片。",
     [("術後保障，為什麼差這麼多？", "letters/068-post-treatment-protection-20260801.html"),
      ("出事前先留 3 樣：病歷、明細、術前術後照片", "letters/081-medical-records-consent-evidence-20260828.html")]),
]


def render_checklist_page() -> str:
    first = "\n".join(
        f'            <li><span>{i + 1:02d}</span><div><h2>{html.escape(q, quote=False)}</h2></div></li>' for i, q in enumerate(QUESTIONS))
    more = "\n".join(
        f'            <li><span>{len(QUESTIONS) + i + 1:02d}</span><div><h2>{html.escape(q, quote=False)}</h2>'
        f'<p>{html.escape(a, quote=False)}</p><p>{html.escape(b, quote=False)}</p>'
        f'<p class="y-ck-read">延伸閱讀：' + "".join(f'<a href="{u}">{html.escape(x, quote=False)}</a>' for x, u in links) + '</p></div></li>'
        for i, (q, a, b, links) in enumerate(CHECKLIST_MORE))
    return f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>醫美消費前必問的 7 個問題｜{BRAND}</title>
    <meta name="robots" content="noindex" />
    <meta name="description" content="進診間前，把這 7 題問清楚：想改善什麼、療程處理哪一層、不如預期怎麼辦、恢復期能不能配合、預算怎麼抓、哪些話要先停、出事誰負責。" />
    <meta property="og:title" content="醫美消費前必問的 7 個問題｜{BRAND}" />
    <meta property="og:description" content="進診間前先問清楚，截圖存著，諮詢時一題一題對。" />
    <meta property="og:type" content="article" />
    <meta property="og:image" content="{SITE_URL}/assets/line/checklist-card.jpg" />
    <link rel="canonical" href="{SITE_URL}/checklist.html" />
    {head_block("")}
  </head>
  <body>
    {header_block("")}
    <main>
      <section class="page-hero">
        <div class="section-inner page-hero-narrow">
          <p class="eyebrow">Consultation Checklist</p>
          <h1>醫美消費前必問的 7 個問題</h1>
          <p class="letter-dek">進診間前，先把這 7 題問清楚。可以截圖存在手機，諮詢時一題一題對。</p>
        </div>
      </section>
      <section class="section">
        <div class="section-inner page-hero-narrow">
          <ol class="y-ck">
{first}
{more}
          </ol>
          <p class="y-ck-note">這份清單只幫你把問題問對，不取代醫師面診。想把自己的狀況整理成問題，可以直接在 LINE 問蘇菲。</p>
          <div class="hero-actions"><a class="button primary" href="consult.html">看諮詢整理方式</a><a class="button secondary" href="letters/index.html">看全部文章</a></div>
        </div>
      </section>
    </main>
    {footer_block("")}
    {script_block("")}
  </body>
</html>
"""


def ensure_sitemap_entry(repo: Path, rel: str, lastmod: str, bump: bool) -> bool:
    """sitemap.xml 沒有這一頁就補上；bump＝這次內容有變，lastmod 換成今天。回傳有沒有改檔。"""
    sm = repo / "sitemap.xml"
    if not sm.exists():
        return False
    t = sm.read_text(encoding="utf-8")
    loc = f"{SITE_URL}/{rel}"
    m = re.search(r"<loc>" + re.escape(loc) + r"</loc>(\s*<lastmod>)([^<]*)(</lastmod>)", t)
    if m:
        if not bump or m.group(2) == lastmod:
            return False
        t = t[:m.start(2)] + lastmod + t[m.end(2):]
    elif "</urlset>" in t:
        t = t.replace("</urlset>", f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>\n</urlset>", 1)
    else:
        return False
    sm.write_text(t, encoding="utf-8", newline="\n")
    return True


# ---------------------------------------------------------------- 全站重套

def apply_theme(repo: Path) -> list[str]:
    touched = []
    # picks.html 由 affiliate_sync.py 自己產（已用同一組 head/header/footer 函式），不在這裡重套，免得兩邊互相改空白造成每次都有 diff
    # videos.html 由 build_indexes 整頁產生，也不重套
    targets = [(f, "") for f in repo.glob("*.html") if f.name not in ("index.html", "404.html", "picks.html", "videos.html", "checklist.html")]
    targets += [(f, "../") for f in (repo / "letters").glob("*.html") if f.name != "index.html"]
    targets += [(f, "../") for f in (repo / "topics").glob("*.html")]
    for f, p in targets:
        old = f.read_text(encoding="utf-8")
        new = theme_page(old, p, page_path=f, make_webp=True)
        if new != old:
            f.write_text(new, encoding="utf-8", newline="\n")
            touched.append(f.relative_to(repo).as_posix())
    # 文章列表與首頁會引用的固定圖
    ensure_webp(repo / "assets" / "sophie-lib" / "consult-listen-cup.jpg")
    for rel, text in build_indexes(repo).items():
        f = repo / rel
        if not f.exists() or f.read_text(encoding="utf-8") != text:
            f.write_text(text, encoding="utf-8", newline="\n")
            touched.append(rel)
    if ensure_sitemap_entry(repo, "videos.html", date.today().isoformat(), "videos.html" in touched):
        touched.append("sitemap.xml")
    if write_llms(repo):
        touched.append("llms.txt")
    missing = [v["id"] for v in load_videos(repo) if not v.get("publishedDate")]
    if missing:
        print(f"[videos] {len(missing)} 支影片還沒填 publishedDate（VideoObject 會缺 uploadDate）：{', '.join(missing)}",
              file=sys.stderr)
    return touched


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import argparse
    ap = argparse.ArgumentParser(description="蘇菲餘白：全站套用版型／重建首頁與文章列表")
    ap.add_argument("cmd", choices=["apply-theme", "indexes", "llms"])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    if args.cmd == "apply-theme":
        changed = apply_theme(repo)
    elif args.cmd == "llms":
        changed = ["llms.txt"] if write_llms(repo) else []
    else:
        changed = []
        for rel, text in build_indexes(repo).items():
            (repo / rel).write_text(text, encoding="utf-8", newline="\n")
            changed.append(rel)
    print(f"changed {len(changed)} files")
    for c in changed:
        print("  " + c)
