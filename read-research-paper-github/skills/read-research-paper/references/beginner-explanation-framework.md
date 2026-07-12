# Beginner Explanation Framework

Use this framework to make a paper understandable without flattening its technical content.

## 1. Start from the reader's concrete question

Answer these four questions in order:

1. What real task is the paper trying to do?
2. Why is that task difficult under the paper's assumptions?
3. What changes in this paper compared with the previous approach?
4. What evidence shows the change helps?

Do not begin with architecture names, literature history, or notation unless they are necessary to answer those questions.

## 2. Build a minimal prerequisite ladder

List only concepts that the later explanation actually uses. For each concept, give:

- a one-sentence plain definition;
- its role in this paper;
- an optional tiny example.

Define acronyms at first use. Distinguish a task, dataset, metric, model, loss, and benchmark; beginners often conflate them.

## 3. Explain the key idea at three resolutions

### One sentence

Use a causal form:

“Because the old approach has limitation A, the paper changes mechanism X into Y, which enables benefit B.”

### Intuition

Give a small example or analogy. Map the analogy explicitly:

- analogy object → real input/component;
- analogy action → real operation;
- analogy outcome → real objective/output.

State where the analogy stops matching the method.

### Precise mechanism

Describe the actual data flow, learned parameters, optimization objective, and assumptions. Do not let the analogy replace this layer.

## 4. Explain a pipeline

For each stage, record:

- input and its shape/type when important;
- operation and purpose;
- learned, fixed, sampled, or retrieved status;
- output passed to the next stage;
- behavior during training versus inference.

End with one full worked path through a tiny example when feasible.

## 5. Explain an equation

Use this order:

1. **Purpose:** what question the equation answers.
2. **Variables:** what every symbol represents and which values are observed, predicted, sampled, or learned.
3. **Operation:** read the expression in plain language.
4. **Training effect:** explain what minimizing/maximizing each term encourages.
5. **Assumptions:** identify independence, approximation, normalization, smoothness, or distribution assumptions.
6. **Connection:** show where the equation appears in the pipeline and experiments.

If a derivation is central, explain each transformation and its justification. If it is not central, explain the start, end, and key step rather than reproducing algebra.

## 6. Explain experiments as claim tests

Do not narrate tables row by row. For each central claim, identify:

- claim being tested;
- dataset/task;
- metric and whether higher or lower is better;
- comparison and whether it is fair;
- result and meaningful difference;
- paper location;
- what the result does not prove.

Explain practical magnitude, not only statistical direction. A small improvement may still matter under lower compute, stronger robustness, or a harder setting; state the trade-off.

Use ablations to connect design choices to claimed effects. Treat qualitative examples as illustrations, not substitutes for representative evaluation.

## 7. Test novelty rather than repeating it

Compare the paper with the closest prior work along:

- problem definition;
- core mechanism;
- training signal/objective;
- data or supervision;
- evaluation setting;
- enabled capability or analysis.

Name what remains inherited. Explain why the changed element is consequential. If the contribution is mainly a dataset, benchmark, empirical finding, or synthesis, describe that honestly instead of forcing an architectural novelty.

## 8. Explain limits constructively

Separate evidence from speculation. For an inferred limitation, give:

- observed clue;
- reasoning chain;
- scenario in which it could matter;
- smallest experiment that could test it.

Avoid generic statements such as “needs more data” or “use a larger model” unless tied to a specific failure mechanism.

## 9. Control cognitive load

Use a layered report: one-minute answer, identity card, prerequisites, deep dive, evidence, critique, and reading route. Keep each paragraph responsible for one idea.

Use tables for repeated comparisons and mappings. Use a diagram only when it clarifies a multi-stage or branching relationship. Avoid decorating a simple explanation with unnecessary structure.

End major sections with “所以这意味着什么” when the practical meaning is not obvious.

## 10. Run a beginner self-check

Before delivery, verify that a new reader can answer:

- What is the input and expected output?
- What exactly was difficult before this paper?
- What is the one non-obvious change?
- Which components are learned?
- What training signal makes them learn?
- Which experiment supports the main claim?
- What remains uncertain or untested?

If any answer depends on unexplained jargon, revise the explanation.
