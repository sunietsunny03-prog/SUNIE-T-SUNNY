---
name: arena
description: Run a head-to-head "arena" that pits 2-4 candidate answers, designs, prompts, or implementations against each other, scores them on explicit criteria, and declares a winner. Use when the user says "arena", "compare these", "which is better", "battle", or wants the best of several options.
---

# Arena

Pit candidates against each other, judge them fairly, and name a winner.

## Steps

1. **Define the contest.** State the task and the candidates (2-4). If the user supplied only a task, generate the candidates yourself with deliberately different approaches. Label them A, B, C, D.
2. **Set criteria before looking.** Pick 3-5 criteria that fit the task (e.g. correctness, clarity, completeness, originality, effort/cost). Give each a weight; weights sum to 100. Ask the user only if the criteria are genuinely ambiguous.
3. **Blind the judging.** Evaluate each candidate on content alone, ignoring order, length, and which one you wrote. Score each criterion 1-10 with a one-line justification.
4. **Run rounds if useful.** For close scores (within ~5%), do a head-to-head tiebreak on the single most important criterion, then swap the order and re-judge to check for position bias.
5. **Declare the result.** Output a scoreboard table, the winner, and why it won. Note any strong ideas from losing candidates worth merging into the winner.
6. **Offer a next move.** Suggest applying the winner, merging the best parts, or running another round with a refined field.

## Output format

```
## Arena: <task>
| Candidate | <crit 1> (w) | <crit 2> (w) | ... | Total |
|-----------|--------------|--------------|-----|-------|
| A         | 8            | 6            | ... | 74    |

**Winner:** B - <one-sentence reason>
**Worth stealing:** <ideas from other candidates>
**Caveats:** <uncertainty, ties, bias checks>
```

## Rules

- Never change criteria or weights after seeing scores.
- Be honest about ties and uncertainty rather than forcing a margin.
- Keep justifications specific and short; no padding.
