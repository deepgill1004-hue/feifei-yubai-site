# -*- coding: utf-8 -*-
r"""
yubai_site.py -- 蘇菲餘白網站版型的唯一來源（C 版：雜誌底＋電影章節，2026-10-12 起）

負責：
  * 每一頁的 <head> 樣式、頁首、頁尾、動態腳本（theme_page）
  * 首頁 index.html 與文章列表 letters/index.html：每次從 letters/*.html 文章頁重新產生（build_indexes）
  * 文章主視覺自動轉 WebP（ensure_webp）

被誰呼叫：
  * weekly-linkedin-vocus\scripts\site_publish.py（每篇新文章上架）
  * 手動：python scripts\yubai_site.py apply-theme [--repo <站台 clone>]   # 全站重套版型（可重複執行）

改版型只改這支＋assets/yubai.css／yubai-home.css／yubai.js，不要回頭改各頁 HTML。
"""
from __future__ import annotations

import html
import re
import sys
import urllib.parse
from pathlib import Path

SITE_URL = "https://deepgill1004-hue.github.io/feifei-yubai-site"
LINE_URL = "https://line.me/R/ti/p/@371arhqu"
NEWS_URL = "https://sophie-yubai.beehiiv.com/"
BRAND = "蘇菲餘白"
ASSET_VER = "20261012"
FOOTER_NOTE = "內容僅供衛教與消費判斷參考，不取代醫師診療或個別法律意見。"
HOME_CARDS = 6            # 首頁「最新文章」除主打外再列幾篇
WEBP_MAX = 1600

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com" />'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,400;1,500'
         '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=Noto+Serif+TC:wght@500;700;900&amp;display=swap" rel="stylesheet" />')

esc = lambda s: html.escape(s, quote=True)  # noqa: E731


# ---------------------------------------------------------------- 共用區塊

def head_block(p: str, home: bool = False) -> str:
    css = (f'<link rel="stylesheet" href="{p}assets/yubai.css?v={ASSET_VER}" />'
           f'<link rel="stylesheet" href="{p}assets/yubai-home.css?v={ASSET_VER}" />' if home else
           f'<link rel="stylesheet" href="{p}assets/styles-v2.css?v=20260503-2" />'
           f'<link rel="stylesheet" href="{p}assets/yubai.css?v={ASSET_VER}" />')
    return f"<!--yubai:head-->\n    {FONTS}\n    {css}\n    <!--/yubai:head-->"


def header_block(p: str) -> str:
    return (f'<header class="site-header" aria-label="主要導覽">\n'
            f'      <a class="brand" href="{p}index.html" aria-label="回到首頁">{BRAND}</a>\n'
            f'      <nav><a class="m-hide" href="{p}about.html">關於</a><a href="{p}treatments.html">療程主題</a>'
            f'<a href="{p}letters/index.html">文章</a><a class="m-hide" href="{p}faq.html">FAQ</a>'
            f'<a class="m-hide" href="{p}consult.html">諮詢</a>'
            f'<a class="nav-cta" href="{LINE_URL}" rel="noopener">加入 LINE</a></nav>\n'
            f'    </header>')


def footer_block(p: str) -> str:
    return (f'<footer class="site-footer y-footer">\n'
            f'      <p class="footer-brand">{BRAND}</p>\n'
            f'      <nav class="footer-nav" aria-label="網站導覽"><a href="{p}about.html">關於</a><a href="{p}treatments.html">療程主題</a>'
            f'<a href="{p}letters/index.html">文章</a><a href="{p}faq.html">FAQ</a><a href="{p}consult.html">諮詢</a></nav>\n'
            f'      <p class="footer-links"><a href="{LINE_URL}" rel="noopener">官方 LINE</a>'
            f'<a href="{NEWS_URL}" rel="noopener">電子報</a><a href="{p}feed.xml">RSS</a></p>\n'
            f'      <p class="fine">{BRAND}｜{FOOTER_NOTE}</p>\n'
            f'    </footer>')


def script_block(p: str) -> str:
    return f'<script src="{p}assets/yubai.js?v={ASSET_VER}" defer></script>'


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

def theme_page(text: str, p: str, page_path: Path | None = None, make_webp: bool = False) -> str:
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
    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
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
    return {
        "file": name, "issue": m.group(1), "title": _strip(h1.group(1)),
        "desc": html.unescape(desc.group(1)) if desc else "", "date": date_s, "img": img_rel,
    }


def collect(repo: Path, extra: dict[str, str] | None = None) -> list[dict]:
    pages = {}
    for f in (repo / "letters").glob("*.html"):
        pages[f.name] = f.read_text(encoding="utf-8")
    for k, v in (extra or {}).items():
        pages[k] = v
    metas = [a for n, t in pages.items() if (a := article_meta(n, t, repo))]
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
    return f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>《蘇菲餘白》文章｜醫美判斷力筆記</title>
    <meta name="description" content="蘇菲餘白文章庫：每篇只拆一個醫美判斷題，從療程、預算、風險到診所話術，幫你把問題問對。" />
    <meta property="og:title" content="《蘇菲餘白》文章｜醫美判斷力筆記" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="{SITE_URL}/assets/sophie-portrait-laugh.jpg" />
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
          <figure class="letter-portrait"><img src="../assets/sophie-portrait-laugh.webp" alt="蘇菲在診所場景中整理醫美文章" /></figure>
        </div>
      </section>

      <section id="letters" class="section">
        <div class="section-inner">
          <div class="letters-heading">
            <h2>已發佈文章</h2>
            <p>共 {n} 篇，由新到舊排列。慢慢讀，<span class="nowrap">把醫美選擇從焦慮裡拿回來。</span></p>
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
<meta property="og:image" content="{SITE_URL}/assets/sophie-portrait-clinic.jpg" />
<link rel="canonical" href="{SITE_URL}/" />
<link rel="alternate" type="application/rss+xml" title="{BRAND}" href="feed.xml" />
{head_block("", home=True)}
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
    <div class="card-grid">
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
    return {"letters/index.html": render_letters_index(metas), "index.html": render_home(metas)}


# ---------------------------------------------------------------- 全站重套

def apply_theme(repo: Path) -> list[str]:
    touched = []
    targets = [(f, "") for f in repo.glob("*.html") if f.name not in ("index.html", "404.html")]
    targets += [(f, "../") for f in (repo / "letters").glob("*.html") if f.name != "index.html"]
    targets += [(f, "../") for f in (repo / "topics").glob("*.html")]
    for f, p in targets:
        old = f.read_text(encoding="utf-8")
        new = theme_page(old, p, page_path=f, make_webp=True)
        if new != old:
            f.write_text(new, encoding="utf-8", newline="\n")
            touched.append(f.relative_to(repo).as_posix())
    # 文章列表與首頁會引用的固定圖
    ensure_webp(repo / "assets" / "sophie-portrait-laugh.jpg")
    for rel, text in build_indexes(repo).items():
        f = repo / rel
        if not f.exists() or f.read_text(encoding="utf-8") != text:
            f.write_text(text, encoding="utf-8", newline="\n")
            touched.append(rel)
    return touched


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import argparse
    ap = argparse.ArgumentParser(description="蘇菲餘白：全站套用版型／重建首頁與文章列表")
    ap.add_argument("cmd", choices=["apply-theme", "indexes"])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    if args.cmd == "apply-theme":
        changed = apply_theme(repo)
    else:
        changed = []
        for rel, text in build_indexes(repo).items():
            (repo / rel).write_text(text, encoding="utf-8", newline="\n")
            changed.append(rel)
    print(f"changed {len(changed)} files")
    for c in changed:
        print("  " + c)
