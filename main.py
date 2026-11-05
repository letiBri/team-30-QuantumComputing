"""Execute the main pipeline.

Combines all the scripts from 'src' folder and runs the main pipeline.  
"""

from src.stage00_config import load_config
from src.stage01_extract import sector_family_ids, report_query_info
from src.stage02_clean import calculate_scopes, get_family_applicants, get_family_cpc, get_first_patents, cached
from src.stage03_landscape import landscape_analysis, competitive_landscape_analysis
from epo.tipdata.patstat import PatstatClient
from pathlib import Path


def main():
    
    # load config 
    cfg = load_config()
    patstat = PatstatClient(env=cfg.env)
    db = patstat.orm()

    # load variables
    do_exploring = cfg.do_exploring
    show_plots_and_tables = cfg.show_plots_and_tables
    
    QC_CORE_PREFIXES = ("G06N10",)
    Q_COMM_PREFIXES = tuple(p for p in cfg.cpc_prefixes if not p.startswith("G06N10")) or ("H04L9/0852", "H04B10/70")
    ML_COMP_PREFIXES = ("G06N20",)

    # extract
    sector_ids = sector_family_ids(db, cfg)
    qc_core_ids = sector_family_ids(db, cfg, cpc_prefixes=QC_CORE_PREFIXES, keywords=(), exclusions=())
    q_comm_ids  = sector_family_ids(db, cfg, cpc_prefixes=Q_COMM_PREFIXES,  keywords=(), exclusions=())
    ml_comp_ids = sector_family_ids(db, cfg, cpc_prefixes=ML_COMP_PREFIXES, keywords=(), exclusions=())

    report_query_info(patstat, db, cfg)

    # calculate cleaned data
    scopes, approp_scopes, family_approp_scopes = calculate_scopes(cfg, db, sector_ids, qc_core_ids, q_comm_ids, ml_comp_ids)
    families = scopes[1].sq
    raw_sector = cached(cfg, "raw_sector", lambda: get_family_applicants(patstat, db, families))
    family_cpc = cached(cfg, "family_cpc", lambda: get_family_cpc(patstat, db, families))
    first_patents = cached(cfg, "first_patents", lambda: get_first_patents(patstat, db, raw_sector, cfg.year_max))

    # analysis (landscape, competetive landscape, ...)
    if do_exploring:
        landscape_analysis(cfg, patstat, db, scopes, approp_scopes, family_approp_scopes, sector_ids, show_plots_and_tables)
        competitive_landscape_analysis(cfg, raw_sector, family_cpc, first_patents, show_plots_and_tables)
        
if __name__ == "__main__":
    main()