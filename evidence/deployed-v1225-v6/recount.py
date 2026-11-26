"""Recount the public paired verdicts and exact two-sided McNemar tests."""
import csv
from collections import Counter
from math import comb
from pathlib import Path
import re

with Path(__file__).with_name("pairs.csv").open(newline="") as stream:
    reader = csv.DictReader(stream)
    assert reader.fieldnames == ["case_key", "control_treatment", "control_label",
                                 "control_e2e", "v1225_label", "v1225_e2e"]
    rows = list(reader)

strict = {"correct", "correct_refusal"}
labels = strict | {"partial", "incorrect", "incorrect_refusal", "uncertain"}
assert len(rows) == len({r["case_key"] for r in rows}) == 2000
assert Counter(r["control_treatment"] for r in rows) == {"retained": 1990, "rejudged": 4, "regenerated": 6}
for r in rows:
    assert None not in r and re.fullmatch("[0-9a-f]{64}", r["case_key"])
    for arm in ("control", "v1225"):
        assert r[arm+"_label"] in labels and r[arm+"_e2e"] in {"0", "1"}
        if r["control_treatment"] != "retained":
            assert r[arm+"_label"] != "uncertain"
assert sum(r["v1225_label"] == "uncertain" for r in rows) == 21
assert not any(r["control_label"] == "uncertain" for r in rows)

def passed(row, arm, endpoint):
    if endpoint == "e2e":
        return row[arm+"_e2e"] == "1"
    return row[arm+"_label"] in (strict if endpoint == "strict" else strict | {"partial"})

for endpoint, expected in [("strict", (1316, 1521, 359, 154)), ("strict_or_partial", (1741, 1856, 202, 87)),
                           ("e2e", (1100, 1501, 523, 122))]:
    ct = Counter((passed(r, "control", endpoint), passed(r, "v1225", endpoint)) for r in rows)
    gain, loss = ct[False, True], ct[True, False]
    totals = (ct[True, True]+loss, ct[True, True]+gain, gain, loss)
    assert totals == expected
    n = gain + loss
    p = min(1, 2 * sum(comb(n, j) for j in range(min(gain, loss)+1)) / 2**n)
    print(f"{endpoint}: control={totals[0]} v1225={totals[1]} gained={gain} lost={loss} net={gain-loss:+d} p={p:.6g}")
