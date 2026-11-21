---
name: exam-check-for-teachers
description: Grades students' handwritten physics exams from scans or phone photos, in Hebrew. The teacher puts one exam and many students' solutions in a folder; the skill builds and verifies an answer key, grades every student 0-100 by the exam's points, circles each error on the student's own page with the points taken off and a 4-5 word Hebrew reason, estimates for each student how likely the exam was solved with an AI model (0-100, 100 = AI for sure) with the evidence, and writes a marked PDF per student plus a class summary (PDF and Excel CSV). Use it whenever a teacher asks to check, grade or mark exams or quizzes (לבדוק מבחנים, בדיקת מבחן, לתת ציון, לסמן טעויות, מחוון, בוחן, מחברות בחינה), to grade scanned or photographed student work, or to check whether a student used AI or ChatGPT on a test, even if they do not mention a folder.
---

# Exam check for teachers

Grade a class set of exams the way a careful teacher would: a verified key first, the same deduction for the same
mistake in every paper, every deduction visible on the student's page with a short reason, and an honest,
evidence-based estimate of AI use. Everything the teacher sees is in Hebrew.

Requirements: Python 3.10+, Google Chrome or Chromium, poppler (`pdftoppm`, `pdftotext`, `pdfinfo`). Photos in
HEIC or TIFF are converted with macOS `sips`; a Word exam needs LibreOffice (or the teacher saves it as PDF).
Building PDFs loads the Heebo font from Google Fonts.

Student work is private and belongs to minors: keep every file inside the teacher's workspace, never upload pages
or names anywhere, and if the workspace is a git repository make sure the exam folder is in its .gitignore.

## The folder

```
<exam folder>/
├── מבחן.pdf              the exam (PDF, Word, or photos named מבחן 1.jpg, מבחן 2.jpg)
├── מחוון.pdf             optional: the teacher's own solution or rubric
└── פתרונות/              the students' work, one PDF or one folder of photos per student
    ├── דני כהן.pdf
    ├── נועה לוי/  (photos)
    └── יוסי 1.jpg, יוסי 2.jpg
```

Student files lying next to the exam also work. All output goes to `<exam folder>/בדיקה/`.

## 1. Find and prepare the files

If you do not know the folder, look for one with an exam and students' work in the workspace, or ask for it.

```
python3 scripts/find_exam.py "<exam folder>"        # exam, key, students -> בדיקה/נתונים/files.json
python3 scripts/prepare_pages.py "<exam folder>"    # page images + locator grids (in the background for big classes)
```

Read the warnings. If the exam was not found or photos cannot be grouped by student, ask the teacher (or rerun
with `--exam FILE`). Look at the exam's first page to see whether it says "choose N of M". Tell the teacher in one
line how many students were found.

## 2. Ask the teacher how to grade, before reading any student's work

A grade is only as fair as its rules, and the rules are the teacher's call. Ask in two AskUserQuestion calls, in
Hebrew, before you grade anything; skip only what the teacher already said. Each question offers the usual rule
first, marked "(מומלץ)", and the teacher can type a rule of their own in "Other" (for example "חוסר נימוק: 2 נקודות").

Round 1:
1. "יש מחוון (פתרון של המורה)?": "לא, תבנה מחוון ותראה לי לפני הבדיקה (מומלץ)" / "לא, תבנה ותבדוק בלי
   לעצור" / "כן, הוא בתיקייה" (put this one first when find_exam.py found a key).
2. "כמה להוריד כשחסר נימוק בסעיף שביקש לנמק?": "חצי מהסעיף (מומלץ)" / "רבע מהסעיף" / "את כל הסעיף".
3. "כמה להוריד על טעות חישוב כשהדרך נכונה?": "נקודה אחת (מומלץ)" / "2 נקודות" / "רבע מהסעיף".
4. Only if the exam says "choose N of M": "תלמיד שענה על יותר שאלות מהנדרש": "לספור את הטובות ביותר
   (מומלץ)" / "לספור את הראשונות לפי הסדר במחברת". Otherwise ask round 2's first question here.

Round 2:
1. "יחידות חסרות או שגויות בתשובה הסופית": "חצי נקודה (מומלץ)" / "נקודה אחת" / "לא להוריד".
2. "טעות נגררת (שימוש נכון בתוצאה שגויה מסעיף קודם)": "להוריד רק במקום שבו נעשתה (מומלץ)" / "להוריד בכל
   סעיף שבו היא מופיעה".
3. "תשובה סופית נכונה בלי דרך או חישוב": "חצי מהסעיף (מומלץ)" / "ניקוד מלא" / "אפס".
4. "מספר, נוסחה או צעד בלי הסבר מאיפה הגיעו": "נקודה אחת (מומלץ)" / "לא להוריד".

Write the answers into key.json `policy` (`rules`, `extra_questions`, `carry_forward`; references/schemas.md),
confirm them to the teacher in two or three Hebrew lines, and apply them to every student. Cases the teacher was
not asked about follow the default table in references/grading.md section 3. The AI check always runs; it is part
of every report.

## 3. Build and verify the key

Follow `references/grading.md` section 1: read the exam and its figures, solve every part, prove every number in
`נתונים/key_check.py`, have one subagent solve the exam blind and compare, then write `נתונים/key.json`
(`references/schemas.md`) and `python3 scripts/report.py "<exam folder>" key`. If the teacher wants to approve the
key, show a short Hebrew table of the answers and wait.

## 4. Grade every student

For each student (yourself for up to 3, otherwise one grader subagent per student, `references/grading.md` section 5):
1. Read every page; name, class, answered questions; ignore existing teacher marks.
2. Grade each part against the key and the policy: partial credit, error carried forward counted once, the same
   mistake gets the same deduction (`common_deductions`). Reasons: Hebrew, 4-5 words.
3. Locate every deduction on the locator grid (`references/marking.md`) and write the box.
4. Estimate the AI likelihood with the evidence (`references/ai-detection.md`); for a score above 40 add questions
   for a short talk with the student.
5. Write `נתונים/<id>.json` and run `python3 scripts/annotate.py "<exam folder>" <id> --check` until it passes.

Then compare the class: the same part across students (consistent points), and unusual shared mistakes or wording
(`similar_to`).

## 5. Build the reports and look at them

```
python3 scripts/annotate.py "<exam folder>" --all          # בדיקה/<name> - בדוק.pdf for every student
python3 scripts/report.py "<exam folder>" summary          # בדיקה/סיכום ציונים.pdf + סיכום ציונים.csv
```

Render the marked pages (`references/marking.md`, "Check the result") and look at every page with marks for at
least the first two students and a sample of the rest. Fix boxes and labels, rebuild.

## 6. Report to the teacher (Hebrew, short)

* A table: student, score, AI suspicion (score and level), one line on the main mistakes.
* Class average and the two or three most common mistakes.
* Students with AI suspicion above 40: the main evidence, and that it is an estimate to check in a short talk,
  not proof.
* Anything for the teacher to check (unreadable lines, missing pages, a key value they gave that looks wrong).
* Links to `בדיקה/סיכום ציונים.pdf`, the CSV, the key and the marked PDFs.

If the teacher disagrees with a deduction, change that student's JSON (and `common_deductions` if it applies to
everyone), rerun `annotate.py` for the affected students and `report.py summary`.

## Files in this skill

* `scripts/find_exam.py`: find the exam, the key and each student's files.
* `scripts/prepare_pages.py`: page images (any scan size, photos, HEIC, Word) and percent locator grids.
* `scripts/annotate.py`: validate a grading JSON and build the marked PDF (cover page, circled errors, talk questions).
* `scripts/report.py`: class summary PDF and CSV, and the key as a PDF.
* `scripts/common.py`: folders, Chrome printing, poppler rendering.
* `references/grading.md` (key, points, reasons, grader subagents), `references/marking.md` (boxes and checking),
  `references/ai-detection.md` (signs, score bands, talk questions), `references/schemas.md` (JSON formats).
