"""Load the sector configuration.

Every parameter that defines the dataset — CPC codes, keywords, the time window,
the counting rules — lives in ``config/sector.yaml``. Nothing in the analysis
hard-codes them. This module is the single place that reads that file.

Usage, from a notebook on TIP or from a script in this folder::

    from stage00_config import load_config      # with src/ on sys.path
    from src.stage00_config import load_config  # from the repository root, as main.py does

    cfg = load_config()
    print(cfg.sector_name, len(cfg.cpc_prefixes), "CPC codes")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# config/sector.yaml, found relative to this file so that the working directory
# does not matter.
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "sector.yaml"


@dataclass(frozen=True)
class SectorConfig:
    """The sector definition, as read from sector.yaml."""

    sector_name: str
    client: str
    team: int

    cpc_core: tuple[str, ...]
    cpc_hardware: tuple[str, ...]
    cpc_communication: tuple[str, ...]
    cpc_legacy: tuple[str, ...]
    cpc_excluded: tuple[str, ...]
    keywords: tuple[str, ...]
    keyword_exclusions: tuple[str, ...]

    year_min: int
    year_max: int
    last_complete_year: int
    family_time_column: str
    appln_time_column: str
    split_year: int

    ipr_type: str
    ip5_offices: tuple[str, ...]
    top_n: int
    env: str

    output: str

    show_plots_and_tables: bool
    do_exploring: bool

    raw: dict = field(repr=False, default_factory=dict)

    @property
    def cpc_prefixes(self) -> tuple[str, ...]:
        """The CPC codes actually used to select the sector.

        Legacy codes are left out: they belong to the pre-2019 scheme, and the
        diagnostic in docs/methodology.md section 7 found that group empty.
        Excluded codes are left out by decision, with the evidence recorded in
        sector.yaml and in docs/methodology.md section 8.
        """
        return self.cpc_core + self.cpc_hardware + self.cpc_communication

    @property
    def cpc_computing_only(self) -> tuple[str, ...]:
        """The sector without the quantum-communication classes.

        Used for the sensitivity analysis that settles the scope boundary
        (docs/methodology.md, section 6).
        """
        return self.cpc_core + self.cpc_hardware


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> SectorConfig:
    """Read sector.yaml and return it as a frozen SectorConfig."""
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    cpc = raw["cpc"]
    time = raw["time"]
    counting = raw["counting"]


    return SectorConfig(
        sector_name=raw["sector"]["name"],
        client=raw["sector"]["client"],
        team=int(raw["sector"]["team"]),
        cpc_core=tuple(cpc["core"]),
        cpc_hardware=tuple(cpc.get("hardware") or ()),
        cpc_communication=tuple(cpc["communication"]),
        cpc_legacy=tuple(cpc.get("legacy", ())),
        cpc_excluded=tuple(cpc.get("excluded", ())),
        keywords=tuple(raw["keywords"]),
        keyword_exclusions=tuple(raw.get("keyword_exclusions") or ()),
        year_min=int(time["year_min"]),
        year_max=int(time["year_max"]),
        last_complete_year=int(time["last_complete_year"]),
        family_time_column=time["family_time_column"],
        appln_time_column=time["appln_time_column"],
        split_year=int(time["split_year"]),
        ipr_type=counting["ipr_type"],
        ip5_offices=tuple(counting["ip5_offices"]),
        top_n=int(counting["top_n"]),
        env=raw["patstat"]["env"],
        raw=raw,
        output=str(raw["output"]['directory']),
        show_plots_and_tables=bool(raw["additions"]["show_plots_and_tables"]),
        do_exploring=bool(raw["additions"]["do_exploring"]),
    )
