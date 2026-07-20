from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
DIAGRAM_DIR = ROOT / "docs" / "architecture-diagrams"
OUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
PDF_PATH = OUT_DIR / "asteria-architecture-premium-low-color.pdf"

FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

COLORS = {
    "bg": "#F3EFE7",
    "paper": "#FFFCF6",
    "card": "#FFFFFF",
    "ink": "#1E1915",
    "muted": "#6D625B",
    "line": "#D8CEC3",
    "accent": "#C6532F",
    "green": "#2F6B5D",
    "amber_bg": "#FFF8E8",
    "green_bg": "#EFF8F4",
}


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def set_fill(c: canvas.Canvas, color: str) -> None:
    c.setFillColorRGB(*hex_to_rgb(color))


def set_stroke(c: canvas.Canvas, color: str) -> None:
    c.setStrokeColorRGB(*hex_to_rgb(color))


def font(weight: str = "regular") -> str:
    return {"regular": "NotoSC", "medium": "NotoSC-Medium", "bold": "NotoSC-Bold"}[weight]


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("NotoSC", FONT_REGULAR, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("NotoSC-Medium", FONT_BOLD, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("NotoSC-Bold", FONT_BOLD, subfontIndex=0))


def wrap_text(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    buf = ""
    for ch in text:
        if ch == "\n":
            if buf:
                lines.append(buf)
            buf = ""
            continue
        if len(buf) >= max_chars:
            lines.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        lines.append(buf)
    return lines


def wrap_text_width(text: str, max_width: float, font_name: str, size: int) -> list[str]:
    lines: list[str] = []
    buf = ""
    for ch in text:
        if ch == "\n":
            if buf:
                lines.append(buf)
            buf = ""
            continue
        trial = buf + ch
        if buf and pdfmetrics.stringWidth(trial, font_name, size) > max_width:
            lines.append(buf)
            buf = ch
        else:
            buf = trial
    if buf:
        lines.append(buf)
    return lines


def draw_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    size: int,
    color: str = COLORS["ink"],
    weight: str = "regular",
    max_chars: int | None = None,
    max_width: float | None = None,
    max_lines: int | None = None,
    leading: float | None = None,
) -> float:
    set_fill(c, color)
    font_name = font(weight)
    c.setFont(font_name, size)
    leading = leading or size * 1.42
    if max_width:
        lines = wrap_text_width(text, max_width, font_name, size)
    elif max_chars:
        lines = wrap_text(text, max_chars)
    else:
        lines = text.splitlines()
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip("，。、,.;； ") + "..."
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def rounded(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str = COLORS["card"],
    stroke: str = COLORS["line"],
    radius: float = 12,
    line_width: float = 0.8,
) -> None:
    set_fill(c, fill)
    set_stroke(c, stroke)
    c.setLineWidth(line_width)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)


def header(c: canvas.Canvas, title: str, page_no: int) -> None:
    w, h = landscape(A4)
    set_fill(c, COLORS["bg"])
    c.rect(0, 0, w, h, stroke=0, fill=1)
    set_fill(c, COLORS["accent"])
    c.roundRect(0, 0, 8, h, 4, stroke=0, fill=1)
    draw_text(c, "ASTERIA ARCHITECTURE", 28, h - 32, 8, "#8A8078", "bold")
    draw_text(c, title, 28, h - 58, 20, COLORS["ink"], "bold")
    draw_text(c, f"{page_no:02d}", w - 44, h - 40, 12, COLORS["muted"], "bold")


def metric(c: canvas.Canvas, x: float, y: float, num: str, label: str, note: str) -> None:
    rounded(c, x, y, 116, 58, COLORS["paper"], COLORS["line"], 10)
    draw_text(c, num, x + 14, y + 32, 22, COLORS["accent"], "bold")
    draw_text(c, label, x + 47, y + 34, 9, COLORS["ink"], "bold")
    draw_text(c, note, x + 47, y + 18, 7, COLORS["muted"], "regular")


def page_cover(c: canvas.Canvas) -> None:
    w, h = landscape(A4)
    header(c, "低色彩高级版 / PDF", 1)
    draw_text(c, "业务流程图：从材料到可复用报告资产", 42, h - 122, 30, COLORS["ink"], "bold")
    draw_text(
        c,
        "这一版保留 Figma 里的 no-cross v4 作为基线，同时新增更完整、更像正式交付稿的版本。主色只保留陶土橙和深绿，其他靠网格、留白、线条和信息层级撑住。",
        44,
        h - 162,
        11,
        COLORS["muted"],
        "regular",
        max_chars=60,
        leading=18,
    )
    metric(c, 44, h - 258, "9", "主流程步骤", "完整业务链路")
    metric(c, 176, h - 258, "5", "业务路径", "路由显式化")
    metric(c, 308, h - 258, "4", "质量门", "返修前置")
    metric(c, 440, h - 258, "5", "交付资产", "复用沉淀")

    rounded(c, 44, 88, 344, 182, COLORS["paper"], COLORS["line"], 14)
    draw_text(c, "新版判断", 64, 238, 16, COLORS["ink"], "bold")
    bullets = [
        "主链从任务、材料、数据结构、质量门一路走到交付复用。",
        "分流和交付改成矩阵，避免用复杂箭头硬塞信息。",
        "质量门前置，让业务同事能看懂为什么需要补材料或返修。",
        "PDF 采用同一套低色彩系统，避免花但不显空。",
    ]
    y = 210
    for item in bullets:
        set_fill(c, COLORS["accent"])
        c.circle(66, y + 3, 2.2, stroke=0, fill=1)
        y = draw_text(c, item, 76, y, 9, COLORS["muted"], "regular", max_chars=38, leading=13) - 5

    rounded(c, 414, 88, 374, 182, COLORS["green_bg"], "#BDD8CF", 14)
    draw_text(c, "交付口径", 434, 238, 16, COLORS["green"], "bold")
    draw_text(
        c,
        "这份 PDF 的默认版本是 Premium Low Color，集中呈现业务流程、技术主链和端点附录，形成可直接交付的架构说明。",
        434,
        210,
        10,
        COLORS["muted"],
        "regular",
        max_chars=40,
        leading=16,
    )
    c.showPage()


def draw_image_fit(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    with Image.open(path) as img:
        iw, ih = img.size
    scale = min(w / iw, h / ih)
    rw, rh = iw * scale, ih * scale
    c.drawImage(ImageReader(str(path)), x + (w - rw) / 2, y + (h - rh) / 2, rw, rh, preserveAspectRatio=True, mask="auto")


def page_image(c: canvas.Canvas, title: str, page_no: int, image: Path, caption: str) -> None:
    w, h = landscape(A4)
    header(c, title, page_no)
    rounded(c, 26, 52, w - 52, h - 122, COLORS["paper"], COLORS["line"], 14)
    draw_image_fit(c, image, 38, 66, w - 76, h - 150)
    draw_text(c, caption, 32, 30, 8, COLORS["muted"], "regular")
    c.showPage()


def card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    accent: str,
    body_size: int = 8,
    body_lines: int = 3,
) -> None:
    rounded(c, x, y, w, h, COLORS["card"], COLORS["line"], 10)
    set_fill(c, accent)
    c.roundRect(x + 12, y + h - 37, 4, 24, 2, stroke=0, fill=1)
    draw_text(c, title, x + 24, y + h - 28, 11, COLORS["ink"], "bold")
    if body_lines > 0 and body:
        body_y = y + h - 52 if h >= 60 else y + 6
        draw_text(
            c,
            body,
            x + 24,
            body_y,
            body_size,
            COLORS["muted"],
            "regular",
            max_width=w - 48,
            max_lines=body_lines,
            leading=body_size * 1.5,
        )


def arrow(c: canvas.Canvas, x1: float, y: float, x2: float, color: str) -> None:
    set_stroke(c, color)
    c.setLineWidth(2)
    c.line(x1, y, x2 - 8, y)
    set_fill(c, color)
    c.line(x2 - 8, y + 4, x2, y)
    c.line(x2 - 8, y - 4, x2, y)


def page_technical(c: canvas.Canvas) -> None:
    w, h = landscape(A4)
    header(c, "技术主链 / 低色彩版", 3)
    draw_text(c, "系统怎么从请求走到结果", 42, h - 102, 24, COLORS["ink"], "bold")
    draw_text(c, "这一页呈现技术骨架；完整 endpoint 入口位于下一页附录。", 44, h - 132, 10, COLORS["muted"], "regular")
    items = [
        ("1. 工作台界面", "收集数据、需求、背景与批注。"),
        ("2. API 门面", "接住数据、报告、修订和配置入口。"),
        ("3. 判断引擎", "理解结构、目标和业务语境。"),
        ("4. 执行引擎", "进入统计、代码、R 工作流或 agent。"),
        ("5. 交付资产", "报告、图表、明细和运行记录归档。"),
    ]
    x0, y0, cw, ch, gap = 42, h - 280, 138, 116, 18
    for i, item in enumerate(items):
        card(c, x0 + i * (cw + gap), y0, cw, ch, item[0], item[1], COLORS["accent"] if i < 3 else COLORS["green"], body_size=8, body_lines=4)
        if i < len(items) - 1:
            arrow(c, x0 + i * (cw + gap) + cw + 4, y0 + ch / 2, x0 + (i + 1) * (cw + gap) - 6, COLORS["accent"] if i < 2 else COLORS["green"])

    rounded(c, 42, 90, 360, 154, COLORS["amber_bg"], "#E5D39A", 12)
    draw_text(c, "生成链", 62, 214, 14, "#8C6815", "bold")
    for idx, txt in enumerate(["同步报告", "异步任务", "延长链和专项链", "注册回报告目录"]):
        card(c, 62 + (idx % 2) * 158, 172 - (idx // 2) * 58, 136, 42, txt, "", COLORS["accent"], body_size=7, body_lines=0)

    rounded(c, 430, 90, 360, 154, COLORS["green_bg"], "#BDD8CF", 12)
    draw_text(c, "修订链", 450, 214, 14, COLORS["green"], "bold")
    for idx, txt in enumerate(["创建工作区", "收批注附件", "执行修改", "发布新版"]):
        card(c, 450 + (idx % 2) * 158, 172 - (idx // 2) * 58, 136, 42, txt, "", COLORS["green"], body_size=7, body_lines=0)
    c.showPage()


def page_endpoint(c: canvas.Canvas) -> None:
    w, h = landscape(A4)
    header(c, "端点附录 / 压缩清单", 4)
    draw_text(c, "完整性放在附录，主图保持干净", 42, h - 102, 24, COLORS["ink"], "bold")
    draw_text(c, "这一页按业务面压缩 endpoint surface，方便核对当前系统暴露能力。", 44, h - 132, 10, COLORS["muted"], "regular")
    groups = [
        ("基础与配置", "health / manifest / market / skills / settings / codex health"),
        ("数据与背景", "datasets / historical reports / backgrounds / upload / workflow"),
        ("分析与报告", "statistics / code execution / smart report / report catalog"),
        ("修订工作台", "sessions / messages / events / files / diff / publish"),
        ("运行时治理", "processes / codex runs / jobs / pipeline / retry"),
        ("学习与交付", "learning ledger / register output / revision entry"),
    ]
    for i, (title, body) in enumerate(groups):
        x = 42 + (i % 2) * 382
        y = h - 230 - (i // 2) * 112
        card(c, x, y, 348, 88, title, body, COLORS["accent"] if i < 3 else COLORS["green"], body_size=8, body_lines=3)
    c.showPage()


def page_final(c: canvas.Canvas) -> None:
    w, h = landscape(A4)
    header(c, "交付结论", 5)
    draw_text(c, "默认版本：Premium Low Color", 42, h - 112, 28, COLORS["ink"], "bold")
    draw_text(
        c,
        "保留 no-cross v4 作为对照版；新增 Figma frame `05 Business Flow Premium v1 - Low Color` 作为当前推荐稿。PDF 采用同一低色彩系统，便于继续迭代。",
        44,
        h - 154,
        11,
        COLORS["muted"],
        "regular",
        max_chars=66,
        leading=18,
    )
    checks = [
        ("没有交叉箭头", "主流程采用蛇形阅读，分流和交付改成矩阵。"),
        ("信息量增加", "9 步主链、5 路径、4 质量门、5 类交付资产。"),
        ("颜色克制", "主视觉只使用陶土橙和深绿，其余是中性色。"),
        ("适合后续修改", "Figma 与 PDF 都是独立产物，旧版不被覆盖。"),
    ]
    for i, item in enumerate(checks):
        x = 58 + (i % 2) * 362
        y = h - 276 - (i // 2) * 104
        card(c, x, y, 320, 78, item[0], item[1], COLORS["accent"] if i < 2 else COLORS["green"])
    c.showPage()


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    c = canvas.Canvas(str(PDF_PATH), pagesize=landscape(A4))
    c.setTitle("Asteria Architecture Premium Low Color")
    page_cover(c)
    page_image(
        c,
        "业务流程 / 新增高级版",
        2,
        DIAGRAM_DIR / "business-flow-premium-low-color-v1.png",
        "Figma node 52:2 - 05 Business Flow Premium v1 - Low Color",
    )
    page_technical(c)
    page_endpoint(c)
    page_final(c)
    c.save()


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
