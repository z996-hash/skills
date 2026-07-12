---
name: read-research-paper
description: "Read and explain academic research papers from PDF files or paper links. Verify bibliographic metadata (title, authors, preprint and formal-publication years, venue and publication status, DOI or arXiv ID), locate and classify official or community GitHub/code repositories, reconstruct the problem-insight-method-evidence logic, explain terminology, equations, experiments, novelty, limitations, related work, trends, and extensions for a beginner, and produce structured reading guides or group reading notes with page, figure, table, and equation evidence. Use for paper reading, paper summaries, literature walkthroughs, reading notes, journal-club preparation, code-repository checks, or beginner-friendly explanations of research PDFs."
---

# Read Research Paper

## Core standard

Base the analysis on the paper itself. Treat blogs, videos, AI summaries, and social posts as background aids only after reading the primary text.

Separate four kinds of statements:

- **PDF fact:** content directly visible in the exact PDF under analysis.
- **Author claim:** a claim made by the paper that still depends on the adequacy of its evidence.
- **External verification:** a bibliographic, venue, repository, or later-work fact supported by an authoritative current source.
- **Analyst interpretation or inference:** the reader's explanation or critique; label it explicitly and state the reasoning.

Assume the reader has no field-specific background unless the user says otherwise. Define a term before relying on it, but do not dilute technical accuracy.

Present the result as a pre-reading guide or post-reading cross-check, not as proof that the user has personally read the paper. Do not invent first-person reading claims on the user's behalf. When preparing a group-submission note, remind the user to verify the cited passages, figures, equations, and judgments against the PDF before submission.

Never turn missing search results into proof of absence. Write “截至 YYYY-MM-DD，未找到可核验的官方代码仓库” instead of “没有代码” unless an authoritative source explicitly establishes that fact.

## Workflow

### 1. Establish the exact document

1. Open the supplied PDF or obtain the exact PDF from the supplied paper link.
2. Confirm the title, author list, visible identifier, page count, and whether the file is a preprint, accepted manuscript, proceedings version, journal version, or supplement.
3. If extraction is weak or the PDF is scanned, use OCR or page images. Visually inspect pages containing figures, tables, formulas, multi-column text, and footnotes; do not trust plain-text extraction for layout-sensitive content.
4. Record both PDF page index and printed paper page when they differ. Cite locations as “PDF p.7 / 论文页 4, §3.2”.
5. State any missing pages, unreadable content, or version ambiguity before drawing conclusions.

### 2. Build an evidence ledger before drafting

Record each important claim with:

- the claim;
- source type: PDF or external;
- exact location: page and section, plus figure/table/equation number when applicable;
- confidence: high, medium, or low;
- whether it is fact, interpretation, or inference.

Use this ledger to prevent details from the abstract, project page, and later versions from being mixed together. Do not expose the full working ledger unless useful; carry its citations into the final answer.

### 3. Verify metadata, venue, and code

Read [references/verification-protocol.md](references/verification-protocol.md) whenever the report includes publication metadata, a code-repository check, or recent related work; these are default parts of a full report.

Browse current authoritative sources unless the user forbids network use. Prefer the publisher or official proceedings, DOI record, OpenReview venue page or decision, arXiv record, author/project page, and repository itself. Use indexes such as Semantic Scholar or Papers with Code for discovery, not as the sole evidence for disputed claims.

Report separately:

- first public/preprint year;
- formal publication year and venue, if verified;
- publication status;
- DOI/arXiv/OpenReview identifiers;
- paper and project links;
- code link, ownership classification, and verification evidence;
- verification date.

Never call arXiv a conference or journal. Never describe a repository as official solely because it has a matching name or many stars.

### 4. Classify the contribution type

Identify the paper's main contribution before imposing an analysis template:

- For an empirical or ML-method paper, emphasize pipeline, objective, training/inference, benchmarks, and ablations.
- For a theoretical paper, emphasize definitions, assumptions, theorem statements, proof strategy, and validity boundary.
- For a systems paper, emphasize architecture, request/data path, bottleneck, throughput, latency, resource cost, and workload realism.
- For a dataset or benchmark paper, emphasize collection, annotation, quality control, task design, metrics, coverage, leakage, and bias.
- For a survey or position paper, emphasize scope, taxonomy, selection criteria, synthesis, omissions, and strength of argument.

Mark irrelevant fields as “不适用（原因）”. Never invent a loss, training stage, theorem, or experiment to fill a template.

### 5. Read the paper in passes

Use the passes as an analysis order, not as permission to skip evidence:

1. **Orientation:** read title, abstract, introduction, conclusion, and the main overview figure. Predict the problem, claimed gap, key idea, and result.
2. **Mechanism:** read the method, algorithms, objectives, important derivations, implementation details, and relevant appendix. Trace input → transformations → output and mark learned versus fixed components.
3. **Validation:** read experiments, datasets, baselines, metrics, main tables, ablations, qualitative results, error analysis, related work, limitations, footnotes, and supplementary material.
4. **Reconciliation:** test whether the method actually answers the motivation and whether each major claim is supported by an appropriate experiment.

For every section, be able to say in one or two sentences what that section advances in the argument.

### 6. Reconstruct the argument

Organize notes with the PMIDE-L chain:

- **P — Problem:** exact task and boundary.
- **M — Motivation:** why prior approaches are insufficient.
- **I — Insight:** the non-obvious idea that enables the method.
- **D — Design:** architecture, algorithm, data flow, and training objective.
- **E — Evidence:** experiments supporting each central claim.
- **L — Limitation:** stated limitations and independently inferred weaknesses.

Express the key idea as a causal sentence, not a method label. Prefer “By changing X into Y, the method gains Z because …” over “The paper uses a Transformer.”

Redraw the pipeline in your own structure. Use a compact arrow flow for simple methods or a Mermaid diagram when several components or branches materially benefit from a visual. Do not paste the paper's figure as a substitute for understanding.

### 7. Explain for a beginner

Read [references/beginner-explanation-framework.md](references/beginner-explanation-framework.md) for the detailed explanation patterns.

Use three layers:

1. **Plain-language intuition:** what goes in, what problem occurs, and what changes.
2. **Precise mechanism:** components, data flow, objective, and assumptions.
3. **Evidence and boundaries:** what the experiments establish, what they do not establish, and when the method may fail.

When using an analogy, map each part of the analogy to the real method and name where the analogy stops being accurate. Define prerequisites in a short glossary before the deep explanation.

For every important equation, explain the optimization goal, all symbols, the role of each term, what changes during training, the intuition, and any approximation or assumption. Do not merely translate notation into words.

### 8. Audit novelty, experiments, and limitations

Test novelty against the closest prior work. Explain both the changed mechanism and the new capability, evidence, problem setting, or analytical perspective it enables. A new dataset, parameter tuning, or combination of known modules is not automatically a technical novelty.

Build a claim–evidence table for the main experiments. Include task/dataset, metric and direction, strongest fair baseline, paper result, absolute or relative difference as appropriate, evidence location, and caveat. Check:

- comparable data, compute, model size, tuning budget, and baseline versions;
- whether the metric actually measures the stated goal;
- ablations for key design choices;
- uncertainty, error bars, repeated runs, and statistical significance when relevant;
- cherry-picked subsets, missing comparisons, and contradictory appendix results.

Keep two limitation lists:

- **Authors' stated limitations**, with PDF evidence;
- **Analyst-inferred limitations**, with explicit reasoning and a feasible test.

### 9. Place the paper in the field

For a full report, separate two sets and verify each item from its primary paper or venue page:

- **Historical lineage:** a small set of closest predecessors and direct follow-ups, regardless of age.
- **Current frontier:** two to five directly relevant works first published or materially revised within the last 12 months. Widen to 24 or 36 months only when the field is sparse, and disclose the window used.

Explain the relationship—predecessor, competing approach, follow-up, correction, or extension—instead of listing titles. If no qualifying current work can be verified, state the queries, venues/indexes, and date range checked rather than silently substituting old papers.

Treat “latest,” repository state, citation counts, and acceptance status as date-sensitive. Attach a verification date and sources. If current browsing is unavailable, omit current claims and list them under “待联网核验”.

Infer a trend only from multiple pieces of evidence. Label it as an inference, state the evidence pattern, and avoid turning two papers into a field-wide conclusion.

### 10. Produce the report

Match the user's language; default to Chinese for a Chinese request. Lead with the answer, then deepen the explanation. Use the following structure for a full beginner report:

1. **一分钟看懂:** three to six sentences covering problem, key idea, how it works, and main evidence.
2. **论文身份卡:** title, authors, affiliations when visible, contribution type, version, preprint year, formal publication, venue/status, identifiers, links, code classification, and verification date.
3. **阅读前置知识:** only the concepts needed for this paper, each in one or two plain sentences.
4. **问题与动机:** problem boundary, why it matters, and why prior work is insufficient.
5. **一句话 Key Idea:** one causal sentence, followed by intuition and a bounded analogy if helpful.
6. **方法拆解:** input, numbered pipeline, learned/fixed parts, output, training versus inference, and important equations.
7. **实验到底证明了什么:** claim–evidence table, main numbers, ablations, fairness, and evidence locations.
8. **真正的创新与前人差异:** closest prior work, changed mechanism, and enabled value.
9. **局限与可信边界:** authors' statements, analyst inferences, and untested cases.
10. **相关工作与趋势:** separate historical lineage from the verified 12–24 month frontier, then give a cautious trend synthesis.
11. **可行的后续方向:** one or two technically grounded ideas, why they matter, and the minimum validating experiment.
12. **一个想问作者的问题:** ask one question aimed at the method's central assumption, evidence, or boundary—not a detail already answered in the PDF.
13. **新手阅读路线:** recommended sections/pages, likely stumbling blocks, and questions to carry while reading.
14. **证据索引与待确认事项:** map important conclusions to PDF locations or external sources, then list unresolved metadata, ambiguous claims, or unavailable evidence.

Do not hide absent information by omitting a heading. Use “论文未报告”, “未能核验”, or “不适用” as appropriate.

If the user requests a saved full Markdown guide, copy and fill [assets/beginner-paper-guide-template.md](assets/beginner-paper-guide-template.md). If the user requests the group's compressed reading note, copy and fill [assets/reading-note-template.md](assets/reading-note-template.md); keep it concise and preserve evidence locations.

## Quality gate

Before delivering, confirm all of the following:

- The analyzed PDF version is identified, and preprint year is not confused with formal publication year.
- Venue/status is supported by an authoritative source or explicitly unresolved.
- Every repository is classified as confirmed official, probable official, anonymous author-provided/unverified, community implementation, unresolved provenance, or not found as of the dated search.
- The report structure matches the contribution type and does not invent inapplicable ML-specific fields.
- The key idea states a mechanism and causal benefit rather than a technology name.
- The pipeline names input, transformations, learned components, objective, and output.
- Every main experimental claim has a number or concrete observation plus a PDF location.
- Novelty is compared with specific prior work, not repeated from the abstract.
- Stated and inferred limitations are separated.
- New terminology is defined before use, and analogies have stated boundaries.
- Current claims have dated external sources; unresolved items are visible.
- A full report includes a genuinely current 12–24 month frontier or an explicit dated account of the unsuccessful search.
- Strong words such as “first”, “best”, “SOTA”, “official”, “proves”, “significant”, and “only” have matching primary evidence and calibrated scope.
- Paraphrase dominates. Quote only short fragments when exact wording is essential, with a location.

If any check fails, return to the PDF or authoritative source before finalizing.
