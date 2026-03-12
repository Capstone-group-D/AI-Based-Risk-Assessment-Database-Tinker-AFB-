"""
import_aul.py — Import Krystal's AUL CSV into PostgreSQL

Reads the AUL CSV, applies cleaning rules, and loads into the normalized
materials / shops / material_authorizations tables.

Prerequisites:
    1. PostgreSQL running with the risk_assessment_db database created
    2. Schema applied:  psql risk_assessment_db < db/schema.sql
    3. psycopg2 installed:  pip install psycopg2-binary
    4. DATABASE_URL set in environment or api/.env

Usage:
    DATABASE_URL=postgresql://localhost:5432/risk_assessment_db python3 db/import_aul.py

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

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR / "seed_data" / "aul_mxsg_2026-03-03.csv"

DEFAULT_DB_URL = "postgresql://localhost:5432/risk_assessment_db"


def get_database_url():
    """Resolve DATABASE_URL from environment or api/.env file."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    env_path = SCRIPT_DIR.parent / "api" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    print(f"WARNING: DATABASE_URL not set, using default: {DEFAULT_DB_URL}", file=sys.stderr)
    return DEFAULT_DB_URL


def load_and_clean_csv(path):
    """
    Parse the AUL CSV with cleaning rules:
    - Skip metadata row (line 1)
    - Trim whitespace on all text fields
    - Convert Bulk Issue Y/N to boolean
    - Parse Dist % as float (None if blank)
    - Parse Max On Hand as int (None if blank)
    - Log warnings for parse failures
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip metadata row
        header = next(reader)
        rows = []
        parse_warnings = []

        for line_num, row in enumerate(reader, start=3):
            msn = row[0].strip()
            noun = row[1].strip()
            bulk_raw = row[2].strip()
            process_name = row[3].strip()
            local_process_name = row[4].strip()
            dist_raw = row[5].strip()
            max_raw = row[6].strip()
            shop_code = row[7].strip()
            org_symbol = row[8].strip() if len(row) > 8 else ""

            bulk_issue = True if bulk_raw == "Y" else False if bulk_raw == "N" else None
            if bulk_issue is None and bulk_raw:
                parse_warnings.append(f"  Line {line_num}: unexpected bulk_issue value '{bulk_raw}', storing as NULL")

            dist_pct = None
            if dist_raw:
                try:
                    dist_pct = float(dist_raw)
                except ValueError:
                    parse_warnings.append(f"  Line {line_num}: dist_pct parse failed for '{dist_raw}', storing as NULL")

            max_on_hand = None
            if max_raw:
                try:
                    max_on_hand = int(max_raw)
                except ValueError:
                    parse_warnings.append(f"  Line {line_num}: max_on_hand parse failed for '{max_raw}', storing as NULL")

            rows.append({
                "msn": msn,
                "noun": noun,
                "bulk_issue": bulk_issue,
                "process_name": process_name or None,
                "local_process_name": local_process_name or None,
                "dist_pct": dist_pct,
                "max_on_hand": max_on_hand,
                "shop_code": shop_code,
                "org_symbol": org_symbol or None,
            })

    return rows, parse_warnings


def deduplicate_materials(rows):
    """
    Build the materials dimension from rows.
    Uses majority-wins heuristic for the single known msn->noun conflict.
    """
    noun_counts = {}   # msn -> Counter of nouns
    bulk_by_msn = {}   # msn -> bulk_issue

    for r in rows:
        msn = r["msn"]
        noun_counts.setdefault(msn, Counter())[r["noun"]] += 1
        bulk_by_msn[msn] = r["bulk_issue"]

    materials = {}
    conflicts = []

    for msn, counter in noun_counts.items():
        if len(counter) > 1:
            winner = counter.most_common(1)[0][0]
            conflicts.append(
                f"  MSN {msn}: selected \"{winner}\" ({counter[winner]} rows) "
                f"over alternatives: {', '.join(f'\"{n}\" ({c} rows)' for n, c in counter.most_common()[1:])}\n"
                f"    NOTE: This is a temporary data-quality heuristic, not a confirmed business rule."
            )
            noun = winner
        else:
            noun = counter.most_common(1)[0][0]

        materials[msn] = {"msn": msn, "noun": noun, "bulk_issue": bulk_by_msn[msn]}

    return materials, conflicts


def deduplicate_shops(rows):
    """Build the shops dimension from rows. Profiling confirmed 1:1 mapping."""
    shops = {}
    for r in rows:
        sc = r["shop_code"]
        if sc not in shops:
            shops[sc] = {"shop_code": sc, "org_symbol": r["org_symbol"]}
    return shops


def deduplicate_authorizations(rows):
    """
    Remove exact-duplicate authorization rows (all columns matching).
    Rows sharing msn+shop_code but differing in any other column are
    treated as distinct valid authorizations and preserved.
    """
    seen = set()
    unique = []
    dupes_removed = 0

    for r in rows:
        key = (
            r["msn"], r["shop_code"], r["process_name"],
            r["local_process_name"], r["dist_pct"], r["max_on_hand"],
        )
        if key in seen:
            dupes_removed += 1
            continue
        seen.add(key)
        unique.append(r)

    return unique, dupes_removed


def insert_data(conn, materials, shops, auth_rows):
    """Insert into materials, shops, then material_authorizations (FK order)."""
    cur = conn.cursor()

    cur.executemany(
        "INSERT INTO materials (msn, noun, bulk_issue) VALUES (%s, %s, %s) ON CONFLICT (msn) DO NOTHING",
        [(m["msn"], m["noun"], m["bulk_issue"]) for m in materials.values()],
    )
    mat_count = cur.rowcount

    cur.executemany(
        "INSERT INTO shops (shop_code, org_symbol) VALUES (%s, %s) ON CONFLICT (shop_code) DO NOTHING",
        [(s["shop_code"], s["org_symbol"]) for s in shops.values()],
    )
    shop_count = cur.rowcount

    cur.executemany(
        """INSERT INTO material_authorizations
           (msn, shop_code, process_name, local_process_name, dist_pct, max_on_hand)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        [
            (r["msn"], r["shop_code"], r["process_name"],
             r["local_process_name"], r["dist_pct"], r["max_on_hand"])
            for r in auth_rows
        ],
    )
    auth_count = cur.rowcount

    conn.commit()
    cur.close()
    return mat_count, shop_count, auth_count


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    db_url = get_database_url()
    print(f"Loading CSV: {CSV_PATH}")
    print(f"Target DB:   {db_url.split('@')[-1] if '@' in db_url else db_url}")

    # --- Load and clean ---
    rows, parse_warnings = load_and_clean_csv(CSV_PATH)
    print(f"\nRows parsed from CSV: {len(rows)}")

    if parse_warnings:
        print(f"\nParse warnings ({len(parse_warnings)}):", file=sys.stderr)
        for w in parse_warnings:
            print(w, file=sys.stderr)

    # --- Deduplicate ---
    materials, noun_conflicts = deduplicate_materials(rows)
    shops = deduplicate_shops(rows)
    auth_rows, dupes_removed = deduplicate_authorizations(rows)

    print(f"Unique materials (by MSN): {len(materials)}")
    print(f"Unique shops (by shop_code): {len(shops)}")
    print(f"Exact duplicate rows removed: {dupes_removed}")
    print(f"Authorization rows to insert: {len(auth_rows)}")

    if noun_conflicts:
        print(f"\nNoun conflicts resolved ({len(noun_conflicts)}):", file=sys.stderr)
        for c in noun_conflicts:
            print(c, file=sys.stderr)

    # --- Insert ---
    try:
        conn = psycopg2.connect(db_url)
    except psycopg2.OperationalError as e:
        print(f"\nERROR: Could not connect to database: {e}", file=sys.stderr)
        print("Make sure PostgreSQL is running and the database exists.", file=sys.stderr)
        print(f"  createdb risk_assessment_db", file=sys.stderr)
        print(f"  psql risk_assessment_db < db/schema.sql", file=sys.stderr)
        sys.exit(1)

    try:
        mat_count, shop_count, auth_count = insert_data(conn, materials, shops, auth_rows)
    except Exception as e:
        conn.rollback()
        print(f"\nERROR during insert: {e}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    conn.close()

    # --- Summary ---
    print("\n" + "=" * 56)
    print("  IMPORT COMPLETE")
    print("=" * 56)
    print(f"  materials rows inserted:              {mat_count}")
    print(f"  shops rows inserted:                  {shop_count}")
    print(f"  material_authorizations rows inserted: {auth_count}")
    print(f"  exact duplicates skipped:             {dupes_removed}")
    print(f"  noun conflicts resolved:              {len(noun_conflicts)}")
    print("=" * 56)


if __name__ == "__main__":
    main()
