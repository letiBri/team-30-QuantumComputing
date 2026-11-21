# Present score: who holds the most valuable quantum patents today

Step 3 of the project work, run on PROD in two notebooks: `notebooks/STEP3_present_score_incumbent.ipynb`
(Part 1, sections 1-8 below) and `notebooks/STEP3_present_score_entrant.ipynb` (Part 2, sections 9-14).
This file collects the choices we have to defend and the results that go into the
deck; the notebook has the code, the charts and the full tables. Outputs are in
`notebooks/outputs/step3/`.

## 1. The question

Dell asks which firms of the quantum computing sector hold the most valuable
patents **today**. "Today" means what has already happened to the patents:
citations received, decisions of the examiners, countries where they are
protected. We answer with one number per firm, the **present score**, which is one
of the two axes of the Magic Quadrant (Step 5).

## 2. Set-up

| Choice | Value | Why |
|---|---|---|
| Unit | DOCDB family, applicants harmonised with `prepare_applicants` (Step 2), firms only | one invention = one family; subsidiaries merged |
| Window | priority years **2010-2018** | later families are not granted or cited *yet* (grant-rate curve, §2.1) |
| Firms | top **10** by families in the window, at least 10 families | below that a single patent swings every rate |
| Families in the window | 3,061 (7,772 applications) | |

The ten firms: IBM (150 families), Intel (88), Google (86), Toshiba (81),
Microsoft (76), D-Wave (71), QuantumCTek (64), State Grid (50), Rigetti (49),
Northrop Grumman (41).

## 3. The four indicators

| Dimension | Basic indicator | Notebook |
|---|---|---|
| Volume | share of the sector's families in the window | §4.1 |
| Influence | forward citations within 5 years of first publication ÷ mean of the families with the same priority year (1 = average) | §5.1 |
| Success | granted ÷ national applications at **all** offices, no `WO` and no kind `T` | §6.1 |
| Globalization | mean number of distinct offices per family, no `WO` and no kind `T` | §7.1 |

Success and globalization are measured at all offices and not only at the EPO,
unlike the tutorial: only 21% of our families have an EP application.

## 4. Globalization (§7), the section added in this step

| Measure | What it showed |
|---|---|
| Offices per family (basic) | sector average 1.8; **69%** of families filed at one office only. CNIPA and USPTO 52% of families each, EPO 21%, JPO 17%, KIPO 11%. Three groups: worldwide filers (Northrop Grumman 5.2, Google 4.8), US-first filers (IBM 2.9 … Intel 1.5), domestic filers (QuantumCTek 1.3, State Grid 1.0) |
| EP validation states (`TLS231`) | median 8 states, almost exactly the London-Agreement states with no translation requirement (GB, CH, DE, FR, LU, IE, BE). Only 14% of the families have a granted EP patent, so **not used in the score** |
| Quadrilateral share (Clarivate) | only 7% of families (217); Google 45%, IBM 26%. **Northrop Grumman 0%** despite the most offices: it files in US, EP, JP, CA, AU, KR but **never in China** |
| Foreign reach (our refinement) | share of families protected outside the home market. State Grid 2%, QuantumCTek 14% vs Toshiba, D-Wave, Google, Northrop Grumman ≥ 90%. Biased in favour of non-US firms (for D-Wave "abroad" = the US) |

## 5. From four indicators to one score (§8)

**Diagnostics before weighting** (OECD-JRC Handbook, 2008): success separates the
firms much less than the others (coefficient of variation 0.16 vs 0.41-0.59);
volume, influence and globalization each have one firm at about twice the
average; no pair of indicators is strongly correlated (max 0.47), so nothing is
counted twice.

**Method: Reciprocal Rank Fusion** (Cormack et al., 2009), c = 10. Chosen over the
ratio to the mean because three indicators are skewed (with the mean, Rigetti's
influence alone would give it 76 of 126 points and the 2nd place while it is 7th
or worse on three dimensions), because Dell's question is a shortlist, and because
portfolios of 41-150 families make the order more reliable than the exact ratios.

**Weights**

| Influence | Globalization | Volume | Success |
|---:|---:|---:|---:|
| 0.35 | 0.25 | 0.20 | 0.20 |

Influence first because the dominant qubit design is not settled and the firms
others build on are the ones most likely to own it; globalization because a
patent protects Dell only where it is in force; volume below influence because
part of it is domestic-only filing and it already selects the firms; success low
because it barely separates the firms and depends on where they file.

## 6. Result

| Rank | Firm | Score (RRF) | Tier |
|---:|---|---:|---|
| 1 | IBM | 83.7 | Leader |
| 2 | Google | 81.1 | Leader |
| 3 | Northrop Grumman | 80.1 | Leader |
| 4 | Intel | 76.7 | Challenger |
| 5 | Rigetti | 75.7 | Challenger |
| 6 | D-Wave Systems | 75.2 | Challenger |
| 7 | Microsoft | 71.4 | Follower |
| 8 | Toshiba | 69.0 | Follower |
| 9 | QuantumCTek | 65.0 | Follower |
| 10 | State Grid | 57.8 | Follower |

## 7. Robustness (§9-§10)

| Test | Result |
|---|---|
| Three methods (mean, RRF, geometric mean) | same bottom four; IBM, Google, Northrop Grumman in the first four in every method; Rigetti moves (2nd / 5th / 3rd) |
| 8 hand-picked weight sets | Spearman 0.85-0.98 with ours, except **without influence (0.62)**: Rigetti 5th → 9th, Intel 4th → 8th |
| 2,000 random weight sets (Dirichlet) | P(top 3): IBM 93%, Google 78%, Northrop Grumman 62%; Rigetti ranges 1st-9th; State Grid always 10th |
| 1,000 bootstrap resamples of each firm's families | P(top 3): IBM 100%, Northrop Grumman 96%, Google 91%; Intel, Rigetti, D-Wave cannot be ordered (ranks 3-7) |
| Refinements in the score | blocking patents, links to science, 3-year window: Spearman 0.95-0.98. Quadrilateral / foreign reach instead of offices: 0.83 / 0.77, moving only Northrop Grumman (down) and D-Wave (up), because of the limits of those measures (§4) |

The ranking is more sensitive to the weights than to the data, and the weight
that matters most is the one on influence. We therefore report **tiers**, not ten
positions.

## 8. Reading for the deck

1. **Leaders: IBM, Google, Northrop Grumman**, robust to method, weights and
   data. IBM is the only firm good on every dimension; Google and Northrop
   Grumman add strong influence to the widest protection of the sector.
2. **Influence without protection: Rigetti and Intel.** The most cited
   portfolios (Rigetti also the highest share of blocking patents), protected in
   few offices; Intel has the lowest grant rate. Natural candidates for the
   future score.
3. **Big at home only: QuantumCTek and State Grid.** Large, little cited,
   protected almost only in China.
4. **The present score looks backwards.** Origin Quantum (14 families in
   2010-2018, 546 in 2019-2022), IonQ (13 vs 109) and Baidu (0 vs 179) are
   absent by construction: Step 4 has to catch them.

---

# Part 2 · Entrants

Run on PROD in `notebooks/STEP3_present_score_entrant.ipynb`, with outputs in
`notebooks/outputs/step3/` under an `_entrant` suffix (`present_score_entrant.csv`,
`present_score_robustness_entrant.csv`, `present_score_design_entrant.json`,
`fig_present_score_entrant.png`, `fig_rank_uncertainty_entrant.png`,
`fig_leaderboard_entrant.png`) plus the joint scale (`present_score_joint.csv`,
`fig_present_score_joint.png`).

## 9. Set-up

| Choice | Value |
|---|---|
| Population | entrants: first family in the sector in 2015 or later (`SPLIT_YEAR`) |
| Cleaning | manual aliases for Chinese name variants (Origin Quantum, Ruban, Qasky, Shenzhou, Hengtong, 1QBit); Bank of America removed as a false positive; one research institute removed as non-firm |
| Window, indicators, method, weights | **identical to the incumbents**, so that the two lists share one yardstick |
| Firms | top 11 entrants by families in 2010-2018, at least 10 families (11 because of a tie) |

The eleven entrants: Zhejiang Shenzhou Quantum Network (39 families), Ruban
Quantum Technology (32), Anhui Qasky (31), 1QBit (22), Origin Quantum (22),
PsiQuantum (16), Jiangsu Hengtong Wentian (15), Zhejiang Quantum Technology (13),
IonQ (13), Bull (12), Wells Fargo Bank (12). Six are mainly on quantum
communication/security (title-based classification, 50% threshold).

## 10. Diagnostics and choices

- Success separates the entrants least (coefficient of variation 0.19),
  globalization most (0.72): seven of eleven file every family at one office.
- **Influence and success are correlated 0.82** among entrants. Both follow
  geography: US filers (IonQ, 1QBit, PsiQuantum, Wells Fargo) are cited and
  granted more (USPTO grants 87% of the sector's applications, CNIPA 73%).
  Tested in robustness: dropping success gives Spearman 0.85.
- **Method: RRF** as for incumbents; with the mean, Bull would take 43 of its 99
  points from globalization alone and jump to 4th.
- **Weights: the same as incumbents** (0.35 / 0.25 / 0.20 / 0.20). An
  "entrant view" with volume at 0.10 gives Spearman 0.94 with ours.

## 11. Result

| Rank | Entrant | Focus | Score (RRF) | Tier |
|---:|---|---|---:|---|
| 1 | IonQ | computing | 91.1 | Leader |
| 2 | 1QBit | computing | 83.2 | Leader |
| 3 | PsiQuantum | computing | 82.3 | Leader |
| 4 | Origin Quantum | computing | 77.6 | Middle |
| 5 | Wells Fargo Bank | communication | 75.3 | Middle |
| 6 | Ruban Quantum Technology | communication | 74.1 | Middle |
| 7 | Zhejiang Shenzhou Quantum Network | communication | 73.6 | Middle |
| 8 | Anhui Qasky | communication | 70.1 | Follower |
| 9 | Bull | computing | 70.0 | Middle |
| 10 | Jiangsu Hengtong Wentian | communication | 61.9 | Follower |
| 11 | Zhejiang Quantum Technology | communication | 60.8 | Follower |

Bull sits in the middle tier despite rank 9: its bootstrap range (5th-9th)
overlaps the middle group, and two of the three methods place it 4th-5th.

## 12. Robustness

| Test | Result |
|---|---|
| Three methods | same top three and same last two; Bull (4th / 9th / 5th) and Wells Fargo (8th / 5th / 8th) move |
| 9 hand-picked weight sets | Spearman 0.83-0.99; IonQ 1st in all nine; lowest is "size first" (0.83), where the large Chinese portfolios climb |
| 2,000 random weight sets | IonQ first in 78%, top 3 in 86%; 1QBit 69%, PsiQuantum 65% in the top 3 |
| 1,000 bootstrap resamples | P(top 3): IonQ 99%, 1QBit 92%, PsiQuantum 82%; middle group (Origin, Wells Fargo, Ruban, Shenzhou, Bull) not separable |
| Refinements in the score | Spearman 0.95-1.00; no change in the top three |

## 13. Entrants and incumbents on one scale

The four basic indicators are computed identically in both notebooks and
referenced to the whole sector, so the 21 firms can be ranked together (RRF,
c = 21, same weights). Main facts:

- **IonQ is 4th of 21** (behind Northrop Grumman, IBM and Google, less than
  two points behind the leader) and **1st of 21 without volume**.
- 1QBit and PsiQuantum are 9th and 10th (7th and 9th without volume), next to
  Intel and Microsoft.
- Positions 16-21 are all Chinese quantum-communication firms, incumbent (State
  Grid) or entrant.
- Caveats: entrants start ~3 points behind on success (sector grant rate 80.6%
  for 2010-2014 families vs 77.7% for 2015-2018, pending applications); volume
  is structurally lower for entrants, hence the no-volume version.

**Suggested input for the Magic Quadrant (Step 5):** the joint score with our
weights (`present_score_joint.csv`), with the no-volume version as a check.

## 14. Reading for the deck

1. **IonQ is the standout entrant**: first in every test, and already at the
   level of the incumbent leaders.
2. **1QBit and PsiQuantum** complete the leading group: 1QBit protects widely
   (3.5 offices per family), PsiQuantum is very cited with the highest share of
   blocking patents among entrants (38%) but files almost only in the US.
3. **Most Chinese entrants are a domestic quantum-communication cluster**
   (five of six file only at CNIPA); Origin Quantum is the only Chinese
   computing entrant.
4. **Wells Fargo (a bank, a likely customer) and Bull (a supercomputer maker,
   a Dell competitor) are not acquisition targets**, even if scored.
5. **The window shows only the start**: after 2018 Origin Quantum goes from 22
   to 590 families, IonQ from 13 to 109, Ruban from 32 to 72, while Zhejiang
   Shenzhou stops (39 to 1). This is the job of the future score (Step 4).

## References

- Cormack, G. V., Clarke, C. L. A., Büttcher, S. (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. *SIGIR '09*.
- Efron, B. (1979). Bootstrap methods: another look at the jackknife. *Annals of Statistics* 7(1).
- OECD / JRC (2008). *Handbook on Constructing Composite Indicators: Methodology and User Guide*. OECD Publishing.
- Saisana, M., Saltelli, A., Tarantola, S. (2005). Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. *JRSS A* 168(2).
- Tutorial 4, `40_present_value_score.ipynb`, Innovation Management, Politecnico di Torino.
