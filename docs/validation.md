# Validating the sector definition

**Status: labelled and measured.** Weighted precision of the sector definition:
**85.5%** (95% CI 72.3–98.8%). See *Results* below.

The project brief asks us to hand-label about 100 random families, or to find
another defensible way of validating the query. This note sets out what we did
and why, so that the result can be reported as a measurement rather than an
assertion.

## Why the work so far is not yet validation

We chose CPC codes by reading the official scheme definitions. That is
*construction*: it justifies why each code is in the list. It produces no
evidence about what the resulting set actually contains. Those are different
claims, and only the second is validation.

## Why we do not sample uniformly

A uniform draw of 100 families from the sector's 12,311 would return roughly 91
families selected by CPC and 9 selected by keywords alone. The CPC branch is
dominated by `G06N10`, a class literally titled "Quantum computing" — its
precision should be close to unity by construction, and confirming that across 91
families teaches us little. Meanwhile the branch most likely to be wrong would be
represented by nine observations.

We therefore stratify, and sample from the parts of the definition that can
actually fail.

## Protocol

**The definition measured** is the one in `config/sector.yaml`: `H10N60/12` is
not in it, and the keyword branch excludes the stem `quantum comput` and
post-quantum phrases (`anti-quantum`, `post-quantum`, `quantum-resistant`, ...).
The population is patents of invention with earliest priority year 2000–2022.

**Strata.** Two groups, sampled independently:

| Stratum | Families | Sample | What it tests |
|---|---:|---:|---|
| A — core CPC (`G06N10`) | 6,293 | 20 | sanity check; expected near-perfect |
| C — keyword-only (no CPC match at all) | 1,163 | 60 | precision of the free-text branch |
| Communication only (scope, not sampled) | 4,855 | — | — |
| **Sector, 2000–2022** | **12,311** | 80 | |

Stratum C is weighted most heavily because it is where the uncertainty sits:
its families rest on free-text matching with no classification support.

Families reachable only through the quantum-communication codes
(`H04B10/70`, `H04L9/0852`) are a **scope** question rather than a precision
question — they are correctly classified, the issue is whether they belong in
this sector — and are handled in `docs/methodology.md`, not here.

**Labelling.** For each sampled family, read the title and the English abstract
of the earliest member and record one of:

- `1` — quantum computing: the invention concerns qubits, quantum processors,
  quantum algorithms, error correction, control electronics or software whose
  purpose is quantum computation;
- `0` — not quantum computing;
- `?` — cannot tell from title and abstract alone.

Each family is labelled independently twice, and disagreements are settled by the
written rule above. The disagreement rate is reported — it is a measure of how
well defined our own boundary is, and a high rate is itself a finding.

**Reporting.** Precision is computed per stratum, with a 95% Wilson interval, then
recombined by population weight:

$$
p = \frac{N_A p_A + N_C p_C}{N_A + N_C}
$$

Report the per-stratum figures as well as the weighted total. A poor $p_C$ is
actionable: it means the keyword branch can be dropped, at a known cost of 9.4%
of the sector.

## Recall

Precision measures what fraction of what we caught belongs. It says nothing about
what we missed. Recall cannot be measured without a gold-standard set we do not
have, so we approach it from the literature instead: compare our CPC list against
published quantum-patent studies and record, in `docs/methodology.md`, every code
they include that we do not, together with the reason for excluding it.

## Results

| Stratum | Families | n | Precision | 95% CI |
|---|---:|---:|---:|---|
| A — core CPC | 6,293 | 20 | 85.0% (17/20) | 64.0–94.8% |
| C — keyword-only | 1,163 | 60 | 88.3% (53/60) | 77.8–94.2% |
| **Weighted total** | 7,456 | 80 | **85.5%** | 72.3–98.8% |

The weighted figure covers the 7,456 families outside the communication-only
block. No family was labelled `?` in the final labels.

**Raters.** Both strata were labelled independently by two raters, from the same
title and abstract and against the same written rule.

| Stratum | n | Agreement | Disagreements | Cohen's kappa |
|---|---:|---:|---:|---:|
| A — core CPC | 20 | 65.0% | 7 | 0.34 |
| C — keyword-only | 60 | 56.7% | 26 | 0.16 |
| **All** | 80 | 58.8% | 33 | 0.21 |

(`?` counts as a label of its own, as in the notebook.)

- The disagreement was one-sided. In 30 of the 31 `0`/`1` disagreements rater 1
  said `0` and rater 2 said `1`; in stratum C rater 1 labelled `1` only 30 of the
  60 families, rater 2 labelled 52. Most of these are qubit hardware, quantum
  circuits and error mitigation, which the written rule counts as `1`.
- Settlement of the final label: all 31 `0`/`1` disagreements were settled as
  `1`, following rater 2 30 times and rater 1 once (stratum C, row 40); the 2
  families rater 2 marked `?` (stratum C, rows 17 and 51) kept rater 1's `0`; and
  one family both raters labelled `0` was settled as `1` (stratum A, row 20).


Files: `outputs/tables/validation_labels.csv` (stratum A labels),
`outputs/tables/validation_to_label_round2 - Labels.csv` (stratum C labels; both
ratings, final, stratum), `validation_population_round2.csv`,
`validation_results_round2.csv`; computed by section 7 of
`notebooks/STEP0_validation.ipynb` with `ROUND = 2`.
