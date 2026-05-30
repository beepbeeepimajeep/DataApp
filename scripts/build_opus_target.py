"""Build the Opus production target list (Set A anchor ∪ Set B contested).

Reference filter validated by strategy. Reads from the 151B repo, writes the
535-id target list to dataapp_outputs/opus/target_535.json and prints a
reconciliation. NO API calls. Size-gate: target must == 535.
"""
import json
from pathlib import Path
import pandas as pd

C = Path.home() / "cse151b/151B_SP26_Competition"
OUT = Path(__file__).resolve().parent.parent / "dataapp_outputs/opus"
OUT.mkdir(parents=True, exist_ok=True)

# NOTE: dtype only forces `id` to str. `is_mcq` is intentionally left to
# pandas inference so it parses as native bool (np.bool_), matching the
# strategy-validated reference filter which compares `is_mcq == True`.
# Forcing is_mcq to str breaks the slot-4 exclusion (gives 558, not 535).
breakdown = pd.read_csv(C / "data/search/teachers/teacher_agreement_breakdown.csv", dtype={"id": str})
master = pd.read_csv(C / "data/master_item_tracker.csv", dtype={"id": str}, usecols=["id", "is_mcq"])
anchor = pd.read_csv(C / "data/search/teachers/anchor_set_FINAL.csv", dtype={"id": str})
assert master["is_mcq"].dtype == bool, f"is_mcq must be bool, got {master['is_mcq'].dtype}"
for df in (breakdown, master, anchor):
    df["id"] = df["id"].apply(lambda x: str(x).zfill(4))


def has_xhigh_in_3(j):
    try:
        return any(len(c) == 3 and "xhigh" in c for c in json.loads(j))
    except Exception:
        return False


m = breakdown.merge(master[["id", "is_mcq"]], on="id", how="left")
exclude_unan = m["cluster_pattern"] == "4"
exclude_slot4 = (
    (m["cluster_pattern"] == "3+1")
    & m["cluster_membership_json"].apply(has_xhigh_in_3)
    & (m["is_mcq"] == True)  # noqa: E712 — bool compare, matches reference
)
exclude_anchor = m["id"].isin(set(anchor["id"]))

set_b_breakdown = set(m[~exclude_unan & ~exclude_slot4 & ~exclude_anchor]["id"])
set_b_no_breakdown = set(master["id"]) - set(breakdown["id"]) - set(anchor["id"])
A = set(anchor["id"])
B = set_b_breakdown | set_b_no_breakdown
target = sorted(A | B)

report = {
    "anchor_A": len(A),
    "setB_from_breakdown": len(set_b_breakdown),
    "setB_no_breakdown": len(set_b_no_breakdown),
    "setB_total": len(B),
    "A_intersect_B": len(A & B),
    "target_total": len(target),
    "diamonds_present": [x for x in ["0017", "0019", "0041", "0285", "0451"] if x in set(target)],
}
print(json.dumps(report, indent=2))

if len(target) == 535:
    (OUT / "target_535.json").write_text(json.dumps(target))
    print("OK: saved", OUT / "target_535.json")
else:
    print("SIZE GATE FAIL: target=%d (expected 535)" % len(target))
