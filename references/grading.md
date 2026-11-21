# Grading

## 1. The key comes first

Every grade depends on the key, so an error there repeats for every student.

1. Read the whole exam: `נתונים/exam.txt` for a typed exam, and the page images `עמודים/exam/` for the figures.
   Note the points of every part, the "choose N of M" instruction, the given data, and every figure.
2. Solve every question part by part, the way the class learned it, starting every calculation from a formula as
   it is printed on the formula sheet (`נתונים/formulas.txt` and `עמודים/formulas/`; without one, the exam's formula
   box, else the standard Ministry of Education sheet for the subject) and using the sheet's constants, and g = 10
   unless the teacher or the sheet says otherwise (many sheets do not print g). Write that formula in the part's `start_formula`. Compute every number in a
   small Python file `נתונים/key_check.py` (assert each final value) so arithmetic slips cannot enter the key.
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
* Recompute every step the student wrote (in `full_work` and `answer_first` modes), not only the final answer: each substitution, division and unit
  conversion. A correct final answer after a step that cannot produce it (350/25 written as 20) still gets the
  arithmetic deduction, on that step. If the right answer could not have come from the student's own work, add
  it to `ai_signs` (references/ai-detection.md) and to `flags` so the teacher can ask where it came from.
* Starting formula: for every calculation, check that the student first wrote a formula as it appears on the
  formula sheet and only then rearranged or substituted. A difference of notation only counts as the sheet's
  formula: W = −qΔV for W = qV_AB (the sheet itself defines V_AB = V_A − V_B and ΔV = V_B − V_A), Δx for d,
  σ/2ε₀ for 2πkσ (ε₀ = 1/4πk is printed too). What does not count is a formula already solved for another
  quantity (V = E·d when the sheet has E = V_AB/d, σ = E·ε₀, Q = V·r/k, r² = kQ/E) or a ready-made
  combination (a = g − qE/m instead of starting from ΣF = ma). Reading a slope
  off a graph is not a formula and is not penalized. Without the class's own sheet, apply this only to clear cases
  and say so in `flags`.
* g: note every part where the student substituted 9.8 (or another value) instead of the class's 10. A later part
  that only reuses a result computed with 9.8 is an error carried forward, not a new 9.8 deduction.

## 3. Points

The points of a part come from the exam. A part starts at full points; every deduction is subtracted; the part
never goes below 0. A question is the sum of its parts; the grade is the sum of the counted questions, rounded.

Grading mode (`policy.grading_mode`, asked first):
* `full_work` (default): every written step is checked and the deductions below apply.
* `answer_first`: a correct final answer gets the part's full points; the work is graded with the deductions
  below only to give partial credit to a wrong answer.
* `final_answer`: a part is right (full points) or wrong (zero); a part that asks to explain is graded on the
  explanation, which is its answer. Units and g still follow the teacher's rules, because they change the answer.
In every mode, a right final answer that does not follow from the written work goes to `flags` and `ai_signs`.

The teacher's rules come first: apply `policy.rules` from key.json exactly (they were asked in SKILL.md
section 2). For every case the teacher was not asked about, or answered "(מומלץ)", use this default table
(bagrut style). The README shows the same table to teachers, so keep the two in step.

| Situation | Default deduction |
|---|---|
| The explanation asked for ("נמקו", "הסבירו") is missing | half of the part |
| Arithmetic slip, method correct | 1 point |
| Missing or wrong units in the final answer | 0.5 point |
| Did not start from the formula as printed on the formula sheet | 1 point per part |
| Used g = 9.8 instead of 10 (the formula sheet's value) | 1 point in each part where 9.8 was substituted |
| A number or step without saying where it came from | 1 point |
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
  formula sheet:  <folder>/בדיקה/נתונים/formulas.txt and עמודים/formulas/ (if the teacher gave one)
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
