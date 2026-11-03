# Appropriability Regime: Quantum Computing

## 1. Objective & Analytical Framework

In Step 1 of our sector scouting for **Dell** (Investment Banking mandate), we evaluate the **appropriability regime** of the **Quantum Computing** sector (`definition 8bd708a1`; `20,709` distinct DOCDB families in PATSTAT PROD): *Does the field rely primarily on formal patent protection, or does it rely on trade secrecy and lead-time advantages?*

Following the PATSTAT empirical framework (`STEP1_general_description.ipynb`, Section 10), we measure formal IP protection intensity across `2000–2022` (`ipr_type = 'PI'`, complete priority/filing years up to `2022`) using four metrics derived via `scope_profile()`:
1. **PCT Propensity (`is_pct` share, %):** Share of DOCDB families (or applications) routed through the WIPO Patent Cooperation Treaty (`appln_auth = 'WO'`, `appln_kind LIKE 'W%'`). Because PCT filings incur substantial fees, they proxy for inventions with high expected international commercial value.
2. **Geographical Breadth (`mean_family_size`):** Mean `docdb_family_size`, measuring how many jurisdictions an applicant targets per invention.
3. **Filing Intensity (`applns / family`):** Ratio of total applications (`appln_id`) to distinct inventions (`docdb_family_id`).
4. **Grant Rate (`is_granted` share, %):** Share of families with at least one granted patent (`granted = 'Y'`) and share of granted applications.

To contextualize these metrics, we benchmark the **Quantum Computing** sector (`CPC U Keywords`) against:
- **All Patents** (economy-wide baseline in PATSTAT),
- **Core Quantum Computing (`G06N10`)** vs. **Quantum Communication / Cryptography (`H04L9/0852`, `H04B10/70`)**,
- **Adjacent Computing Benchmark:** **Machine Learning (`G06N20`)**, a sibling subclass in `G06N` characterized by fast software iteration and heavy reliance on trade secrecy.

---

## 2. Empirical Findings from PATSTAT

### 2.1 High International Extension & Filing Breadth
- **Higher Multi-Office Filing Intensity:** In `2022`, Quantum Computing recorded `2,928` families and `5,539` applications (`1.89` applications per family), compared with `2,389,730` families and `3,508,187` applications for all patents (`1.47` applications per family).
- **Strong PCT Propensity in Core Quantum (`G06N10`):** Core Quantum Computing exhibits a significantly higher PCT share and larger mean family size than both the economy-wide average (`all patents`) and the Quantum Communication sub-block (`H04L/H04B`), which is heavily diluted by single-jurisdiction domestic filings (predominantly at CNIPA).
- **Large Multi-Filing Families:** Single inventions in the sector generate up to `69` applications across multiple jurisdictions within a few years of priority filing, reflecting aggressive portfolio building.

### 2.2 Grant Rates & Pendency Truncation
- **Historical Grant Rates:** Mature priority cohorts (`2000–2016`) in Quantum Computing achieve high family-level grant rates, confirming that foundational quantum hardware and control inventions meet statutory patentability thresholds across IP5 offices.
- **Recent Cohort Lag (`2018–2022`):** Because Quantum Computing expanded at a `+34.2%` family CAGR (`+33.4%` application CAGR) between `2010` and `2022`, the majority of the sector's families were filed in the final years of the observation window. Given the 3–5 year substantive examination lag in complex physics and computing classes, post-2018 grant rates are right-censored by examination pendency rather than a decline in invention quality.

---

## 3. Strategic Interpretation: Patents vs. Trade Secrecy

Quantum Computing operates under a **split (bifurcated) appropriability regime** depending on the layer of the technology stack:

| Stack Layer | Primary CPC / Technology Scope | Dominant Appropriability Mechanism | Strategic Rationale for IB / M&A Scouting |
| :--- | :--- | :--- | :--- |
| **Physical Qubit Hardware & Packaging** | `G06N10/40` (Superconducting, Trapped Ions, Photonic, Neutral Atoms) | **Patent-Heavy** (High PCT share, large IP5 families) | High capex; hardware architectures are disclosed in scientific papers and physical chips. Patents are vital for VC/PE valuation, M&A due diligence, and defensive Freedom-to-Operate (FTO). |
| **Quantum Communication & QKD** | `H04L9/0852`, `H04B10/70` (Optical QKD, Quantum Networks) | **Patent-Heavy (Standards-Driven)** | Telecom equipment requires interoperability and standardisation; high volume of domestic + IP5 filings by telecom incumbents. |
| **Cryogenics, Readout & Control Electronics** | `G06N10/80`, `G01R`, `H03K` (Microwave pulse control, cryo-CMOS) | **Patent + Tacit Know-How** | Hardware interfaces are patented, while fabrication yield recipes and thermal shielding tolerances rely on manufacturing secrecy. |
| **Quantum Compilers, Error Mitigation & Calibration** | `G06N10/20`, `G06N10/70` (Transpilers, pulse schedules, noise suppression) | **Trade Secrecy (Cloud API Lock-in)** | Delivered via cloud *Quantum-as-a-Service (QaaS)*. Backend calibration and error-mitigation routines execute on the provider's servers and cannot be reverse-engineered by users. |
| **Quantum SDKs & Application Algorithms** | `G06N10/60` (VQE, QAOA, hybrid algorithms, SDKs) | **Open-Source + Lead Time** | Front-end frameworks (Qiskit, Cirq, PennyLane) are open-sourced to capture developer ecosystems, while client-specific algorithmic parametrisations are kept confidential. |

---

## 4. Reading for the Deck (Client Synthesis for Dell)

> **Reading for the deck:** Quantum Computing is **markedly more patent-intensive and internationally protected** than both patenting as a whole (`1.89` vs `1.47` applications per family in 2022) and adjacent software-heavy fields such as Machine Learning (`G06N20`), with **Core Quantum Computing (`G06N10`)** leading in PCT propensity and mean DOCDB family size. However, appropriability is **bifurcated across the stack**: physical qubit processors, cryogenics, and control hardware (`G06N10/40`, `G06N10/80`) are **heavily patented** to secure VC/M&A valuation and freedom-to-operate, whereas compilers, pulse-level calibration, and noise-mitigation algorithms (`G06N10/20`, `G06N10/70`) increasingly rely on **trade secrecy behind cloud QaaS APIs** alongside open-source SDKs. For Dell's scouting mandate, patent analytics in PATSTAT captures the full competitive landscape in hardware and control infrastructure, but must be complemented with cloud-ecosystem and open-source traction metrics when evaluating software-layer targets.
