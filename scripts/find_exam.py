"""Find the exam, the optional answer key, and every student's pages in an exam folder.

    python3 find_exam.py "<exam folder>" [--exam FILE] [--key FILE] [--formulas FILE]
    python3 find_exam.py "<new exam folder>" --create     make the folder (and פתרונות/) for the teacher to fill

Layout the teacher is asked to use (see SKILL.md):

    <exam folder>/
        מבחן.pdf                 the exam (PDF, Word, or photos named מבחן 1.jpg, מבחן 2.jpg ...)
        מחוון.pdf                optional: the teacher's own solution / rubric
        דף נוסחאות.pdf           recommended: the formula sheet the class uses (deductions follow it)
        פתרונות/                 the students' work, any name works for this folder
            דני כהן.pdf           one PDF per student (scan) ...
            נועה לוי/             ... or one folder of photos per student
            יוסי 1.jpg, יוסי 2.jpg  ... or photos named <name> <page number>

It also copes with student files lying next to the exam. Writes <exam folder>/בדיקה/נתונים/files.json
(paths relative to the exam folder) and prints a summary.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DOC_EXT, IMAGE_EXT, OUT_DIR, data_dir, save_json  # noqa: E402

FORMULA_RX = re.compile(r"נוסחא|נוסחאות|נוסחות|formula", re.I)
KEY_RX = re.compile(r"מחוון|פתרון\s*(?:של\s*)?ה?מורה|תשובות\s*ה?מורה|פתרון\s*מלא|answer[\s_-]*key|rubric|solution", re.I)
EXAM_RX = re.compile(r"מבחן|בוחן|שאלון|exam|test|quiz", re.I)
CONTAINER_RX = re.compile(r"פתרונות|תלמידים|סריקות|מחברות|עבודות|solutions|students|scans|answers", re.I)
GENERIC_RX = re.compile(r"^(?:img|dsc|pxl|dcim|whatsapp|photo|image|screenshot|camscanner|scan|scanned|doc|document)", re.I)
CAMERA_RX = re.compile(r"^(?:img|dsc|pxl|dcim|whatsapp|photo|image|screenshot)[\s_\-]", re.I)
PAGE_SUFFIX_RX = re.compile(r"(?:[\s_\-]+(?:עמוד|עמ'?|page|p)?[\s_\-]*|(?:עמוד|page)\s*)\d{1,2}$", re.I)
SKIP_DIRS = {OUT_DIR, "מקור", "__pycache__"}


def is_doc(p):
    return p.is_file() and p.suffix.lower() in DOC_EXT and not p.name.startswith((".", "~$"))


def has_text_layer(pdf):
    if pdf.suffix.lower() != ".pdf":
        return pdf.suffix.lower() in {".docx", ".doc", ".odt"}
    try:
        txt = subprocess.run(["pdftotext", "-l", "2", str(pdf), "-"], capture_output=True, text=True, timeout=60).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return len(re.sub(r"\s", "", txt)) > 200


def natural_key(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def group_images(images):
    """Photos named '<name> 1.jpg', '<name> 2.jpg' belong to one student."""
    groups = {}
    for img in sorted(images, key=natural_key):
        stem = PAGE_SUFFIX_RX.sub("", img.stem).strip() or img.stem
        groups.setdefault(stem, []).append(img)
    return groups


def student(name, files, warnings):
    files = sorted(files, key=natural_key)
    generic = bool(GENERIC_RX.match(name)) or not name.strip()
    return {"name": "" if generic else name, "label": name, "files": files, "name_from_page": generic}


def students_in(container, warnings):
    out = []
    children = sorted([c for c in container.iterdir() if not c.name.startswith(".")], key=natural_key)
    images = [c for c in children if is_doc(c) and c.suffix.lower() in IMAGE_EXT]
    camera = [c for c in images if CAMERA_RX.match(c.stem)]
    if camera:
        warnings.append(f"{container.name}: {len(camera)} photos with camera names (IMG_...). They cannot be grouped "
                        "by name: ask the teacher to put each student's photos in a folder named after the student, "
                        "or group them yourself by the name written on the pages.")
    for c in children:
        if c.is_dir() and c.name not in SKIP_DIRS:
            files = [f for f in c.rglob("*") if is_doc(f)]
            if files:
                out.append(student(c.name, files, warnings))
        elif is_doc(c) and c.suffix.lower() not in IMAGE_EXT:
            out.append(student(c.stem, [c], warnings))
    for stem, imgs in group_images([i for i in images if i not in camera]).items():
        out.append(student(stem, imgs, warnings))
    for img in camera:
        out.append(student(img.stem, [img], warnings))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--exam", action="append", help="the exam file (repeat for several photos)")
    ap.add_argument("--key", action="append", help="the teacher's answer key file(s)")
    ap.add_argument("--formulas", action="append", help="the formula sheet file(s)")
    ap.add_argument("--create", action="store_true", help="create the folder layout for the teacher and stop")
    a = ap.parse_args()
    if not a.folder.strip():
        raise SystemExit("give the exam folder path")
    folder = Path(a.folder).resolve()
    if a.create:
        if (Path(__file__).resolve().parent.parent) in [folder, *folder.parents]:
            raise SystemExit("refusing to create an exam folder inside the skill itself")
        (folder / "פתרונות").mkdir(parents=True, exist_ok=True)
        print(f"created {folder}")
        print(f"  put the exam or quiz and the formula sheet in: {folder}")
        print(f"  put the students' scans (one PDF or one folder of photos each) in: {folder / 'פתרונות'}")
        return
    if not folder.is_dir():
        raise SystemExit(f"not a folder: {folder}")
    warnings = []
    top_docs = sorted([p for p in folder.iterdir() if is_doc(p)], key=natural_key)
    subdirs = sorted([p for p in folder.iterdir() if p.is_dir() and not p.name.startswith(".")
                      and p.name not in SKIP_DIRS], key=natural_key)

    formulas = ([Path(f).resolve() for f in a.formulas] if a.formulas
                else [p for p in top_docs if FORMULA_RX.search(p.stem)])
    key = ([Path(k).resolve() for k in a.key] if a.key
           else [p for p in top_docs if KEY_RX.search(p.stem) and p not in formulas])
    if a.exam:
        exam = [Path(e).resolve() for e in a.exam]
    else:
        named = [p for p in top_docs if EXAM_RX.search(p.stem) and p not in key and p not in formulas]
        typed = [p for p in named if has_text_layer(p)]
        named_imgs = [p for p in named if p.suffix.lower() in IMAGE_EXT]
        if typed:
            exam = typed[:1]
        elif named_imgs and len(named_imgs) == len(named):
            exam = named_imgs                                  # the exam photographed page by page
        elif named:
            exam = named[:1]
        else:
            rest = [p for p in top_docs if p not in key and p not in formulas]
            exam = rest[:1] if (subdirs and len(rest) >= 1) or len(rest) == 1 else []
    if not exam:
        warnings.append("No exam file found. Ask the teacher which file is the exam and rerun with --exam.")

    students = []
    loose = [p for p in top_docs if p not in exam and p not in key and p not in formulas]
    if loose:
        students += students_in_list(loose, warnings)
    for d in subdirs:
        files = [f for f in d.iterdir() if is_doc(f)]
        inner_dirs = [f for f in d.iterdir() if f.is_dir() and not f.name.startswith(".")]
        pdfs = [f for f in files if f.suffix.lower() not in IMAGE_EXT]
        if CONTAINER_RX.search(d.name) or inner_dirs or len(pdfs) >= 2:
            students += students_in(d, warnings)
        elif files:
            students.append(student(d.name, [f for f in d.rglob("*") if is_doc(f)], warnings))

    rel = lambda p: str(Path(p).resolve().relative_to(folder)) if Path(p).resolve().is_relative_to(folder) else str(p)
    result = {
        "folder": str(folder),
        "exam": {"files": [rel(p) for p in exam], "text_layer": bool(exam) and has_text_layer(exam[0])},
        "key": {"files": [rel(p) for p in key]},
        "formulas": {"files": [rel(p) for p in formulas], "text_layer": bool(formulas) and has_text_layer(formulas[0])},
        "students": [{"id": f"s{i:02d}", "name": s["name"], "label": s["label"], "name_from_page": s["name_from_page"],
                      "files": [rel(f) for f in s["files"]]} for i, s in enumerate(students, 1)],
        "warnings": warnings,
    }
    save_json(data_dir(folder) / "files.json", result)

    print(f"exam:     {', '.join(result['exam']['files']) or '(not found)'}"
          f"{'  [text layer]' if result['exam']['text_layer'] else ''}")
    print(f"key:      {', '.join(result['key']['files']) or '(none: build one)'}")
    print(f"formulas: {', '.join(result['formulas']['files']) or '(no formula sheet: use the exam\'s formula box or ask the teacher)'}")
    print(f"students: {len(students)}")
    for s in result["students"]:
        who = s["name"] or f"(name from the first page; file: {s['label']})"
        print(f"  {s['id']}  {who}  <- {len(s['files'])} file(s): {', '.join(s['files'][:3])}{' ...' if len(s['files']) > 3 else ''}")
    for w in warnings:
        print("WARNING:", w)
    print(f"wrote {data_dir(folder) / 'files.json'}")


def students_in_list(files, warnings):
    """Student files lying next to the exam: PDFs one each, photos grouped by name."""
    out = []
    imgs = [f for f in files if f.suffix.lower() in IMAGE_EXT]
    for f in files:
        if f not in imgs:
            out.append(student(f.stem, [f], warnings))
    for stem, group in group_images(imgs).items():
        out.append(student(stem, group, warnings))
    return out


if __name__ == "__main__":
    main()
