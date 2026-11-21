"""Shared helpers: folders, file types, Chrome (HTML to PDF) and poppler (PDF to images)."""
import html
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

OUT_DIR = "בדיקה"                      # everything the skill writes goes in <exam folder>/בדיקה
DATA_DIR = "נתונים"                    # JSON: files.json, key.json, one file per student
PAGES_DIR = "עמודים"                   # page images and locator grids, one folder per document

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".bmp"}
DOC_EXT = {".pdf", ".docx", ".doc", ".odt"} | IMAGE_EXT
LONG_SIDE = 1800                       # pixels on the long side of every page image (handwriting stays readable)

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800'
         '&display=swap" rel="stylesheet">')


def out_dir(folder):
    return Path(folder) / OUT_DIR


def data_dir(folder):
    d = out_dir(folder) / DATA_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def pages_dir(folder, doc_id):
    d = out_dir(folder) / PAGES_DIR / doc_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def esc(s):
    return html.escape(str(s), quote=True)


_SYM = "A-Za-z0-9½¼¾⅓√∞αβγδεηθκλμνπρστφωΔΣΩΦ₀₁₂₃₄₅₆₇₈₉"           # letters, digits, Greek, fractions
_TOK = rf"[{_SYM}][{_SYM}_.,′'²³⁻⁰¹⁴⁵⁶⁷⁸⁹()|/·]*"
LTR_RUN = re.compile(_TOK + r"(?:(?:\s*[=+\-−·×/<>≈]\s*[+\-−]?|[ \t]+)" + _TOK + r")*")


def _trim(run):
    """Leave sentence punctuation and an unmatched closing parenthesis outside the formula."""
    while run and (run[-1] in ".,;:" or (run[-1] == ")" and run.count("(") < run.count(")"))):
        run = run[:-1]
    return run


def bidi(s):
    """Escape text for Hebrew HTML and wrap every formula or Latin/number run in a left-to-right isolate,
    so "g=9.8" or "σ = E·ε₀" inside a Hebrew sentence is not shown reversed (as "9.8=g")."""
    s = str(s)
    out, last = [], 0
    for m in LTR_RUN.finditer(s):
        if m.start() < last:
            continue
        run = _trim(m.group())
        if not run:
            continue
        out.append(esc(s[last:m.start()]))
        out.append(f'<span class="num">{esc(run)}</span>')
        last = m.start() + len(run)
    out.append(esc(s[last:]))
    return "".join(out)


def fmt(x):
    """Points as the teacher writes them: 7, 4.33, 0.5 (no trailing zeros)."""
    x = round(float(x), 2)
    return f"{x:g}"


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|]+', "-", str(s)).strip() or "תלמיד"


def find_chrome():
    env = os.environ.get("CHROME")
    if env:
        return env
    candidates = {
        "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Chromium.app/Contents/MacOS/Chromium"],
        "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    }.get(platform.system(), [])
    for c in candidates:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    raise SystemExit("Google Chrome / Chromium not found. Install it or set the CHROME environment variable.")


def html_to_pdf(html_text, html_path, pdf_path):
    """Write the HTML next to its images and print it to PDF with headless Chrome."""
    html_path = Path(html_path)
    html_path.write_text(html_text, encoding="utf-8")
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--virtual-time-budget=15000",
                    f"--print-to-pdf={Path(pdf_path).resolve()}", html_path.resolve().as_uri()],
                   check=True, capture_output=True, timeout=300)
    return Path(pdf_path)


def pdf_pages(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else 0


def pdf_to_jpegs(pdf, dest, prefix="p", long_side=LONG_SIDE, first=1, last=None):
    """Render PDF pages to JPEGs with a fixed long side (scanner apps make pages of any size)."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    n = pdf_pages(pdf)
    last = last or n
    files = []
    for i in range(first, last + 1):
        target = dest / f"{prefix}{i:02d}.jpg"
        tmp = dest / f".tmp-{prefix}{i:02d}"
        subprocess.run(["pdftoppm", "-scale-to", str(long_side), "-jpeg", "-jpegopt", "quality=85",
                        "-f", str(i), "-l", str(i), "-singlefile", str(pdf), str(tmp)], check=True)
        Path(str(tmp) + ".jpg").replace(target)
        files.append(target)
    return files


PAGE_CSS = """
@page { size: A4; margin: 6mm; }
* { box-sizing: border-box; }
html, body { margin: 0; background: #fff; }
body { font-family: Heebo, Arial, sans-serif; color: #1c1b1f; }
.pg { height: 284mm; display: flex; align-items: flex-start; justify-content: center; overflow: hidden;
      page-break-after: always; break-after: page; }
.pg:last-child { page-break-after: auto; break-after: auto; }
.frame { position: relative; display: inline-block; line-height: 0; }
.frame img { display: block; max-width: 198mm; max-height: 283mm; }
.ov { position: absolute; inset: 0; line-height: 1.3; }
"""
