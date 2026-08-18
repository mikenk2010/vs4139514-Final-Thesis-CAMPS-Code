"""Build the E3 (GRA) manifest and dispersion file, keyed to corpus IDs.

Maps each GRA-rated essay (4_Summary, S/E == 'E') to its WE corpus text
file via the Original Code (W_REG_ID_BAND -> WE_REG_PTJ0_ID_BAND; all
140 rated essays are PTJ0), appends cohort='gra' rows to the manifest,
and writes per-essay human rating dispersion for BDS validation.
"""
from __future__ import annotations

import statistics
from pathlib import Path

import openpyxl
import pandas as pd

XLSX = "data/GRA/ICNALE GRA2_1/ICNALE GRA 2_1.xlsx"
CORPUS_ROOT = Path("data")


def corpus_id(original_code: str) -> str:
    # W_TWN_005_B1_2 -> WE_TWN_PTJ0_005_B1_2
    parts = original_code.split("_")
    region, sid, band = parts[1], parts[2], "_".join(parts[3:])
    return f"WE_{region}_PTJ0_{sid}_{band}"


def main() -> None:
    wb = openpyxl.load_workbook(XLSX, read_only=True)

    # --- essay list from 4_Summary
    ws = wb["4_Summary"]
    essays = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 4 or row[0] != "E":
            continue
        essays.append({"sample": row[1], "orig": row[2],
                       "region": row[3], "band": row[4]})
    print(f"GRA essays in summary: {len(essays)}")

    # --- locate corpus files
    files = {p.stem: p for p in CORPUS_ROOT.rglob("WE_*_PTJ0_*.txt")
             if "Unclassified_Unmerged" in str(p)}
    rows, missing = [], []
    for e in essays:
        eid = corpus_id(e["orig"])
        p = files.get(eid)
        if p is None and e["region"] == "ENS":
            # ENS original codes carry no band (W_ENS_001_ENS); match by
            # prefix against the corpus files (WE_ENS_PTJ0_001_XX_1 etc.)
            sid = e["orig"].split("_")[2]
            prefix = f"WE_ENS_PTJ0_{sid}_"
            cands = [k for k in files if k.startswith(prefix)]
            if len(cands) == 1:
                eid, p = cands[0], files[cands[0]]
        if p is None:
            missing.append(eid)
            continue
        rows.append({"essay_id": eid, "module": "WE", "region": e["region"],
                     "task": "PTJ0", "student_id": eid.split("_")[3],
                     "cefr": "_".join(eid.split("_")[4:]),
                     "path": str(p.relative_to(CORPUS_ROOT)),
                     "cohort": "gra"})
    print(f"matched to corpus files: {len(rows)}; missing: {missing[:5]}")

    # --- append to manifest (replacing any previous gra rows)
    mf = Path("results/manifest.csv")
    m = pd.read_csv(mf)
    m = m[m.cohort != "gra"]
    m = pd.concat([m, pd.DataFrame(rows)], ignore_index=True)
    m.to_csv(mf, index=False)
    print(f"manifest now {len(m)} rows: "
          f"{m.groupby('cohort').size().to_dict()}")

    # --- dispersion keyed by corpus essay_id
    ws = wb["3_Rating"]
    hdr, per = None, {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 2:
            hdr = [str(c) if c else "" for c in row]
            idxs = {h: j for j, h in enumerate(hdr)}
            content = [j for h, j in idxs.items() if "(Content)" in h]
            holc = next(j for h, j in idxs.items() if "Holistic" in h)
            oc, sec = idxs["Original Code"], idxs["S/E"]
            continue
        if hdr is None or row[sec] != "E":
            continue
        try:
            cm = statistics.mean(float(row[j]) for j in content)
            hol = float(row[holc])
        except (TypeError, ValueError):
            continue
        per.setdefault(corpus_id(str(row[oc])), []).append((cm, hol))
    out = pd.DataFrame([
        {"essay_id": k, "n_raters": len(v),
         "content_mean": statistics.mean(x[0] for x in v),
         "dispersion": statistics.stdev(x[0] for x in v),
         "holistic_mean": statistics.mean(x[1] for x in v),
         "holistic_dispersion": statistics.stdev(x[1] for x in v)}
        for k, v in sorted(per.items())]).round(3)
    out.to_csv("results/gra_dispersion.csv", index=False)
    print(f"dispersion file: {len(out)} essays -> results/gra_dispersion.csv")


if __name__ == "__main__":
    main()
