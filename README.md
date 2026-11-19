# DGA Causal-Claims Audit

I'm building a research pipeline that checks whether the certainty the *2025–2030 Dietary Guidelines for Americans* (DGA) asserts for its causal claims matches the evidence it cites. It combines LLM-applied appraisal frameworks with Python code that checks the LLM's work instead of trusting it.

## Why

Dietary guidance often states its recommendations with high confidence. I'm not trying to decide whether a recommendation is right. I'm asking a narrower question: **is the confidence behind each claim earned by the evidence on record?** When it isn't, I try to show exactly where the gap is, and to point to existing evidence the guidance left out.

My governing framework is the **Russo–Williamson Thesis** (the EBM+ view). It holds that a causal claim needs two kinds of support:

- a **difference-making** leg: trials and cohort studies showing that the outcome varies with the cause;
- a **mechanistic** leg: an evidenced pathway.

I check the two legs separately. On top of that I apply standard appraisal tools: GRADE, the Bradford Hill criteria, the E-value and quantitative bias analysis, plus risk-of-bias and reporting instruments where the study design calls for them.

## How it works

The pipeline has six stages. Status is marked honestly: **working** means code in this repo you can run today.

```
DGA report + appendices
        │
1. Claim selection ............ by hand, on purpose (I don't let a model decide what a claim is)
2. Reference acquisition ...... done by hand with LLM help so far; no script in this repo yet
3. Evidence records ........... WORKING: schema + validator (src/stage3_evidence_hierarchy.py)
4. Framework appraisal ........ LLM applies the frameworks; WORKING verification layer (src/stage4/)
5. Statistical evaluation ..... open design question, not started
6. Gap identification ......... done by hand so far
```

- **Stage 3** turns each piece of evidence behind a claim into a structured `EvidenceRecord`, defined in `src/schema/evidence-record.md`. Each record carries the source document and page, whether the number was reported by the source or derived from it, and a provenance tier. The validator checks 11 of the schema's 13 rules; the other two need Stage 4 appraisal records or the source PDFs, so they can't be checked from the records alone. For the whole-grains claim (WG-01) there are 28 records, and they validate with 0 errors.
- **Stage 4** is where an LLM applies each framework to published, worked examples. Before I trust it on the guidelines, it has to reproduce those examples correctly (see "Verification" below). The E-value is the first framework I'm calibrating; GRADE, Bradford Hill and QBA follow once it is finished.

## Verification: how the code checks the LLM

Early on, I ran the model on its own (prompt versions v1–v4). It reasoned about the framework well, but it was unreliable at bookkeeping: it skipped some values, made small changes to quotations, and reported checks it hadn't actually done. So I split the work. **The model does the judgment; code does the mechanics.**

1. **The model fills a structured table, and an embedded calculator computes every number.** For each estimate, the model enters a JSON row: the measure, the estimate, the CI and the targets. It then runs `evalue_calc.py`, which is embedded in the prompt word for word. The model is told never to compute E-values by hand. From prompt v11, the calculator also prints the full interpretation sentence for every result, and the model copies it unchanged.
2. **`validate_evalue.py` re-runs every row and compares it with an answer key** that I built from the source papers. The key stays out of the repo and is never shown to the model. The validator flags any rows that are missing, inputs that are wrong, a wrong conversion path (for example treating an odds ratio as rare when the outcome is common), duplicate entries, and E-value-like numbers in the prose that the calculator never produced. A D4 screen also flags any example with no complete interpretation sentence. It's a heuristic, so I read its flags rather than treating them as scores.
3. **`verify_quotes.py` checks every quotation against the source PDF.** Each quotation must appear word for word, and it must be on the page the model cited for it. If two quotations share one citation in the same sentence, both are checked against that page. For example, when I ran it on a sentence from one calibration output, it printed:
   ```
   PAGE cited [7] (shared citation), found [8]: is more closely analogous to Rosenbaum's design sensitivity
   ```
4. **I read every output in full** and score it against a written rubric. From v5 on, each prompt version is run 3 times on each of 3 source papers, in fresh isolated chats, and I report how reliable it is across runs, not just its best run.

Every prompt version and the reason for each change are in `src/prompts/` (version log in `src/prompts/README.md`, unified diffs in `src/prompts/diffs/`). The calibration results so far are recorded there too, including the version that made things worse (v10).

## Quick start

You need Python 3.10 or newer. `verify_quotes.py` also needs `pdftotext` (poppler) and a source PDF. The PDFs are copyrighted, so they aren't in the repo.

```bash
git clone https://github.com/nicdenoto/United-States-Food-Pyramid.git
cd United-States-Food-Pyramid
python3 -m venv .venv && source .venv/bin/activate
pip install -r src/requirements.txt

# 1. Validate the 28 whole-grain evidence records (exit code 0 = clean)
python src/stage3_evidence_hierarchy.py

# 2. Run the calculator's test suite (published answer-key values, edge cases)
cd src/stage4
python test_evalue_calc.py

# 3. Run the calculator on two examples from VanderWeele & Ding (2017)
python run_example.py example_table.json
```

The code doesn't need any API keys: no stage calls an LLM API. I run the calibration chats myself in a locked-down claude.ai project (details below).

## Example output

These are real outputs from the commands above.

Stage 3 validator (first lines):
```
28 records, 2 claim(s), 0 error(s), 0 note(s)

WG-01a (26 record(s)):
  WG01-EV-001 [SOURCE_REPORTED, T1] DIFFERENCE_MAKING -- CITED_DIRECTLY: all-cause mortality, high vs low whole-grain intake
  WG01-EV-003 [SOURCE_REPORTED, T1] DIFFERENCE_MAKING -- CITED_DIRECTLY: cardiovascular disease, high vs low whole-grain intake
```

Calculator on the Huybrechts example, where the confidence interval already contains the null (the long note column is cut short here):
```
line | RR | CI on RR scale | target | E point | E CI | limit | note
Huybrechts -> 1 (null) | 1.060 | (0.930, 1.220) | 1 | 1.312 | 1.000 | target inside CI | CI E-value is 1: ...

[Huybrechts -> 1 (null), estimate] With an observed risk ratio of 1.06, an unmeasured confounder that was associated with both antidepressant use in pregnancy and infant cardiac defects by a risk ratio of 1.31-fold each, above and beyond the measured confounders, could explain away the estimate, but weaker confounding could not.
```

## Project status and limitations

**Done**
- The claim inventory (`corpus/claim-inventory.md`). The whole-grains claim is verified against primary sources. The first-pass entries for five more food groups are drawn from the appendix text only and are not yet verified.
- The Stage 3 schema and validator, with 28 validated whole-grain evidence records.
- The E-value verification layer, with 33 passing tests.
- Eleven prompt versions. Ten have been run on the calibration set; v6 was replaced before it was used.

**In progress**
- E-value calibration. No prompt version has passed all three gates yet. The current round tests v11 side by side with v9 as a control, in the same sitting, so that a change in the model can be told apart from a change in the prompt.
- Paper drafts (`paper/`): the introduction and methodology.

**Not started or still open**
- GRADE, Bradford Hill and QBA calibration.
- Stage 5, whose statistical design is still undecided.
- A reference-acquisition script. Stages 1, 2, 5 and 6 are stubs in `src/`.
- After whole grains, the next claims to run through the pipeline will be vegetables, then saturated fat.

**Known limitations**
- The LLM step is run by hand in a chat interface, not through an API. That keeps the model's context tightly controlled (prompt plus one attached paper, with no web search, memory or past chats), but it means the runs aren't scripted.
- The model is Claude Sonnet 5 at medium reasoning effort, the only setup available to me without cost.
- Some of the scoring is my own judgment against a written rubric. To keep it honest I count borderline items as failures, and I log every call in the scoring worksheets.
- With 3 runs per paper, small differences between prompt versions aren't statistically meaningful.

## Repository layout

```
src/
  stage3_evidence_hierarchy.py   Stage 3 validator (working)
  schema/evidence-record.md      EvidenceRecord specification
  stage4/                        E-value calculator, validator, quote verifier, tests (working)
  prompts/                       every calibration prompt version, version log, diffs
  stage1_…, stage2_…, stage4_…, stage5_…, stage6_…   stubs for stages not implemented here
corpus/
  dga/                           the DGA front-end report and appendices (U.S. federal work, public domain)
  claim-inventory.md             the claims under audit
  stage3_evidence_records/       validated EvidenceRecords (WG-01)
  reference-library/, primary_studies/   citation manifests only (the PDFs are copyrighted, not tracked)
paper/                           drafts of the paper's introduction and methodology
archive/notes/                   my raw early working notes, kept for provenance
```

## Provenance tags

Every factual claim in the corpus and the drafts is tagged by how I know it:

- **[T1]** I verified it against the primary document.
- **[T2]** It comes from a secondary source or search, and is not yet verified.
- **[STRUCTURE]** I inferred it from the structure of the document.

## How I use AI tools

Claude and GPT helped me with extraction, review passes and drafting. The logs in `corpus/stage3_evidence_records/WG-01.md` record which passes the LLM reviewer did, and they are signed "Reviewer: Claude". I made the decisions, checked the sources and approved every change, and the code above exists so that the AI output gets checked rather than taken on trust.

## Tech stack

Python 3.10+: the standard library, plus PyYAML for Stage 3. `pdftotext` (poppler-utils) for quote verification. Claude Sonnet 5 via claude.ai for the calibration runs. Tests run in GitHub Actions (`.github/workflows/tests.yml`).

## License

The code is under the MIT License (`LICENSE`). The writing, prompts, claim inventory and evidence records are under CC BY 4.0 (`LICENSE-docs.md`). The DGA documents in `corpus/dga/` are U.S. government works in the public domain.

## Author

**Nic DeNoto**, High School Researcher, SUNY Polytechnic Institute. [github.com/nicdenoto](https://github.com/nicdenoto)
