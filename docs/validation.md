# Validating the sector definition

**Status: protocol agreed, sample not yet drawn.**

> **Update, 30 October 2026.** Both rounds are labelled. Round 1 measured the
> first definition (58.5%); the definition was tightened on its evidence, and
> round 2 measured the result (69.5%). See *Results* and *Results — round 2* below.

The project brief asks us to hand-label about 100 random families, or to find
another defensible way of validating the query. This note sets out what we will
do and why, so that the result can be reported as a measurement rather than an
assertion.

## Why the work so far is not yet validation

We chose CPC codes by reading the official scheme definitions. That is
*construction*: it justifies why each code is in the list. It produces no
evidence about what the resulting set actually contains. Those are different
claims, and only the second is validation.

## Why we do not sample uniformly

A uniform draw of 100 families from the union of 50,239 would return roughly 93
families selected by CPC and 7 selected by keywords alone. The CPC branch is
dominated by `G06N10`, a class literally titled "Quantum computing" — its
precision is close to unity by construction, and confirming that across 93
families teaches us nothing we did not already know. Meanwhile the branch most
likely to be wrong would be represented by seven observations.

We therefore stratify, and sample from the parts of the definition that can
actually fail.

## Protocol

**Strata.** Three groups, sampled independently:

| Stratum | Population | Sample | What it tests |
|---|---:|---:|---|
| A — core CPC (`G06N10` only) | 6,293 | 20 | sanity check; expected near-perfect |
| B — peripheral hardware only (`H10N60/12`, no core code) | 563 | 20 | precision of the enabling-hardware class |
| C — keyword-only (no CPC match at all) | 3,468 | 60 | precision of the free-text branch |

Stratum C is weighted most heavily because it is where the uncertainty now sits.
After `B82Y10/00` was removed from the definition (`docs/methodology.md` §8),
keyword-only families rose from 6.6% to 14.8% of the dataset: roughly one family
in seven now rests on free-text matching with no classification support. The
branch that most needs measuring is also the one that grew.

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

Each family is labelled independently twice, and disagreements are resolved by
discussion. The disagreement rate is reported — it is a measure of how well
defined our own boundary is, and a high rate is itself a finding.

**Reporting.** Precision is computed per stratum, then recombined by population
weight:

$$
p = \frac{N_A p_A + N_B p_B + N_C p_C}{N_A + N_B + N_C}
$$

Report the per-stratum figures as well as the weighted total. A poor $p_C$ is
actionable: it means the keyword branch can be dropped, at a known cost of 6.6%
of the dataset.

## Recall

Precision measures what fraction of what we caught belongs. It says nothing about
what we missed. Recall cannot be measured without a gold-standard set we do not
have, so we approach it from the literature instead: compare our CPC list against
published quantum-patent studies and record, in `docs/methodology.md`, every code
they include that we do not, together with the reason for excluding it.

## Results

*To be completed once the sample has been labelled.*

| Stratum | n | Precision | 95% CI |
|---|---:|---:|---|
| A — core CPC | 20 | 70.0% (14/20) | 48.1–85.5% |
| B — peripheral hardware | 20 | 5.0% (1/20) | 0.9–23.6% |
| C — keyword-only | 60 | 35.0% (21/60) | 24.2–47.6% |
| **Weighted total** | 100 | **58.5%** | 43.7–73.3% |

Sector size at the time of labelling: 23,492 families (CPC 20,024, keywords
11,599, keyword-only 3,468).

Inter-rater disagreement rate: 23% (23 of 100 families; agreement 77%, Cohen's kappa 0.49)

Date of labelling:

Labelled by: Amirtay Almarua, Thekkedath Prince

## Results — round 2

**30 October 2026.** Round 1 led to three changes to the definition, recorded in
`config/sector.yaml`: `H10N60/12` dropped (stratum B was 5% precise), the keyword
stem `quantum comput` dropped (27 of the 39 keyword-only false positives), and
post-quantum phrases (`anti-quantum`, `post-quantum`, `quantum-resistant`, ...)
excluded from the keyword branch. Round 2 measures the definition after those
changes. Only stratum C changed, so only C was redrawn; A keeps its definition and
its round-1 labels; B no longer exists.

**Population** (patents of invention, earliest priority year 2000–2022, new definition):

| Stratum | Families | Sample | Labels |
|---|---:|---:|---|
| A — core CPC (`G06N10`) | 6,293 | — | round 1, reused |
| B — peripheral hardware | 0 | — | removed from the definition |
| C — keyword-only | 1,163 | 60 | round 2 |
| Communication only (scope, not sampled) | 4,855 | — | — |
| **Sector, 2000–2022** | **12,311** | | |

**Precision:**

| Stratum | n | Precision | 95% CI |
|---|---:|---:|---|
| A — core CPC | 20 | 70.0% (14/20) | 48.1–85.5% |
| C — keyword-only | 60 | 66.7% (40/60) | 54.1–77.3% |
| **Weighted total** | 80 | **69.5%** | 52.4–86.5% |

The weighted figure covers the 7,456 families outside the communication-only
block. Against round 1, stratum C rose from 35.0% to 66.7% and the weighted total
from 58.5% to 69.5%. No family was labelled `?` in the final labels.

**Raters.** Round 2 was labelled by one team member (rater 1); the second rating
was produced independently against the same written rule, from the same title and
abstract and with a one-line reason, before rater 1's labels were compared with it.

- Agreement: 54.2% on 59 families (rater 1 left one blank), 27 disagreements,
  Cohen's kappa 0.19.
- The disagreement was systematic. In 15 cases rater 1 labelled `0` a patent on
  qubit hardware, quantum software or error correction, which the written rule
  counts as `1`; in 5 cases rater 1 labelled `1` a quantum-inspired classical
  algorithm, a quantum-cryptography patent, or a component where quantum computing
  is only one listed use, which the rule counts as `0`. The
  two readings of "quantum computing" differed, more than the patents were hard.
- Settlement of the final label: 32 families where both agreed; 20 disagreements
  settled by the written rule; 7 where the second rating was unsure (`?`) and
  rater 1's label was kept; 1 left blank by rater 1, settled by the rule. Each row
  records how in the `settled_by` column.

Because the written rule settled 20 disputes and in each of them sided with the
second rating's reading, the round-2 figure leans on that reading. A team member
as second rater would remove this caveat: fill `rater_2` in the labels file and
re-run section 7 of the notebook.

Files: `outputs/tables/validation_to_label_round2 - Labels.csv` (labels, both
ratings, final, `settled_by`, stratum),
`validation_population_round2.csv`, `validation_results_round2.csv`; computed by
section 7 of `notebooks/STEP0_validation.ipynb` with `ROUND = 2`.