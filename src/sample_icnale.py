"""Build the stratified sampling manifest from an ICNALE download.

Parses ICNALE file names per the official naming rules (June 2023 revision):
    WE_<REGION>_<TASK>_<ID>_<CEFR>   e.g. WE_THA_PTJ0_001_B1_2
Outputs a CSV manifest of essay IDs only (no essay text), so the manifest
is safe to commit and share (licence: no redistribution of texts).
"""
from __future__ import annotations

import argparse
import random
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

# WE/WEP file name, e.g. WE_THA_PTJ0_001_B1_2 (CEFR uses inner underscores)
FILENAME_RE = re.compile(
    r"^(?P<module>WE|WEP)_(?P<region>[A-Z]{3})_(?P<task>PTJ0|SMK0)"
    r"_(?P<sid>\d{3})_(?P<cefr>[A-Z0-9]{2}_\d)$"
)


@dataclass(frozen=True)
class EssayRecord:
    essay_id: str
    module: str
    region: str
    task: str
    student_id: str
    cefr: str
    path: str


def scan_corpus(root: Path) -> list[EssayRecord]:
    """Scan unzipped ICNALE folders for individual essay text files."""
    records: list[EssayRecord] = []
    for txt in root.rglob("*.txt"):
        stem = txt.stem
        m = FILENAME_RE.match(stem)
        if m:
            records.append(
                EssayRecord(
                    essay_id=stem,
                    module=m["module"],
                    region=m["region"],
                    task=m["task"],
                    student_id=m["sid"],
                    cefr=m["cefr"],
                    path=str(txt.relative_to(root)),
                )
            )
    return records


def build_manifest(cfg: dict) -> pd.DataFrame:
    root = Path(cfg["paths"]["icnale_root"])
    rng = random.Random(cfg["seed"])
    tasks = set(cfg["sampling"]["tasks"])
    bands = set(cfg["sampling"]["bands"])

    records = scan_corpus(root)
    if not records:
        raise SystemExit(
            f"No ICNALE essay files found under {root}. "
            "Unzip WE/WEP there first (see README)."
        )
    df = pd.DataFrame([r.__dict__ for r in records])
    # the corpus ships each essay in several folder variants (unmerged,
    # classified, merged); keep one copy per essay, preferring the
    # Unclassified_Unmerged path for stability
    df = (df.assign(pref=~df.path.str.contains("Unclassified_Unmerged"))
            .sort_values(["essay_id", "pref"])
            .drop_duplicates("essay_id")
            .drop(columns="pref"))
    print(f"Scanned {len(df)} unique essays "
          f"({df.region.nunique()} regions, tasks: {sorted(df.task.unique())})")

    rows: list[pd.DataFrame] = []
    for cohort, spec in cfg["sampling"]["cohorts"].items():
        pool = df[df.region.isin(spec["regions"]) & df.task.isin(tasks)]
        if cohort == "native":
            # ENS files use XX_<type> in the CEFR slot; keep college students
            wanted = set(spec.get("ens_types", ["XX_1"]))
            pool = pool[pool.cefr.isin(wanted)]
        else:
            pool = pool[pool.cefr.isin(bands)]
        n = spec["n"]
        # stratify evenly over task x region (x band for learners)
        strata_cols = ["task", "region"] + ([] if cohort == "native" else ["cefr"])
        strata = list(pool.groupby(strata_cols))
        if not strata:
            print(f"WARNING: cohort '{cohort}' has an empty pool; skipping")
            continue
        per_stratum = max(1, n // len(strata))
        chosen: list[pd.DataFrame] = []
        for _, g in strata:
            take = min(per_stratum, len(g))
            chosen.append(g.sample(n=take, random_state=rng.randint(0, 2**31)))
        sel = pd.concat(chosen)
        # top up to n if rounding left us short
        if len(sel) < n:
            rest = pool.drop(sel.index)
            extra = rest.sample(n=min(n - len(sel), len(rest)),
                                random_state=rng.randint(0, 2**31))
            sel = pd.concat([sel, extra])
        sel = sel.assign(cohort=cohort)
        rows.append(sel)
        print(f"  cohort '{cohort}': {len(sel)} essays "
              f"from {sorted(sel.region.unique())}")
    manifest = pd.concat(rows).reset_index(drop=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    manifest = build_manifest(cfg)
    out = Path(cfg["paths"]["manifest"])
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(out, index=False)
    print(f"Wrote {len(manifest)} rows to {out}")
    print(manifest.groupby(["cohort", "task"]).size())


if __name__ == "__main__":
    main()
