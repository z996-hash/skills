# Verification Protocol

Use this protocol for bibliographic metadata, publication status, code repositories, and recent-paper claims.

## 1. Match the identity and version

Before merging sources, match at least title plus author overlap, and preferably one stable identifier such as DOI, arXiv ID, OpenReview forum ID, ACL Anthology ID, or publisher record.

Check whether titles changed between preprint and publication. If authors, method details, or results differ, treat the files as separate versions and state which one was analyzed.

Use the PDF to establish its visible content and version clues. Do not use a PDF footer or citation suggestion as sole proof of final acceptance when an authoritative venue record is available.

## 2. Use a source hierarchy

Choose sources by fact type. For paper content, use the exact PDF first, then its matching supplement; use other versions only to describe version differences. Never let a project page or later paper silently overwrite the supplied PDF.

For bibliographic, venue, and repository facts, prefer sources in this order:

1. Official publisher, journal, conference proceedings, society anthology, or venue program.
2. DOI registration record and official review/decision platform such as the paper's OpenReview venue page.
3. arXiv record for submission history and preprint versions.
4. Author or institutional project page.
5. The repository itself and links from verified author/organization profiles.
6. Scholarly indexes such as Semantic Scholar, DBLP, or Papers with Code.
7. Search snippets, blogs, news posts, videos, and social media.

Use levels 6–7 to discover candidates. Confirm consequential or conflicting claims with levels 1–5.

## 3. Report dates without collapsing them

Record separate fields:

- **First public version:** earliest verified public preprint or technical report date.
- **Formal publication:** year attached to the verified proceedings issue, journal volume, or official publication record.
- **Current PDF version:** version number or revision date of the file actually read.

When only a preprint is verified, write “预印本，未核验到正式发表记录”. Do not put the arXiv year in a “conference year” field.

When official sources disagree, show both values and explain their meaning, such as online-first year versus issue year. Do not silently choose one.

## 4. Classify venue and status

Use one of these statuses:

- **Published:** present in official proceedings or a journal issue/article record.
- **Accepted:** an official acceptance/decision exists, but the final publication record is not yet available.
- **Workshop paper:** verified as a workshop contribution; do not shorten it to the parent conference.
- **Preprint only:** an arXiv or repository manuscript is verified, with no formal venue found.
- **Under review / anonymous submission:** explicitly shown by the source; do not infer acceptance.
- **Submitted:** the source says only that it was submitted; do not upgrade this to under review, accepted, or published.
- **Withdrawn / rejected:** report only from an authoritative decision or withdrawal record.
- **Unresolved:** evidence is missing or conflicting.

Do not infer publication from phrases such as “submitted to”, a conference-style PDF template, an anonymous OpenReview page, or an author's aspirational citation.

## 5. Classify code repositories

Use exactly one classification per repository:

### Confirmed official

Require at least one direct provenance link:

- the PDF links to the repository;
- the verified project/author/venue page links to it;
- the repository belongs to a verified author or institution and its README explicitly identifies the paper, with corroborating identity evidence.

### Probable official

Use only when strong identity signals exist but no direct provenance link can be found. State the signals and the missing proof. Never shorten this label to “official”.

### Anonymous author-provided, identity unverified

Use when the PDF or anonymous submission links a repository but blind-review identity prevents author verification. Report that the PDF provides the link without claiming verified ownership.

### Community implementation

Use when a third party implements or reproduces the method without verified author provenance. This can be useful, but keep it separate from the authors' release.

### Unresolved provenance

Use when the repository matches the paper but ownership evidence is too weak or conflicting for any stronger label.

### Not found as of date

Use only after checking the PDF, project/author pages, repository search, and a scholarly code index. State the search date and major places checked. This means “not found”, not “does not exist”.

For each repository, record URL, owner, classification, provenance evidence, current accessibility, and verification date. Optionally report license, release completeness, pretrained weights, and archived/read-only state when relevant. Treat stars, forks, recent commits, and issue status as volatile and date them.

Red flags that are not proof of official status:

- matching repository or method name;
- high star count;
- a README that cites the paper;
- appearing first in a search result;
- being listed by an aggregator without a provenance link.

## 6. Verify recent related work

Search forward citations, shared task/benchmark terms, and closest-method keywords. Prefer primary paper pages and official venue records. For each selected work, verify title, year/status, and one specific relationship to the target paper.

Choose a small, relevant set rather than a long bibliography. Keep historical lineage separate from a current-frontier set published or materially revised in the last 12 months; widen to 24 or 36 months only when necessary and state the window. Separate:

- direct follow-ups;
- competing solutions to the same problem;
- work that corrects, audits, or challenges the claim;
- broader surveys or benchmarks.

Use publication or latest-version dates that are actually supported. Label a work as “recent” relative to the verification date.

If the search yields no qualifying current work, report the date window, search terms, citation paths, and venues/indexes checked. Do not fill a “latest work” section with older landmark papers without labeling them as historical.

Audit strong language before delivery. Any claim using “first”, “best”, “state of the art”, “official”, “proves”, “statistically significant”, “only”, or an equivalent must have evidence whose scope matches the wording; otherwise weaken the statement.

## 7. Handle conflicts and uncertainty

When sources conflict:

1. Confirm that they refer to the same paper/version.
2. Prefer the higher-authority source for the field it controls.
3. Preserve meaningful distinctions instead of forcing one value.
4. State the conflict and the chosen interpretation.

Use confidence labels:

- **High:** direct primary evidence with an exact identifier or provenance link.
- **Medium:** multiple consistent sources but missing direct evidence for one element.
- **Low:** indirect, incomplete, or conflicting evidence.

For unresolved claims, say what would resolve them.

## 8. Cite evidence precisely

For paper content, cite the PDF location: page, section, and figure/table/equation when available. Example: “PDF p.9 / 论文页 6, Table 2”.

For external facts, link the exact authoritative page and include the access/verification date in the metadata section. Avoid linking search-result pages.

Keep quotations short. Prefer paraphrase with precise locations.
