from __future__ import annotations

import csv
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = Path(r"C:\Users\user\Downloads\FB_5月26-6月1_發布文案_最終版_v4.pdf")
TEMPLATE_DIR = Path(r"C:\Users\user\Downloads\蘇菲形象\蘇菲模板")
OUTPUT_DIR = ROOT / "outputs" / "sophie-fb-2026-05-26-to-2026-06-01"


@dataclass(frozen=True)
class ImagePick:
    slug: str
    source_name: str
    note: str


IMAGE_PICKS = {
    "5-26": ImagePick(
        "2026-05-26-sun-shu-mei-baseball.png",
        "sophie_sunshumi_baseball.png",
        "孫淑媚開球、凍齡與日常保養主題",
    ),
    "5-27": ImagePick(
        "2026-05-27-oral-glp1.png",
        "sophie_oral_glp1.png",
        "口服 GLP-1 / Wegovy 減重市場主題",
    ),
    "5-28": ImagePick(
        "2026-05-28-nose-failure.png",
        "sophie_nose_fail.png",
        "隆鼻失敗、名醫迷思與醫美糾紛主題",
    ),
    "5-29": ImagePick(
        "2026-05-29-clinic-privacy.png",
        "day4_clinic_consult.png",
        "診所隱私與反偷拍自保主題",
    ),
    "5-30": ImagePick(
        "2026-05-30-work-stress-aging.png",
        "day5_office_night.png",
        "職場女性壓力與壓力型衰老主題",
    ),
    "5-31": ImagePick(
        "2026-05-31-aesthetic-fear-comments.png",
        "day6_cafe_friends.png",
        "互動留言、醫美安全恐懼討論主題",
    ),
    "6-1": ImagePick(
        "2026-06-01-longevity-medicine.png",
        "day7_lab_longevity.png",
        "細胞衰老逆轉與長壽醫學主題",
    ),
}


def extract_pdf_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)


def tidy_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "5⁄26": "5/26",
        "5⁄27": "5/27",
        "5⁄28": "5/28",
        "5⁄29": "5/29",
        "5⁄30": "5/30",
        "5⁄31": "5/31",
        "6⁄1": "6/1",
        "——": "—",
        "⸺": "—",
        "@ 371arhqu": "@371arhqu",
        "https://deepgill1004-\nhue.github.io": "https://deepgill1004-hue.github.io",
        "https://sophie-yubai.beehiiv.com /\n": "https://sophie-yubai.beehiiv.com/\n",
        "https://sophie-yubai.beehiiv.com /": "https://sophie-yubai.beehiiv.com/",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"(?<=[\u4e00-\u9fff]),", "，", text)
    text = re.sub(r",(?=[\u4e00-\u9fff])", "，", text)
    text = text.replace("!", "！").replace("?", "？")
    text = re.sub(r"(?<!https)(?<!http):(?!//)", "：", text)

    lines = []
    for line in text.splitlines():
        line = line.rstrip()
        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")
    return "\n".join(lines).strip()


def join_wrapped_lines(text: str) -> str:
    lines = text.splitlines()
    merged: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if merged and merged[-1] != "":
                merged.append("")
            continue

        if not merged or merged[-1] == "":
            merged.append(stripped)
            continue

        prev = merged[-1]
        starts_new = bool(
            re.match(r"^(週|標題選項|文案|互動引導：|\d+\.\s|想知道更多|1\.|2\.|3\.)", stripped)
        )
        prev_ends = prev.endswith(("。", "！", "？", "：", "；", "」", "/", "）"))
        if starts_new or prev_ends:
            merged.append(stripped)
        else:
            merged[-1] = prev + stripped
    return "\n".join(merged)


def parse_posts(text: str) -> list[dict[str, str]]:
    text = tidy_text(text)
    pattern = re.compile(r"(?=週[一二三四五六日]\s+\d+/\d+\s+—)")
    chunks = [chunk.strip() for chunk in pattern.split(text) if chunk.strip().startswith("週")]
    posts = []

    for chunk in chunks:
        chunk = join_wrapped_lines(tidy_text(chunk))
        header = chunk.splitlines()[0]
        header_match = re.match(r"週(?P<weekday>[一二三四五六日])\s+(?P<date>\d+/\d+)\s+—\s+(?P<theme>.+)", header)
        if not header_match:
            raise ValueError(f"Cannot parse post header: {header}")

        title_match = re.search(r"1\.\s*(.+)", chunk)
        if not title_match:
            raise ValueError(f"Cannot parse title option for: {header}")

        body_match = re.search(r"文案\s*\n?(?P<body>.+)", chunk, flags=re.S)
        if not body_match:
            raise ValueError(f"Cannot parse body for: {header}")

        date_key = header_match.group("date").replace("/", "-")
        body = body_match.group("body").strip()
        posts.append(
            {
                "weekday": "週" + header_match.group("weekday"),
                "date": header_match.group("date"),
                "date_key": date_key,
                "theme": header_match.group("theme").strip(),
                "title": title_match.group(1).strip(),
                "body": body,
            }
        )

    if len(posts) != 7:
        raise ValueError(f"Expected 7 posts, got {len(posts)}")
    return posts


def image_size(path: Path) -> str:
    with Image.open(path) as image:
        return f"{image.width}x{image.height}"


def write_outputs(posts: list[dict[str, str]]) -> None:
    posts_dir = OUTPUT_DIR / "posts"
    images_dir = OUTPUT_DIR / "images"
    posts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    overview_lines = [
        "# 蘇菲餘白 FB 上架包｜2026-05-26 至 2026-06-01",
        "",
        f"來源 PDF：`{PDF_PATH}`",
        f"上架圖來源：`{TEMPLATE_DIR}`",
        "",
        "## 發布清單",
        "",
    ]

    for index, post in enumerate(posts, start=1):
        pick = IMAGE_PICKS[post["date_key"]]
        source_image = TEMPLATE_DIR / pick.source_name
        if not source_image.exists():
            raise FileNotFoundError(source_image)

        target_image = images_dir / pick.slug
        shutil.copy2(source_image, target_image)
        size = image_size(target_image)

        post_file = posts_dir / f"{index:02d}_{post['date'].replace('/', '-')}_fb.txt"
        post_text = (
            f"{post['weekday']} {post['date']} — {post['theme']}\n"
            f"建議標題：{post['title']}\n"
            f"上架圖：../images/{pick.slug}\n\n"
            f"{post['body']}\n"
        )
        post_file.write_text(post_text, encoding="utf-8", newline="\n")

        rows.append(
            {
                "order": index,
                "date": post["date"],
                "weekday": post["weekday"],
                "theme": post["theme"],
                "suggested_title": post["title"],
                "post_file": str(post_file.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                "image_file": str(target_image.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                "image_source": str(source_image),
                "image_size": size,
                "image_note": pick.note,
            }
        )

        overview_lines.extend(
            [
                f"### {index:02d}. {post['weekday']} {post['date']}｜{post['theme']}",
                "",
                f"- 建議標題：{post['title']}",
                f"- 文案檔：`posts/{post_file.name}`",
                f"- 上架圖：`images/{pick.slug}`（{size}）",
                f"- 圖片說明：{pick.note}",
                "",
            ]
        )

    index_path = OUTPUT_DIR / "upload-index.csv"
    with index_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    (OUTPUT_DIR / "README.md").write_text("\n".join(overview_lines), encoding="utf-8", newline="\n")
    write_contact_sheet(images_dir)


def write_contact_sheet(images_dir: Path) -> None:
    images = sorted(images_dir.glob("*.png"))
    if not images:
        return

    cell_width = 240
    cell_height = 310
    thumb_width = 190
    thumb_height = 253
    columns = 4
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)

    for index, image_path in enumerate(images):
        with Image.open(image_path) as image:
            thumbnail = image.convert("RGB")
            thumbnail.thumbnail((thumb_width, thumb_height))

        x = (index % columns) * cell_width + 25
        y = (index // columns) * cell_height + 20
        sheet.paste(thumbnail, (x, y))
        draw.text((x, y + thumb_height + 8), image_path.stem[:30], fill=(0, 0, 0))

    sheet.save(OUTPUT_DIR / "contact-sheet.jpg", quality=92)


def main() -> int:
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH}", file=sys.stderr)
        return 1
    if not TEMPLATE_DIR.exists():
        print(f"Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    text = extract_pdf_text(PDF_PATH)
    posts = parse_posts(text)
    write_outputs(posts)
    print(f"Prepared {len(posts)} FB posts in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
