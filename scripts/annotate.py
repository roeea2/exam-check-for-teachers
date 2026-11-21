"""Check a student's grading JSON and build the marked PDF: a Hebrew cover page, then the student's own pages
with every deduction circled in red and explained, then (when the AI suspicion is high) questions for a talk.

    python3 annotate.py "<exam folder>" s01 [s02 ...]      build those students
    python3 annotate.py "<exam folder>" --all               build everyone who has a JSON
    python3 annotate.py "<exam folder>" --all --check       only validate the JSON files (no PDF)

Reads בדיקה/נתונים/<id>.json (format: references/schemas.md) and בדיקה/עמודים/<id>/p01.jpg ...
Writes בדיקה/<student name> - בדוק.pdf. Exits with code 1 when a JSON has errors.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (FONTS, PAGE_CSS, bidi, data_dir, esc, fmt, html_to_pdf, load_json, out_dir,  # noqa: E402
                    pages_dir, safe_name)

AI_LEVELS = [(20, "נמוך מאוד"), (40, "נמוך"), (60, "לא חד-משמעי"), (80, "גבוה"), (100, "גבוה מאוד")]
TOL = 0.011


def ai_level(score):
    return next(name for top, name in AI_LEVELS if score <= top)


def words(s):
    return len([w for w in re.split(r"\s+", s.strip()) if w])


def validate(st, n_pages):
    """Return (errors, warnings). Errors block the PDF; warnings are printed."""
    err, warn = [], []
    qs = st.get("questions", [])
    if not qs:
        err.append("no questions")
    seen = set()
    for q in qs:
        qn = q.get("q")
        if qn in seen:
            err.append(f"question {qn} appears twice")
        seen.add(qn)
        parts = q.get("parts", [])
        psum_max = sum(float(p.get("max", 0)) for p in parts)
        if parts and abs(psum_max - float(q.get("max", psum_max))) > 0.02:
            warn.append(f"q{qn}: parts add up to {fmt(psum_max)}, question max is {fmt(q['max'])} (check the exam's points)")
        psum = 0.0
        for p in parts:
            tag = f"q{qn}{p.get('part', '?')}"
            mx, sc = float(p.get("max", 0)), float(p.get("score", 0))
            if sc < -TOL or sc > mx + TOL:
                err.append(f"{tag}: score {fmt(sc)} outside 0..{fmt(mx)}")
            ded = 0.0
            for m in p.get("marks", []):
                kind = m.get("kind", "deduct")
                if kind == "deduct":
                    pts = float(m.get("points", 0))
                    if pts >= 0:
                        err.append(f"{tag}: a deduction needs negative points, got {fmt(pts)}")
                    ded += pts
                    r = m.get("reason", "")
                    if not r.strip():
                        err.append(f"{tag}: deduction without a reason")
                    elif not 3 <= words(r) <= 6:
                        warn.append(f"{tag}: reason has {words(r)} words, aim for 4-5: '{r}'")
                if "box" in m:
                    b = m["box"]
                    if len(b) != 4 or b[2] <= 0 or b[3] <= 0 or b[0] < 0 or b[1] < 0 or b[0] + b[2] > 100.5 or b[1] + b[3] > 100.5:
                        err.append(f"{tag}: box {b} must be [x, y, w, h] in percent inside the page")
                    if not 1 <= int(m.get("page", 0)) <= n_pages:
                        err.append(f"{tag}: page {m.get('page')} not in 1..{n_pages}")
                elif kind == "deduct" and "page" in m:
                    warn.append(f"{tag}: deduction on page {m['page']} has no box (shown on the cover page only)")
            if abs(mx + ded - sc) > TOL:
                err.append(f"{tag}: max {fmt(mx)} + deductions {fmt(ded)} = {fmt(mx + ded)}, but score is {fmt(sc)}")
            psum += sc
        if parts and abs(psum - float(q.get("score", psum))) > 0.02:
            err.append(f"q{qn}: parts add up to {fmt(psum)}, question score is {fmt(q.get('score'))}")
    counted = st.get("counted") or [q["q"] for q in qs]
    unknown = [c for c in counted if c not in seen]
    if unknown:
        err.append(f"counted questions {unknown} are not in 'questions'")
    raw = sum(float(q.get("score", 0)) for q in qs if q["q"] in counted)
    total = st.get("total")
    if total is None or abs(round(raw) - float(total)) > 0.5:
        err.append(f"total should be round({fmt(raw)}) = {round(raw)}, got {total}")
    elif not 0 <= float(total) <= 100:
        err.append(f"total {total} outside 0..100")
    ai = st.get("ai") or {}
    if not isinstance(ai.get("score"), (int, float)) or not 0 <= ai["score"] <= 100:
        err.append("ai.score must be a number 0..100")
    elif not (ai.get("human_signs") or ai.get("ai_signs")):
        warn.append("ai: give the evidence (human_signs / ai_signs), not only a number")
    for n in st.get("notes", []):
        if "box" in n and not 1 <= int(n.get("page", 0)) <= n_pages:
            err.append(f"note on page {n.get('page')} not in 1..{n_pages}")
    return err, warn


CSS = PAGE_CSS + """
.cover { padding: 2mm 4mm; direction: rtl; font-size: 10pt; line-height: 1.4; page-break-after: always; break-after: page; }
.num { direction: ltr; unicode-bidi: isolate; display: inline-block; white-space: nowrap; }
.ai, .flags { break-inside: avoid; }
.cover h1 { font-size: 19pt; margin: 0 0 1mm; color: #2a1650; }
.cover .sub { color: #555; margin-bottom: 4mm; }
.top { display: flex; gap: 6mm; align-items: center; margin-bottom: 4mm; }
.score { width: 34mm; height: 34mm; border-radius: 50%; border: 3px solid #c62828; color: #c62828; display: flex;
         flex-direction: column; align-items: center; justify-content: center; flex: none; }
.score b { font-size: 30pt; line-height: 1; }
.score span { font-size: 10pt; }
.who { font-size: 13pt; }
.who div { margin: 1mm 0; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 3mm; font-size: 9.3pt; }
tr { break-inside: avoid; }
th, td { border: 1px solid #ddd3ee; padding: .8mm 2mm; text-align: right; vertical-align: top; }
th { background: #f3eefb; color: #2a1650; }
tr.qrow td { background: #faf8fd; font-weight: 700; }
td.pts { white-space: nowrap; text-align: center; width: 16mm; }
td.red { color: #c62828; }
.ai { border: 2px solid #4a2a7f; border-radius: 3mm; padding: 3mm 4mm; margin-top: 2mm; }
.ai h2 { font-size: 12.5pt; margin: 0 0 1.5mm; color: #2a1650; }
.bar { height: 4mm; background: linear-gradient(90deg, #2e7d32, #f9a825, #c62828); border-radius: 2mm; position: relative; margin: 2mm 0 1mm; direction: ltr; }
.bar i { position: absolute; top: -1.5mm; width: 1.2mm; height: 7mm; background: #1c1b1f; border-radius: 1mm; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; margin-top: 2mm; }
.cols h3 { font-size: 10.5pt; margin: 0 0 1mm; }
.cols ul { margin: 0; padding-right: 5mm; }
.small { font-size: 8.8pt; color: #666; margin-top: 2mm; }
.flags { background: #fff6e0; border-radius: 2mm; padding: 2mm 4mm; margin-top: 3mm; }
.mk { position: absolute; border: 2.4px solid #e0201b; border-radius: 50%; }
.nt { position: absolute; border: 1.8px dashed #1565c0; border-radius: 2mm; }
.lb { position: absolute; direction: rtl; font: 700 9.5pt Heebo, Arial, sans-serif; color: #c00000;
      background: rgba(255, 255, 255, .93); border: 1.2px solid #e0201b; border-radius: 1.6mm; padding: .4mm 1.6mm;
      max-width: 50%; line-height: 1.25; }
.lb .p { direction: ltr; unicode-bidi: isolate; font-weight: 800; margin-left: 1.2mm; }
.lb.blue { color: #0d47a1; border-color: #1565c0; }
.ok { position: absolute; color: #2e7d32; font: 800 20pt Heebo, Arial, sans-serif; line-height: 1; transform: translate(-50%, -50%); }
.stamp { position: absolute; left: 1.5%; top: 1%; width: 17mm; height: 17mm; border-radius: 50%; border: 2.6px solid #c62828;
         color: #c62828; background: rgba(255,255,255,.9); font: 800 15pt Heebo, Arial, sans-serif; display: flex;
         align-items: center; justify-content: center; line-height: 1; }
.oral { padding: 6mm 8mm; direction: rtl; font-size: 11pt; line-height: 1.55; }
.oral h1 { font-size: 16pt; color: #2a1650; margin: 0 0 2mm; }
.oral li { margin: 2mm 0; }
"""


def label_css(box, label_at=None, below=True, width=None):
    css = f"max-width:{width}%;" if width else ""
    return css + _label_pos(box, label_at, below)


def _label_pos(box, label_at, below):
    x, y, w, h = box
    if label_at:
        lx, ly = label_at[0], label_at[1]
        if len(label_at) > 2 and label_at[2] == "left":       # [x, y, "left"]: the label's top-LEFT corner
            return f"left:{lx:.2f}%;top:{ly:.2f}%"
        return f"right:{100 - lx:.2f}%;top:{ly:.2f}%"         # [x, y]: the label's top-right corner
    horiz = f"left:{x:.2f}%" if x + w / 2 < 35 else f"right:{max(0.5, 100 - x - w):.2f}%"
    if below and y + h < 90:
        return f"{horiz};top:{y + h + 0.5:.2f}%"
    return f"{horiz};bottom:{100 - y + 0.5:.2f}%"


def page_overlay(st, page_no):
    items = []
    for q in st["questions"]:
        for p in q.get("parts", []):
            for m in p.get("marks", []):
                if int(m.get("page", 0)) != page_no or "box" not in m:
                    continue
                x, y, w, h = m["box"]
                kind = m.get("kind", "deduct")
                if kind == "deduct":
                    items.append(f'<div class="mk" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%"></div>')
                    items.append(f'<div class="lb" style="{label_css(m["box"], m.get("label_at"), width=m.get("label_w"))}">'
                                 f'<span class="p">{esc("−" + fmt(abs(float(m["points"]))))}</span>{bidi(m["reason"])}</div>')
                elif kind == "ok":
                    items.append(f'<div class="ok" style="left:{x + w:.2f}%;top:{y + h / 2:.2f}%">✓</div>')
                elif kind == "note":
                    items.append(f'<div class="nt" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%"></div>')
                    items.append(f'<div class="lb blue" style="{label_css(m["box"], m.get("label_at"))}">{bidi(m.get("text", ""))}</div>')
    for n in st.get("notes", []):
        if int(n.get("page", 0)) == page_no and "box" in n:
            x, y, w, h = n["box"]
            if n.get("kind") == "ok":
                items.append(f'<div class="ok" style="left:{x + w:.2f}%;top:{y + h / 2:.2f}%">✓</div>')
            else:
                items.append(f'<div class="nt" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%"></div>')
                items.append(f'<div class="lb blue" style="{label_css(n["box"], n.get("label_at"))}">{bidi(n.get("text", ""))}</div>')
    if page_no == 1:
        items.append(f'<div class="stamp">{esc(st["total"])}</div>')
    return "".join(items)


def cover(st, key):
    title = key.get("title", "") if key else ""
    counted = st.get("counted") or [q["q"] for q in st["questions"]]
    rows = []
    for q in sorted(st["questions"], key=lambda q: (q["q"] not in counted, counted.index(q["q"]) if q["q"] in counted else 0)):
        note = "" if q["q"] in counted else " (לא נספרה בציון)"
        topic = f" · {bidi(q['title'])}" if q.get("title") else ""
        rows.append(f'<tr class="qrow"><td colspan="2">שאלה {esc(q["q"])}{topic}{note}</td>'
                    f'<td class="pts"><span class="num">{fmt(q["score"])} / {fmt(q["max"])}</span></td><td></td></tr>')
        for p in q.get("parts", []):
            reasons = [f'<span class="num">{esc("−" + fmt(abs(float(m["points"]))))}</span> {bidi(m["reason"])}'
                       for m in p.get("marks", []) if m.get("kind", "deduct") == "deduct"]
            full = abs(float(p["score"]) - float(p["max"])) < TOL
            rows.append(f'<tr><td></td><td>סעיף {esc(p["part"])}</td>'
                        f'<td class="pts{"" if full else " red"}"><span class="num">{fmt(p["score"])} / {fmt(p["max"])}</span></td>'
                        f'<td class="red">{"<br>".join(reasons) if reasons else ("✓" if full else "")}</td></tr>')
    ai = st.get("ai", {})
    sc = int(round(ai.get("score", 0)))
    lst = lambda xs: "".join(f"<li>{bidi(x)}</li>" for x in xs) or "<li>-</li>"
    flags = st.get("flags", [])
    flags_html = (f'<div class="flags"><b>לבדיקת המורה:</b><ul>{lst(flags)}</ul></div>') if flags else ""
    who = esc(st.get("student") or st.get("label") or st.get("id"))
    cls = f'<div>כיתה: {esc(st["class"])}</div>' if st.get("class") else ""
    return f"""<div class="cover">
  <h1>בדיקת מבחן{(": " + esc(title)) if title else ""}</h1>
  <div class="sub">נבדק בעזרת Claude לפי מחוון. הסימונים באדום מופיעים על דפי התלמיד בעמודים הבאים.</div>
  <div class="top"><div class="score"><b>{esc(st["total"])}</b><span>מתוך 100</span></div>
    <div class="who"><div><b>{who}</b></div>{cls}<div>שאלות שנספרו: {", ".join(esc(c) for c in counted)}</div></div></div>
  <table><tr><th style="width:22%">שאלה</th><th style="width:14%">סעיף</th><th>ניקוד</th><th>הורדות</th></tr>{"".join(rows)}</table>
  <div class="ai"><h2>חשד לשימוש בבינה מלאכותית: <span class="num">{sc} / 100</span> ({ai_level(sc)})</h2>
    <div class="bar"><i style="left:calc({sc}% - .6mm)"></i></div>
    <div>{bidi(ai.get("summary", ""))}</div>
    <div class="cols"><div><h3>סימנים לעבודה עצמית</h3><ul>{lst(ai.get("human_signs", []))}</ul></div>
      <div><h3>סימנים לשימוש ב-AI</h3><ul>{lst(ai.get("ai_signs", []))}</ul></div></div>
    <div class="small">זו הערכה לפי דרך הפתרון והכתיבה, לא הוכחה. בחשד גבוה מומלץ לברר בשיחה קצרה עם התלמיד/ה.</div>
  </div>{flags_html}
</div>"""


def oral(st):
    qs = (st.get("ai") or {}).get("questions") or []
    if not qs:
        return ""
    items = "".join(f"<li>{bidi(x)}</li>" for x in qs)
    return f"""<section class="pg"><div class="oral" style="width:100%"><h1>שאלות לשיחה קצרה עם התלמיד/ה</h1>
  <div>שאלות על הצעדים והטעויות של התלמיד/ה עצמו/ה. מי שפתר/ה בעצמו/ה מסביר/ה אותן מיד.</div><ol>{items}</ol></div></section>"""


def build(folder, sid, check_only):
    data = data_dir(folder)
    st = load_json(data / f"{sid}.json")
    pages = sorted(pages_dir(folder, sid).glob("p[0-9][0-9].*"))
    err, warn = validate(st, len(pages))
    for w in warn:
        print(f"  {sid} warning: {w}")
    if err:
        for e in err:
            print(f"  {sid} ERROR: {e}")
        return False
    if check_only:
        print(f"  {sid} ok: total {st['total']}, ai {st['ai']['score']}")
        return True
    key = load_json(data / "key.json") if (data / "key.json").exists() else {}
    body = cover(st, key)
    for i, img in enumerate(pages, 1):
        body += (f'<section class="pg"><div class="frame"><img src="{img.name}">'
                 f'<div class="ov">{page_overlay(st, i)}</div></div></section>')
    body += oral(st)
    html_text = (f'<!doctype html><html lang="he"><head><meta charset="utf-8"><title>{esc(st.get("student") or sid)}</title>'
                 f'{FONTS}<style>{CSS}</style></head><body>{body}</body></html>')
    name = safe_name(st.get("student") or st.get("label") or sid)
    pdf = out_dir(folder) / f"{name} - בדוק.pdf"
    html_to_pdf(html_text, pages_dir(folder, sid) / "marked.html", pdf)
    print(f"  {sid} -> {pdf.relative_to(folder)}  (score {st['total']}, ai {st['ai']['score']})")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="validate only")
    a = ap.parse_args()
    folder = Path(a.folder).resolve()
    ids = a.ids
    if a.all:
        ids = sorted(p.stem for p in data_dir(folder).glob("s[0-9]*.json"))
    if not ids:
        raise SystemExit("give student ids (s01 ...) or --all")
    ok = [build(folder, sid, a.check) for sid in ids]
    sys.exit(0 if all(ok) else 1)


if __name__ == "__main__":
    main()
