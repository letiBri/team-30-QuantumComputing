"""Step 0 — select the sector from PATSTAT.

Builds the query that defines the sector and reports how much each branch of the
definition contributes. This is the refactored form of what the Step 1 notebook
does in its section 2.1, with the codes and keywords read from
``config/sector.yaml`` rather than written into the code.

Runs only inside the EPO Technology Intelligence Platform, which supplies the
``epo.tipdata`` client and authenticated access to PATSTAT::

    python main.py

Expect a few minutes on PROD: the keyword branch scans titles and abstracts
across the whole database.
"""

from __future__ import annotations

from sqlalchemy import and_, distinct, func, not_, or_

from epo.tipdata.patstat import PatstatClient
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN,
    TLS202_APPLN_TITLE,
    TLS203_APPLN_ABSTR,
    TLS224_APPLN_CPC,
)


# --------------------------------------------------------------------------- #
# Query building blocks
# --------------------------------------------------------------------------- #

def symbol_prefix_condition(symbol_column, codes):
    """OR-condition: the blank-stripped classification symbol starts with a code.

    PATSTAT pads CPC symbols to a fixed width (``F03B  13/14``), so blanks are
    removed on both sides before comparing. Matching is a string prefix, not a
    hierarchy walk — see docs/methodology.md, section 5.
    """
    symbol = func.replace(symbol_column, " ", "")
    return or_(*(symbol.like(code.replace(" ", "") + "%") for code in codes))


def keyword_condition(terms, exclusions=()):
    """Any term appears in the title or abstract, and no exclusion phrase does.

    Case-insensitive. A missing title or abstract is read as empty text: without
    the COALESCE, NOT applied to a NULL comparison is NULL, and SQL would drop the
    application silently instead of keeping it.
    """
    title = func.lower(func.coalesce(TLS202_APPLN_TITLE.appln_title, ""))
    abstract = func.lower(func.coalesce(TLS203_APPLN_ABSTR.appln_abstract, ""))
    match = or_(*(col.like(f"%{t.lower()}%") for t in terms for col in (title, abstract)))
    if not exclusions:
        return match
    excluded = or_(*(col.like(f"%{x.lower()}%") for x in exclusions for col in (title, abstract)))
    return and_(match, not_(excluded))


def families_by_cpc(db, prefixes):
    """Families with at least one application carrying one of the CPC prefixes."""
    return (
        db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
        .join(TLS224_APPLN_CPC, TLS201_APPLN.appln_id == TLS224_APPLN_CPC.appln_id)
        .filter(symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, prefixes))
    )


def families_by_keywords(db, terms, exclusions=()):
    """Families with at least one application matching a keyword in title or abstract,
    that application carrying none of the exclusion phrases."""
    return (
        db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
        .outerjoin(TLS202_APPLN_TITLE, TLS201_APPLN.appln_id == TLS202_APPLN_TITLE.appln_id)
        .outerjoin(TLS203_APPLN_ABSTR, TLS201_APPLN.appln_id == TLS203_APPLN_ABSTR.appln_id)
        .filter(keyword_condition(terms, exclusions))
    )


def sector_family_ids(db, cfg, cpc_prefixes=None, keywords=None, exclusions=None):
    """Query of the docdb_family_ids that belong to the sector (CPC codes OR keywords).
    Default values come from cfg, arguments optionally overwrite them.
    UNION removes duplicates, so a family caught by both branches counts once.
    """
    cpc_prefixes = cfg.cpc_prefixes if cpc_prefixes is None else cpc_prefixes
    keywords     = cfg.keywords if keywords is None else keywords
    exclusions   = cfg.keyword_exclusions if exclusions is None else exclusions

    family_id = TLS201_APPLN.docdb_family_id.label("docdb_family_id")
    by_cpc = (
        db.query(family_id)
        .join(TLS224_APPLN_CPC, TLS201_APPLN.appln_id == TLS224_APPLN_CPC.appln_id)
        .filter(symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, cpc_prefixes))
    )
    if not keywords:
        return by_cpc.distinct()
    by_keywords = (
        db.query(family_id)
        .outerjoin(TLS202_APPLN_TITLE, TLS201_APPLN.appln_id == TLS202_APPLN_TITLE.appln_id)
        .outerjoin(TLS203_APPLN_ABSTR, TLS201_APPLN.appln_id == TLS203_APPLN_ABSTR.appln_id)
        .filter(keyword_condition(keywords, exclusions))
    )
    return by_cpc.union(by_keywords)


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def count_families(patstat, db, query, label):
    """Execute a family-id query and report how many distinct families it returns."""
    sq = query.distinct().subquery()
    n = patstat.df(
        db.query(func.count(distinct(sq.c.docdb_family_id)).label("n"))
    ).loc[0, "n"]
    print(f"{label:<28} {n:>12,}")
    return int(n)


def report_query_info(patstat, db, cfg):
    """Print info about number of families extracted by cpc, keywords and the union.
    """
    print("-" * 42)
    print(f"{cfg.sector_name} | env: {cfg.env} | {cfg.year_min}-{cfg.year_max}")
    print("-" * 42)
    
    n_cpc = count_families(patstat, db, families_by_cpc(db, cfg.cpc_prefixes), "CPC branch")
    n_kw = count_families(patstat, db, families_by_keywords(db, cfg.keywords, cfg.keyword_exclusions),
                          "Keyword branch")
    n_union = count_families(patstat, db, sector_family_ids(db, cfg), "UNION (the sector)")

    keyword_only = n_union - n_cpc
    overlap = n_kw - keyword_only

    print("-" * 42)
    print(f"{'keyword-only families':<28} {keyword_only:>12,}  ({keyword_only / n_union:.1%} of sector)")
    print(f"{'confirmed by both':<28} {overlap:>12,}  ({overlap / n_kw:.1%} of keyword branch)")
    print("-" * 42)
