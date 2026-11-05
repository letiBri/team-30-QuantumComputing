# outputs/

Everything here is produced by the Step 1 notebook and regenerates if deleted.
All figures and tables below are from the run of 17 October, on PROD, with
`B82Y10/00` excluded from the definition.

## figures/

| File | Shows | Where it belongs |
|---|---|---|
| `fig_volume.png` | Families and applications per year, with the PCT share, at both levels | Landscape slide |
| `fig_dating.png` | The same patents dated by filing, publication and priority year | Technical appendix |
| `fig_growth.png` | Sector growth against all patenting, indexed to 2000 | Landscape slide |
| `fig_applicants_countries_over_time.png` | Countries of origin of each applicant over time | Landscape slide |
| `fig_cpc_subclasses.png` | Shares of CPC subclasses over time | Landscape slide |
| `fig_fillings_at_the_ip5_offices.png` | Fillings at the IP5 offices over time | Landscape slide |
| `fig_wipo_sectors.png` | Shares across the 5 WIPO technology sectors | Landscape slide |
| `fig_applicants_active_entry_exit.png` | Applicants, entry and exit over time | Landscape slide |
| `fig_subfield_growth.png` | Map of subfield growth | Landscape slide |
| `fig_appropriability.png` | Appropriability indicators over time | Landscape slide |
| `fig_country_bubble_map.png` | Map of applicant and inventor countries | Landscape slide |
| `fig_cpc_absolute_volume.png` | Absolute number of CPC subclasses over time | Landscape slide |
| `fig_share_of_all_patents.png` | Share of Quantum Computing to all patents | Landscape slide |
| `fig_top_5_countries_abs.png` | Top 5 applicant countries over time | Landscape slide |
| `fig_blocks.png` | Each block of the definition counted separately | **Technical appendix — see below** |

`fig_blocks.png` is the one to keep. It is the evidence behind excluding
`B82Y10/00`: the blue line is nanotechnology, peaking in 2004 and collapsing by
2014, and it was the whole of the sector's apparent decline. The orange line,
`G06N10`, is quantum computing, and it never declines. Note that the figure still
counts `B82Y10/00` — that is deliberate, since the point of the decomposition is
to show what the excluded code was doing.

A figure that shows how a definition was corrected says more about the quality of
the analysis than one more growth curve does.

## tables/

| File | Contents |
|---|---|
| `tab_growth.csv` | Counts and growth for the sector and for all patenting, at both levels, from 2000 and from 2010 |
| `tab_blocks.csv` | Families per year for each block of the definition |
| `sector_definition_counts.csv` | Families caught by the CPC branch, the keyword branch, their overlap, and the union |
| `tab_cpc_subclasses.csv` | Shares of CPC subclasses|
| `tab_sector_geo_shares.csv` | Shares of countries of origin (general)|
| `tab_sector_geo_shares_with_unknown.csv` | Shares of countries of origin for both applicant and inventor countries (WITH unknown / null countries)   |
| `tab_sector_geo_shares_without_unknown.csv` | Shares of countries of origin for both applicant and inventor countries (WITHOUT unknown / null countries) |
| `tab_wipo_fields.csv` | Shares of WIPO technology fields |
| `tab_wipo_sectors.csv` | Shares of WIPO technology sectors |
| `tab_appropriability.csv` | Appropriability analysis |
| `tab_field_concentration.csv` | Concentration measures of patenting in the sector (complete years only) |
| `tab_share_of_each_years_families.csv` | Top applicants ranked by number of families, with the year of their first family in the sector and their status |
| `tab_categorised_applicants.csv` | Applicants per year divided into categories |
| `tab_incumbents_and_entrants.csv` | Summary of the 30 largest applicants: number of incumbents and entrants|
| `tab_growth_between_periods.csv` | Families per CPC subfield in the past and recent period, with growth between them (%) |
| `tab_fastest_growers.csv` | Three fastest-growing subfields |


## cache/

`.pkl` files are the aggregates behind the
figures. Each is a few kilobytes and each stands in for a PROD query of several
minutes, so they are committed: a teammate can re-run the analysis without
paying for the queries again.

They are derived data, not source. **If the sector definition changes, delete
them** — `cached()` will otherwise hand back results computed under the old
definition, with nothing to warn you. That is exactly what had to be done when
`B82Y10/00` was removed.
