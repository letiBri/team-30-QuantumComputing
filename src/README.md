# src/

The pipeline, as it is lifted out of the notebooks.

The project brief asks for a repository that reproduces the analysis end to end,
from the sector query to the Magic Quadrant, with configuration kept out of the
code. We are refactoring towards that shape as each step stabilises, rather than
writing modules for analysis we have not yet done.

## What is here

| File | Does | State |
|---|---|---|
| `stage00_config.py` | Reads `config/sector.yaml` and exposes it as a frozen object. Runs anywhere. | **Working / done** |
| `stage01_extract.py` | Builds the sector query and reports the contribution of each branch. Runs on TIP. | **Working / done** |
| `stage02_clean.py` | Prepares data obtained from query for the analysis. Harmonisation.| **Working / done** |
| `stage03_landscape.py` | Steps 1–2: volume, growth, technology mix, geography, concentration, entry. Main analysis. Competitive landscape.| **Working / done** |

## What is planned

Following the structure set out in the project brief:

| File | Will do |
|---|---|
| `stage04_present_score.py` | Step 3: influence, volume, success, globalization — the quadrant's vertical axis |
| `stage05_future_score.py` | Step 4: our own forward-looking algorithm |
| `stage06_quadrant.py` | Steps 3–5 figures, including the Magic Quadrant |

Until a step appears above as working, **the notebook is the source of truth for
it**, not a module in this folder. `notebooks/` holds the analysis as actually
run on TIP.

## One refactor worth doing early

`sector_family_ids()` returns a SQLAlchemy *query*, not a result. Every time it
is used to restrict a later query, PATSTAT re-derives the whole union — including
the text scan over titles and abstracts. For Step 1 this is tolerable; by Step 3,
with per-firm indicators, it will not be.

`stage02_clean.py` should execute the union **once**, persist the family ids, and hand
that frozen set to everything downstream. That is also what makes the pipeline
reproducible in the sense the brief asks for: a later step consumes a dataset,
not a query that might resolve differently on a different PATSTAT edition.

`ALT_BASE_YEAR` is defined manually but can be added to config file


## Changes done
- file names were changed from e.g. `02_clean.py` to `stage02_clean.py` to allow importing modules into main.py, as Python does not accept module names starting with numbers in regular import statements
- exploring (Landscape analysis etc.) is now optional to define in the configurtion file
- to avoid multiimporting `cfg` variable is now an argument in every function requiring any global varaible defined in configuration file


## Info
- if any global variable is missing import it from config
- if any variable is missing in config add it to config yaml file
- to visualise (not only save) plots and tables uncomment appropriate code lines in `stage03_landscape.py`
- `cached` function was not used in `stage03_landscape.py` for steps §8 and §9, however the running time is still short (if needed can be added later)
- `ALT_BASE_YEAR` is defined manually
- some functions differs between notebooks and `src` files, however as notebooks are for exploring, the final versions of functions are the ones in `src` folder and `main.py`
