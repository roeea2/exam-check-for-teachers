"""Builds docs/exam-check-guide.pdf: a one-page Hebrew guide for teachers.

    python3 docs/make_guide.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from common import find_chrome  # noqa: E402

REPO = "https://github.com/roeea2/exam-check-for-teachers"

LOGO = r"""   _______
  /       \      ____                             _      ___
 /  \ | /  \    |  _ \    ___     ___    ___     / \    |_ _|
|  -- O --  |   | |_) |  / _ \   / _ \  / _ \   / _ \    | |
 \  / | \  /    |  _ &lt;  | (_) | |  __/ |  __/  / ___ \   | |
  \_______/     |_| \_\  \___/   \___|  \___| /_/   \_\ |___|"""

CSS = """
@page { size: A4; margin: 10mm 12mm 9mm 12mm; }
* { box-sizing: border-box; }
html, body { margin: 0; background: #fff; }
body { font-family: Heebo, Arial, sans-serif; font-size: 10.2pt; line-height: 1.42; color: #1c1b1f; }
.top { background: linear-gradient(135deg, #2a1650, #4a2a7f 60%, #6a3fb0); color: #fff; border-radius: 12px; padding: 7pt 14pt 8pt; text-align: center; }
.logo { font-family: 'JetBrains Mono', Menlo, Consolas, monospace; font-size: 6.6pt; line-height: 1.1; margin: 0 auto 3pt; display: inline-block; text-align: left; direction: ltr; color: #e9dcff; }
h1 { margin: 0; font-size: 18pt; letter-spacing: 0.4pt; direction: ltr; }
.tag { font-size: 10.3pt; color: #e9dcff; margin-top: 1pt; }
h2 { font-size: 11.4pt; color: #4a2a7f; margin: 0 0 3pt; }
.card { border: 1px solid #ddd3ee; border-radius: 10px; padding: 6pt 11pt 7pt; margin-top: 6pt; }
.main { border: 2px solid #4a2a7f; background: #fcfaff; padding: 8pt 12pt 9pt; }
.main h2 { font-size: 15pt; margin-bottom: 6pt; }
.steps { display: grid; grid-template-columns: 1.15fr 1fr; gap: 12pt; align-items: start; }
.steps > *, .row2 > * { min-width: 0; }
.step { display: flex; gap: 8pt; margin: 0 0 9pt; font-size: 11.6pt; line-height: 1.48; }
.step:last-child { margin-bottom: 0; }
.step .n { background: #4a2a7f; color: #fff; border-radius: 50%; width: 21pt; height: 21pt; display: inline-flex; align-items: center; justify-content: center; font-size: 11.5pt; font-weight: 700; flex: none; margin-top: 1pt; }
.step b.h { color: #4a2a7f; }
.small { font-size: 9.6pt; color: #555; }
.tree { background: #fff; border: 1px solid #ddd3ee; border-radius: 8px; padding: 8pt 10pt; font-size: 10.8pt; }
.tree .cap { font-weight: 700; color: #4a2a7f; margin-bottom: 4pt; font-size: 10.4pt; }
.row { display: flex; align-items: center; gap: 5pt; margin: 5pt 0; white-space: nowrap; }
.row svg { flex: none; }
.in1 { padding-right: 16pt; } .in2 { padding-right: 34pt; }
.hl { background: #fff3b0; border-radius: 5px; padding: 1pt 5pt; font-weight: 700; }
.pill { background: #4a2a7f; color: #fff; border-radius: 9px; padding: 0 6pt; font-size: 8.6pt; font-weight: 600; }
.mute { color: #8a8494; font-size: 8.8pt; }
.prompt { background: #f3eefb; border-right: 4px solid #4a2a7f; border-radius: 6px; padding: 5pt 9pt; margin: 3pt 0; font-weight: 500; }
.cmd { font-family: 'JetBrains Mono', Menlo, Consolas, Heebo, monospace; font-size: 8.6pt; direction: ltr; text-align: left; background: #1f1b2e; color: #e9e3ff; border-radius: 6px; padding: 4pt 8pt; margin: 3pt 0 0; white-space: pre; }
.ltr { direction: ltr; unicode-bidi: isolate; font-family: 'JetBrains Mono', Menlo, monospace; font-size: 0.9em; white-space: nowrap; }
.url { display: block; direction: ltr; text-align: left; font-family: 'JetBrains Mono', Menlo, monospace; font-size: 8.8pt; margin: 1pt 0; color: #4a2a7f; }
.ex { background: #f8f6fc; border-radius: 6px; padding: 2pt 8pt; margin: 3pt 0; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 6pt; }
ul { margin: 2pt 0 0; padding-right: 15pt; }
li { margin: 1pt 0; }
.foot { margin-top: 7pt; text-align: center; font-size: 8.6pt; color: #6c6878; }
.foot b { color: #4a2a7f; }
"""

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800'
         '&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')

FOLDER = ('<svg width="15" height="12" viewBox="0 0 15 12"><path d="M1 2.2C1 1.5 1.5 1 2.2 1H5.6L7 2.6H12.8C13.5 2.6 14 3.1 14 3.8V9.8C14 10.5 13.5 11 12.8 11H2.2C1.5 11 1 10.5 1 9.8Z" '
          'fill="#b9a3e6" stroke="#4a2a7f" stroke-width="0.9"/></svg>')
FILE = ('<svg width="11" height="13" viewBox="0 0 11 13"><path d="M1 1.5C1 1.2 1.2 1 1.5 1H7L10 4V11.5C10 11.8 9.8 12 9.5 12H1.5C1.2 12 1 11.8 1 11.5Z" '
        'fill="#fff" stroke="#6c6878" stroke-width="0.9"/><path d="M7 1V4H10" fill="none" stroke="#6c6878" stroke-width="0.9"/></svg>')

BODY = f"""
<div class="top">
  <pre class="logo">{LOGO}</pre>
  <h1>Exam Check for Teachers</h1>
  <div class="tag">סקיל ל-Claude Code שבודק מבחנים בפיזיקה מסריקות או מצילומים, מסמן טעויות על הדף ומעריך שימוש ב-AI</div>
</div>

<div class="card main">
  <h2>מה צריך לעשות? שלושה צעדים</h2>
  <div class="steps">
    <div>
      <div class="step"><span class="n">1</span><div><b class="h">מתקינים פעם אחת.</b> פותחים את Claude Code בתיקייה של הפרויקט שלכם, ומדביקים את הודעת ההתקנה שבתיבה למטה.</div></div>
      <div class="step"><span class="n">2</span><div><b class="h">שמים מבחן ופתרונות בתיקייה.</b> את המבחן בתיקייה עצמה, ואת העבודות בתת-תיקייה <b>פתרונות</b>: קובץ PDF לכל תלמיד, או תיקייה עם הצילומים שלו.<br>
        <span class="small">סריקה, צילום מהטלפון או CamScanner, הכול עובד. מחוון משלכם לא חובה.</span></div></div>
      <div class="step"><span class="n">3</span><div><b class="h">מבקשים בדיקה.</b> כותבים למשל "תבדוק את המבחנים בתיקייה מבחן חשמל", עונים על שתיים-שלוש שאלות, ומקבלים הכול בדוק.</div></div>
    </div>
    <div class="tree">
      <div class="cap">כך נראית התיקייה:</div>
      <div class="row">{FOLDER}<b>מבחן חשמל</b> <span class="mute">(תיקייה לכל מבחן)</span></div>
      <div class="row in1">{FILE}<span class="hl">מבחן</span> <span class="pill">המבחן עצמו</span></div>
      <div class="row in1">{FILE}מחוון <span class="mute">(לא חובה)</span></div>
      <div class="row in1">{FOLDER}<span class="hl">פתרונות</span> <span class="pill">העבודות של התלמידים</span></div>
      <div class="row in2">{FILE}דני כהן</div>
      <div class="row in2">{FOLDER}נועה לוי <span class="mute">(צילומים)</span></div>
      <div class="row in1">{FOLDER}בדיקה <span class="mute">(התוצאות נשמרות כאן)</span></div>
    </div>
  </div>
</div>

<div class="card">
  <h2>הודעת ההתקנה (צעד 1)</h2>
  <div class="prompt">התקן בפרויקט הזה את הסקיל exam-check-for-teachers מהכתובת
  <span class="url">{REPO}</span>
  לתיקייה <span class="ltr">.claude/skills/exam-check-for-teachers</span> של הפרויקט (לא בהתקנה גלובלית),
  ובדוק ש-Python&nbsp;3.10+, Google&nbsp;Chrome ו-poppler מותקנים. אמור לי אם חסר משהו.</div>
  <span class="small">או מהטרמינל, מתוך תיקיית הפרויקט:</span>
  <div class="cmd">git clone {REPO}.git \\
  .claude/skills/exam-check-for-teachers</div>
</div>

<div class="row2">
  <div class="card">
    <h2>מה מקבלים</h2>
    <ul>
      <li><b>לכל תלמיד PDF:</b> דף ציון 0-100, ואחריו הדפים שלו עם כל טעות מוקפת באדום, הנקודות שירדו וסיבה של 4-5 מילים</li>
      <li><b>חשד לשימוש ב-AI:</b> ציון 0-100 עם הסימנים, ובחשד גבוה שאלות לשיחה קצרה</li>
      <li><b>סיכום כיתתי:</b> ממוצע, התפלגות, טעויות נפוצות, וקובץ לאקסל</li>
    </ul>
  </div>
  <div class="card">
    <h2>חשוב לדעת</h2>
    <ul>
      <li>הסקיל בונה מחוון ומאמת אותו לפני הבדיקה. אפשר לבקש לראות ולאשר אותו קודם</li>
      <li>ציון ה-AI הוא הערכה לפי דרך הפתרון, לא הוכחה</li>
      <li>רוצים לשנות? "בשאלה 2א תוריד רק נקודה לכולם", והכול נבנה מחדש</li>
    </ul>
  </div>
</div>

<div class="foot">העבודות של התלמידים נשארות במחשב שלכם: הסקיל לא מעלה דפים או שמות לשום מקום.<br>
דרישות: Python 3.10+ · Google Chrome · poppler · חיבור לאינטרנט בזמן הבנייה<br>
<span class="ltr">{REPO}</span> &nbsp;·&nbsp; רישיון MIT &nbsp;·&nbsp; <b>RoeeAI</b></div>
"""


def main():
    html = HERE / "guide.html"
    html.write_text(f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>Exam Check for Teachers</title>'
                    f'{FONTS}<style>{CSS}</style></head><body>{BODY}</body></html>', encoding="utf-8")
    pdf = HERE / "exam-check-guide.pdf"
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True)
    print("wrote", pdf)


if __name__ == "__main__":
    main()
