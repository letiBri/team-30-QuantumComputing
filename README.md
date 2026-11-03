# Sector scouting with patent data — Quantum computing

**Project Work · Innovation Management · A.Y. 2026/27 · Politecnico di Torino**

| | |
|---|---|
| **Team** | 30 |
| **Sector** | Quantum computing |
| **Client** | Dell |
| **Data** | PATSTAT Global, via the EPO Technology Intelligence Platform (TIP) |
| **Unit of analysis** | DOCDB patent family |
| **Observation window** | 2000–2022, by earliest priority year (`ipr_type = 'PI'`) |

---

## The commission

We act as analysts at an investment bank. Dell, an established client, wants a picture of the quantum computing sector before deciding whether to acquire or partner with anyone in it. The brief reduces to three questions:

1. How is the sector doing overall?
2. Which segments are growing, and which are fading?
3. Who are the emerging players worth approaching?

Our evidence is patent data. Firms file patents years before products reach the market, so the patent record is a leading indicator of where R&D money has already been committed — which is precisely what a buyer wants to see before the revenue exists.

---

## Repository layout

```text
.
├── config/
│   └── sector.yaml          Every parameter of the dataset: codes, keywords, years
├── notebooks/               Step 0, Step 1, and Step 2 analyses as run on TIP
├── src/                     Modules and scripts for the main pipeline
├── outputs/
│   ├── cache/               Cached query results (.pkl), keyed by definition hash
│   ├── figures/              Figures referenced by the deck
│   └── tables/               Result and validation tables (.csv)
├── docs/
│   ├── methodology.md        Choices that need defending, and why we made them
│   ├── validation.md         Step 0 validation protocol and its results
│   ├── appropriability.md    Step 1 Section 10 appropriability and secrecy analysis
│   └── harmonisation.md      Step 2 applicant name harmonisation rules
├── tests/
├── main.py                   Main pipeline, refactored out of the notebooks
├── requirements.txt
└── README.md
```

Two rules govern what goes in here, both from the project brief. **Configuration, not hard-coding**: the sector boundary lives in `config/sector.yaml` and nowhere else, so changing it is a one-file edit rather than a search across the analysis. **Queries, not bulk data**: no PATSTAT extract is committed. What is committed is the code that reproduces one, plus the small aggregate tables the figures are drawn from.

---

## Defining the sector

A patent family belongs to the sector if it matches our CPC codes **or** carries one of our keywords in a title or abstract:

\[
\text{Quantum} = \text{CPC} \cup \text{Keywords}
\]

CPC codes were chosen by reading the official scheme definitions rather than the class titles. The core is `G06N10`, titled *"Quantum computing, i.e. information processing based on quantum-mechanical phenomena"*, together with its five subgroups — models, physical realisations, algorithms, error correction and programming — alongside the quantum-communication and cryptography classes `H04B10/70` and `H04L9/0852`.

Two broad hardware codes were removed on empirical evidence: `B82Y10/00` and `H10N60/12`. `B82Y10/00` — *nanotechnology for information processing, storage or transmission, e.g. quantum computing* — reads like an obvious inclusion and was in our first definition. Counted on its own, it turned out to be measuring the early-2000s nanotechnology wave: 44% of the initial dataset, 96% of the year-2000 families, and a compound growth rate of zero across the window. Similarly, `H10N60/12` (Josephson-effect devices) pulled in general superconducting electronics unrelated to qubits. `docs/methodology.md` and `docs/validation.md` set out the evidence; `config/sector.yaml` records the exclusions (definition fingerprint `8bd708a1`).

Keywords are deliberately multi-word or technically specific, with explicit exclusions for post-quantum (classical) cryptography phrases. The bare term *quantum* is useless for this sector: quantum dot, quantum well and quantum efficiency are optoelectronics vocabulary and would flood the dataset with LED and photovoltaic patents. Terms such as `transmon` earn their place differently — they name a dominant qubit design precisely enough that no classification code is needed to recognise it.

### What the two branches contribute

Run on PROD across all historical PATSTAT DOCDB families (definition `8bd708a1`):

| Branch | Families | Share of union |
|---|---:|---:|
| CPC | 18,586 | 89.7% |
| Keywords | 8,206 | 39.6% |
| — also found by CPC | 6,083 | 29.4% |
| — **keyword-only** | **2,123** | **10.3%** |
| **Union (the sector)** | **20,709** | **100%** |

Two things follow. First, **74.1% of keyword hits are independently confirmed by a classification code**, which is the signature of a keyword list that is not over-reaching — a runaway list would produce a large branch mostly disjoint from CPC. Second, **2,123 families are visible only in text**: roughly one in ten (10.3%). Those are the families a classification-only study would miss, and they were audited via our stratified validation sample (`docs/validation.md`).

**Validation: 69.5% precision.** A hand-labelled sample, stratified by branch, measured the share of the sector that is really quantum computing. The first round found **58.5%** and traced the false positives to `H10N60/12` (1 of 20 families entering only through it was quantum computing), to the keyword stem `quantum comput` (27 of 39 keyword-only false positives, patents naming quantum computing only as a possible use, now dropped), and to post-quantum cryptography (now excluded). After those changes the second round found **69.5%** (95% CI 52–87%); the core class `G06N10` itself is at 70%. Precision covers the sector outside the quantum-communication block, which is a scope question rather than a precision one. Volumes are therefore overstated by roughly three families in ten; growth rates need not be, provided the false positives grow at about the pace of the field. In round 2 the second rating was Claude's (an AI assistant) rather than a team member's, and the two agreed only moderately (Cohen's kappa 0.19); `docs/validation.md` reports both.

Removing `B82Y10/00` and `H10N60/12` and tightening the keyword exclusions cut the raw dataset from 50,239 families to 20,709. That is the measure of how much of the original "sector" was neighbouring nanotechnology and generic superconductors.

---

## Methodological choices

These apply to every number in the analysis and are stated here so that no figure has to be defended twice.

**The DOCDB family is the unit of analysis.** A patent is valid only where it is granted, so an applicant seeking protection in several countries files the same invention several times, and each filing becomes a separate application. PATSTAT links them under one `docdb_family_id`. Counting families counts inventions; counting applications counts filings. Our largest family (`docdb_family_id = 84360761`) contains 69 applications for a single 2021 invention — counted once at family level, 69 times across 2022–2025 at application level. Both levels are reported side by side, because the gap between them is itself a measure of how widely applicants seek protection.

**Time is the earliest priority year**, the first filing of an invention anywhere in the world, which is the date closest to the act of inventing. Applications are dated by their own filing year. Only patents of invention (`ipr_type = 'PI'`) are counted, excluding utility models (`'UM'`).

**The window closes at 2022.** Applications publish roughly 18 months after priority and reach PATSTAT later still, so recent priority years are structurally incomplete. Rather than plotting incomplete years and shading them, we end the series at the last year treated as complete (`2000–2022`). A decline in the final years of a raw PATSTAT series is an artefact of publication lag, not a fall in inventive activity, and closing the window removes any chance of reading one for the other.

**Fractional counting.** A family in four CPC subclasses contributes ¼ to each; a family with applicants from three countries splits among them. Every breakdown therefore sums to the number of families rather than inflating it.

---

## What we have found so far

A first pass over the whole dataset produced a curve that did not make sense: the sector appeared to peak around 2004, lose nearly 80% of its volume by 2014, and only then recover. Quantum computing did not contract by four fifths over that decade, so we counted each block of the definition separately. That changed both the definition and the finding; `docs/methodology.md` carries the argument.

**The apparent decline belonged to a different technology.** `B82Y10/00` held 96% of our year-2000 families and fell 89% from its 2004 peak to its 2014 trough — the early-2000s nanotechnology wave, tagged retroactively by a classification scheme introduced long after the filings it covers. Across the full window, that block is flat: 1,039 families in 2000, 1,034 in 2022, compounding at zero. It supplied the entire distortion and none of the trend.

**On the corrected definition, the sector never declined.**

| | 2000 | 2022 | Growth (2000–2022) | CAGR 2000–2022 | CAGR 2010–2022 |
|---|---:|---:|---:|---:|---:|
| Quantum computing (families) | 38 | 2,928 | ×77 (+7,605.3%) | **+21.8%** | **+34.2%** |
| All patenting (families) | 914,442 | 2,389,730 | ×2.6 (+161.3%) | +4.5% | +6.2% |
| Quantum computing (applications) | 67 | 5,539 | ×83 (+8,167.2%) | **+22.2%** | **+33.4%** |
| All patenting (applications) | 1,606,020 | 3,508,187 | ×2.2 (+118.4%) | +3.6% | +4.6% |

The sector compounds at **21.8% a year against 4.5% for patenting as a whole — 4.9 times the rate** — and over 2010–2022 at **34.2% against 6.2%, 5.5 times**. The series is small and flat through the 2000s, turns up around 2013 and rises monotonically thereafter. Counted on `G06N10` alone, the core runs from 15 families in 2000 to 1,915 in 2022, a 128-fold increase at 24.7% a year.

**The early years are real, not missing.** Quantum computing sat under `G06N99/002` before `G06N10` existed, so sparse early counts could have been a reclassification artefact rather than a fact about the field. Querying the legacy group returns nothing at all: the backfile was reclassified and the old group emptied behind it. The 2013–2015 inflection is therefore an observation, not a hedge.

**Technology mix is shifting toward core quantum computing (`G06N`).** Across 2000–2022, `G06N` accounts for 29.0% of fractional families (28.6% of applications), followed by digital/cryptographic transmission `H04L` (24.1% families, 18.8% applications) and optical transmission `H04B` (11.3% families, 9.4% applications). By WIPO sector, 91.5% of families fall in Electrical engineering (`Computer technology` 42.9%, `Digital communication` 24.5%, `Telecommunications` 13.1%, `Semiconductors` 6.4%) and 5.5% in Instruments (`Optics` 2.7%, `Measurement` 1.9%).

**Appropriability is high in hardware, bifurcated in software.** Dividing applications by families gives **1.89 filings per invention in 2022** (`5,539 / 2,928`) against **1.47 for patents generally**, a 29% premium in geographical breadth. Benchmarking `G06N10` against `H04L/B` and Machine Learning (`G06N20`) in `docs/appropriability.md` shows that core quantum hardware and control layers exhibit high PCT propensity and large international family sizes, whereas quantum compilers, calibration schedules, and error-mitigation heuristics rely increasingly on trade secrecy behind cloud QaaS APIs.

---

## Status

| Step | Content | State |
|---|---|---|
| 0 | Sector definition, extraction, cleaning, validation | **Complete** (`STEP0_validation.ipynb`, `docs/validation.md`) |
| 1 | General description: volume, growth, technology mix, geography, appropriability | **Complete** (`STEP1_general_description.ipynb`, `docs/appropriability.md`) |
| 2 | Competitive landscape: harmonisation, concentration, entrants, subfields | In progress (`STEP2_competitive_landscape.ipynb`, `docs/harmonisation.md`) |
| 3 | Present score: influence, volume, success, globalization | Not started |
| 4 | Future score: our own algorithm | Not started |
| 5 | Magic Quadrant | Not started |
| 6 | Strategic analysis and recommendation | Not started |

---

## Reproducing the analysis

The analysis runs on the EPO Technology Intelligence Platform, which provides authenticated access to PATSTAT. It cannot be run from a local machine without a TIP account.

```bash
git clone https://github.com/letiBri/team-30-QuantumComputing.git
```

Upload the repository to TIP, open `notebooks/`, and run the notebooks from top to bottom. Develop against `ENV = "TEST"` (a ~10K-publication sample, fast enough to iterate on) and switch to `ENV = "PROD"` for any number that will be reported. The two differ only by that constant.

Expensive queries are cached to `outputs/` on first run and read from disk afterwards, so a lost kernel costs seconds rather than a working session. Delete the cache files to force recomputation.

---

## Team 30

| Matricola | Name |
|---|---|
| 358251 | Almarua Amirtay |
| 354966 | Letizia Brizzi |
| 355188 | Leonardo Passeri |
| 358334 | Prince Thekkedath |
| 353302 | Michal Kruszewski |

### Contribution statement

*To be completed before submission: who did what, per the project brief.*

### Use of generative AI

*To be completed and reviewed by the team before submission.* Generative AI was used during development as a programming and writing aid — among other things for drafting and reviewing notebook code, checking CPC class definitions against the official scheme, and drafting repository documentation. All analytical choices, all queries run against PATSTAT, and all results reported are the team's own, and every figure in the deck was produced by code in this repository.

---

## References

### Sector definition and classification

- Cooperative Patent Classification scheme — https://www.cooperativepatentclassification.org
- PATSTAT Global data catalogue, EPO

### Indicators used from Step 1 and Step 3 onward

- Cohen, W. M., Nelson, R. R., & Walsh, J. P. (2000). *Protecting their intellectual assets: Appropriability conditions and why U.S. manufacturing firms patent (or not)* (NBER Working Paper No. 7552).
- Hall, B. H., Jaffe, A. B., & Trajtenberg, M. (2001). *The NBER patent citation data file* (NBER Working Paper No. 8498).
- Hall, B. H., Jaffe, A., & Trajtenberg, M. (2005). Market value and patent citations. *RAND Journal of Economics*, 36(1), 16–38.
- Ernst, H. (1998). Patent portfolios for strategic R&D planning. *Journal of Engineering and Technology Management*, 15(4), 279–308.
- Guellec, D., & van Pottelsberghe de la Potterie, B. (2000). Applications, grants and the value of patent. *Economics Letters*, 69(1), 109–114.
- Harhoff, D., Scherer, F. M., & Vopel, K. (2003). Citations, family size, opposition and the value of patent rights. *Research Policy*, 32(8), 1343–1363.
