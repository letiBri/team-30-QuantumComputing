# Applicant Harmonization in Quantum Computing

This document outlines the strategy, method evolution, and validation framework implemented to harmonize applicant names (`applicants`) for the competitive landscape analysis (`Step 2`).

---

## 1. The Problem: The "Name Game" in PATSTAT

Within PATSTAT, the exact same corporate or research entity frequently appears under dozens of distinct spelling and formal variants (*SIEMENS AG*, *Siemens Aktiengesellschaft*, *SIEMENS AKTIENGESELLSCHAFT MUENCHEN*, etc.). Treating each variant as an independent entity artificially fractures major market players into smaller fragments, distorting the market share or concentration metrics.

While PATSTAT's standardized name column (`psn_name`) provides a foundational normalization pass, structural challenges remain unaddressed:
* Presence or absence of diverse legal forms (*Inc.*, *GmbH*, *AG*, *KK*, etc.).
* Dotted abbreviations and heterogeneous international naming conventions.
* The need to consolidate language variants, institutional abbreviations, and subsidiaries under their parent organizations.

---

## 2. Harmonization Strategies Evaluated

The cleaning pipeline builds upon progressive methodologies, evaluated both independently and in combination:

| Method | Description | Strengths | Limitations |
|---|---|---|---|
| **A · Dictionary of Legal Forms** | Uppercasing, punctuation removal, and trimming of legal-form keywords from the start/end of strings. | Effective for variants differing solely through standard formal suffixes. | Fails on dotted abbreviations, translations, or complex corporate groups. |
| **B · `cleanco` + Dictionary** | Integration of the `cleanco` Python package (specializing in global business entity extensions) followed by Method A's keyword filter. | Cleanly resolves complex punctuation and dotted abbreviations (e.g., turning *FIAT S.p.A.* into *FIAT*). | Still requires dedicated rules for major public institutions or academic bodies. |
| **C · Terrorizer** | Advanced NLP and network theory techniques (name similarity scoring and community detection). | Highly powerful at clustering variants and radically different naming forms. | Requires rigorous manual oversight of generated clusters and presents installation/dependency constraints. |

---

## 3. The Adopted Solution: Tailored Sector Pipeline

To overcome these limitations, the adopted pipeline relies on a custom tuning layer (`my_harmonisation`) combining:
1. **Preliminary Normalization:** Uppercasing, accent removal, special character stripping, and whitespace regularization.
2. **Institutional Wrapper & Prefix Removal:** Stripping recurring boilerplate wrappers (e.g., *Board of Trustees of...*, *Regents of...*) that conceal the true patent owner.
3. **Abbreviation & Filler Dictionaries:** Standardizing common cross-lingual tokens (e.g., mapping *Univ*, *Université*, *Universität* to *UNIVERSITY*; stripping redundant prepositions and articles).
4. **Manual Aliases for Top Players:** Regular-expression-driven rules ensuring high-precision mapping for core global quantum computing stakeholders. 

**Harmonization in Action (Example):**
Without this pipeline, a single stakeholder might be split across the database. By applying our custom rules, variants such as `INTERNATIONAL BUSINESS MACHINES`, `IBM CORP`, `IBM INC`, and `IBM GLOBAL SERVICES` are all successfully identified, cleaned, and grouped under a single, unified name: **`IBM`**. This ensures the full weight of the company's patent portfolio is accurately represented in our rankings.

---

## 4. Entity Type Classification and Geographic Assignment

Once names are harmonized, the pipeline determines each applicant's key metadata attributes:
* **Applicant Type (`type`):** Derived from PATSTAT's `psn_sector` field or directly inferred from the raw name via keywords and legal forms, categorizing subjects into *firm*, *university*, *government / non-profit*, *hospital*, or *individual*.
* **Primary Country (`ctry`):** Assigns each applicant the stable country code that occurs most frequently across its patent portfolio.

---

## 5. Statistical Validation & Audit Results

To quantitatively measure the harmonization pipeline's performance before deploying it across the entire dataset, we conducted a statistical audit using random sampling and text similarity matching. The evaluation focuses on two core metrics:

1. **Precision (Over-merging Check):** We extract a random sample of 50 merged entity groups to manually verify if the algorithm incorrectly grouped completely different organizations under the same name (False Positives).
2. **Missed Merges (Under-merging Check):** We extract 50 pairs of *unmerged* entities that share a high text similarity score (≥ 0.6) to manually verify if they are actually the same organization that the algorithm failed to link (False Negatives).

### Initial Audit Results

Based on our first comprehensive audit, the automated Entity Linking algorithm performed as follows:

| Metric | Score | 95% Confidence Interval (Wilson) | Interpretation |
| :--- | :--- | :--- | :--- |
| **Precision** | **98.0%** | [89.5% – 99.6%] | **49 out of 50** merged groups truly refer to the same organization. The algorithm is highly reliable at avoiding false groupings. |
| **Missed Merges** | **46.0%** | [33.0% – 59.6%] | **23 out of 50** highly similar applicant pairs were actually the same organization but left unmerged. |

### Iterative Improvement
Entity harmonization is inherently an iterative process. A high Precision (98%) ensures that our market data is not corrupted by merging unrelated companies, which is the most critical factor for a reliable landscape analysis. While the Missed Merges rate highlights that some subsidiaries or spelling variants still escape the automated logic, these results establish a validated baseline. 

The pipeline's performance can be continuously improved by reviewing new missed merge samples and manually adding specific entities to the `ORG_ALIASES` dictionary, incrementally reducing the false negative rate without altering the core algorithm.





