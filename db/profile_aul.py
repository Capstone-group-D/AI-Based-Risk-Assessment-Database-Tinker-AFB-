"""
profile_aul.py — Read-only data profiling for Krystal's AUL CSV

Validates normalization assumptions BEFORE schema finalization or DB import.
Does NOT require PostgreSQL — operates only on the CSV file.

Usage:
    python3 db/profile_aul.py

Source:
    db/seed_data/aul_mxsg_2026-03-03.csv
    Sheet: "HM - MATERIAL AUTH IN SHOP SEQ"
    Prepared: 03-MAR-2026 by Krystal Tilson, Tinker AFB
"""

import csv
import os
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR / "seed_data" / "aul_mxsg_2026-03-03.csv"

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def load_csv(path):
    """Read the AUL CSV, skip the metadata row, return header + data rows."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip metadata row ("Prepared: 03-MAR-2026 ...")
        header = next(reader)
        rows = list(reader)
    return header, rows


def profile(header, rows):
    results = []
    total = len(rows)
    results.append(("Total data rows", total, PASS))

    msns = set()
    shop_codes = set()
    nouns_by_msn = {}
    bulk_by_msn = {}
    org_by_shop = {}
    bulk_values = set()

    null_msn = 0
    null_shop = 0
    dist_blanks = 0
    dist_non_numeric = []
    max_blanks = 0
    max_non_numeric = []
    max_decimal_digits_dist = 0

    for i, row in enumerate(rows):
        msn = row[0].strip()
        noun = row[1].strip()
        bulk = row[2].strip()
        process_name = row[3].strip()
        local_process = row[4].strip()
        dist_pct = row[5].strip()
        max_on_hand = row[6].strip()
        shop_code = row[7].strip()
        org_symbol = row[8].strip() if len(row) > 8 else ""

        if not msn:
            null_msn += 1
        if not shop_code:
            null_shop += 1

        msns.add(msn)
        shop_codes.add(shop_code)
        bulk_values.add(bulk)

        nouns_by_msn.setdefault(msn, Counter())[noun] += 1
        bulk_by_msn.setdefault(msn, set()).add(bulk)
        org_by_shop.setdefault(shop_code, set()).add(org_symbol)

        if not dist_pct:
            dist_blanks += 1
        else:
            try:
                float(dist_pct)
                parts = dist_pct.split(".")
                if len(parts) > 1:
                    max_decimal_digits_dist = max(max_decimal_digits_dist, len(parts[1]))
            except ValueError:
                dist_non_numeric.append((i + 3, dist_pct))

        if not max_on_hand:
            max_blanks += 1
        else:
            try:
                int(max_on_hand)
            except ValueError:
                max_non_numeric.append((i + 3, max_on_hand))

    # --- Key counts ---
    results.append(("Unique MSN values", len(msns), PASS))
    results.append(("Unique Shop Code values", len(shop_codes), PASS))
    results.append(("Null/blank MSN rows", null_msn, PASS if null_msn == 0 else FAIL))
    results.append(("Null/blank Shop Code rows", null_shop, PASS if null_shop == 0 else FAIL))

    # --- MSN -> Noun consistency ---
    multi_noun = {msn: counts for msn, counts in nouns_by_msn.items() if len(counts) > 1}
    if multi_noun:
        results.append(("MSN -> Noun conflicts", len(multi_noun), WARN))
        for msn, counts in multi_noun.items():
            for noun, count in counts.most_common():
                results.append((f"  MSN {msn}: \"{noun}\"", f"{count} rows", ""))
    else:
        results.append(("MSN -> Noun mapping", "1:1 (consistent)", PASS))

    # --- MSN -> Bulk Issue consistency ---
    multi_bulk = {msn: vals for msn, vals in bulk_by_msn.items() if len(vals) > 1}
    if multi_bulk:
        results.append(("MSN -> Bulk Issue conflicts", len(multi_bulk), FAIL))
        for msn, vals in list(multi_bulk.items())[:5]:
            results.append((f"  MSN {msn}", str(vals), ""))
    else:
        results.append(("MSN -> Bulk Issue mapping", "1:1 (consistent)", PASS))

    # --- Shop Code -> Org Symbol consistency ---
    multi_org = {sc: vals for sc, vals in org_by_shop.items() if len(vals) > 1}
    if multi_org:
        results.append(("Shop Code -> Org Symbol conflicts", len(multi_org), FAIL))
        for sc, vals in list(multi_org.items())[:5]:
            results.append((f"  Shop {sc}", str(vals), ""))
    else:
        results.append(("Shop Code -> Org Symbol mapping", "1:1 (consistent)", PASS))

    # --- Bulk Issue values ---
    results.append(("Bulk Issue distinct values", str(sorted(bulk_values)), PASS if bulk_values <= {"Y", "N"} else WARN))

    # --- Dist % quality ---
    results.append((f"Dist % blank rows", f"{dist_blanks} of {total} ({100*dist_blanks/total:.1f}%)", PASS))
    if dist_non_numeric:
        results.append(("Dist % non-numeric values", str(dist_non_numeric[:5]), FAIL))
    else:
        results.append(("Dist % numeric parse", "all clean", PASS))
    results.append(("Dist % max decimal places", max_decimal_digits_dist, WARN if max_decimal_digits_dist > 2 else PASS))

    # --- Max On Hand quality ---
    results.append((f"Max On Hand blank rows", f"{max_blanks} of {total}", PASS))
    if max_non_numeric:
        results.append(("Max On Hand non-integer values", str(max_non_numeric[:5]), FAIL))
    else:
        results.append(("Max On Hand integer parse", "all clean", PASS))

    # --- Exact duplicates ---
    row_tuples = [tuple(c.strip() for c in r[:9]) for r in rows]
    dupe_counts = Counter(row_tuples)
    exact_dupes = sum(count - 1 for count in dupe_counts.values() if count > 1)
    results.append(("Exact duplicate rows (all 9 cols)", exact_dupes, WARN if exact_dupes > 0 else PASS))

    return results


def print_report(results):
    print("=" * 72)
    print("  AUL CSV DATA PROFILE")
    print("  Source: db/seed_data/aul_mxsg_2026-03-03.csv")
    print("=" * 72)

    has_fail = False
    for label, value, status in results:
        tag = f"[{status}]" if status else "      "
        print(f"  {tag:6s}  {label}: {value}")
        if status == FAIL:
            has_fail = True

    print("=" * 72)
    if has_fail:
        print("  RESULT: FAIL — resolve issues above before finalizing schema")
        return False
    else:
        print("  RESULT: ALL CHECKS PASSED — safe to proceed with schema and import")
        return True


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    header, rows = load_csv(CSV_PATH)
    results = profile(header, rows)
    passed = print_report(results)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
