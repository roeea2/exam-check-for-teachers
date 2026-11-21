# Was the exam solved with an AI model?

Give every student `ai.score` from 0 to 100 (100 = solved with AI for sure) with the evidence. It is an estimate
from the way the solution is written and reasoned, never proof: a strong student can look clean, and a student who
copied can make mistakes. Write it carefully, because a teacher may act on it with a minor.

## How to look

Compare the student's work with three things: the key (your own solution, which is close to what a model writes),
the student's other answers in the same exam, and the other students. Look for patterns across several parts, not
one sentence.

### Signs of the student's own work (lower the score)

| Sign | Example |
|---|---|
| Inconsistency between parts of the same question | a graph in part א that contradicts the values used in part ב |
| Right reasoning, wrong conclusion | "the slope must increase", then the graph with the decreasing slope |
| Idiosyncratic shortcuts | a number like "75" appearing without saying it is kQ |
| Given data left unused | ignoring a distance the question gives |
| Parts left unfinished | the acceleration is computed but the time asked for is not |
| Requests that were not answered | no direction when the question asks "from which to which" |
| Process traces | crossed-out lines, corrections, arrows, re-done steps, a check like "8.34 ≈ 8.33" |
| Personal notation and units | Σf, numbers not in standard form (4500·10⁻⁹ J), rounding mid-way |
| Typical student slips | sign errors in energy conservation, misreading a figure, mixed-up labels |
| Order of answering by confidence | starting with question 3, skipping question 1 |

### Signs of AI use (raise the score)

| Sign | Example |
|---|---|
| Every request answered completely, in every part | direction, units and final sentence everywhere, nothing skipped |
| Uniform, formal textbook phrasing | "נשתמש בחוק שימור האנרגיה", "נציב את הנתונים", "לכן התשובה הסופית היא" in every part |
| Symbolic derivation before numbers everywhere, same structure in every part | "נתונים / פתרון / תשובה" headings |
| Constants with extra precision or not used in class | k = 8.99·10⁹, ε₀ = 8.854·10⁻¹², e = 1.602·10⁻¹⁹ |
| Methods or notation beyond the syllabus | calculus or vector notation the class did not learn |
| Perfect consistency and no process traces | clean copy, no corrections, even pacing over many pages |
| Distinctive steps identical to the key or to a model's typical solution | the same unusual order of steps and the same wording |
| Model-style errors | a value that is not in the exam (hallucinated), a figure read in left-to-right order (graph labels I↔IV swapped), a confident wrong claim with a polished explanation |
| Typed work: model formatting left in | `**`, `###`, LaTeX like `\frac`, `$...$`, bullet structure, English words |
| Same unusual errors or wording as another student | points to a shared source (AI or each other): fill `similar_to` |

## Score bands

| Score | Meaning | Typical picture |
|---|---|---|
| 0-20 | נמוך מאוד | several clear signs of own work, no AI signs |
| 21-40 | נמוך | mostly own work, one or two neutral "clean" features |
| 41-60 | לא חד-משמעי | mixed signs, or too little written to judge |
| 61-80 | גבוה | several independent AI signs, few process traces |
| 81-100 | גבוה מאוד | converging AI signs: model-style errors or formatting, identical distinctive steps, no traces of work |

Calibrate: good handwriting, correct answers and a high grade are not AI signs on their own. A short or mostly
empty exam is 41-60 at most ("אין מספיק חומר לשפוט") unless something specific points either way.

## What to write

* `summary`: one Hebrew sentence with the conclusion.
* `human_signs` and `ai_signs`: 2-5 concrete items each, with the question and part ("שאלה 2א: ...").
* `questions`: for a score above 40, 4-6 questions for a short spoken talk with the student, about the
  student's own unusual steps and mistakes ("מה זה ה-75 שכתבת?", "למה בחרת בגרף II?"), plus one or two small
  questions with new numbers. Someone who solved it explains at once; someone who copied cannot explain their
  own idiosyncratic steps. Use wording that is the same for a boy and a girl (past tense: "כתבת", "בחרת", "הגעת").

## Across the class

After grading everyone, compare: identical unusual mistakes, identical wording, the same skipped part solved the
same odd way. Put the ids of similar students in `similar_to` and mention it in the summary report; raise the AI
score only if the shared pattern also looks like model output (otherwise it may be copying between students,
which is a different conversation).
