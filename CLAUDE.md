# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Historical ICPC México data: fetches contest results from the ICPC public API, stores them as JSON/CSV under `data/`, and generates Markdown reports (in Spanish) under `analysis/`. Both `data/` and `analysis/` are committed outputs, so regenerating them produces diffs to review. There is no test suite or linter.

## Commands

- Setup: Python 3.8.10 (`.tool-versions`, use `asdf install`), then `pip install -r requirements.txt`.
- Run: `python src/run.py` from the **repo root**. Paths (`data/`, `analysis/`) are resolved against `os.getcwd()`, and `icpc_mexico` is imported relative to `src/`. If the import fails, run with `PYTHONPATH=src`.
- Flags:
  - `--refresh-contests`: re-query the ICPC API for all contests.
  - `--refresh-schools`: rebuild `icpc_mexico_schools.json`.
  - `--refresh-school-history`: regenerate the per-school pages in `analysis/escuela/`.

## Architecture

Pipeline in `src/run.py`: contests CSV → `processor.get_finished_contests` (ICPC API via `icpc_api.py`) → `data/icpc_mexico_results.json` → `processor.get_schools` → `data/icpc_mexico_schools.json` → `Queries` → `Analyzer` → Markdown.

- `data/icpc_mexico_contests.csv` is the hand-maintained contest catalog (year, type, `url_id`, API `id`). Add new contests here. `comments` is significant: `Manual` means there is no API data (see `_get_teams_without_api` in `processor.py`, which hard-codes 1997/1998 results), and a value starting with `TBD` is skipped.
- Incremental behavior: if the results JSON exists, only contests missing from it are fetched. If any contest was fetched, schools are rebuilt and the school history is regenerated. The results JSON is also rewritten on every run to keep it in sync with the dataclasses.
- `data.py` holds frozen `dataclass_json` models (`Contest`, `FinishedContest`, `TeamResult`, `School`, `SchoolCommunity`, `ContestType`). `storage.py` serializes them with `to_dict`/`from_dict`. Changing a dataclass field changes the JSON schema.
- `processor.get_schools` contains the **hand-curated school registry**: canonical name, `alt_names`, country, state, community (TecNM/ITESM) and `is_eligible`. School matching uses `normalize_school_name` (`utils.py`) against name and alt names. New or renamed institutions in API data need entries here, otherwise they are treated as unknown.
- `_clean_up_teams` dedups teams and validates rank continuity. It raises `ProcessingError` on unexpected ranks (non-manual contests), which usually means bad API data or a new edge case.
- `queries.py` and `query_data.py` compute rankings, percentiles, seasons and community/country ranks from contests and schools. `analysis.py` (`Analyzer`) and `markdown.py` render them to `analysis/mexico.md`, `tecnm.md`, `sinaloa.md` and `analysis/escuela/<slug>.md`.
