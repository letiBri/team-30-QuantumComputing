"""Step 1 — general description of the sector

Conducts the analysis of the sector.
Provides helper functions for the data analysis
Contains code from the sections 6-9 from the Step 1 notebook.

"""
from src.stage02_clean import family_scope, application_scope, Scope, cached, consolidated_names, prepare_applicants
from src.stage01_extract import symbol_prefix_condition
from pathlib import Path
import pandas as pd
from sqlalchemy import and_, case, distinct, func, literal, or_
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN,               # import the needed tables for the extractions
    TLS202_APPLN_TITLE,
    TLS203_APPLN_ABSTR,
    TLS206_PERSON,
    TLS207_PERS_APPLN,
    TLS224_APPLN_CPC,
    TLS230_APPLN_TECHN_FIELD,
    TLS901_TECHN_FIELD_IPC,
)
from matplotlib.ticker import MaxNLocator
import numpy as np
import seaborn as sns
import geopandas as gpd
import pycountry
from matplotlib.ticker import PercentFormatter

# --------------------------------------------------------------------------- #
# config and global variables
# --------------------------------------------------------------------------- #

LEVELS = ("family", "application")
UNIT_LABEL = {"family": "families", "application": "applications"}
ALT_BASE_YEAR = 2010        # later base, for a sector whose early counts are thin
BLOCKS = {
    "G06N10 (core)":        ("G06N10",),
    "B82Y10/00 (nanotech)": ("B82Y10/00",),
    "H10N60/12 (Josephson)":("H10N60/12",),
    "H04L9/0852 + H04B10/70 (comms)": ("H04L9/0852", "H04B10/70"),
}
CPC_DEFINITIONS = {
    "G06N": "COMPUTING ARRANGEMENTS BASED ON SPECIFIC COMPUTATIONAL MODELS",
    "H04L": "TRANSMISSION OF DIGITAL INFORMATION, e.g. TELEGRAPHIC COMMUNICATION",
    "H04B": "TRANSMISSION",
    "G06F": "ELECTRIC DIGITAL DATA PROCESSING",
    "H10N": "ELECTRIC SOLID-STATE DEVICES NOT OTHERWISE PROVIDED FOR",
    "B82Y": "SPECIFIC USES OR APPLICATIONS OF NANOSTRUCTURES; MEASUREMENT OR ANALYSIS OF NANOSTRUCTURES; MANUFACTURE OR TREATMENT OF NANOSTRUCTURES",
    "Y02D": "CLIMATE CHANGE MITIGATION TECHNOLOGIES IN INFORMATION AND COMMUNICATION TECHNOLOGIES [ICT]",
    "G06Q": "INFORMATION AND COMMUNICATION TECHNOLOGY [ICT] SPECIALLY ADAPTED FOR ADMINISTRATIVE, COMMERCIAL, FINANCIAL, MANAGERIAL OR SUPERVISORY PURPOSES",
    "H03K": "PULSE TECHNIQUE",
    "H10D": "INORGANIC ELECTRIC SEMICONDUCTOR DEVICES",
    "Other": "other fields",
    "Total": ""
}

WORLD_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"


# --------------------------------------------------------------------------- #
# data counting functions
# --------------------------------------------------------------------------- #


def _join_applications(cfg, q, scope):
    """Join each unit to its applications: all members of a family, or the application itself."""
    IPR_TYPE = cfg.ipr_type
    key = TLS201_APPLN.docdb_family_id if scope.level == "family" else TLS201_APPLN.appln_id
    return q.join(TLS201_APPLN, key == scope.sq.c.unit_id).filter(TLS201_APPLN.ipr_type == IPR_TYPE)


def _tag(df, scope):
    return df.assign(scope=scope.name, level=scope.level)


def count_per_year(patstat, db, scope, only_pct=False):
    """Units per year; only_pct keeps those filed through the PCT."""
    sq = scope.sq
    q = db.query(sq.c.year, func.count().label("n")).group_by(sq.c.year).order_by(sq.c.year)
    if only_pct:
        q = q.filter(sq.c.is_pct == 1)
    return _tag(patstat.df(q), scope)


def _split_equally(patstat, db, scope, unit_category, category):
    """Fractional counting: each unit is split equally across its distinct categories."""
    pairs = unit_category.distinct().subquery()
    k = db.query(pairs.c.unit_id, func.count().label("k")).group_by(pairs.c.unit_id).subquery()
    q = (
        db.query(getattr(pairs.c, category), pairs.c.year, func.sum(1.0 / k.c.k).label("n_frac"))
        .join(k, k.c.unit_id == pairs.c.unit_id)
        .group_by(getattr(pairs.c, category), pairs.c.year)
    )
    return _tag(patstat.df(q), scope)


def fractional_by_country(cfg, patstat, db, scope, role="applicant", count_unknown=False):
    """Fractional counts by person country and year (role: 'applicant' or 'inventor')."""
    sq = scope.sq
    seq_nr = TLS207_PERS_APPLN.applt_seq_nr if role == "applicant" else TLS207_PERS_APPLN.invt_seq_nr
    raw_ctry = func.trim(TLS206_PERSON.person_ctry_code)   # unknown countries are NULL, '' or blanks

    if count_unknown:
        ctry = func.coalesce(
            func.nullif(raw_ctry, ""),
            "Unknown" # counting unknown countries 
        )
        country_filter = seq_nr > 0
    else:
        ctry = raw_ctry
        country_filter = (
            (seq_nr > 0)
            & raw_ctry.isnot(None)
            & (raw_ctry != "") # deleting unkonown countries
        )
        
    persons = (
        _join_applications(
            cfg, db.query(sq.c.unit_id, sq.c.year, TLS207_PERS_APPLN.person_id, ctry.label("ctry")).distinct(), scope
        )
        .join(TLS207_PERS_APPLN, TLS207_PERS_APPLN.appln_id == TLS201_APPLN.appln_id)
        .join(TLS206_PERSON, TLS206_PERSON.person_id == TLS207_PERS_APPLN.person_id)
        .filter(country_filter)
        .subquery()
    )
    k = db.query(persons.c.unit_id, func.count().label("k")).group_by(persons.c.unit_id).subquery()
    q = (
        db.query(persons.c.ctry, persons.c.year, func.sum(1.0 / k.c.k).label("n_frac"))
        .join(k, k.c.unit_id == persons.c.unit_id)
        .group_by(persons.c.ctry, persons.c.year)
    )
    
    return _tag(patstat.df(q), scope).assign(role=role)


def fractional_by_cpc_subclass(cfg, patstat, db, scope):
    """Fractional counts by CPC subclass (the first 4 characters) and year."""
    sq = scope.sq
    subclass = func.substr(func.replace(TLS224_APPLN_CPC.cpc_class_symbol, " ", ""), 1, 4)
    q = (
        _join_applications(cfg, db.query(sq.c.unit_id, sq.c.year, subclass.label("subclass")), scope)
        .join(TLS224_APPLN_CPC, TLS224_APPLN_CPC.appln_id == TLS201_APPLN.appln_id)
    )
    return _split_equally(patstat, db, scope, q, "subclass")


def fractional_by_techn_field(cfg, patstat, db, scope):
    """Fractional counts by WIPO technology field (1-35) and year.

    tls230 weights sum to 1 per application; at family level they are rescaled
    so that every family also sums to 1.
    """
    sq = scope.sq
    unit_field = (
        _join_applications(
            cfg,
            db.query(sq.c.unit_id, sq.c.year, TLS230_APPLN_TECHN_FIELD.techn_field_nr,
                     func.sum(TLS230_APPLN_TECHN_FIELD.weight).label("w")),
            scope,
        )
        .join(TLS230_APPLN_TECHN_FIELD, TLS230_APPLN_TECHN_FIELD.appln_id == TLS201_APPLN.appln_id)
        .group_by(sq.c.unit_id, sq.c.year, TLS230_APPLN_TECHN_FIELD.techn_field_nr)
        .subquery()
    )
    unit_total = (
        db.query(unit_field.c.unit_id, func.sum(unit_field.c.w).label("w_total"))
        .group_by(unit_field.c.unit_id)
        .subquery()
    )
    q = (
        db.query(unit_field.c.techn_field_nr, unit_field.c.year,
                 func.sum(unit_field.c.w / unit_total.c.w_total).label("n_frac"))
        .join(unit_total, unit_total.c.unit_id == unit_field.c.unit_id)
        .group_by(unit_field.c.techn_field_nr, unit_field.c.year)
    )
    return _tag(patstat.df(q), scope)


def count_by_office(cfg, patstat, db, scope):
    """Units per office and year.

    Family level: families with at least one application at the office.
    Application level: applications filed at the office.
    """
    sq = scope.sq
    q = (
        _join_applications(
            cfg,
            db.query(TLS201_APPLN.appln_auth.label("office"), sq.c.year,
                     func.count(distinct(sq.c.unit_id)).label("n")),
            scope,
        )
        .group_by(TLS201_APPLN.appln_auth, sq.c.year)
    )
    return _tag(patstat.df(q), scope)


def scope_profile(cfg, patstat, db, scope):
    """Units, units via PCT, granted units and mean family size."""
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    sq = scope.sq
    q = db.query(
        func.count().label("n"),
        func.sum(sq.c.is_pct).label("n_pct"),
        func.sum(sq.c.is_granted).label("n_granted"),
        func.avg(sq.c.family_size * 1.0).label("mean_family_size"),
    ).filter(sq.c.year <= LAST_COMPLETE_YEAR)
    return _tag(patstat.df(q), scope)

def profile_per_year(patstat, db, scope):
    """Yearly units, PCT units, granted units and mean family size."""
    sq = scope.sq
    q = (
        db.query(
            sq.c.year,
            func.count().label("n"),
            func.sum(sq.c.is_pct).label("n_pct"),
            func.sum(sq.c.is_granted).label("n_granted"),
            func.avg(sq.c.family_size * 1.0).label("mean_family_size"),
        )
        .group_by(sq.c.year)
        .order_by(sq.c.year)
    )
    return _tag(patstat.df(q), scope)


# --------------------------------------------------------------------------- #
# helper functions
# --------------------------------------------------------------------------- #

def shade_truncated(cfg, ax):
    """Shade incomplete years; a no-op while the window ends at the last complete year."""
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    YEAR_MAX = cfg.year_max
    if LAST_COMPLETE_YEAR >= YEAR_MAX:
        return
    ax.axvspan(LAST_COMPLETE_YEAR + 0.5, YEAR_MAX + 0.5, color="grey", alpha=0.15, lw=0,
               label="incomplete years")


def complete_years(cfg, df):
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    return df[df["year"] <= LAST_COMPLETE_YEAR]


def pool_other(cfg, df, category, n=None, value="n_frac", other_label="Other"):
    """Keep the n largest categories and pool the rest into 'Other'."""
    n = cfg.top_n if n is None else n
    top = complete_years(cfg, df).groupby(category)[value].sum().nlargest(n).index
    out = df.copy()
    out[category] = out[category].where(out[category].isin(top), other_label)
    return out.groupby([category, "year"], as_index=False)[value].sum()


def share_table(counts):
    """Counts -> percentages summing to 100 per column, 'Other' last, with a Total row."""
    shares = counts / counts.sum() * 100
    order = [c for c in shares.sort_values(shares.columns[0], ascending=False).index if c != "Other"]
    order += ["Other"] if "Other" in shares.index else []
    shares = shares.loc[order]
    shares.loc["Total"] = shares.sum()
    return shares


def share_over_time(cfg, df, category, value="n_frac"):
    """Year x category table of percentages (each year sums to 100)."""
    wide = df.pivot_table(index="year", columns=category, values=value, aggfunc="sum", fill_value=0)
    wide = wide.div(wide.sum(axis=1), axis=0) * 100
    order = [c for c in complete_years(cfg, wide.reset_index()).set_index("year").sum().sort_values(ascending=False).index
             if c != "Other"]
    return wide[order + (["Other"] if "Other" in wide.columns else [])]


def stack_100(cfg, ax, shares, title):
    """Stacked area of percentages, y axis from 0% to 100%."""
    YEAR_MIN = cfg.year_min
    YEAR_MAX = cfg.year_max
    palette = [c for i, c in enumerate(plt.get_cmap("tab10").colors) if i != 7]   # grey reserved for "Other"
    colors = ["lightgrey" if c == "Other" else palette[i % len(palette)] for i, c in enumerate(shares.columns)]
    ax.stackplot(shares.index, shares.T.values, labels=shares.columns, colors=colors, alpha=0.85)
    shade_truncated(cfg, ax)
    ax.set(title=title, xlabel="year", xlim=(YEAR_MIN, YEAR_MAX), ylim=(0, 100))
    ax.yaxis.set_major_formatter(PercentFormatter(100))


def pct_format(df):
    return df.style.format("{:.1f}%")


def side_by_side(title, **kw):
    """Two axes: families (left) and applications (right)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), **kw)
    fig.suptitle(title)
    return fig, axes


def _dating_series(cfg, patstat, db, sector_ids, volume):
    SECTOR_NAME = cfg.sector_name
    FAMILY_TIME_COLUMN = cfg.family_time_column
    by_col = [
        count_per_year(patstat, db, Scope(SECTOR_NAME, "application", application_scope(sector_ids, col)))
        .assign(series=f"applications by {col}")
        for col in ("appln_filing_year", "earliest_publn_year", "earliest_filing_year")
    ]
    fam = volume[(volume["scope"] == SECTOR_NAME)
                 & (volume["level"] == "family")
                 & (volume["series"] == "all")].assign(series=f"families by {FAMILY_TIME_COLUMN}")
    return pd.concat(by_col + [fam], ignore_index=True)


def growth_block(cfg, start, end, volume, totals):
    SECTOR_NAME = cfg.sector_name
    rows = [(lvl, s) for lvl in LEVELS for s in ("all patents", SECTOR_NAME)]
    return pd.DataFrame({
        f"count {start}": totals.loc[start],
        f"count {end}": totals.loc[end],
        f"growth {start}-{end} (%)": (totals.loc[end] / totals.loc[start] - 1) * 100,
        f"CAGR {start}-{end} (%)": ((totals.loc[end] / totals.loc[start]) ** (1 / (end - start)) - 1) * 100,
    }).loc[rows]


def block_series(cfg, patstat, db, prefixes):
    SECTOR_NAME = cfg.sector_name
    ids = (db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
           .join(TLS224_APPLN_CPC, TLS201_APPLN.appln_id == TLS224_APPLN_CPC.appln_id)
           .filter(symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, prefixes))
           .distinct())
    return count_per_year(patstat, db, Scope(SECTOR_NAME, "family", family_scope(ids)))


def _iso3(alpha2):
    try:
        c = pycountry.countries.get(alpha_2=alpha2)
        return c.alpha_3 if c else None
    except (AttributeError, KeyError):
        return None


def herfindahl(patents_per_firm):
    "Sum of the squared shares of the firms."
    shares = np.asarray(patents_per_firm) / np.sum(patents_per_firm)
    return np.sum(shares ** 2)


def concentration_ratio(patents_per_firm, k=4):
    "Share (%) of all patents held by the k largest firms."
    largest_first = np.sort(patents_per_firm)[::-1]
    return largest_first[:k].sum() / largest_first.sum() * 100


def field_measures(patents_per_firm):
    "Chosen measures for one group of firms, as one row of a table."
    return {
        "firms": len(patents_per_firm),
        "patents (sum over firms)": int(np.sum(patents_per_firm)),
        "CR4 (%)": concentration_ratio(patents_per_firm),
        "HH": herfindahl(patents_per_firm),
        "1/HH": 1 / herfindahl(patents_per_firm),
    }

# --------------------------------------------------------------------------- #
# plotting and calculating functions
# --------------------------------------------------------------------------- #


def plot_volume_per_year(cfg, volume, sector_scopes, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    FAMILY_TIME_COLUMN = cfg.family_time_column
    APPLN_TIME_COLUMN = cfg.appln_time_column
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = side_by_side(f"{SECTOR_NAME}: volume per year", sharex=True)
    for ax, scope in zip(axes, sector_scopes):
        data = volume.query("scope == @scope.name and level == @scope.level")
        for series, grp in data.groupby("series"):
            ax.plot(grp["year"], grp["n"], marker="o", ms=3, label=f"{UNIT_LABEL[scope.level]}, {series}")
        shade_truncated(cfg, ax)
        year_col = FAMILY_TIME_COLUMN if scope.level == "family" else APPLN_TIME_COLUMN
        ax.set(title=f"{UNIT_LABEL[scope.level]} per {year_col}", xlabel="year", ylabel=UNIT_LABEL[scope.level])
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_volume.png", dpi=200, bbox_inches="tight")

    if show_plots_and_tables:
        plt.show()

def plot_patents_dated_in_different_ways(cfg, dating, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    fig, ax = plt.subplots(figsize=(10, 5))
    for series, grp in dating.groupby("series"):
        ax.plot(grp["year"], grp["n"], marker="o", ms=3, label=series)
    shade_truncated(cfg, ax)
    ax.set(title=f"{SECTOR_NAME}: the same patents dated in different ways", xlabel="year", ylabel="count")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_dating.png", dpi=200, bbox_inches="tight")
    
    if show_plots_and_tables:
        plt.show()


def calculate_growth(cfg, volume, totals, show_plots_and_tables):
    YEAR_MIN = cfg.year_min
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    OUTPUT_DIR = Path(cfg.output)
    growth = growth_block(cfg, YEAR_MIN, LAST_COMPLETE_YEAR, volume, totals).join(
        growth_block(cfg, ALT_BASE_YEAR, LAST_COMPLETE_YEAR, volume, totals)[
            [f"growth {ALT_BASE_YEAR}-{LAST_COMPLETE_YEAR} (%)",
             f"CAGR {ALT_BASE_YEAR}-{LAST_COMPLETE_YEAR} (%)"]
        ]
    )
    growth.to_csv(OUTPUT_DIR / "tables" / "tab_growth.csv")
    
    if show_plots_and_tables:
        print(growth.style.format({c: ("{:,.0f}" if c.startswith("count") else "{:+.1f}%") for c in growth.columns}))
                  

def plot_sector_growth_percentage(cfg, growth_path, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    YEAR_MIN = cfg.year_min
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = side_by_side(f"{SECTOR_NAME} vs all patents: growth (%) since {YEAR_MIN}", sharey=True)
    for ax, level in zip(axes, LEVELS):
        for scope_name in ("all patents", SECTOR_NAME):
            ax.plot(growth_path.index, growth_path[(level, scope_name)], marker="o", ms=3, label=scope_name)
        ax.axhline(0, color="grey", lw=0.8)
        ax.set(title=UNIT_LABEL[level], xlabel="year", ylabel=f"growth since {YEAR_MIN}")
        ax.yaxis.set_major_formatter(PercentFormatter(100))
        ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_growth.png", dpi=200, bbox_inches="tight")
    # plt.show()


def plot_sector_share_of_all_patents(cfg, share, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = side_by_side(f"{SECTOR_NAME}: share of all patents", sharex=True)
    for ax, level in zip(axes, LEVELS):
        s = share[(level, SECTOR_NAME)] / share[(level, "all patents")] * 100
        ax.plot(s.index, s.values, marker="o", ms=3)
        ax.set(title=UNIT_LABEL[level], xlabel="year", ylabel="share of all patents")
        ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=2))
        ax.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_share_of_all_patents.png", dpi=200, bbox_inches="tight")
    
    if show_plots_and_tables:
        plt.show()


def plot_volume_by_code_block(cfg, blocks, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    fig, ax = plt.subplots(figsize=(11, 5))
    for name, g in blocks.groupby("block"):
        ax.plot(g["year"], g["n"], marker="o", ms=3, label=name)
    ax.set(title=f"{SECTOR_NAME}: volume by code block", xlabel="year", ylabel="families")
    ax.legend()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_blocks.png", dpi=200, bbox_inches="tight")
    
    if show_plots_and_tables:
        plt.show()


def plot_and_calculate_cpc_subclasses(cfg, patstat, db, sector_scopes, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    cpc_mix = cached(
        cfg, 
        "cpc_mix",
        lambda: pd.concat([fractional_by_cpc_subclass(cfg, patstat, db, s) for s in sector_scopes], ignore_index=True),
    )
    cpc_pooled = pd.concat([pool_other(cfg, cpc_mix[cpc_mix["level"] == lvl], "subclass").assign(level=lvl)
                            for lvl in LEVELS], ignore_index=True)

    # table
    cpc_counts = complete_years(cfg, cpc_pooled).pivot_table(index="subclass", columns="level", values="n_frac",
                                                        aggfunc="sum", fill_value=0)[list(LEVELS)]
    cpc_shares = share_table(cpc_counts)
    cpc_shares["definition (fill in from the CPC scheme)"] = (cpc_shares.index.map(CPC_DEFINITIONS))
    cpc_shares.to_csv(OUTPUT_DIR / "tables" / "tab_cpc_subclasses.csv")
        
    if show_plots_and_tables:
        print(cpc_shares.style.format("{:.1f}%", subset=list(LEVELS)))

    # plot share
    fig, axes = side_by_side(f"{SECTOR_NAME}: CPC subclass mix over time", sharey=True)
    for ax, level in zip(axes, LEVELS):
        stack_100(cfg, ax, share_over_time(cfg, cpc_pooled[cpc_pooled["level"] == level], "subclass"),
                  f"share of {UNIT_LABEL[level]}")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes[-1].legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_cpc_subclasses.png", dpi=200, bbox_inches="tight")
    
    if show_plots_and_tables:
        plt.show()

    # plot absolute
    cpc_abs = complete_years(cfg, cpc_pooled)

    fig, axes = side_by_side(f"{SECTOR_NAME}: CPC subclasses, absolute volume", sharex=True)
    for ax, level in zip(axes, LEVELS):
        wide = (cpc_abs[cpc_abs["level"] == level]
                .pivot_table(index="year", columns="subclass", values="n_frac", aggfunc="sum", fill_value=0))
        order = wide.sum().sort_values(ascending=False).index.tolist()
        if "Other" in order:                      # "Other" zawsze na górze stosu
            order = [c for c in order if c != "Other"] + ["Other"]
        wide = wide[order]
        ax.stackplot(wide.index, wide.T.values, labels=wide.columns)
        ax.set(title=UNIT_LABEL[level], xlabel="year", ylabel=f"{UNIT_LABEL[level]} (fractional)")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes[-1].legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" /"fig_cpc_absolute_volume.png", dpi=200, bbox_inches="tight")
    
    if show_plots_and_tables:
        plt.show()


def plot_and_calculate_wipo_technology_mix(cfg, patstat, db, sector_scopes, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    TOP_N = cfg.top_n
    OUTPUT_DIR = Path(cfg.output)

    # table wipo sector
    field_names = cached(
        cfg,
        "field_names",
        lambda: patstat.df(
            db.query(TLS901_TECHN_FIELD_IPC.techn_field_nr, TLS901_TECHN_FIELD_IPC.techn_field,
                     TLS901_TECHN_FIELD_IPC.techn_sector).distinct()
        ).drop_duplicates("techn_field_nr"),
    )
    
    fields_raw = cached(
        cfg,
        "techn_fields",
        lambda: pd.concat([fractional_by_techn_field(cfg, patstat, db, s) for s in sector_scopes], ignore_index=True),
    )
    fields = fields_raw.merge(field_names, on="techn_field_nr", how="left")
    
    techn_sector_counts = complete_years(cfg, fields).pivot_table(index="techn_sector", columns="level", values="n_frac",
                                                             aggfunc="sum", fill_value=0)[list(LEVELS)]
    techn_sector_shares = share_table(techn_sector_counts)
    techn_sector_shares.to_csv(OUTPUT_DIR / "tables" / "tab_wipo_sectors.csv")
        
    if show_plots_and_tables:
        print(pct_format(techn_sector_shares))

    # plot wipo sectors
    bars = techn_sector_shares.drop("Total").T
    fig, ax = plt.subplots(figsize=(11, 3))
    left = np.zeros(len(bars))
    for techn_sector in bars.columns:
        values = bars[techn_sector].values
        ax.barh([UNIT_LABEL[l] for l in bars.index], values, left=left, label=techn_sector)
        for y, (x0, v) in enumerate(zip(left, values)):
            if v >= 5:
                ax.text(x0 + v / 2, y, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=9)
        left += values
    ax.set(title=f"{SECTOR_NAME}: split across the 5 WIPO technology sectors", xlim=(0, 100))
    ax.xaxis.set_major_formatter(PercentFormatter(100))
    ax.invert_yaxis()
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.savefig(OUTPUT_DIR / "figures" / "fig_wipo_sectors.png", dpi=200, bbox_inches="tight")
        
    if show_plots_and_tables:
        plt.show()

    # table wipo fields
    field_counts = complete_years(cfg, fields).pivot_table(index="techn_field", columns="level", values="n_frac",aggfunc="sum", fill_value=0)[list(LEVELS)]
    top_fields = field_counts["family"].nlargest(TOP_N).index
    field_counts = field_counts.groupby(field_counts.index.where(field_counts.index.isin(top_fields), "Other")).sum()
    pct_format(share_table(field_counts))
    share_table(field_counts).to_csv(OUTPUT_DIR / "tables" / "tab_wipo_fields.csv")
        
    if show_plots_and_tables:
        print(pct_format(share_table(field_counts)))


def calculate_shares_of_sector_applications(cfg, offices, show_plots_and_tables):
    OUTPUT_DIR = Path(cfg.output)
    office_counts = complete_years(cfg, offices.query("level == 'application'")).groupby("office")["n"].sum().to_frame("applications")
    office_shares = share_table(office_counts)
    pct_format(office_shares)
    office_shares.to_csv(OUTPUT_DIR / "tables" / "tab_sector_geo_shares.csv")
        
    if show_plots_and_tables:
        print(pct_format(office_shares))


def plot_fillings_at_the_ip5_offices(cfg, offices, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    IP5_OFFICES = cfg.ip5_offices
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = side_by_side(f"{SECTOR_NAME}: filings at the IP5 offices", sharex=True)
    for ax, level in zip(axes, LEVELS):
        data = offices.query("level == @level and office in @IP5_OFFICES")
        for office, g in data.groupby("office"):
            ax.plot(g["year"], g["n"], marker="o", ms=3, label=office)
        shade_truncated(cfg, ax)
        title = ("families with an application at the office" if level == "family"
                 else "applications filed at the office")
        ax.set(title=title, xlabel="year", ylabel=UNIT_LABEL[level])
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes[-1].legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_fillings_at_the_ip5_offices.png", dpi=200, bbox_inches="tight")
       
    if show_plots_and_tables:
        plt.show()


def calculate_investor_and_applicants_countries(cfg, sector_scopes, countries, count_unknown, show_plots_and_tables):
    OUTPUT_DIR = Path(cfg.output)
    if count_unknown:
        name = "_with_unknown"
    else:
        name = "_without_unknown"
    country_counts = complete_years(cfg, countries).pivot_table(index="ctry", columns=["level", "role"], values="n_frac",
                                                           aggfunc="sum", fill_value=0)
    country_counts = country_counts[[(lvl, role) for lvl in LEVELS for role in ("applicant", "inventor")]]
    top_countries = country_counts[("family", "applicant")].nlargest(cfg.top_n).index
    country_counts = country_counts.groupby(country_counts.index.where(country_counts.index.isin(top_countries), "Other")).sum()
    share_table(country_counts).to_csv(OUTPUT_DIR / "tables" / f"tab_sector_geo_shares{name}.csv")
        
    if show_plots_and_tables:
        print(pct_format(share_table(country_counts)))


def plot_applicant_countries_share_over_time(cfg, countries, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = side_by_side(f"{SECTOR_NAME}: applicant countries over time", sharey=True)
    for ax, level in zip(axes, LEVELS):
        data = countries.query("role == 'applicant' and level == @level")
        stack_100(cfg, ax, share_over_time(cfg, pool_other(cfg, data, "ctry"), "ctry"), f"share of {UNIT_LABEL[level]}")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes[-1].legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_applicants_countries_over_time.png", dpi=200, bbox_inches="tight")
        
    if show_plots_and_tables:
        plt.show()


def plot_top_k_applicant_countries_over_time(cfg, top_k, countries, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = side_by_side(f"{SECTOR_NAME}: top {top_k} applicant countries", sharex=True)
    for ax, level in zip(axes, LEVELS):
        d = complete_years(cfg, countries.query("role == 'applicant' and level == @level"))
        wide = d.pivot_table(index="year", columns="ctry", values="n_frac", aggfunc="sum", fill_value=0)
        for ctry in wide.sum().nlargest(top_k).index:
            ax.plot(wide.index, wide[ctry], marker="o", ms=3, label=ctry)
        ax.set(title=UNIT_LABEL[level], xlabel="year", ylabel=f"{UNIT_LABEL[level]} (fractional)")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / f"fig_top_{top_k}_countries_abs.png", dpi=200, bbox_inches="tight")
        
    if show_plots_and_tables:
        plt.show()


def plot_country_bubble_map(cfg, countries, world, show_plots_and_tables, n_labels=8, max_bubble_area=1800):
    SECTOR_NAME = cfg.sector_name
    YEAR_MIN = cfg.year_min
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    OUTPUT_DIR = Path(cfg.output)
    centroids = world.set_index("iso3").geometry.representative_point()

    d = (complete_years(cfg, countries)
         .groupby(["level", "role", "ctry"], as_index=False)["n_frac"].sum())
    d["iso3"] = d["ctry"].map(_iso3)
    d = d[d["iso3"].isin(centroids.index)]
    vmax = d["n_frac"].max()  # wspólna skala dla wszystkich paneli

    roles = (("applicant", "#d62728"), ("inventor", "#1f77b4"))

    fig, axes = plt.subplots(len(LEVELS), len(roles),
                             figsize=(16, 4.5 * len(LEVELS)), squeeze=False)
    fig.suptitle(f"{SECTOR_NAME}: applicant and inventor countries "
                 f"({YEAR_MIN}-{LAST_COMPLETE_YEAR}, fractional counts)")

    for row, level in enumerate(LEVELS):
        for col, (role, color) in enumerate(roles):
            ax = axes[row, col]
            world.plot(ax=ax, color="#eeeeee", edgecolor="white", linewidth=0.4)

            g = (d.query("level == @level and role == @role")
                 .sort_values("n_frac", ascending=False).reset_index(drop=True))
            pts = centroids.loc[g["iso3"]]
            ax.scatter(pts.x, pts.y, s=g["n_frac"] / vmax * max_bubble_area,
                       color=color, alpha=0.6, edgecolor="white", linewidth=0.5)
            for i in range(min(n_labels, len(g))):
                ax.annotate(g.loc[i, "ctry"], (pts.iloc[i].x, pts.iloc[i].y),
                            ha="center", va="center", fontsize=8)

            ax.set_title(f"{role.capitalize()} countries: {UNIT_LABEL[level]}")
            ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_country_bubble_map.png", dpi=200, bbox_inches="tight")
        
    if show_plots_and_tables:
        plt.show()


def calculate_appropriability_table(cfg, profile_df, scope_order, show_plots_and_tables):
    OUTPUT_DIR = Path(cfg.output)
    profile_tab = profile_df.copy()
    profile_tab["pct_share (%)"]  = (profile_tab["n_pct"] / profile_tab["n"]) * 100
    profile_tab["grant_rate (%)"] = (profile_tab["n_granted"] / profile_tab["n"]) * 100
    
    ratio_map = (
        profile_tab.pivot(index="scope", columns="level", values="n")
        .assign(applns_per_family=lambda x: x["application"] / x["family"])["applns_per_family"]
    )
    profile_tab["applns_per_family"] = profile_tab["scope"].map(ratio_map)
    
    rows_order = [(lvl, s) for lvl in LEVELS for s in scope_order]
    
    tab_appropriability = (
        profile_tab.set_index(["level", "scope"])[
            ["n", "n_pct", "pct_share (%)", "n_granted", "grant_rate (%)", "mean_family_size", "applns_per_family"]
        ]
        .loc[rows_order]
        .rename(columns={
            "n": "units (2000-2022)",
            "n_pct": "via PCT",
            "pct_share (%)": "PCT share (%)",
            "n_granted": "granted",
            "grant_rate (%)": "grant rate (%)",
            "mean_family_size": "mean family size",
            "applns_per_family": "applns / family",
        })
    )
    
    tab_appropriability.to_csv(OUTPUT_DIR / "tables" / "tab_appropriability.csv")
    
    tab_appropriability.style.format({
        "units (2000-2022)": "{:,.0f}",
        "via PCT": "{:,.0f}",
        "PCT share (%)": "{:.1f}%",
        "granted": "{:,.0f}",
        "grant rate (%)": "{:.1f}%",
        "mean family size": "{:.2f}",
        "applns / family": "{:.2f}",
    })

    tab_appropriability.to_csv(OUTPUT_DIR / "tables" / "tab_appropriability.csv")
        
    if show_plots_and_tables:
        print(tab_appropriability)


def plot_appropriability_over_time(cfg, approp_yearly, scope_order, show_plots_and_tables):
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    approp_yearly = complete_years(cfg, approp_yearly).copy()
    approp_yearly["pct_share"]  = (approp_yearly["n_pct"] / approp_yearly["n"]) * 100
    approp_yearly["grant_rate"] = (approp_yearly["n_granted"] / approp_yearly["n"]) * 100
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 4.8), sharex=True)
    fig.suptitle(f"{SECTOR_NAME} vs benchmarks: appropriability indicators over time (family level)")
    
    for scope_name in scope_order:
        grp = approp_yearly[approp_yearly["scope"] == scope_name]
        lw = 2.4 if scope_name == SECTOR_NAME else 1.5
        ls = "--" if scope_name == "all patents" else "-"
    
        axes[0].plot(grp["year"], grp["pct_share"], marker="o", ms=2.5, lw=lw, ls=ls, label=scope_name)
        axes[1].plot(grp["year"], grp["mean_family_size"], marker="o", ms=2.5, lw=lw, ls=ls, label=scope_name)
        axes[2].plot(grp["year"], grp["grant_rate"], marker="o", ms=2.5, lw=lw, ls=ls, label=scope_name)
    
    axes[0].set(title="PCT propensity (% of families)", xlabel="earliest_filing_year", ylabel="PCT share")
    axes[0].yaxis.set_major_formatter(PercentFormatter(100))
    
    axes[1].set(title="Geographical breadth (mean family size)", xlabel="earliest_filing_year", ylabel="applications per family")
    
    axes[2].set(title="Grant rate (% of families with >=1 grant)", xlabel="earliest_filing_year", ylabel="grant rate")
    axes[2].yaxis.set_major_formatter(PercentFormatter(100))
    
    for ax in axes:
        shade_truncated(cfg, ax)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(fontsize=8)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figures" / "fig_appropriability.png", dpi=200, bbox_inches="tight")
        
    if show_plots_and_tables:
        plt.show()


def calculate_field_concentration_table(cfg, links, show_plots_and_tables):
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    complete = links[links["year"] <= LAST_COMPLETE_YEAR]
    families_per_applicant = complete.groupby("applicant")["unit_id"].nunique()
    
    pd.Series(field_measures(families_per_applicant.to_numpy()), name=SECTOR_NAME).round(3).to_frame().to_csv(OUTPUT_DIR / "tables" / "tab_field_concentration.csv")
        
    if show_plots_and_tables:
        print(pd.Series(field_measures(families_per_applicant.to_numpy()), name=SECTOR_NAME).round(3).to_frame())


def calculate_share_of_each_years_families_table(cfg, top_applicants, show_plots_and_tables):
    OUTPUT_DIR = Path(cfg.output)
    top_applicants["status"] = np.where(top_applicants["first year in the sector"] < cfg.split_year, "incumbent", "entrant")
    top_applicants = top_applicants.sort_values("families", ascending=False)

    top_applicants.to_csv(OUTPUT_DIR / "tables" / "tab_share_of_each_years_families.csv")
        
    if show_plots_and_tables:
        print(top_applicants)


def calculate_categorised_applicants_table(cfg, links, entry_exit, first_ever, first_year, show_plots_and_tables):
    OUTPUT_DIR = Path(cfg.output)
        
    # share of each year's families with at least one applicant new to the sector
    links_new = links.assign(new=links["year"] == links["applicant"].map(first_year))
    entry_exit["entrants' share of families (%)"] = links_new.groupby(["year", "unit_id"])["new"].any().groupby("year").mean() * 100
    entry_exit = entry_exit.round(1)

    entry_exit.to_csv(OUTPUT_DIR / "tables" / "tab_categorised_applicants.csv")

    if show_plots_and_tables:
        print(entry_exit)


def plot_applicants_active_entry_exit(cfg, entry_exit, show_plots_and_tables):
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    YEAR_MAX = cfg.year_max
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    entry_exit[["active_applicants", "new_to_the_sector", "new_to_patenting"]].plot(ax=axes[0], marker="o", ms=3)
    axes[0].set(title="applicants per year", xlabel="year")
    entry_exit[["entrants' share of families (%)", "rate of disappearance (%)"]].plot(ax=axes[1], marker="o", ms=3)
    axes[1].set(title="entry and exit", xlabel="year", ylim=(0, 100))
    axes[1].yaxis.set_major_formatter(PercentFormatter(100))
    for ax in axes:
        ax.axvspan(LAST_COMPLETE_YEAR + 0.5, YEAR_MAX + 0.5, color="grey", alpha=0.15)   # incomplete years
    fig.suptitle(f"{SECTOR_NAME}: entry and exit")
    plt.tight_layout()
    
    fig.savefig(OUTPUT_DIR / "figures" / "fig_applicants_active_entry_exit.png", bbox_inches="tight")

    if show_plots_and_tables:
        plt.show()


def calculate_incumbents_and_entrants_table(cfg, top_applicants, entry_exit, show_plots_and_tables):
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    OUTPUT_DIR = Path(cfg.output)
    top_num = 30
    top = top_applicants.sort_values("families", ascending=False).head(top_num)
    incumbents = top[top["status"] == "incumbent"].index.tolist()
    entrants = top[top["status"] == "entrant"].index.tolist()
    recent_entry = entry_exit.loc[LAST_COMPLETE_YEAR - 4:LAST_COMPLETE_YEAR, "entrants' share of families (%)"].mean()
    
    results = pd.DataFrame({
        "metric": [
            f"Incumbents among the {top_num} largest applicants",
            f"Entrants among the {top_num} largest applicants",
            "Largest incumbents",
            f"Largest entrants (first family from {cfg.split_year})",
            "Average entrants' share of families in the last five complete years (%)"
        ],
        "value": [
            len(incumbents),
            len(entrants),
            ", ".join(incumbents[:3]) or "none",
            ", ".join(entrants[:3]) or "none",
            f"{recent_entry:.0f}%"
        ]
    })

    results.to_csv(OUTPUT_DIR / "tables" / "tab_incumbents_and_entrants.csv", index=False)

    if show_plots_and_tables:
        print(results)


def calculate_growth_between_periods_table(cfg, family_cpc, RECENT, PAST, show_plots_and_tables):
    """Calculates growth between periods table and returns subfields to be used in other functions.
    """    
    SECTOR_CPC_PREFIXES = cfg.cpc_prefixes
    OUTPUT_DIR = Path(cfg.output)
    
    def subfield(cpc):
        "CPC group with the first two digits after the slash: H01M8/1004 -> H01M8/10."
        main_group, subgroup = cpc.split("/")
        return f"{main_group}/{subgroup[:2]}"
    
    
    in_sector = family_cpc[family_cpc["cpc"].str.startswith(tuple(SECTOR_CPC_PREFIXES))].copy()
    in_sector["subfield"] = in_sector["cpc"].map(subfield)
    in_sector = in_sector.drop_duplicates(["unit_id", "subfield"])
    
    past = in_sector[in_sector["year"].between(*PAST)].groupby("subfield")["unit_id"].nunique()
    recent = in_sector[in_sector["year"].between(*RECENT)].groupby("subfield")["unit_id"].nunique()
    subfields = pd.DataFrame({f"families {PAST[0]}-{PAST[1]}": past, f"families {RECENT[0]}-{RECENT[1]}": recent}).fillna(0)
    subfields["growth (%)"] = (subfields.iloc[:, 1] / subfields.iloc[:, 0] - 1) * 100
    subfields = subfields.sort_values(subfields.columns[1], ascending=False)
    subfields = subfields.round(1)

    subfields.to_csv(OUTPUT_DIR / "tables" / "tab_growth_between_periods.csv")

    if show_plots_and_tables:
        print(subfields)

    return subfields


def plot_subfield_growth(cfg, subfields, RECENT, PAST, show_plots_and_tables):
    """Plots subfield growth and returns plot to be used in other functions.
    """
    SECTOR_NAME = cfg.sector_name
    OUTPUT_DIR = Path(cfg.output)
    plot = subfields[subfields.iloc[:, 0] > 0]                   # growth is defined only if the subfield existed before
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(plot.iloc[:, 1], plot["growth (%)"], s=80, alpha=0.6)
    for name, row in plot.iterrows():
        ax.annotate(name, (row.iloc[1], row["growth (%)"]), xytext=(5, 4), textcoords="offset points", fontsize=9)
    ax.axhline(0, color="grey", lw=0.8)
    ax.set(title=f"{SECTOR_NAME}: subfield growth map", xlabel=f"families {RECENT[0]}-{RECENT[1]} (size today)",
           ylabel=f"growth vs {PAST[0]}-{PAST[1]}")
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    
    fig.savefig(OUTPUT_DIR / "figures" / "fig_subfield_growth.png", bbox_inches="tight")

    if show_plots_and_tables:
        plt.show()

    return plot


def calculate_fastest_growers_table(cfg, plot, RECENT, PAST, show_plots_and_tables):
    OUTPUT_DIR = Path(cfg.output)
    # fastest-growing subfields, among those at least as large as the median subfield today
    size_today = plot.iloc[:, 1]
    fastest = plot[size_today >= size_today.median()].sort_values("growth (%)", ascending=False).head(3)
    
    results = fastest[["growth (%)"]].copy()
    results = results.reset_index()
    results.columns = ["subfield", "growth (%)"]

    results["growth (%)"] = results["growth (%)"].map(lambda x: f"{x:+.0f}%")

    results["description"] = (
        f"Growth of families from {PAST[0]}-{PAST[1]} to {RECENT[0]}-{RECENT[1]}, "
        "among the subfields at least as large as the median one. "
        "Check the titles of these CPC groups in the CPC scheme."
    )

    results.to_csv(OUTPUT_DIR / "tables" / "tab_fastest_growers.csv", index=False)

    if show_plots_and_tables:
        print(results)


# --------------------------------------------------------------------------- #
# analysis functions
# --------------------------------------------------------------------------- #


def analyse_volume(cfg, patstat, db, scopes, sector_ids, show_plots_and_tables):
    """Conducts an analysis of the volume. 
    1. volume per year
    2. same patents dated in different ways
    3. growth table
    4. sector growth percentage in comparison to all patents
    5. volume by code block
    6. TODO sector share of all patents"""
    SECTOR_NAME = cfg.sector_name
    YEAR_MIN = cfg.year_min
    LAST_COMPLETE_YEAR = cfg.last_complete_year
    sector_scopes = [s for s in scopes if s.name == SECTOR_NAME]  # family first, then application
    start, end = YEAR_MIN, LAST_COMPLETE_YEAR

    volume = cached(
        cfg,
        "volume",
        lambda: pd.concat(
            [count_per_year(patstat, db, s).assign(series="all") for s in scopes]
            + [count_per_year(patstat, db, s, only_pct=True).assign(series="via PCT") for s in scopes],
            ignore_index=True,
        ),
    )
    dating = cached(cfg, "dating", lambda: _dating_series(cfg, patstat, db, sector_ids, volume))
    totals = volume.query("series == 'all'").pivot_table(index="year", columns=["level", "scope"], values="n")
    growth_path = (totals.loc[start:end] / totals.loc[start] - 1) * 100
    blocks = cached(cfg, "blocks", lambda: pd.concat([block_series(cfg, patstat, db, p).assign(block=name) for name, p in BLOCKS.items()], ignore_index=True))
    share = (totals.loc[YEAR_MIN:LAST_COMPLETE_YEAR])

    # 1
    plot_volume_per_year(cfg, volume, sector_scopes, show_plots_and_tables)

    # 2
    plot_patents_dated_in_different_ways(cfg, dating, show_plots_and_tables)

    # 3
    calculate_growth(cfg, volume, totals, show_plots_and_tables)

    # 4
    plot_sector_growth_percentage(cfg, growth_path, show_plots_and_tables)

    # 5
    plot_volume_by_code_block(cfg, blocks, show_plots_and_tables)

    # 6
    plot_sector_share_of_all_patents(cfg, share, show_plots_and_tables)


def analyse_technology_mix(cfg, patstat, db, scopes, show_plots_and_tables):
    """Conducts the analysis of technology mix. 
    1. CPC subclasses
    2. WIPO technology fields and split across sectors"""
    SECTOR_NAME = cfg.sector_name
    sector_scopes = [s for s in scopes if s.name == SECTOR_NAME]

    # 1
    plot_and_calculate_cpc_subclasses(cfg, patstat, db, sector_scopes, show_plots_and_tables)

    # 2
    plot_and_calculate_wipo_technology_mix(cfg, patstat, db, sector_scopes, show_plots_and_tables)


def analyse_geography(cfg, patstat, db, scopes, show_plots_and_tables):
    """Conducts the analysis of geography.
    1. shares of the sector's applications
    2. fillings at the IP5 offices per year
    3. applicant and inventor countries without unknown
    4. applicant and inventor countries with unknown
    5. applicant countries share over time
    6. top k applicant countries absolute over time
    7. map of applicant countries
    """
    SECTOR_NAME = cfg.sector_name
    IP5_OFFICES = cfg.ip5_offices
    sector_scopes = [s for s in scopes if s.name == SECTOR_NAME]
    
    offices = cached(
        cfg, 
        "offices",
        lambda: pd.concat([count_by_office(cfg, patstat, db, s) for s in sector_scopes], ignore_index=True),
    )
    offices["office"] = offices["office"].where(offices["office"].isin(IP5_OFFICES + ("WO",)), "Other")
    offices = offices.groupby(["level", "office", "year"], as_index=False)["n"].sum()

    countries_without_unknown = cached(
        cfg, 
        "countries_known_only",
        lambda: pd.concat(
            [fractional_by_country(cfg, patstat, db, s, role) for s in sector_scopes for role in ("applicant", "inventor")],
            ignore_index=True,
        ),
    )
    countries_with_unknown = cached(
        cfg, 
        "countries_with_unknown",
        lambda: pd.concat(
            [fractional_by_country(cfg, patstat, db, s, role, count_unknown=True) for s in sector_scopes for role in ("applicant", "inventor")],
            ignore_index=True,
        ),
    )

    world = cached(cfg, "world_map", lambda: gpd.read_file(WORLD_URL))
    world = world[world["CONTINENT"] != "Antarctica"].to_crs("EPSG:4326")
    world["iso3"] = world["ISO_A3"].where(world["ISO_A3"] != "-99", world["ADM0_A3"])

    # 1
    calculate_shares_of_sector_applications(cfg, offices, show_plots_and_tables)

    # 2
    plot_fillings_at_the_ip5_offices(cfg, offices, show_plots_and_tables)

    # 3
    count_unknown = False
    calculate_investor_and_applicants_countries(cfg, sector_scopes, countries_without_unknown, count_unknown, show_plots_and_tables)

    # 4
    count_unknown = True
    calculate_investor_and_applicants_countries(cfg, sector_scopes, countries_with_unknown, count_unknown, show_plots_and_tables)

    # 5
    plot_applicant_countries_share_over_time(cfg, countries_without_unknown, show_plots_and_tables)

    # 6
    plot_top_k_applicant_countries_over_time(cfg, 5, countries_without_unknown, show_plots_and_tables)

    # 7
    plot_country_bubble_map(cfg, countries_without_unknown, world, show_plots_and_tables)


def anaylse_appropriability(cfg, patstat, db, approp_scopes, family_approp_scopes, show_plots_and_tables):
    """Conducts the analysis of appropriability.
    1. appropriability table
    2. appropriability evolution over time
    """
    SECTOR_NAME = cfg.sector_name
    profile_df = cached(
        cfg,
        "appropriability_profile",
        lambda: pd.concat([scope_profile(cfg, patstat, db, s) for s in approp_scopes], ignore_index=True),
    )
    approp_yearly = cached(
        cfg, 
        "appropriability_yearly",
        lambda: pd.concat([profile_per_year(patstat, db, s) for s in family_approp_scopes], ignore_index=True),
    )

    scope_order = [
        "all patents",
        SECTOR_NAME,
        "Core QC (G06N10)",
        "Quantum Comm (H04L/B)",
        "Machine Learning (G06N20)",
    ]

    # 1
    calculate_appropriability_table(cfg, profile_df, scope_order, show_plots_and_tables)

    # 2
    plot_appropriability_over_time(cfg, approp_yearly, scope_order, show_plots_and_tables)


def analyse_field_concentration(cfg, raw_sector, show_plots_and_tables):
    """Conducts the analysis of field concentration.
    1. Herfindahl index (HH), Numbers-equivalent (1/HH) and 4-firm concentration ratio (CR4) table
    """
    
    links = prepare_applicants(raw_sector)

    # 1
    calculate_field_concentration_table(cfg, links, show_plots_and_tables)

    
def analyse_applicants(cfg, raw_sector, first_patents, show_plots_and_tables):
    """Conducts the analysis of the applicants.
    1. share of each year's families with at least one applicant new to the sector table
    2. share of categorised applicants
    3. applicants active, entry and exit plot
    4. incubents and entrants table
    """
    LAST_COMPLETE_YEAR = cfg.last_complete_year

    links = prepare_applicants(raw_sector)
    by_applicant = links.groupby("applicant")

    psn = raw_sector[["psn_id", "psn_name"]].drop_duplicates().merge(first_patents, on="psn_id")
    psn["applicant"] = psn["psn_name"].map(consolidated_names(psn["psn_name"]))
    first_ever = psn.groupby("applicant")["first_patent_year"].min()

    first_year = by_applicant["year"].min()      # first family of each applicant in the sector
    last_year = by_applicant["year"].max()       # last family of each applicant in the sector

    active = links[["applicant", "year"]].drop_duplicates()
    active["new to the sector"] = active["year"] == active["applicant"].map(first_year)
    active["new to patenting"] = active["year"] == active["applicant"].map(first_ever)
    active["last family"] = active["year"] == active["applicant"].map(last_year)
    
    entry_exit = active.groupby("year").agg(
        active_applicants=("applicant", "count"),
        new_to_the_sector=("new to the sector", "sum"),
        new_to_patenting=("new to patenting", "sum"),
        leaving=("last family", "sum"),
    )
    entry_exit["rate of disappearance (%)"] = entry_exit["leaving"] / entry_exit["active_applicants"] * 100
    entry_exit.loc[entry_exit.index > LAST_COMPLETE_YEAR - 3, "rate of disappearance (%)"] = np.nan

    top_applicants = pd.DataFrame({
        "type": by_applicant["type"].first(),
        "country": by_applicant["ctry"].first(),
        "families": by_applicant["unit_id"].nunique(),
        f"families since {cfg.split_year}": links[links["year"] >= cfg.split_year].groupby("applicant")["unit_id"].nunique(),
        "first year in the sector": by_applicant["year"].min(),
        "last year in the sector": by_applicant["year"].max(),
        "first patent ever": first_ever,
    }).dropna(subset=["families"]).fillna({f"families since {cfg.split_year}": 0})

    # 1
    calculate_share_of_each_years_families_table(cfg, top_applicants, show_plots_and_tables)

    # 2
    calculate_categorised_applicants_table(cfg, links, entry_exit, first_ever, first_year, show_plots_and_tables)

    # 3
    plot_applicants_active_entry_exit(cfg, entry_exit, show_plots_and_tables)

    # 4
    calculate_incumbents_and_entrants_table(cfg, top_applicants, entry_exit, show_plots_and_tables)


def analyse_subfields(cfg, family_cpc, show_plots_and_tables):
    """Conducts an analysis of the subfields.
    1. growth between periods table
    2. subfield growth plot
    3. fastest growers table
    """
    LAST_COMPLETE_YEAR = cfg.last_complete_year

    RECENT = (LAST_COMPLETE_YEAR - 4, LAST_COMPLETE_YEAR)          # the last 5 complete years
    PAST = (RECENT[0] - 5, RECENT[0] - 1)                          # the 5 years before
    
    # 1
    subfields = calculate_growth_between_periods_table(cfg, family_cpc, RECENT, PAST, show_plots_and_tables)

    # 2
    plot = plot_subfield_growth(cfg, subfields, RECENT, PAST, show_plots_and_tables)

    # 3
    calculate_fastest_growers_table(cfg, plot, RECENT, PAST, show_plots_and_tables)



    
# --------------------------------------------------------------------------- #
# main landscape function
# --------------------------------------------------------------------------- #

def landscape_analysis(cfg, patstat, db, scopes, approp_scopes, family_approp_scopes, sector_ids, show_plots_and_tables):
    analyse_volume(cfg, patstat, db, scopes, sector_ids, show_plots_and_tables)
    analyse_technology_mix(cfg, patstat, db, scopes, show_plots_and_tables)
    analyse_geography(cfg, patstat, db, scopes, show_plots_and_tables)
    anaylse_appropriability(cfg, patstat, db, approp_scopes, family_approp_scopes, show_plots_and_tables)


# --------------------------------------------------------------------------- #
# main competitive landscape function
# --------------------------------------------------------------------------- #

def competitive_landscape_analysis(cfg, raw_sector, family_cpc, first_patents, show_plots_and_tables):
    analyse_field_concentration(cfg, raw_sector, show_plots_and_tables)
    analyse_applicants(cfg, raw_sector, first_patents, show_plots_and_tables)
    analyse_subfields(cfg, family_cpc, show_plots_and_tables)