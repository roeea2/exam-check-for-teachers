"""Turn the exam, the key and every student's work into page images, plus locator grids for marking.

    python3 prepare_pages.py "<exam folder>" [--only s01,s02] [--no-grid] [--force]

Needs files.json from find_exam.py. For each document (exam, key, s01, s02 ...) it writes
<exam folder>/בדיקה/עמודים/<id>/p01.jpg ... (scans of any page size come out with an 1800 px long side;
phone photos are copied, HEIC/TIFF are converted with macOS sips) and, unless --no-grid,
grid-p01.png ...: the same page with a percent grid (x from the left edge, y from the top edge, 0-100).
Read the grid images to give every mark its box in percent; annotate.py draws on the same frame.
Also writes נתונים/pages.json and, for a typed exam or formula sheet, נתונים/exam.txt / formulas.txt.
"""
import argparse
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (FONTS, IMAGE_EXT, LONG_SIDE, PAGE_CSS, data_dir, html_to_pdf, load_json,  # noqa: E402
                    pages_dir, pdf_to_jpegs, save_json)

GRID_CSS = PAGE_CSS + """
.gv, .gh { position: absolute; }
.gv { top: 0; bottom: 0; border-left: 1px solid rgba(0, 110, 255, .30); }
.gh { left: 0; right: 0; border-top: 1px solid rgba(0, 110, 255, .30); }
.gv.mj { border-left: 1.6px solid rgba(230, 0, 0, .55); }
.gh.mj { border-top: 1.6px solid rgba(230, 0, 0, .55); }
.gl { position: absolute; font: 700 10px Heebo, Arial, sans-serif; color: #c00000; background: rgba(255,255,255,.88);
      padding: 0 2px; border-radius: 2px; line-height: 1.2; }
.gx { transform: translateX(-50%); }
.gy { transform: translateY(-50%); }
.gi { position: absolute; font: 600 8.5px Heebo, Arial, sans-serif; color: #0b4fb3; background: rgba(255,255,255,.80);
      padding: 0 2px; transform: translate(-50%, -50%); line-height: 1.2; }
"""


def convert_image(src, dest_stem):
    """Copy a photo; convert formats Chrome cannot show (HEIC, TIFF) to JPEG with macOS sips."""
    ext = src.suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
        dest = dest_stem.with_suffix(ext if ext != ".jpeg" else ".jpg")
        shutil.copy2(src, dest)
        return dest
    dest = dest_stem.with_suffix(".jpg")
    if shutil.which("sips"):
        subprocess.run(["sips", "-s", "format", "jpeg", "-Z", str(LONG_SIDE * 2), str(src), "--out", str(dest)],
                       check=True, capture_output=True)
        return dest
    raise SystemExit(f"cannot convert {src.name} ({ext}) here: ask the teacher to save it as JPG or PDF")


def office_to_pdf(src, dest_dir):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise SystemExit(f"{src.name}: Word file and no LibreOffice; ask the teacher to save the exam as PDF")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(dest_dir), str(src)],
                   check=True, capture_output=True, timeout=180)
    return dest_dir / (src.stem + ".pdf")


def render_document(folder, doc_id, files, force):
    dest = pages_dir(folder, doc_id)
    existing = sorted(dest.glob("p[0-9][0-9].*"))
    if existing and not force:
        return doc_id, existing
    for old in existing:
        old.unlink()
    pages, n = [], 0
    for rel in files:
        src = folder / rel
        ext = src.suffix.lower()
        if ext in {".docx", ".doc", ".odt"}:
            src, ext = office_to_pdf(src, dest), ".pdf"
        if ext == ".pdf":
            tmp = dest / ".pdf-pages"
            for img in pdf_to_jpegs(src, tmp):
                n += 1
                target = dest / f"p{n:02d}.jpg"
                img.replace(target)
                pages.append(target)
            shutil.rmtree(tmp, ignore_errors=True)
        elif ext in IMAGE_EXT:
            n += 1
            pages.append(convert_image(src, dest / f"p{n:02d}"))
    return doc_id, pages


def grid_html(pages):
    lines = "".join(f'<div class="gv{" mj" if i % 2 == 0 else ""}" style="left:{i * 5}%"></div>'
                    f'<div class="gh{" mj" if i % 2 == 0 else ""}" style="top:{i * 5}%"></div>' for i in range(1, 20))
    labels = "".join(f'<div class="gl gx" style="left:{v}%;top:0">{v}</div>'
                     f'<div class="gl gx" style="left:{v}%;bottom:0">{v}</div>'
                     f'<div class="gl gy" style="top:{v}%;left:0">{v}</div>'
                     f'<div class="gl gy" style="top:{v}%;right:0">{v}</div>' for v in range(10, 100, 10))
    inner = "".join(f'<div class="gi" style="left:{x}%;top:{y}%">{x},{y}</div>'
                    for x in (20, 40, 60, 80) for y in (20, 40, 60, 80))
    body = "".join(f'<section class="pg"><div class="frame"><img src="{p.name}">'
                   f'<div class="ov">{lines}{labels}{inner}</div></div></section>' for p in pages)
    return (f'<!doctype html><html lang="he"><head><meta charset="utf-8">{FONTS}<style>{GRID_CSS}</style></head>'
            f'<body>{body}</body></html>')


def render_grid(folder, doc_id, pages):
    dest = pages_dir(folder, doc_id)
    for old in dest.glob("grid-p*.png"):
        old.unlink()
    pdf = html_to_pdf(grid_html(pages), dest / "locator.html", dest / "locator.pdf")
    subprocess.run(["pdftoppm", "-scale-to", "1600", "-png", str(pdf), str(dest / "grid-p")], check=True)
    out = []
    for i, f in enumerate(sorted(dest.glob("grid-p-*.png")), 1):
        target = dest / f"grid-p{i:02d}.png"
        f.replace(target)
        out.append(target)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--only", help="comma-separated document ids, e.g. exam,s01,s02")
    ap.add_argument("--no-grid", action="store_true")
    ap.add_argument("--force", action="store_true", help="render again even if the pages exist")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    folder = Path(a.folder).resolve()
    files = load_json(data_dir(folder) / "files.json")

    docs = {}
    if files["exam"]["files"]:
        docs["exam"] = files["exam"]["files"]
    if files["key"]["files"]:
        docs["key"] = files["key"]["files"]
    if files.get("formulas", {}).get("files"):
        docs["formulas"] = files["formulas"]["files"]
    for s in files["students"]:
        docs[s["id"]] = s["files"]
    if a.only:
        wanted = set(a.only.split(","))
        docs = {k: v for k, v in docs.items() if k in wanted}

    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        rendered = dict(ex.map(lambda kv: render_document(folder, kv[0], kv[1], a.force), docs.items()))

    pages_json = data_dir(folder) / "pages.json"
    index = load_json(pages_json) if pages_json.exists() else {}
    for doc_id, pages in rendered.items():
        index[doc_id] = [str(p.relative_to(folder)) for p in pages]
        print(f"{doc_id:6} {len(pages):3} page(s)")
    save_json(pages_json, index)

    for doc in ("formulas",):
        if doc in rendered and files.get(doc, {}).get("text_layer"):
            src = folder / files[doc]["files"][0]
            if src.suffix.lower() == ".pdf":
                txt = subprocess.run(["pdftotext", "-layout", str(src), "-"], capture_output=True, text=True).stdout
                (data_dir(folder) / f"{doc}.txt").write_text(txt, encoding="utf-8")
                print(f"wrote {doc}.txt (the formula sheet's text layer)")
    if "exam" in rendered and files["exam"]["text_layer"]:
        exam_src = folder / files["exam"]["files"][0]
        if exam_src.suffix.lower() == ".pdf":
            txt = subprocess.run(["pdftotext", "-layout", str(exam_src), "-"], capture_output=True, text=True).stdout
            (data_dir(folder) / "exam.txt").write_text(txt, encoding="utf-8")
            print("wrote exam.txt (the exam's text layer)")

    if not a.no_grid:
        grid_ids = [d for d in rendered if d not in ("exam", "key", "formulas")]
        with ThreadPoolExecutor(max_workers=min(a.jobs, 3)) as ex:
            for doc_id, grids in zip(grid_ids, ex.map(lambda d: render_grid(folder, d, rendered[d]), grid_ids)):
                print(f"{doc_id:6} {len(grids):3} locator grid(s)")
    print(f"wrote {pages_json}")


if __name__ == "__main__":
    main()
