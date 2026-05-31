from __future__ import annotations

import csv
import html
import re
import shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "outputs" / "sophie-fb-2026-05-26-to-2026-06-01"
SITE_URL = "https://deepgill1004-hue.github.io/feifei-yubai-site"
ASSET_VERSION = "20260531-1"


POSTS = [
    {
        "issue": "022",
        "date": "2026-05-26",
        "time": "09:00:00",
        "source_date": "5/26",
        "slug": "sun-shu-mei-aging-daily-care",
        "category": "凍齡保養",
        "label": "孫淑媚開球｜日常保養",
        "description": "孫淑媚開球被讚凍齡，真正值得學的不是神秘醫生，而是防曬、睡眠、運動與日常自律。",
        "takeaways": ["凍齡不是單一療程", "日常保養是基礎", "醫美只能錦上添花"],
        "asset": "sophie-fb-2026-05-26-sun-shu-mei-baseball.png",
    },
    {
        "issue": "023",
        "date": "2026-05-27",
        "time": "09:00:00",
        "source_date": "5/27",
        "slug": "oral-glp1-weight-loss-truth",
        "category": "減重醫學",
        "label": "口服 GLP-1｜減重市場",
        "description": "口服 Wegovy 與新一代減重藥讓減重更方便，但肌肉流失、臉凹與反彈風險仍然不能忽略。",
        "takeaways": ["藥物方便不等於無代價", "減重要保住肌肉", "飲食與訓練才是底層管理"],
        "asset": "sophie-fb-2026-05-27-oral-glp1.png",
    },
    {
        "issue": "024",
        "date": "2026-05-28",
        "time": "09:00:00",
        "source_date": "5/28",
        "slug": "nose-surgery-failure-doctor-myth",
        "category": "手術風險",
        "label": "隆鼻失敗｜名醫迷思",
        "description": "迷信名醫光環前，先看醫師如何溝通風險、處理併發症，以及術後是否願意負責。",
        "takeaways": ["不要迷信稱號", "術前溝通比名氣重要", "證據紀錄要留好"],
        "asset": "sophie-fb-2026-05-28-nose-failure.png",
    },
    {
        "issue": "025",
        "date": "2026-05-29",
        "time": "09:00:00",
        "source_date": "5/29",
        "slug": "clinic-privacy-hidden-camera-safety",
        "category": "診所安全",
        "label": "診所隱私｜反偷拍自保",
        "description": "醫美診所隱私危機提醒我們，療程前要檢查空間、看清同意書，並保護自己的私密界線。",
        "takeaways": ["進房間先看環境", "拒絕模糊錄影同意", "隱私保障是基本門檻"],
        "asset": "sophie-fb-2026-05-29-clinic-privacy.png",
    },
    {
        "issue": "026",
        "date": "2026-05-30",
        "time": "09:00:00",
        "source_date": "5/30",
        "slug": "work-stress-aging-cortisol",
        "category": "壓力型衰老",
        "label": "職場女性｜壓力型衰老",
        "description": "長期高壓會透過皮質醇影響膠原蛋白、屏障與循環，讓疲憊直接寫在臉上。",
        "takeaways": ["壓力會加速膠原流失", "皮膚屏障也會受影響", "抗老要從壓力管理開始"],
        "asset": "sophie-fb-2026-05-30-work-stress-aging.png",
    },
    {
        "issue": "027",
        "date": "2026-05-31",
        "time": "09:00:00",
        "source_date": "5/31",
        "slug": "aesthetic-safety-fears-open-discussion",
        "category": "醫美安全",
        "label": "互動討論｜醫美恐懼",
        "description": "怕失敗、怕痛、怕被偷拍、怕被推銷，先把恐懼說出來，才有機會做出清醒選擇。",
        "takeaways": ["恐懼值得被看見", "資訊不對稱需要拆開", "留言提問比硬撐更有用"],
        "asset": "sophie-fb-2026-05-31-aesthetic-fear-comments.png",
    },
    {
        "issue": "028",
        "date": "2026-06-01",
        "time": "09:00:00",
        "source_date": "6/1",
        "slug": "longevity-medicine-cell-aging-reversal",
        "category": "長壽醫學",
        "label": "細胞衰老｜逆齡醫學",
        "description": "長壽醫學把抗老從表面修補推向細胞管理，未來醫美會更靠近預防醫學與健康壽命。",
        "takeaways": ["抗老正在走向細胞層級", "健康壽命比單純長壽重要", "生活習慣也是細胞投資"],
        "asset": "sophie-fb-2026-06-01-longevity-medicine.png",
    },
]


def read_package_rows() -> dict[str, dict[str, str]]:
    with (PACKAGE_DIR / "upload-index.csv").open(encoding="utf-8-sig", newline="") as csv_file:
        return {row["date"]: row for row in csv.DictReader(csv_file)}


def read_post_body(post_file: str) -> tuple[str, str]:
    text = (PACKAGE_DIR / post_file).read_text(encoding="utf-8")
    title_match = re.search(r"^建議標題：(.+)$", text, flags=re.M)
    body = text.split("\n\n", 1)[1].strip()
    return title_match.group(1).strip(), body


def paragraphs_from_body(body: str) -> list[str]:
    paragraphs = []
    current = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            if current:
                paragraphs.append("".join(current))
                current = []
            continue
        if re.match(r"^\d+\.\s", line):
            if current:
                paragraphs.append("".join(current))
            paragraphs.append(line)
            current = []
        else:
            current.append(line)
    if current:
        paragraphs.append("".join(current))
    return paragraphs


def render_body(body: str) -> str:
    html_parts = []
    list_open = False
    for paragraph in paragraphs_from_body(body):
        if re.match(r"^\d+\.\s", paragraph):
            if not list_open:
                html_parts.append('          <ol class="letter-checks">')
                list_open = True
            html_parts.append(f"            <li>{html.escape(re.sub(r'^\\d+\\.\\s*', '', paragraph))}</li>")
        else:
            if list_open:
                html_parts.append("          </ol>")
                list_open = False
            css_class = ' class="lead"' if not html_parts else ""
            html_parts.append(f"          <p{css_class}>{html.escape(paragraph)}</p>")
    if list_open:
        html_parts.append("          </ol>")
    return "\n".join(html_parts)


def render_article(post: dict[str, str], title: str, body: str) -> str:
    file_name = f"{post['issue']}-{post['slug']}.html"
    canonical = f"{SITE_URL}/letters/{file_name}"
    image = f"../assets/{post['asset']}"
    title_text = f"{title}｜蘇菲餘白"
    sidebar_items = "\n".join(f"              <li>{html.escape(item)}</li>" for item in post["takeaways"])
    return f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title_text)}</title>
    <meta name="description" content="{html.escape(post['description'])}" />
    <meta property="og:title" content="{html.escape(title)}" />
    <meta property="og:description" content="{html.escape(post['description'])}" />
    <meta property="og:type" content="article" />
    <meta property="og:image" content="{html.escape(f'../assets/{post["asset"]}')}" />
    <link rel="canonical" href="{html.escape(canonical)}" />
    <link rel="stylesheet" href="../assets/styles-v2.css?v={ASSET_VERSION}" />
  </head>
  <body>
    <header class="site-header" aria-label="主要導覽">
      <a class="brand" href="../index.html">蘇菲餘白</a>
      <nav>
        <a href="../about.html">關於</a>
        <a href="../treatments.html">療程主題</a>
        <a href="./index.html">文章</a>
        <a href="../faq.html">FAQ</a>
        <a href="../consult.html">諮詢</a>
      </nav>
    </header>
    <main>
      <section class="letter-masthead">
        <div class="section-inner letter-masthead-grid">
          <div>
            <p class="eyebrow">{post['date']} 新上架</p>
            <h1>{html.escape(title)}</h1>
            <p class="letter-dek">{html.escape(post['description'])}</p>
            <div class="letter-meta-row">
              <span>{post['issue']}</span>
              <span>{html.escape(post['category'])}</span>
              <span>{html.escape(post['label'])}</span>
            </div>
          </div>
          <figure class="letter-portrait">
            <img src="{html.escape(image)}" alt="{html.escape(post['label'])}" />
          </figure>
        </div>
      </section>
      <section class="section">
        <div class="section-inner letter-reading-grid">
          <aside class="letter-sidebar">
            <p class="path-label">這篇先看</p>
            <ol>
{sidebar_items}
            </ol>
            <div class="panel-actions">
              <a class="button primary" href="https://line.me/R/ti/p/@371arhqu" rel="noopener">加入 LINE</a>
              <a class="button secondary" href="./index.html">回文章列表</a>
            </div>
          </aside>
          <article class="letter-body">
{render_body(body)}
            <section class="letter-cta">
              <h2>把問題帶進諮詢前，先整理清楚</h2>
              <p>如果妳正在考慮療程，不要只問價格。先把擔心、預算、恢復期和期待效果寫下來，讓諮詢變成判斷，而不是被推銷。</p>
              <div class="panel-actions">
                <a class="button primary" href="../consult.html">整理我的諮詢問題</a>
                <a class="button secondary" href="https://line.me/R/ti/p/@371arhqu" rel="noopener">加入官方 LINE</a>
              </div>
            </section>
          </article>
        </div>
      </section>
    </main>
    <footer class="site-footer">
      <p>蘇菲餘白提供醫美知識整理與判斷力筆記，不能取代醫師當面診斷。</p>
    </footer>
  </body>
</html>
"""


def render_index_item(post: dict[str, str], title: str) -> str:
    file_name = f"{post['issue']}-{post['slug']}.html"
    return f"""            <article class="letter-item">
              <a href="./{file_name}" aria-label="閱讀 {html.escape(title)}">
                <span class="letter-issue">{post['issue']}</span>
                <div>
                  <p class="path-label">{html.escape(post['date'])}｜{html.escape(post['category'])}</p>
                  <h3>{html.escape(title)}</h3>
                  <p>{html.escape(post['description'])}</p>
                </div>
              </a>
            </article>

"""


def update_index(items: str) -> None:
    path = ROOT / "letters" / "index.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'\s*<article class="letter-item">\s*<a href="\./0(?:22|23|24|25|26|27|28)-[\s\S]*?</article>\n*',
        "\n",
        text,
    )
    marker = '          <div class="letter-list">\n'
    text = text.replace(marker, marker + items, 1)
    text = re.sub(r"\n{3,}", "\n\n", text)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_feed_item(post: dict[str, str], title: str, body: str) -> str:
    file_name = f"{post['issue']}-{post['slug']}.html"
    link = f"{SITE_URL}/letters/{file_name}"
    dt = datetime.fromisoformat(f"{post['date']}T{post['time']}+08:00").astimezone(timezone.utc)
    excerpt = paragraphs_from_body(body)[0]
    return f"""    <item>
      <title>{escape(title)}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <pubDate>{format_datetime(dt, usegmt=True)}</pubDate>
      <description><![CDATA[{post['description']}]]></description>
      <content:encoded><![CDATA[<p>{html.escape(excerpt)}</p>]]></content:encoded>
    </item>
"""


def update_feed(items: str) -> None:
    path = ROOT / "feed.xml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'\s*<item>\s*<title>[\s\S]*?letters/0(?:22|23|24|25|26|27|28)-[\s\S]*?</item>\n*',
        "\n",
        text,
    )
    latest = format_datetime(datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc), usegmt=True)
    text = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", f"<lastBuildDate>{latest}</lastBuildDate>", text, count=1)
    marker = "    <item>\n"
    text = text.replace(marker, items + marker, 1)
    text = re.sub(r"\n{3,}", "\n\n", text)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_sitemap_url(post: dict[str, str]) -> str:
    file_name = f"{post['issue']}-{post['slug']}.html"
    return f"""  <url>
    <loc>{SITE_URL}/letters/{file_name}</loc>
    <lastmod>{post['date']}</lastmod>
  </url>
"""


def update_sitemap(items: str) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'\s*<url>\s*<loc>https://deepgill1004-hue\.github\.io/feifei-yubai-site/letters/0(?:22|23|24|25|26|27|28)-[\s\S]*?</url>\n*',
        "\n",
        text,
    )
    text = text.replace("  <url>\n    <loc>https://deepgill1004-hue.github.io/feifei-yubai-site/letters/</loc>\n    <lastmod>2026-05-21</lastmod>\n  </url>",
                        "  <url>\n    <loc>https://deepgill1004-hue.github.io/feifei-yubai-site/letters/</loc>\n    <lastmod>2026-06-01</lastmod>\n  </url>",
                        1)
    marker = "  <url>\n    <loc>https://deepgill1004-hue.github.io/feifei-yubai-site/letters/012-regenerative-medicine-structure-reset.html</loc>"
    text = text.replace(marker, items + marker, 1)
    text = re.sub(r"\n{3,}", "\n\n", text)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    rows = read_package_rows()
    index_items = []
    feed_items = []
    sitemap_items = []

    published = []

    for post in POSTS:
        row = rows[post["source_date"]]
        title, body = read_post_body(row["post_file"])

        source_image = PACKAGE_DIR / row["image_file"]
        target_image = ROOT / "assets" / post["asset"]
        shutil.copy2(source_image, target_image)

        article_path = ROOT / "letters" / f"{post['issue']}-{post['slug']}.html"
        article_path.write_text(render_article(post, title, body), encoding="utf-8", newline="\n")

        published.append((post, title, body))
        sitemap_items.append(render_sitemap_url(post))

    for post, title, body in reversed(published):
        index_items.append(render_index_item(post, title))
        feed_items.append(render_feed_item(post, title, body))

    update_index("".join(index_items))
    update_feed("".join(feed_items))
    update_sitemap("".join(sitemap_items))
    print("Published 7 Sophie FB posts to the static site.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
