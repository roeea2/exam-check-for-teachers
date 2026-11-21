# Grading

## 1. The key comes first

Every grade depends on the key, so an error there repeats for every student.

1. Read the whole exam: `נתונים/exam.txt` for a typed exam, and the page images `עמודים/exam/` for the figures.
   Note the points of every part, the "choose N of M" instruction, the given data, and every figure.
2. Solve every question part by part, the way the class learned it. Compute every number in a small Python file
   `נתונים/key_check.py` (assert each final value) so arithmetic slips cannot enter the key.
3. If the teacher gave a key (`מחוון.pdf`), use it: transcribe it into key.json, still recompute the numbers, and
   tell the teacher about any value you think is wrong instead of silently changing it.
4. Independent check: give one subagent only the exam pages and ask it to solve every part (no key, no student
   work). Compare; resolve every disagreement by re-deriving, not by majority.
5. Write `common_deductions` you expect (missing explanation, units, a typical wrong formula) with their points.
6. If the teacher asked to approve the key, render it (`report.py key`), show the answers in a short Hebrew
   table, and wait. Otherwise continue.

## 2. Reading a student's pages

* Look at every page (`עמודים/<id>/p01.jpg` ...). Zoom by reading the page again when handwriting is small.
* Find the name and class on the first page; put them in `student` and `class`.
* List the questions the student answered (circled numbers, headings) in the order they appear: `answered`.
* Ignore marks that are not the student's: a teacher's red/blue grading, scores, comments. Note them in `flags`
  ("על הדפים כבר יש סימוני מורה") and grade independently.
* If something is unreadable, do not guess in the student's disfavor: grade what you can read and add a flag
  ("עמוד 5 שורות 3-4 לא קריאות, לבדיקת המורה").

## 3. Points

The points of a part come from the exam. A part starts at full points; every deduction is subtracted; the part
never goes below 0. A question is the sum of its parts; the grade is the sum of the counted questions, rounded.

The teacher's rules come first: apply `policy.rules` from key.json exactly (they were asked in SKILL.md
section 2). For every case the teacher was not asked about, or answered "(מומלץ)", use this default table
(bagrut style). The README shows the same table to teachers, so keep the two in step.

| Situation | Default deduction |
|---|---|
| The explanation asked for ("נמקו", "הסבירו") is missing | half of the part |
| Arithmetic slip, method correct | 1 point |
| Missing or wrong units in the final answer | 0.5 point |
| A number, formula or step without saying where it came from | 1 point |
| Error carried forward from an earlier part | only where it was made |
| Correct final answer with no work or calculation | half of the part |
| Wrong sign or direction when the question asks for it | 1-2 points |
| Right idea, wrong formula or a misread given value | half to three quarters of the part |
| Part of the request not answered (the direction, the time) | that request's share of the part |
| A choice (multiple choice, true/false) without the explanation asked for | up to half of the part |
| Wrong answer, no relevant work | the whole part |
| Part not answered at all | the whole part |

* Error carried forward (טעות נגררת): unless the teacher chose otherwise, a wrong value from an earlier part used
  correctly later is penalized only once, where it was made. Check the later part with the student's own value.
* A different correct method gets full credit.
* Multiple-choice and true/false with a required explanation: the choice alone is worth at most half.
* "Choose N of M": count `extra_questions` as the teacher chose: `best` (default) or `first` (in the order
  written). List all answered questions in `questions`; put the counted ones in `counted`.
* If the exam's part points do not add up to the question's share (e.g. 33 instead of 33.33), keep the printed
  points and mention it in key.json `notes`.
* Consistency: before writing a deduction, look in `common_deductions` for the same mistake and use the same
  points and wording; add new mistakes there.

## 4. Deduction reasons

Hebrew, 4-5 words, specific, no blame. They are printed on the student's page.

Good: "חסר נימוק לפוטנציאל במוליך", "טעות חישוב בהוצאת השורש", "חסר כיוון מעבר האלקטרונים",
"לא חושב הזמן המבוקש", "קריאה שגויה של ערך מהגרף", "נוסחה לא מתאימה למצב", "חסרות יחידות בתשובה הסופית",
"נימוק נכון אך גרף שגוי", "הסעיף לא נענה כלל".

Avoid: "שגוי" (too short), whole sentences, English, the student's name.

## 5. Many students: one grader subagent per student

Up to 3 students: grade them yourself. More: run one subagent per student, about 5 at a time in the background,
then validate and spot-check. Prompt template:

```
You are grading one student's Hebrew physics exam for a teacher. Work only from these files:
  exam text:      <folder>/בדיקה/נתונים/exam.txt  (may be missing for a scanned exam)
  exam pages:     <folder>/בדיקה/עמודים/exam/p01.jpg ...
  answer key:     <folder>/בדיקה/נתונים/key.json   (points, answers, the teacher's deduction rules, common deductions)
  student pages:  <folder>/בדיקה/עמודים/<id>/p01.jpg ...  and locator grids grid-p01.png ...
Read <skill>/references/grading.md, <skill>/references/marking.md, <skill>/references/ai-detection.md and
<skill>/references/schemas.md first and follow them exactly.
Write <folder>/בדיקה/נתונים/<id>.json in the schema, then run
  python3 <skill>/scripts/annotate.py "<folder>" <id> --check
and fix every ERROR. Do not write the PDF. Do not open other students' files. Reasons in Hebrew, 4-5 words.
Report back: the student's name, total, ai score, and any deduction you were unsure about.
```

After all subagents finish: run `annotate.py --all --check`, compare the same part across students (same mistake,
same points), adjust `common_deductions` and the outliers, then build the PDFs.
