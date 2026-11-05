"""Step 0 — clean and prepare the extracted data

Prepares the data extracted from queries for further analysis.
Contains code from the section 6.1 from the Step 1 notebook.
Provides result storing (cached function).
Provides harmonisation functions.
"""

from dataclasses import dataclass
from sqlalchemy import and_, case, distinct, func, literal, or_
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
import hashlib
from pathlib import Path
import pandas as pd
from rapidfuzz import fuzz
import unicodedata
import re
from cleanco import basename
import numpy as np

# --------------------------------------------------------------------------- #
# config and global variables
# --------------------------------------------------------------------------- #


IS_PCT_APPLN = and_(TLS201_APPLN.appln_auth == "WO", TLS201_APPLN.appln_kind.like("W%"))


# --------------------------------------------------------------------------- #
# harmonisation variables
# --------------------------------------------------------------------------- #


# ---------------------------------------------------------------- link subsidiaries to the brand ("anchor")
GENERIC_ANCHORS = {   # words that must never absorb other names: add the generic words of our sector
    "UNIVERSITY", "INSTITUTE", "NATIONAL", "INTERNATIONAL", "GENERAL", "UNITED", "AMERICAN", "CHINA", "CHINESE",
    "BEIJING", "SHANGHAI", "SHENZHEN", "TECHNOLOGY", "SYSTEMS", "QUANTUM", "SCIENCE", "RESEARCH", "ELECTRONICS",
    "ELECTRIC", "COMPUTING", "SEMICONDUCTOR", "LABORATORY", "CENTER", "FOUNDATION", "GLOBAL", "DIGITAL",
    "ADVANCED", "APPLIED", "FIRST", "SOUTH", "NORTH", "PHOTONIC", "PHOTONICS", "SILICON", "NANO"}

# ---------------------------------------------------------------- typos in legal forms
LONG_LEGAL = ["CORPORATION", "INCORPORATED", "LIMITED", "COMPANY", "AKTIENGESELLSCHAFT", "GESELLSCHAFT", "KABUSHIKI"]

# ---------------------------------------------------------------- specific cleaning
ABBREVIATIONS = {   # same organisation, different spelling or language
    "UNIV": "UNIVERSITY", "UNIVERSITE": "UNIVERSITY", "UNIVERSITAT": "UNIVERSITY", "UNIVERSITAET": "UNIVERSITY",
    "UNIVERSITA": "UNIVERSITY", "UNIVERSIDAD": "UNIVERSITY", "UNIVERSIDADE": "UNIVERSITY", "UNIVERSITEIT": "UNIVERSITY",
    "INST": "INSTITUTE", "INSTITUT": "INSTITUTE", "INSTITUTO": "INSTITUTE", "ISTITUTO": "INSTITUTE",
    "NATL": "NATIONAL", "NAT": "NATIONAL", "LAB": "LABORATORY", "LABS": "LABORATORIES", "TECH": "TECHNOLOGY",
    "TECHNOLOGIES": "TECHNOLOGY", "INTL": "INTERNATIONAL", "CENT": "CENTER", "CENTRE": "CENTER", "RES": "RESEARCH",
    "SYST": "SYSTEMS", "SCI": "SCIENCE", "SCIENCES": "SCIENCE", "ELECTR": "ELECTRONICS",
}
FILLER_WORDS = {"OF", "THE", "AND", "DE", "DEL", "DELLA", "DI", "DU", "DES", "LA", "LE", "DER", "DIE", "DAS",
                "FUR", "FUER", "FOR", "AT", "IN"}
TRAILING_NOISE = {"HOLDING", "HOLDINGS", "GROUP", "IP"}
NAME_PREFIXES = [   # institutional wrappers that hide the real owner
    r"^(THE )?BOARD OF TRUSTEES OF (THE )?", r"^(THE )?BOARD OF REGENTS( OF)?( THE)? ", r"^(THE )?REGENTS OF (THE )?",
    r"^(THE )?TRUSTEES OF (THE )?", r"^PRESIDENT AND FELLOWS OF ", r"^THE GOVERNING COUNCIL OF (THE )?",
    r"^UNITED STATES OF AMERICA AS REPRESENTED BY (THE )?", r"^(THE )?GOVERNMENT OF ",
]

ORG_WORDS = {"TECHNOLOGY", "SYSTEMS", "QUANTUM", "COMPUTING", "LABORATORY", "LABORATORIES", "SOLUTIONS",
             "SEMICONDUCTOR", "ELECTRONICS", "SOFTWARE", "DEVICES", "NETWORKS", "INDUSTRIES", "ENERGY",
             "RESEARCH", "SCIENCE", "COMMUNICATIONS", "MICRO", "DIGITAL", "DATA"}
ACADEMIC_WORDS = {"UNIVERSITY", "COLLEGE", "ACADEMY", "FACULTY", "SCHOOL", "POLYTECHNIC"}
GOV_WORDS = {"INSTITUTE", "NATIONAL", "CENTER", "MINISTRY", "COMMISSARIAT", "FOUNDATION", "COUNCIL",
             "GOVERNMENT", "LABORATORY", "DEPARTMENT"}

# Legal-form words to remove (extend the set for the countries of your sector)
LEGAL_FORMS = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD", "LIMITED", "LLC", "LP", "PLC",
    "GMBH", "AG", "KG", "MBH", "SE", "SA", "SAS", "SPA", "SRL", "BV", "NV", "AB", "AS", "ASA", "OY", "OYJ",
    "KK", "KABUSHIKI", "KAISHA", "LTDA", "PTY", "THE", "AKTIENGESELLSCHAFT", "GESELLSCHAFT",
    "GCV", "CV", "SARL", "SRO", "PTE", "BHD", "OOO", "ZAO", "OAO", "PJSC", "JSC", "LLP", "ULC", "UG", "SL"}

# Manual aliases for the big players of the sector, modified after testing: (regex on the cleaned name, canonical name)
ORG_ALIASES = [
    (r"^INTERNATIONAL BUSINESS MACHINES|^IBM\b",       "IBM"),
    (r"^GOOGLE\b",                                     "GOOGLE"),
    (r"^MICROSOFT\b",                                  "MICROSOFT"),
    (r"^D WAVE\b|^DWAVE\b",                            "D-WAVE SYSTEMS"),
    (r"^HEWLETT PACKARD|^HP HEWLETT PACKARD",          "HEWLETT PACKARD"), # added 'HP HEWLETT PACKARD' after testing
    (r"^NIPPON TELEGRAPH|^NTT\b",                      "NTT"),
    (r"^ORIGIN QUANTUM",                               "ORIGIN QUANTUM"),
    (r"^CENTER NATIONAL RECHERCHE|^CENTRE NATIONAL RECHERCHE|CNRS", "CNRS"),
    (r"^COMMISSARIAT ENERGIE ATOMIQUE",                "CEA"),
    (r"^ELECTRONIC SCIENCE RESEARCH INSTITUTE",         "ELECTRONIC SCIENCE RESEARCH INSTITUTE CHINA"),
    (r"^INFORMATION SCIENCE ACADEMY",                  "INFORMATION SCIENCE ACADEMY CHINA"),
    (r"^BEIJING BAIDU NETCOM|^BAIDU\b",                "BAIDU"),
    (r"^SGCC\b|^STATE GRID CORPORATION|^STATE GRID CORP",  "STATE GRID CORPORATION OF CHINA"),
    (r"^MIT\b|^MASSACHUSETTS INSTITUTE TECHNOLOGY",        "MIT"),
    (r"^ETRI\b|^ELECTRONICS TELECOMMUNICATIONS RESEARCH INSTITUTE", "ETRI"),
    (r"^HUAWEI",                                       "HUAWEI"),
    (r"^QUANTUMCTEK|^QUANTUM CTEK|^GUO SHIELD|^GUODUN|^SHANGHAI QUANTUMCTEK", "QUANTUMCTEK"), # added  'GUO SHIELD', 'GUODUN' , 'SHANGHAI QUANTUMCTEK' after testing
    (r"^RIGETTI",                                      "RIGETTI"),
    (r"^QUANTINUUM",                                   "QUANTINUUM"),
    (r"^IONQ",                                         "IONQ"),
    (r"^INTEL\b",                                      "INTEL"),
    (r"^TOSHIBA\b",                                    "TOSHIBA"),
    (r"^UNIVERSITY OXFORD\b",                          "UNIVERSITY OXFORD"),
    # new aliases added after testing
    (r"^HONEYWELL",                                    "HONEYWELL"),
    (r"^ATOM COMPUTING|^ATOMIC COMPUTING",             "ATOM COMPUTING"),
    (r"^UNIVERSITY SHANGHAI JIAO TONG|^SHANGHAI JIAO TONGUNIVERSITY", "UNIVERSITY SHANGHAI JIAO TONG"),
]

_ORG = [(re.compile(p), c) for p, c in ORG_ALIASES]


# --------------------------------------------------------------------------- #
# Scope class
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Scope:
    name: str     # "all patents" or the sector name
    level: str    # "family" or "application"
    sq: object    # SQLAlchemy subquery, one row per unit


# --------------------------------------------------------------------------- #
# Cached function
# --------------------------------------------------------------------------- #


def cached(cfg, name, build, force=False):
    """Compute build() once, then serve it from disk. Pass force=True to recompute."""
    DEFINITION_ID = hashlib.sha1(
        repr((cfg.cpc_prefixes, cfg.keywords, cfg.keyword_exclusions)).encode()
    ).hexdigest()[:8]
    OUTPUT_DIR = Path(cfg.output)
    path = OUTPUT_DIR / "cache" / f"{name}_{DEFINITION_ID}.pkl" 
    if path.exists() and not force:
        df = pd.read_pickle(path)
        print(f"[cache] {name:<22} {len(df):>8,} rows")
        return df
    df = build()
    df.to_pickle(path)
    print(f"[query] {name:<22} {len(df):>8,} rows")
    return df


# --------------------------------------------------------------------------- #
# cleaning functions
# --------------------------------------------------------------------------- #

def _restrict(q, family_ids):
    """Keep only the families in family_ids (None = all patents)."""
    if family_ids is None:
        return q
    return q.filter(TLS201_APPLN.docdb_family_id.in_(family_ids.subquery().select()))


def family_scope(cfg, db, family_ids=None):
    """Family level: one row per DOCDB family, dated by its earliest priority year."""
    year = func.min(getattr(TLS201_APPLN, cfg.family_time_column))
    q = db.query(
        TLS201_APPLN.docdb_family_id.label("unit_id"),
        year.label("year"),
        func.max(case((IS_PCT_APPLN, 1), else_=0)).label("is_pct"),
        func.max(case((TLS201_APPLN.granted == "Y", 1), else_=0)).label("is_granted"),
        func.max(TLS201_APPLN.docdb_family_size).label("family_size"),
    ).filter(TLS201_APPLN.ipr_type == cfg.ipr_type)
    return (
        _restrict(q, family_ids)
        .group_by(TLS201_APPLN.docdb_family_id)
        .having(year.between(cfg.year_min, cfg.year_max))
        .subquery()
    )


def application_scope(cfg, db, family_ids=None, time_column=None):
    """Application level: one row per appln_id, dated by its own time_column."""
    time_column = cfg.appln_time_column if time_column is None else time_column
    year = getattr(TLS201_APPLN, time_column)
    q = db.query(
        TLS201_APPLN.appln_id.label("unit_id"),
        year.label("year"),
        case((IS_PCT_APPLN, 1), else_=0).label("is_pct"),
        case((TLS201_APPLN.granted == "Y", 1), else_=0).label("is_granted"),
        TLS201_APPLN.docdb_family_size.label("family_size"),
    ).filter(TLS201_APPLN.ipr_type == cfg.ipr_type, year.between(cfg.year_min, cfg.year_max))
    return _restrict(q, family_ids).subquery()


def get_family_applicants(patstat, db, families):
    """Extracts the applicants of a family. Returns a dataframe.
    """
    q_sector = (
        db.query(families.c.unit_id, families.c.year, TLS206_PERSON.psn_id, TLS206_PERSON.psn_name,
                 TLS206_PERSON.psn_sector, func.trim(TLS206_PERSON.person_ctry_code).label("ctry"))
        .select_from(families)
        .join(TLS201_APPLN, TLS201_APPLN.docdb_family_id == families.c.unit_id)
        .join(TLS207_PERS_APPLN, TLS207_PERS_APPLN.appln_id == TLS201_APPLN.appln_id)
        .join(TLS206_PERSON, TLS206_PERSON.person_id == TLS207_PERS_APPLN.person_id)
        .filter(TLS207_PERS_APPLN.applt_seq_nr > 0)
        .distinct()
    )

    return patstat.df(q_sector)


def get_family_cpc(patstat, db, families):
    """Extracts the cpcs of a family. Returns a dataframe.
    """
    q_cpc = (
        db.query(
            families.c.unit_id,
            families.c.year,
            func.replace(TLS224_APPLN_CPC.cpc_class_symbol, " ", "").label("cpc")
        )
        .select_from(families)
        .join(TLS201_APPLN, TLS201_APPLN.docdb_family_id == families.c.unit_id)
        .join(TLS224_APPLN_CPC, TLS224_APPLN_CPC.appln_id == TLS201_APPLN.appln_id)
        .distinct()
    )

    return patstat.df(q_cpc)


def get_first_patents(patstat, db, raw_sector, year_max, chunk=5000):
    psn_ids = [int(i) for i in raw_sector["psn_id"].unique()]
    
    parts = []
    for i in range(0, len(psn_ids), chunk):
        q = (
            db.query(TLS206_PERSON.psn_id,
                     func.min(TLS201_APPLN.earliest_filing_year).label("first_patent_year"))
            .join(TLS207_PERS_APPLN, TLS207_PERS_APPLN.person_id == TLS206_PERSON.person_id)
            .join(TLS201_APPLN, TLS201_APPLN.appln_id == TLS207_PERS_APPLN.appln_id)
            .filter(TLS206_PERSON.psn_id.in_(psn_ids[i:i + chunk]),
                    TLS207_PERS_APPLN.applt_seq_nr > 0,
                    TLS201_APPLN.earliest_filing_year.between(1900, year_max))
            .group_by(TLS206_PERSON.psn_id)
        )
        parts.append(patstat.df(q))
    return pd.concat(parts, ignore_index=True)


# --------------------------------------------------------------------------- #
# harmonisation functions
# --------------------------------------------------------------------------- #
    

def clean_with_dictionary(name):
    "Upper-case, keep letters and digits only, and drop legal-form words at the start and at the end."
    words = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper()).split()
    while words and words[-1] in LEGAL_FORMS:      # e.g. "TOYOTA JIDOSHA KABUSHIKI KAISHA" -> "TOYOTA JIDOSHA"
        words.pop()
    while words and words[0] in LEGAL_FORMS:       # e.g. "KABUSHIKI KAISHA TOSHIBA" -> "TOSHIBA"
        words.pop(0)
    return " ".join(words)

def clean_with_cleanco(name):
    "Remove legal forms with cleanco, then apply the same upper-case cleaning as method A."
    return clean_with_dictionary(basename(str(name)))


def link_subsidiaries(mapping, skip=frozenset(), min_len=5):
    """{name: harmonised} -> {name: harmonised or its anchor}. A name that starts, as whole words, with another
    harmonised name of the list is linked to it: NOKIA ALUMIINI -> NOKIA. NOKIAN TYRES stays apart.
    Never anchors: universities (NANJING UNIVERSITY != NANJING UNIVERSITY OF POSTS), individuals,
    and names made only of generic words (QUANTUM TECHNOLOGY)."""
    anchors = {v for v in set(mapping.values())
               if v and len(v) >= min_len and v not in skip
               and not v.startswith("UNIVERSITY")
               and not all(w in GENERIC_ANCHORS for w in v.split())}
    def link(v):
        words = v.split()
        for k in range(1, len(words)):                 # shortest prefix first = the brand
            prefix = " ".join(words[:k])
            if prefix in anchors:
                return prefix
        return v
    return {n: link(v) for n, v in mapping.items()}


def strip_misspelled_legal_forms(name):
    "Drop a final word that is a typo of a long legal form (COPPORATION, CORPAORATION...)."
    words = name.split()
    while len(words) > 1 and any(abs(len(words[-1]) - len(f)) <= 1 and fuzz.ratio(words[-1], f) >= 85
                                 for f in LONG_LEGAL):
        words.pop()
    return " ".join(words)


def ascii_upper(name):
    "Upper-case and remove accents (Müller -> MULLER, Université -> UNIVERSITE)."
    s = str(name).replace("ß", "ss").replace("Ø", "O").replace("ø", "o").replace("Æ", "AE").replace("æ", "ae")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.upper().replace("&", " AND ")


def specific_cleaning(name):
    "Brackets, wrappers, abbreviations, filler words, trailing noise, word order of universities."
    s = ascii_upper(name)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = " ".join(s.split())
    for p in NAME_PREFIXES:
        s = re.sub(p, "", s)
    words = [ABBREVIATIONS.get(w, w) for w in s.split()]
    words = [w for w in words if w not in FILLER_WORDS]
    while words and words[-1] in TRAILING_NOISE:
        words.pop()
    if "UNIVERSITY" in words:                                  # OXFORD UNIVERSITY == UNIVERSITY OF OXFORD
        words = ["UNIVERSITY"] + [w for w in words if w != "UNIVERSITY"]
    return " ".join(words)


def my_harmonisation(name, use_aliases=True):
    "A (dictionary) + B (cleanco) + specific cleaning + manual aliases of the sector's big players."
    if name is None or str(name).strip() in ("", "nan", "None"):
        return ""
    base = clean_with_cleanco(ascii_upper(name))   # apply method B and then method A
    base = specific_cleaning(base)                 # add specific cleaning
    base = clean_with_dictionary(base)             # apply again method A
    base = strip_misspelled_legal_forms(base)      # remove typo
    if use_aliases:
        for rx, canon in _ORG:
            if rx.search(base):
                return canon
    return base

def applicant_type(psn_sector, raw_name=""):
    "Type from psn_sector; when it is empty, infer it from the name."
    s = str(psn_sector).upper()
    if "UNIVERSITY" in s or any(t in s for t in ["ACADEMY", "COLLEGE", "FACULTY"]): return "university"
    if "HOSPITAL" in s: return "hospital"
    if any(t in s for t in ["GOV", "MINISTRY", "LABORATORY", "PUBLIC", "RESEARCH INSTITUTE"]): return "government / non-profit"
    if "INDIVIDUAL" in s: return "individual"
    if "COMPANY" in s or "FIRM" in s: return "firm"
    # psn_sector missing: guess from the name
    words = set(re.sub(r"[^A-Z0-9 ]", " ", ascii_upper(raw_name)).split())
    if words & ACADEMIC_WORDS: return "university"
    if words & GOV_WORDS: return "government / non-profit"
    if words & (LEGAL_FORMS - {"THE", "CO"}) or words & ORG_WORDS: return "firm"
    if 2 <= len(words) <= 4: return "individual"      # "HOU XIAOYAN", "ROSE GEORDIE"
    return "unknown"

def build_name_map(raw, use_aliases=True, link=True):
    "{PATSTAT name: applicant}: A + B + specific cleaning + aliases, then subsidiaries linked to the brand."
    names = raw.dropna(subset=["psn_name"])
    names = names[names["psn_name"].str.strip() != ""]
    base_map = {n: my_harmonisation(n, use_aliases) for n in sorted(names["psn_name"].unique())}
    if not link:
        return base_map
    is_indiv = np.array([applicant_type(s, n) == "individual"
                         for s, n in zip(names["psn_sector"], names["psn_name"])])
    indiv = {base_map[n] for n in names.loc[is_indiv, "psn_name"].unique()} # individuals never absorb other names
    return link_subsidiaries(base_map, skip=indiv)


# --------------------------------------------------------------------------- #
# main cleaning functions
# --------------------------------------------------------------------------- #


def calculate_scopes(cfg, db, sector_ids, qc_core_ids, q_comm_ids, ml_comp_ids):
    """Calculates scopes needed to execute pipeline.
    Add more scopes to return if any more scopes required in the future
    """

    scopes = [
        Scope("all patents", "family",      family_scope(cfg, db)),
        Scope(cfg.sector_name,   "family",      family_scope(cfg, db, sector_ids)),
        Scope("all patents", "application", application_scope(cfg, db)),
        Scope(cfg.sector_name,   "application", application_scope(cfg, db, sector_ids)),
    ]

    approp_scopes = scopes + [
        Scope("Core QC (G06N10)",          "family",      family_scope(cfg, db, qc_core_ids)),
        Scope("Core QC (G06N10)",          "application", application_scope(cfg, db, qc_core_ids)),
        Scope("Quantum Comm (H04L/B)",     "family",      family_scope(cfg, db, q_comm_ids)),
        Scope("Quantum Comm (H04L/B)",     "application", application_scope(cfg, db, q_comm_ids)),
        Scope("Machine Learning (G06N20)", "family",      family_scope(cfg, db, ml_comp_ids)),
        Scope("Machine Learning (G06N20)", "application", application_scope(cfg, db, ml_comp_ids)),
    ]

    family_approp_scopes = [s for s in approp_scopes if s.level == "family"]

    return scopes, approp_scopes, family_approp_scopes


# --------------------------------------------------------------------------- #
# main harmonisation functions
# --------------------------------------------------------------------------- #


def consolidated_names(psn_names, use_aliases=True):
    "Dictionary {PATSTAT name: consolidated name}."
    return {n: my_harmonisation(n, use_aliases) for n in sorted(set(psn_names))}


def prepare_applicants(raw, use_aliases=True, link=True):
    "From (unit_id, year, person) rows to one row per (unit_id, applicant) with type and country."
    df = raw.copy()
    df = df.dropna(subset=["psn_name"])
    df = df[df["psn_name"].str.strip() != ""]

    # 1. consolidated name
    df["applicant"] = df["psn_name"].map(build_name_map(df, use_aliases, link))
    df = df[df["applicant"].str.strip() != ""]

    # 2. type: from psn_sector or from the name, then the most frequent type of each applicant
    df["type"] = [applicant_type(s, n) for s, n in zip(df["psn_sector"], df["psn_name"])]
    known_t = df[df["type"] != "unknown"]
    if not known_t.empty:
        main_type = known_t.groupby("applicant")["type"].agg(lambda t: t.value_counts().index[0])
        df["type"] = df["applicant"].map(main_type).fillna("unknown")

    # 3. one country per applicant: the most frequent known one
    df["ctry"] = df["ctry"].replace("", np.nan)
    known = df.dropna(subset=["ctry"]).drop_duplicates(["unit_id", "applicant", "ctry"])
    if not known.empty:
        main_c = known.groupby("applicant")["ctry"].agg(lambda c: c.value_counts().index[0])
        df["ctry"] = df["applicant"].map(main_c)

    # 4. one row per (patent, applicant)
    return df[["unit_id", "year", "applicant", "type", "ctry"]].drop_duplicates(["unit_id", "applicant"])