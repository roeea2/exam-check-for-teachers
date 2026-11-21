# JSON formats

All files live in `<exam folder>/בדיקה/נתונים/`. Write them with `ensure_ascii=False` (Hebrew stays readable).
`annotate.py --check` validates the student files; fix every ERROR it prints.

## files.json and pages.json (written by the scripts)

`find_exam.py` writes `files.json`: `exam.files`, `exam.text_layer`, `key.files`, `formulas.files` (the formula
sheet, a file or a folder with "נוסחאות" or "נוסחאון" in its name; `formulas.bundled` is true when the folder had
none and the skill's own Ministry of Education sheet is used), and `students`, each with
`id` (s01, s02 ...), `name` (empty when the file name is generic, then read it from the first page), `label`
(file or folder name) and `files`. `prepare_pages.py` writes `pages.json`: document id to page images.

## key.json (you write it)

```json
{
  "title": "מבחן מסכם אלקטרוסטטיקה יב",
  "n_questions": 4,
  "choose": 3,
  "policy": {
    "grading_mode": "full_work",
    "extra_questions": "best",
    "carry_forward": true,
    "rules": [
      {"case": "חוסר נימוק כשהשאלה ביקשה לנמק", "deduct": "חצי מהסעיף"},
      {"case": "טעות חישוב כשהדרך נכונה", "deduct": "נקודה אחת"},
      {"case": "לא התחיל מהנוסחה כפי שהיא בדף הנוסחאות", "deduct": "נקודה אחת בכל סעיף"},
      {"case": "שימוש ב-g = 9.8 במקום 10", "deduct": "נקודה אחת בכל סעיף שבו הוצב"},
      {"case": "יחידות חסרות או שגויות בתשובה הסופית", "deduct": "חצי נקודה"},
      {"case": "טעות נגררת", "deduct": "רק במקום שבו נעשתה"},
      {"case": "תשובה סופית נכונה בלי דרך", "deduct": "חצי מהסעיף"},
      {"case": "מספר או צעד בלי הסבר", "deduct": "נקודה אחת"}
    ],
    "summary": "כללי ההורדה שבחר/ה המורה לפני הבדיקה. מקרים אחרים לפי טבלת ברירת המחדל."
  },
  "questions": [
    {"q": 3, "topic": "כדור מוליך וקליפה", "max": 33.33,
     "parts": [
       {"part": "א", "max": 8,
        "answer": "Q = 8.33·10⁻⁹ C ,  r_B = 0.1 m",
        "start_formula": "V = kQ/r (בתוך מוליך: V = kQ/R), E = kQ/r²",
        "method": "V בתוך מוליך שווה ל-V על פניו: 1500 = kQ/0.05. אחר כך 7500 = kQ/r²",
        "full_credit": "נימוק שהפוטנציאל בתוך המוליך קבוע, הצבה נכונה, יחידות",
        "common_deductions": [{"reason": "חסר נימוק לפוטנציאל בתוך המוליך", "points": -2},
                              {"reason": "טעות חישוב בהוצאת השורש", "points": -1}]}
     ]}
  ],
  "notes": ["בשאלה 2 סכום הסעיפים 33 ולא 33.33 (כך במבחן)."]
}
```

* `max` of a part: the points printed in the exam. When the exam prints only per-question points, split them
  sensibly and say so in `notes`.
* `policy.grading_mode`: `full_work` (every step checked), `answer_first` (a right answer gets full points, the
  work decides partial credit for a wrong one) or `final_answer` (right or wrong only).
* `policy.rules`: the teacher's answers from SKILL.md section 2, in Hebrew, one rule per case (a custom rule
  typed in "Other" goes in as written). `extra_questions` is `best` or `first`; `carry_forward` false means
  the teacher wants a carried-forward error deducted in every part. `report.py key` prints the rules.
* `common_deductions` grows while you grade: the same mistake gets the same deduction for every student, and
  its points must follow `policy.rules`.
* `answer` holds the final values (with the formula sheet's constants, and g = 10 unless told otherwise); keep the computation that proves
  them in `key_check.py` next to it. `start_formula`: the formula-sheet formula(s) a full answer starts from.

## <id>.json, one per student (you or a grader subagent write it)

```json
{
  "id": "s01",
  "student": "דני כהן",
  "class": "יב 1",
  "answered": [3, 4, 2],
  "counted": [3, 4, 2],
  "questions": [
    {"q": 3, "title": "כדור מוליך", "max": 33.33, "score": 28.33,
     "parts": [
       {"part": "א", "max": 8, "score": 7,
        "marks": [
          {"kind": "deduct", "points": -1, "reason": "חסר הסבר למקור 75", "page": 2, "box": [23, 16, 9, 6]},
          {"kind": "ok", "page": 1, "box": [31, 72, 30, 5]}
        ]},
       {"part": "ו", "max": 3, "score": 0,
        "marks": [{"kind": "deduct", "points": -3, "reason": "הסעיף לא נענה כלל", "page": 6, "box": [70, 5, 25, 5]}]}
     ]}
  ],
  "total": 74,
  "ai": {
    "score": 12,
    "summary": "הפתרון נראה עבודה עצמית: טעויות אישיות, מחיקות וקיצורי דרך.",
    "human_signs": ["חוסר עקביות בין סעיף א ל-ב בשאלה 2", "המספר 75 חושב בראש בלי הסבר"],
    "ai_signs": ["חלק מהנימוקים מנוסחים כמו בספר"],
    "questions": ["מה זה ה-75 שכתבת בשאלה 3א? איך הגעת אליו?"]
  },
  "flags": ["עמוד 6 חתוך בתחתית: ייתכן שחסרה שורה"],
  "notes": [{"kind": "note", "page": 4, "box": [10, 40, 30, 6], "text": "סימון של המורה, לא נבדק"}],
  "similar_to": []
}
```

Rules `annotate.py` enforces:
* every part: `score = max + sum(deduction points)`, and `0 ≤ score ≤ max`;
* every question: `score = sum(part scores)`;
* `total = round(sum of the counted questions' scores)`, between 0 and 100;
* a deduction has negative `points` and a `reason` (aim for 4-5 Hebrew words, 3-6 accepted);
* `box` is `[x, y, w, h]` in percent of the page image (x from the left edge, y from the top), read from the
  locator grid; `page` is 1-based in the student's own page order;
* `ai.score` is 0-100 (100 = solved with AI for sure), with evidence lists.

Mark kinds: `deduct` (red circle and label with the points and the reason), `ok` (green check at the right edge
of the box, optional), `note` (blue dashed box with `text`, no points). A deduction without a box (for a part the
student skipped and no natural place on the page) appears on the cover page only. `label_at: [x, y]` puts the
label's top-right corner at that point when the automatic place (under the circle) covers writing;
`label_at: [x, y, "left"]` puts its top-left corner there (for a free space to the right of the circle).
`label_w: 16` limits the label to 16% of the page width so it wraps into a narrow margin.
