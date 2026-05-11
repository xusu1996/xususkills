#!/usr/bin/env python3
import argparse
import base64
import html
import json
import math
import re
import unicodedata
from datetime import date
from pathlib import Path

WIDTH = 1080
HEIGHT = 1440
MARGIN = 80
CONTENT_W = WIDTH - MARGIN * 2
TOP = 86
FOOTER_Y = 1366
BOTTOM_LIMIT = 1318
FOOTER_SAFE_GAP = 44
BODY_FONT_SIZE = 38
BODY_LINE_HEIGHT = 58
BLANK_LINE_HEIGHT = 28
BUBBLE_PADDING_X = 36
BUBBLE_PADDING_Y = 34
IMAGE_MAX_W = CONTENT_W
IMAGE_MAX_H = 1080
IMAGE_RADIUS = 22
TITLE_TEXT = "徐宿的思维进化日记"
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif"

THEMES = {
    "dark": {
        "bg": "#1F1F1F",
        "panel": "#1F1F1F",
        "panel_border": "#2D2D2D",
        "user": "#36D38B",
        "user_text": "#07150E",
        "assistant": "#303136",
        "assistant_border": "none",
        "assistant_text": "#ECECF1",
        "text": "#F2F2F2",
        "muted": "#A5A5AA",
        "weak": "#85858B",
    },
    "light": {
        "bg": "#FFFFFF",
        "panel": "#FFFFFF",
        "panel_border": "#E8E8E8",
        "user": "#9CF3A1",
        "user_text": "#07150E",
        "assistant": "#F0F0F2",
        "assistant_border": "none",
        "assistant_text": "#1F1F1F",
        "text": "#1F1F1F",
        "muted": "#88888E",
        "weak": "#A2A2A8",
    },
}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]

PRIVACY_PATTERNS = [
    (re.compile(r"/Users/[^>\n)]+"), "[本地路径已隐藏]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{12,}"), "[已隐藏]"),
    (re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[^'\"\s]+"), r"\1=[已隐藏]"),
    (re.compile(r"\b1[3-9]\d{9}\b"), "[手机号已隐藏]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[邮箱已隐藏]"),
]


def display_width(text):
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def normalize_markdown_for_display(text):
    lines = []
    in_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line)
        line = re.sub(r"^\s{0,3}>\s?", "", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        if in_fence:
            lines.append(line)
        else:
            lines.append(line.rstrip())
    return "\n".join(lines).strip()


def clean_text(text, preserve_privacy=True, render_markdown=False):
    text = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    if preserve_privacy:
        for pattern, replacement in PRIVACY_PATTERNS:
            text = pattern.sub(replacement, text)
    if render_markdown:
        text = normalize_markdown_for_display(text)
    return text


def pil_modules():
    try:
        from PIL import Image, ImageDraw
    except ModuleNotFoundError as exc:
        if exc.name == "PIL":
            raise SystemExit("Image rendering requires Pillow. Use the bundled Python runtime or install Pillow.") from exc
        raise
    return Image, ImageDraw


def workspace_root():
    return Path(__file__).resolve().parents[3]


def slugify(value):
    value = clean_text(value or "对话截图", preserve_privacy=True)
    value = re.sub(r"^关于\s*", "", value).strip()
    value = re.sub(r"[\\/:*?\"<>|#%&{}$!@`+=]+", "", value)
    value = re.sub(r"\s+", "-", value)
    value = value.strip("-._ ")
    return value[:32] or "对话截图"


def default_output_dir(data):
    root = workspace_root()
    topic = data.get("subtitle") or data.get("title") or "对话截图"
    folder = f"{date.today().isoformat()}-{slugify(topic)}"
    return root / "Codex应用工作台" / "4-对话截图卡片" / "exports" / folder


def resolve_path(value, base_dir):
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    candidate = base_dir / path
    if candidate.exists():
        return candidate
    return workspace_root() / path


def mime_type(path):
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def image_dimensions(path):
    Image, _ = pil_modules()
    with Image.open(path) as img:
        return img.size


def display_image_size(path):
    src_w, src_h = image_dimensions(path)
    scale = min(IMAGE_MAX_W / src_w, IMAGE_MAX_H / src_h, 1)
    return max(1, round(src_w * scale)), max(1, round(src_h * scale))


def normalize_image_item(item, base_dir):
    if isinstance(item, str):
        path_value = item
        caption = ""
    else:
        path_value = item.get("path") or item.get("src") or item.get("file")
        caption = item.get("caption", "")
    if not path_value:
        return None
    path = resolve_path(path_value, base_dir)
    if not path.exists():
        raise SystemExit(f"Image not found: {path}")
    width, height = display_image_size(path)
    return {
        "type": "image",
        "path": str(path),
        "caption": clean_text(caption, preserve_privacy=True, render_markdown=True),
        "width": width,
        "height": height,
    }


def wrap_paragraph(paragraph, max_units):
    lines = []
    current = ""
    current_w = 0
    for char in paragraph:
        char_w = 2 if unicodedata.east_asian_width(char) in ("F", "W") else 1
        if current and current_w + char_w > max_units:
            lines.append(current)
            current = char
            current_w = char_w
        else:
            current += char
            current_w += char_w
    lines.append(current)
    return lines


def wrap_text(text, max_units):
    lines = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            lines.append("")
        else:
            lines.extend(wrap_paragraph(paragraph, max_units))
    return lines


def line_height(line):
    return BLANK_LINE_HEIGHT if line == "" else BODY_LINE_HEIGHT


def lines_height(lines):
    return sum(line_height(line) for line in lines)


def is_heading_line(line):
    return bool(re.match(r"^\s*(\d+[.、]|[一二三四五六七八九十]+[、.])\s*\S+", line))


def chunk_has_readable_start(chunk, remaining):
    if not remaining:
        return True
    visible = [line for line in chunk if line.strip()]
    if len(visible) >= 2:
        return True
    if len(visible) == 1 and not is_heading_line(visible[0]):
        return True
    return False


def take_lines_by_height(lines, available_h):
    if available_h < BODY_LINE_HEIGHT:
        return []
    taken = []
    used = 0
    for line in lines:
        h = line_height(line)
        if taken and used + h > available_h:
            break
        if not taken and h > available_h:
            return []
        taken.append(line)
        used += h
    return taken


def message_blocks(messages, preserve_privacy=True, base_dir=None):
    blocks = []
    base_dir = base_dir or Path.cwd()
    for message in messages:
        role = message.get("role", "assistant")
        text = clean_text(message.get("text", ""), preserve_privacy=preserve_privacy, render_markdown=True)
        image_blocks = []
        for item in message.get("images", []):
            image_block = normalize_image_item(item, base_dir)
            if image_block:
                image_block["role"] = role
                image_blocks.append(image_block)
        blocks.extend(image_blocks)
        if not text:
            continue
        max_units = 30 if role == "user" else 34
        lines = wrap_text(text, max_units)
        blocks.append(
            {
                "role": role,
                "lines": lines,
                "continued": False,
                "continues": False,
            }
        )
    return blocks


def block_height(block):
    if block.get("type") == "image":
        caption_h = 68 if block.get("caption") else 0
        return block["height"] + caption_h
    label_h = 28 if block.get("continued") else 0
    return BUBBLE_PADDING_Y * 2 + lines_height(block["lines"]) + label_h


def page_start_y(page_num):
    return TOP + 100 if page_num == 1 else 86


def paginate(blocks):
    pages = []
    current = []
    page_num = 1
    y = page_start_y(page_num)
    for block in blocks:
        if block.get("type") == "image":
            gap = 28 if current else 0
            h = block_height(block)
            if current and y + gap + h > BOTTOM_LIMIT - FOOTER_SAFE_GAP:
                pages.append(current)
                page_num += 1
                current = []
                y = page_start_y(page_num)
                gap = 0
            current.append(block)
            y += gap + h
            continue

        remaining = list(block["lines"])
        first_chunk = True
        while remaining:
            continued = (not first_chunk) or block.get("continued", False)
            gap = 28 if current else 0
            label_h = 28 if continued else 0
            available_h = BOTTOM_LIMIT - FOOTER_SAFE_GAP - y - gap - BUBBLE_PADDING_Y * 2 - label_h
            chunk_lines = take_lines_by_height(remaining, available_h)

            if not chunk_lines:
                if current:
                    pages.append(current)
                    page_num += 1
                    current = []
                    y = page_start_y(page_num)
                    continue
                chunk_lines = remaining[:1]

            if current and not chunk_has_readable_start(chunk_lines, remaining[len(chunk_lines):]):
                pages.append(current)
                page_num += 1
                current = []
                y = page_start_y(page_num)
                continue

            remaining = remaining[len(chunk_lines):]
            chunk = {
                "role": block["role"],
                "lines": chunk_lines,
                "continued": continued,
                "continues": bool(remaining),
            }
            current.append(chunk)
            y += gap + block_height(chunk)
            first_chunk = False

            if remaining and y >= BOTTOM_LIMIT - FOOTER_SAFE_GAP - BUBBLE_PADDING_Y * 2:
                pages.append(current)
                page_num += 1
                current = []
                y = page_start_y(page_num)
    if current:
        pages.append(current)
    return pages


def svg_text_lines(lines, x, y, color, font_size=BODY_FONT_SIZE):
    parts = []
    cursor_y = y
    for line in lines:
        if line:
            parts.append(
                f'<text x="{x}" y="{cursor_y}" fill="{color}" font-size="{font_size}" '
                f'font-family="{FONT_FAMILY}" xml:space="preserve">{html.escape(line)}</text>'
            )
        cursor_y += line_height(line)
    return "\n".join(parts)


def image_data_url(path):
    path = Path(path)
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type(path)};base64,{data}"


def render_image_block(block, y, theme, block_id):
    width = block["width"]
    height = block["height"]
    x = (WIDTH - width) / 2
    caption = block.get("caption", "")
    clip_id = f"image-clip-{block_id}"
    data_url = image_data_url(block["path"])
    parts = [
        f'<clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{IMAGE_RADIUS}"/></clipPath>',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{IMAGE_RADIUS}" fill="{theme["assistant"]}"/>',
        f'<image x="{x}" y="{y}" width="{width}" height="{height}" href="{data_url}" clip-path="url(#{clip_id})" preserveAspectRatio="xMidYMid meet"/>',
    ]
    if caption:
        parts.append(
            f'<text x="{x}" y="{y + height + 44}" fill="{theme["weak"]}" font-size="24" font-family="{FONT_FAMILY}">{html.escape(caption)}</text>'
        )
    return "\n".join(parts)


def render_text_block(block, y, theme):
    role = block["role"]
    lines = block["lines"]
    is_user = role == "user"
    line_max = max([display_width(line) for line in lines] or [1])
    text_w = min(790 if is_user else 880, max(280, math.ceil(line_max * 19.2)))
    bubble_w = text_w + BUBBLE_PADDING_X * 2
    x = WIDTH - MARGIN - bubble_w if is_user else MARGIN
    fill = theme["user"] if is_user else theme["assistant"]
    stroke = "none" if is_user else theme["assistant_border"]
    text_color = theme["user_text"] if is_user else theme["assistant_text"]
    h = block_height(block)
    label = "继续" if block.get("continued") else ""

    stroke_attr = "" if stroke == "none" else f' stroke="{stroke}" stroke-width="1.5"'
    if is_user:
        tail = f'<path d="M {x + bubble_w - 18} {y + 22} C {x + bubble_w + 12} {y + 24}, {x + bubble_w + 18} {y + 34}, {x + bubble_w + 2} {y + 48} L {x + bubble_w - 12} {y + 38} Z" fill="{fill}"/>'
    else:
        tail = f'<path d="M {x + 18} {y + 22} C {x - 12} {y + 24}, {x - 18} {y + 34}, {x - 2} {y + 48} L {x + 12} {y + 38} Z" fill="{fill}"/>'

    parts = [
        tail,
        f'<rect x="{x}" y="{y}" width="{bubble_w}" height="{h}" rx="18" fill="{fill}"{stroke_attr}/>'
    ]
    text_y = y + 56
    if label:
        parts.append(
            f'<text x="{x + 36}" y="{y + 40}" fill="{theme["weak"]}" font-size="22" font-family="{FONT_FAMILY}">{label}</text>'
        )
        text_y += 28
    parts.append(svg_text_lines(lines, x + BUBBLE_PADDING_X, text_y, text_color))
    return "\n".join(parts)


def render_block(block, y, theme, block_id):
    if block.get("type") == "image":
        return render_image_block(block, y, theme, block_id)
    return render_text_block(block, y, theme)


def render_page(data, page_blocks, page_num, total_pages, theme_name):
    theme = THEMES[theme_name]
    subtitle = clean_text(data.get("subtitle", "关于 AI 共创"), preserve_privacy=True)
    if subtitle and not subtitle.startswith("关于"):
        subtitle = f"关于 {subtitle}"
    source = clean_text(data.get("source", ""), preserve_privacy=True)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{theme["bg"]}"/>',
    ]
    if page_num == 1:
        parts.extend(
            [
                f'<text x="{MARGIN}" y="{TOP}" fill="{theme["text"]}" font-size="34" font-weight="650" font-family="{FONT_FAMILY}">{html.escape(TITLE_TEXT)}</text>',
                f'<text x="{MARGIN}" y="{TOP + 48}" fill="{theme["muted"]}" font-size="22" font-family="{FONT_FAMILY}">{html.escape(subtitle)}</text>',
            ]
        )
    y = page_start_y(page_num)
    for index, block in enumerate(page_blocks):
        if index:
            y += 28
        parts.append(render_block(block, y, theme, f"{page_num}-{index}"))
        y += block_height(block)

    footer_left = source if source else "真实对话节选"
    footer_right = f"{page_num}/{total_pages}"
    parts.extend(
        [
            f'<text x="{MARGIN}" y="{FOOTER_Y}" fill="{theme["weak"]}" font-size="20" font-family="{FONT_FAMILY}">{html.escape(footer_left)}</text>',
            f'<text x="{WIDTH - MARGIN}" y="{FOOTER_Y}" fill="{theme["weak"]}" text-anchor="end" font-size="20" font-family="{FONT_FAMILY}">{footer_right}</text>',
            "</svg>",
        ]
    )
    return "\n".join(parts)


def font_path():
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def load_pil_font(size):
    from PIL import ImageFont

    path = font_path()
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def draw_multiline(draw, xy, lines, fill, font):
    x, y = xy
    for line in lines:
        if line:
            draw.text((x, y), line, fill=fill, font=font)
        y += line_height(line)


def rounded_paste(base, img, box, radius):
    Image, ImageDraw = pil_modules()
    x, y, width, height = box
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    base.paste(img, (x, y), mask)


def render_png_image_block(image, draw, block, y, theme, caption_font):
    Image, _ = pil_modules()
    width = block["width"]
    height = block["height"]
    x = round((WIDTH - width) / 2)
    draw.rounded_rectangle((x, y, x + width, y + height), radius=IMAGE_RADIUS, fill=theme["assistant"])
    with Image.open(block["path"]) as src:
        src = src.convert("RGB")
        src.thumbnail((width, height), Image.LANCZOS)
        canvas = Image.new("RGB", (width, height), theme["assistant"])
        paste_x = (width - src.width) // 2
        paste_y = (height - src.height) // 2
        canvas.paste(src, (paste_x, paste_y))
    rounded_paste(image, canvas, (x, y, width, height), IMAGE_RADIUS)
    if block.get("caption"):
        draw.text((x, y + height + 16), block["caption"], fill=theme["weak"], font=caption_font)


def render_png_page(data, page_blocks, page_num, total_pages, theme_name, output):
    from PIL import Image, ImageDraw

    theme = THEMES[theme_name]
    image = Image.new("RGB", (WIDTH, HEIGHT), theme["bg"])
    draw = ImageDraw.Draw(image)

    title_font = load_pil_font(34)
    subtitle_font = load_pil_font(22)
    body_font = load_pil_font(BODY_FONT_SIZE)
    weak_font = load_pil_font(22)

    subtitle = clean_text(data.get("subtitle", "关于 AI 共创"), preserve_privacy=True)
    if subtitle and not subtitle.startswith("关于"):
        subtitle = f"关于 {subtitle}"
    source = clean_text(data.get("source", ""), preserve_privacy=True)

    if page_num == 1:
        draw.text((MARGIN, TOP - 32), TITLE_TEXT, fill=theme["text"], font=title_font)
        draw.text((MARGIN, TOP + 18), subtitle, fill=theme["muted"], font=subtitle_font)

    y = page_start_y(page_num)
    for index, block in enumerate(page_blocks):
        if index:
            y += 28
        if block.get("type") == "image":
            render_png_image_block(image, draw, block, y, theme, weak_font)
            y += block_height(block)
            continue
        role = block["role"]
        is_user = role == "user"
        lines = block["lines"]
        line_max = max([display_width(line) for line in lines] or [1])
        text_w = min(790 if is_user else 880, max(280, math.ceil(line_max * 19.2)))
        bubble_w = text_w + BUBBLE_PADDING_X * 2
        h = block_height(block)
        x = WIDTH - MARGIN - bubble_w if is_user else MARGIN
        fill = theme["user"] if is_user else theme["assistant"]
        text_color = theme["user_text"] if is_user else theme["assistant_text"]
        outline = None if theme["assistant_border"] == "none" or is_user else theme["assistant_border"]
        if is_user:
            tail = [
                (x + bubble_w - 18, y + 22),
                (x + bubble_w + 18, y + 34),
                (x + bubble_w + 2, y + 48),
                (x + bubble_w - 12, y + 38),
            ]
        else:
            tail = [
                (x + 18, y + 22),
                (x - 18, y + 34),
                (x - 2, y + 48),
                (x + 12, y + 38),
            ]
        draw.polygon(tail, fill=fill)
        draw.rounded_rectangle((x, y, x + bubble_w, y + h), radius=18, fill=fill, outline=outline, width=2)
        text_y = y + 36
        if block.get("continued"):
            draw.text((x + 36, text_y), "继续", fill=theme["weak"], font=weak_font)
            text_y += 28
        draw_multiline(draw, (x + BUBBLE_PADDING_X, text_y), lines, text_color, body_font)
        y += h

    footer_left = source if source else "真实对话节选"
    footer_right = f"{page_num}/{total_pages}"
    draw.text((MARGIN, FOOTER_Y - 20), footer_left, fill=theme["weak"], font=weak_font)
    bbox = draw.textbbox((0, 0), footer_right, font=weak_font)
    draw.text((WIDTH - MARGIN - (bbox[2] - bbox[0]), FOOTER_Y - 20), footer_right, fill=theme["weak"], font=weak_font)
    image.save(output)


def write_preview(out_dir, files):
    cards = "\n".join(
        f'<section><img src="{html.escape(path.name)}" alt="{html.escape(path.name)}"></section>'
        for path in files
    )
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>Dialogue Screenshot Cards Preview</title>
<style>
body {{ margin: 0; background: #0f0f0f; color: white; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif; }}
main {{ display: grid; gap: 40px; padding: 40px; justify-content: center; }}
img {{ width: 360px; height: 480px; box-shadow: 0 18px 60px rgba(0,0,0,.35); }}
</style>
<main>
{cards}
</main>
</html>
"""
    (out_dir / "preview.html").write_text(html_text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Render truthful dialogue screenshot cards as SVG files.")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("--out", help="Output directory. Defaults to Codex应用工作台/4-对话截图卡片/exports/YYYY-MM-DD-主题")
    parser.add_argument("--theme", choices=["dark", "light"], help="Override theme")
    parser.add_argument("--no-privacy", action="store_true", help="Disable automatic privacy masking")
    parser.add_argument("--png", action="store_true", help="Also render PNG files when Pillow is available")
    args = parser.parse_args()

    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    out_dir = Path(args.out) if args.out else default_output_dir(data)
    out_dir.mkdir(parents=True, exist_ok=True)

    theme_name = args.theme or data.get("theme", "dark")
    if theme_name not in THEMES:
        theme_name = "dark"

    blocks = message_blocks(data.get("messages", []), preserve_privacy=not args.no_privacy, base_dir=input_path.parent)
    pages = paginate(blocks)
    if not pages:
        raise SystemExit("No messages to render.")

    files = []
    for i, page in enumerate(pages, 1):
        svg = render_page(data, page, i, len(pages), theme_name)
        output = out_dir / f"card-{i:02d}.svg"
        output.write_text(svg, encoding="utf-8")
        files.append(output)
        if args.png:
            png_output = out_dir / f"card-{i:02d}.png"
            try:
                render_png_page(data, page, i, len(pages), theme_name, png_output)
            except ModuleNotFoundError as exc:
                if exc.name == "PIL":
                    raise SystemExit("PNG export requires Pillow. Re-run without --png or use a Python environment with Pillow.") from exc
                raise
    write_preview(out_dir, files)
    print(f"Generated {len(files)} card(s) in {out_dir}")


if __name__ == "__main__":
    main()
