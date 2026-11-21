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
├── דף נוסחאות.pdf        recommended: the class's formula sheet (or a folder named נוסחאון)
└── פתרונות/              the students' work, one PDF or one folder of photos per student
    ├── דני כהן.pdf
    ├── נועה לוי/  (photos)
    └── יוסי 1.jpg, יוסי 2.jpg
```

Student files lying next to the exam also work. All output goes to `<exam folder>/בדיקה/`.

## 1. Ask first: the files, then how to grade

Ask in three AskUserQuestion calls, in Hebrew, before you read any student's work. Skip only what the teacher
already said (for example, a folder named in the request that already holds everything). The usual answer comes
first, marked "(מומלץ)"; the teacher can type their own in "Other" (for example "חוסר נימוק: 2 נקודות").

Round 1:
1. "איפה המבחן, דף הנוסחאות והמבחנים הסרוקים?": "תפתח לי תיקייה ואשים בה הכול (מומלץ)" / "הכול כבר בתיקייה
   אחת (אכתוב את שמה)" / "אכתוב איפה כל קובץ נמצא".
2. "יש מחוון (פתרון של המורה)?": "לא, תבנה מחוון ותראה לי לפני הבדיקה (מומלץ)" / "לא, תבנה ותבדוק בלי
   לעצור" / "כן, אשים אותו בתיקייה עם המבחן".
3. "מה לבדוק: רק את התשובה הסופית, או גם את דרך החישוב?": "גם את דרך החישוב: כל שלב נבדק (מומלץ)" /
   "קודם התשובה: תשובה נכונה מקבלת ניקוד מלא, והדרך נבדקת רק לניקוד חלקי כשהתשובה שגויה" / "רק את התשובה
   הסופית: נכון או לא נכון".
4. "כמה להוריד כשחסר נימוק בסעיף שביקש לנמק?": "חצי מהסעיף (מומלץ)" / "רבע מהסעיף" / "את כל הסעיף".

Then get the files in place (answer to question 1):
* "תפתח לי תיקייה": pick a short Hebrew name from the request (subject and class), run
  `python3 scripts/find_exam.py "<workspace>/בדיקת מבחנים/<name>" --create`, and write to the teacher:
  "פתחתי תיקייה: <the full path>. שימו בה את המבחן או הבוחן ואת דף הנוסחאות (קובץ או תיקייה שיש
  בשמם "נוסחאות" או "נוסחאון"), ובתת-התיקייה פתרונות את המבחנים הסרוקים: קובץ PDF לכל תלמיד, או תיקייה עם הצילומים שלו בשם
  התלמיד. כתבו לי כשסיימתם." Wait for the answer.
* "הכול כבר בתיקייה": use the folder the teacher names.
* "אכתוב איפה כל קובץ נמצא": the teacher types the paths or drags the files into this window. Create a folder
  with `--create` and copy them in: the exam and the formula sheet at the top, the scans into `פתרונות/`.

If the workspace is a git repository, add the exam folder to its .gitignore before any student file lands there.
Then run step 2, and only after it ask rounds 2 and 3.

Round 2:
1. "כמה להוריד על טעות חישוב כשהדרך נכונה?": "נקודה אחת (מומלץ)" / "2 נקודות" / "רבע מהסעיף".
2. "תלמיד שלא התחיל מהנוסחה כפי שהיא מופיעה בדף הנוסחאות (הציב ישר בנוסחה שכבר נפתרה למשתנה אחר)":
   "נקודה אחת בכל סעיף (מומלץ)" / "חצי נקודה בכל סעיף" / "לא להוריד".
3. "שימוש ב-g = 9.8 במקום 10 (הערך המקובל בכיתה)": "נקודה אחת בכל סעיף שבו הוצב (מומלץ)" / "נקודה אחת,
   פעם אחת בכל המבחן" / "לא להוריד".
4. "יחידות חסרות או שגויות בתשובה הסופית": "חצי נקודה (מומלץ)" / "נקודה אחת" / "לא להוריד".

Round 3:
1. "טעות נגררת (שימוש נכון בתוצאה שגויה מסעיף קודם)": "להוריד רק במקום שבו נעשתה (מומלץ)" / "להוריד בכל
   סעיף שבו היא מופיעה".
2. "תשובה סופית נכונה בלי דרך או חישוב": "חצי מהסעיף (מומלץ)" / "ניקוד מלא" / "אפס".
3. "מספר או צעד בלי הסבר מאיפה הגיעו": "נקודה אחת (מומלץ)" / "לא להוריד".
4. Only if the exam says "choose N of M": "תלמיד שענה על יותר שאלות מהנדרש": "לספור את הטובות ביותר
   (מומלץ)" / "לספור את הראשונות לפי הסדר במחברת".

If the teacher chose "רק את התשובה הסופית", skip the questions about the work (round 2 questions 1-2 and round 3
questions 1-3): a part is right (full points) or wrong (zero), and a part that asks to explain is graded on the
explanation, which is its answer. With "קודם התשובה", ask everything: the method rules decide the partial credit
of a wrong answer. In every mode, a right final answer that does not follow from the written work still goes to
`flags` and to `ai_signs`.

Write the answers into key.json `policy` (`grading_mode`, `rules`, `extra_questions`, `carry_forward`;
references/schemas.md),
confirm them to the teacher in two or three Hebrew lines, and apply them to every student. Cases the teacher was
not asked about follow the default table in references/grading.md section 3. The AI check always runs; it is part
of every report.

## 2. Find and prepare the files

```
python3 scripts/find_exam.py "<exam folder>"        # exam, formula sheet, key, students -> בדיקה/נתונים/files.json
python3 scripts/prepare_pages.py "<exam folder>"    # page images + locator grids (in the background for big classes)
```

Tell the teacher in one or two Hebrew lines what was found: the exam, the formula sheet, the key, how many
students. Ask for anything missing before going on:
* no exam: which file it is (rerun with `--exam FILE`);
* no formula sheet in the folder: find_exam.py falls back to the Ministry of Education physics formula sheet
  (2027) that ships with the skill (`assets/physics-formula-sheet-2027.pdf`). Tell the teacher, and if the class
  uses another sheet, ask them to add it (a file or folder with "נוסחאות" or "נוסחאון" in its name);
* photos that cannot be grouped by student: put each student's photos in a folder named after the student.

Look at the exam's first page to see whether it says "choose N of M" (for round 3).

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

* `scripts/find_exam.py`: find the exam, the formula sheet, the key and each student's files; `--create` opens a new
  exam folder (with `פתרונות/`) for the teacher to fill.
* `scripts/prepare_pages.py`: page images (any scan size, photos, HEIC, Word) and percent locator grids.
* `scripts/annotate.py`: validate a grading JSON and build the marked PDF (cover page, circled errors, talk questions).
* `scripts/report.py`: class summary PDF and CSV, and the key as a PDF.
* `scripts/common.py`: folders, Chrome printing, poppler rendering, formulas kept left-to-right in Hebrew.
* `assets/physics-formula-sheet-2027.pdf`: the Ministry of Education physics formula sheet, the default sheet.
* `references/grading.md` (key, points, reasons, grader subagents), `references/marking.md` (boxes and checking),
  `references/ai-detection.md` (signs, score bands, talk questions), `references/schemas.md` (JSON formats).
