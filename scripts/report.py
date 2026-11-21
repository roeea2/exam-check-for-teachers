"""Class reports: the grade summary (PDF + CSV for Excel) and the answer key as a PDF.

    python3 report.py "<exam folder>" summary     -> בדיקה/סיכום ציונים.pdf + סיכום ציונים.csv
    python3 report.py "<exam folder>" key         -> בדיקה/מחוון.pdf (from נתונים/key.json)
"""
import argparse
import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotate import ai_level  # noqa: E402
from common import FONTS, bidi, data_dir, esc, fmt, html_to_pdf, load_json, out_dir  # noqa: E402

CSS = """
@page { size: A4; margin: 12mm 12mm 12mm 12mm; }
* { box-sizing: border-box; }
html, body { margin: 0; background: #fff; }
body { font-family: Heebo, Arial, sans-serif; direction: rtl; font-size: 10pt; line-height: 1.45; color: #1c1b1f; }
h1 { font-size: 18pt; color: #2a1650; margin: 0 0 1mm; }
h2 { font-size: 12.5pt; color: #2a1650; margin: 5mm 0 1.5mm; }
.sub { color: #555; margin-bottom: 3mm; }
.stats { display: flex; gap: 3mm; flex-wrap: wrap; margin: 2mm 0; }
.stat { border: 1px solid #ddd3ee; border-radius: 2.5mm; padding: 2mm 4mm; text-align: center; min-width: 24mm; }
.stat b { display: block; font-size: 16pt; color: #2a1650; }
table { width: 100%; border-collapse: collapse; font-size: 9.4pt; }
th, td { border: 1px solid #ddd3ee; padding: 1.2mm 1.8mm; text-align: right; vertical-align: top; }
th { background: #f3eefb; color: #2a1650; }
td.c { text-align: center; white-space: nowrap; }
.num { direction: ltr; unicode-bidi: isolate; display: inline-block; white-space: nowrap; }
.hi { color: #c62828; font-weight: 700; }
.mid { color: #b26a00; font-weight: 700; }
.bars { display: flex; gap: 2mm; align-items: flex-end; height: 32mm; margin: 2mm 0 1mm; direction: rtl; }
.bars div { flex: 1; background: #b9a3e6; border-radius: 1.5mm 1.5mm 0 0; position: relative; min-height: 1mm; }
.bars span { position: absolute; top: -5mm; left: 0; right: 0; text-align: center; font-weight: 700; }
.blab { display: flex; gap: 2mm; direction: rtl; }
.blab div { flex: 1; text-align: center; font-size: 8.8pt; color: #555; }
.q { break-inside: avoid; border: 1px solid #ddd3ee; border-radius: 2.5mm; padding: 2.5mm 4mm; margin: 3mm 0; }
.part { margin: 1.5mm 0; padding-right: 3mm; border-right: 3px solid #b9a3e6; }
.small { font-size: 8.8pt; color: #666; }
"""

MODES = {"full_work": "התשובה הסופית וגם דרך החישוב, כל שלב",
         "answer_first": "קודם התשובה: נכונה מקבלת ניקוד מלא, הדרך קובעת ניקוד חלקי לתשובה שגויה",
         "final_answer": "רק התשובה הסופית: נכון או לא נכון"}

BUCKETS = [(0, 54, "0-54"), (55, 64, "55-64"), (65, 74, "65-74"), (75, 84, "75-84"), (85, 100, "85-100")]


def students(folder):
    files = load_json(data_dir(folder) / "files.json")
    out = []
    for s in files["students"]:
        p = data_dir(folder) / f"{s['id']}.json"
        if p.exists():
            st = load_json(p)
            st.setdefault("id", s["id"])
            out.append(st)
        else:
            out.append({"id": s["id"], "student": s["name"] or s["label"], "missing": True})
    return out


def summary(folder):
    sts = students(folder)
    graded = [s for s in sts if not s.get("missing")]
    if not graded:
        raise SystemExit("no graded students yet (בדיקה/נתונים/s01.json ...)")
    key = load_json(data_dir(folder) / "key.json") if (data_dir(folder) / "key.json").exists() else {}
    qnums = sorted({q["q"] for s in graded for q in s["questions"]})
    scores = [float(s["total"]) for s in graded]

    # CSV for Excel (UTF-8 with BOM so Hebrew opens correctly)
    csv_path = out_dir(folder) / "סיכום ציונים.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["מס'", "שם", "ציון"] + [f"שאלה {q}" for q in qnums] + ["שאלות שנספרו", "חשד AI (0-100)", "רמת חשד", "הורדות עיקריות"])
        for i, s in enumerate(sts, 1):
            if s.get("missing"):
                w.writerow([i, s["student"], "לא נבדק"])
                continue
            byq = {q["q"]: q for q in s["questions"]}
            top = sorted(((m["points"], m["reason"]) for q in s["questions"] for p in q.get("parts", [])
                          for m in p.get("marks", []) if m.get("kind", "deduct") == "deduct"))[:3]
            w.writerow([i, s.get("student") or s.get("label") or s["id"], s["total"]]
                       + [fmt(byq[q]["score"]) if q in byq else "" for q in qnums]
                       + [" ".join(str(c) for c in (s.get("counted") or [])), s["ai"]["score"], ai_level(s["ai"]["score"]),
                          "; ".join(f"{fmt(p)} {r}" for p, r in top)])

    # common deductions across the class
    reasons = Counter()
    lost = defaultdict(float)
    for s in graded:
        for q in s["questions"]:
            if q["q"] not in (s.get("counted") or [x["q"] for x in s["questions"]]):
                continue
            for p in q.get("parts", []):
                for m in p.get("marks", []):
                    if m.get("kind", "deduct") == "deduct":
                        k = f"שאלה {q['q']}{p['part']}: {m['reason']}"
                        reasons[k] += 1
                        lost[k] += float(m["points"])
    common = "".join(f"<tr><td>{bidi(k)}</td><td class='c'>{n}</td><td class='c'><span class='num'>{fmt(lost[k] / n)}</span></td></tr>"
                     for k, n in reasons.most_common(12))

    counts = [sum(1 for v in scores if lo <= v <= hi) for lo, hi, _ in BUCKETS]
    mx = max(counts) or 1
    bars = "".join(f'<div style="height:{max(3, 100 * c / mx):.0f}%"><span>{c}</span></div>' for c in counts)
    blab = "".join(f"<div>{lab}</div>" for _, _, lab in BUCKETS)

    rows = []
    for i, s in enumerate(sts, 1):
        if s.get("missing"):
            rows.append(f"<tr><td class='c'>{i}</td><td>{esc(s['student'])}</td><td class='c' colspan='{len(qnums) + 2}'>לא נבדק</td></tr>")
            continue
        byq = {q["q"]: q for q in s["questions"]}
        counted = s.get("counted") or list(byq)
        ai = int(round(s["ai"]["score"]))
        cls = "hi" if ai > 60 else ("mid" if ai > 40 else "")
        cells = "".join(f"<td class='c'>{fmt(byq[q]['score']) if q in byq else ''}{'' if q not in byq or q in counted else '*'}</td>"
                        for q in qnums)
        rows.append(f"<tr><td class='c'>{i}</td><td>{esc(s.get('student') or s.get('label') or s['id'])}</td>"
                    f"<td class='c'><b>{esc(s['total'])}</b></td>{cells}<td class='c {cls}'><span class='num'>{ai}</span> ({ai_level(ai)})</td></tr>")
    flagged = [s for s in graded if s["ai"]["score"] > 40]
    flagged_html = "".join(f"<li><b>{esc(s.get('student') or s['id'])}</b>: <span class='num'>{int(round(s['ai']['score']))} / 100</span>. "
                           f"{bidi(s['ai'].get('summary', ''))}</li>" for s in flagged) or "<li>אין תלמידים עם חשד מעל 40.</li>"
    similar = [s for s in graded if s.get("similar_to")]
    similar_html = ("<h2>דמיון חריג בין תלמידים</h2><ul>" + "".join(
        f"<li><b>{esc(s.get('student') or s['id'])}</b> דומה ל: {esc(', '.join(s['similar_to']))}</li>" for s in similar)
        + "</ul>") if similar else ""

    title = key.get("title", "")
    body = f"""<h1>סיכום ציונים{(": " + esc(title)) if title else ""}</h1>
<div class="sub">נבדקו {len(graded)} מתוך {len(sts)} מבחנים. הדפים המסומנים של כל תלמיד נמצאים באותה תיקייה.</div>
<div class="stats"><div class="stat"><b>{fmt(statistics.mean(scores))}</b>ממוצע</div>
<div class="stat"><b>{fmt(statistics.median(scores))}</b>חציון</div><div class="stat"><b>{fmt(max(scores))}</b>הגבוה</div>
<div class="stat"><b>{fmt(min(scores))}</b>הנמוך</div><div class="stat"><b>{sum(1 for v in scores if v >= 55)}</b>עברו (55+)</div></div>
<h2>התפלגות</h2><div class="bars">{bars}</div><div class="blab">{blab}</div>
<h2>ציונים</h2><table><tr><th>מס'</th><th>שם</th><th>ציון</th>{"".join(f"<th>שאלה {q}</th>" for q in qnums)}<th>חשד AI</th></tr>{"".join(rows)}</table>
<div class="small">* שאלה שנענתה ולא נספרה בציון (נענו יותר שאלות מהנדרש).</div>
<h2>הטעויות הנפוצות בכיתה</h2><table><tr><th>סעיף והסיבה</th><th>תלמידים</th><th>הורדה ממוצעת</th></tr>{common or "<tr><td colspan='3'>אין</td></tr>"}</table>
<h2>חשד לשימוש בבינה מלאכותית</h2><ul>{flagged_html}</ul>
<div class="small">ציון החשד (0-100, 100 = כמעט בוודאות AI) הוא הערכה לפי דרך הפתרון והכתיבה, ולא הוכחה. לבירור: שיחה קצרה עם התלמיד/ה על הצעדים שלו/ה.</div>
{similar_html}"""
    pdf = out_dir(folder) / "סיכום ציונים.pdf"
    html_to_pdf(f'<!doctype html><html lang="he"><head><meta charset="utf-8"><title>סיכום ציונים</title>{FONTS}'
                f'<style>{CSS}</style></head><body>{body}</body></html>', data_dir(folder) / "summary.html", pdf)
    print(f"wrote {pdf.relative_to(folder)} and {csv_path.relative_to(folder)}")


def key_pdf(folder):
    key = load_json(data_dir(folder) / "key.json")
    qs = []
    for q in key["questions"]:
        parts = []
        for p in q.get("parts", []):
            ded = "".join(f"<li><span class='num'>{esc(fmt(d['points']))}</span> {bidi(d['reason'])}</li>" for d in p.get("common_deductions", []))
            parts.append(f"""<div class="part"><b>סעיף {esc(p['part'])}</b> ({fmt(p['max'])} נק'): {bidi(p.get('answer', ''))}
  {f"<div>מתחילים מהנוסחה: {bidi(p['start_formula'])}</div>" if p.get('start_formula') else ""}
  {f"<div>דרך: {bidi(p['method'])}</div>" if p.get('method') else ""}
  {f"<div>לניקוד מלא: {bidi(p['full_credit'])}</div>" if p.get('full_credit') else ""}
  {f"<div class='small'>הורדות אופייניות:<ul>{ded}</ul></div>" if ded else ""}</div>""")
        topic = f" · {bidi(q['topic'])}" if q.get("topic") else ""
        qs.append(f'<div class="q"><h2 style="margin-top:0">שאלה {esc(q["q"])}{topic} ({fmt(q["max"])} נק\')</h2>{"".join(parts)}</div>')
    pol = key.get("policy", {})
    notes = "".join(f"<li>{bidi(n)}</li>" for n in key.get("notes", []))
    rules = [(r.get("case", ""), r.get("deduct", "")) for r in pol.get("rules", [])]
    mode = MODES.get(pol.get("grading_mode"))
    if mode:
        rules.insert(0, ("מה נבדק", mode))
    extra = {"best": "נספרות השאלות הטובות ביותר", "first": "נספרות השאלות הראשונות לפי הסדר"}.get(pol.get("extra_questions"))
    if extra:
        rules.append(("תלמיד שענה על יותר שאלות מהנדרש", extra))
    rules_html = ("<h2>כללי הורדת הניקוד</h2><table><tr><th>מצב</th><th>הורדה</th></tr>"
                  + "".join(f"<tr><td>{bidi(c)}</td><td>{bidi(d)}</td></tr>" for c, d in rules) + "</table>") if rules else ""
    body = f"""<h1>מחוון{(": " + esc(key.get('title'))) if key.get('title') else ""}</h1>
<div class="sub">המחוון שלפיו נבדקו המבחנים. {bidi(pol.get('summary', ''))}</div>
{rules_html}{f"<ul>{notes}</ul>" if notes else ""}{"".join(qs)}"""
    pdf = out_dir(folder) / "מחוון.pdf"
    html_to_pdf(f'<!doctype html><html lang="he"><head><meta charset="utf-8"><title>מחוון</title>{FONTS}'
                f'<style>{CSS}</style></head><body>{body}</body></html>', data_dir(folder) / "key.html", pdf)
    print(f"wrote {pdf.relative_to(folder)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("what", choices=["summary", "key"])
    a = ap.parse_args()
    folder = Path(a.folder).resolve()
    summary(folder) if a.what == "summary" else key_pdf(folder)


if __name__ == "__main__":
    main()
