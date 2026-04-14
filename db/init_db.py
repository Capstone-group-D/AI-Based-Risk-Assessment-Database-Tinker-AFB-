import sqlite3
import os
import re
import csv
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR.parent / "risk_assessment.db"
SCHEMA_PATH = SCRIPT_DIR / "schema.sql"
SEED_PATH = SCRIPT_DIR / "seed_data.sql"
AUL_CSV_PATH = SCRIPT_DIR / "seed_data" / "aul_mxsg_2026-03-03.csv"

def init_db():
    print(f"Initializing SQLite database at {DB_PATH}")
    if DB_PATH.exists():
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Read and adapt schema.sql for SQLite
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    
    # SQLite adaptations
    schema_sql = schema_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    # Replace NUMERIC(7,4) and DECIMAL(6,2) with REAL
    schema_sql = re.sub(r'NUMERIC\(\d+,\d+\)', 'REAL', schema_sql)
    schema_sql = re.sub(r'DECIMAL\(\d+,\d+\)', 'REAL', schema_sql)
    schema_sql = schema_sql.replace("BOOLEAN", "INTEGER") # SQLite uses 1/0 for true/false typically, though BOOLEAN works as an alias
    
    # Remove Postgres specific CASCADE drops
    # Not needed for schema_sql since we don't have TRUNCATE in schema


    cur.executescript(schema_sql)
    print("Schema created.")

    # 2. Read and adapt seed_data.sql for SQLite
    with open(SEED_PATH, "r") as f:
        seed_sql = f.read()
    
    # Remove Postgres TRUNCATE statements
    seed_sql = re.sub(r'TRUNCATE TABLE .*?;', '', seed_sql)

    cur.executescript(seed_sql)
    print("Seed data inserted.")

    # 3. Import AUL data
    _import_aul_data(conn)

    conn.commit()
    conn.close()
    print("Database initialization complete.")


def _import_aul_data(conn):
    if not AUL_CSV_PATH.exists():
        print(f"Warnings: CSV not found at {AUL_CSV_PATH}")
        return

    print("Importing AUL CSV data...")
    with open(AUL_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # metadata
        next(reader)  # header
        
        rows = []
        for r in reader:
            if len(r) < 8:
                continue
            rows.append({
                "msn": r[0].strip(),
                "noun": r[1].strip(),
                "bulk_issue": 1 if r[2].strip() == "Y" else 0,
                "process_name": r[3].strip() or None,
                "local_process_name": r[4].strip() or None,
                "dist_pct": float(r[5].strip()) if r[5].strip() else None,
                "max_on_hand": int(r[6].strip()) if r[6].strip() else None,
                "shop_code": r[7].strip(),
                "org_symbol": r[8].strip() if len(r) > 8 else None,
            })
            
    # Deduplicate Materials
    noun_counts = {}
    bulk_by_msn = {}
    for r in rows:
        msn = r["msn"]
        noun_counts.setdefault(msn, Counter())[r["noun"]] += 1
        bulk_by_msn[msn] = r["bulk_issue"]

    materials = []
    for msn, counter in noun_counts.items():
        winner = counter.most_common(1)[0][0]
        materials.append((msn, winner, bulk_by_msn[msn]))

    # Deduplicate Shops
    shops = {}
    for r in rows:
        sc = r["shop_code"]
        if sc not in shops:
            shops[sc] = (sc, r["org_symbol"])
            
    # Deduplicate authorizations
    seen = set()
    auths = []
    for r in rows:
        key = (r["msn"], r["shop_code"], r["process_name"], r["local_process_name"], r["dist_pct"], r["max_on_hand"])
        if key not in seen:
            seen.add(key)
            auths.append(key)

    cur = conn.cursor()
    cur.executemany("INSERT OR IGNORE INTO materials (msn, noun, bulk_issue) VALUES (?, ?, ?)", materials)
    cur.executemany("INSERT OR IGNORE INTO shops (shop_code, org_symbol) VALUES (?, ?)", list(shops.values()))
    cur.executemany(
        "INSERT INTO material_authorizations (msn, shop_code, process_name, local_process_name, dist_pct, max_on_hand) VALUES (?, ?, ?, ?, ?, ?)",
        auths
    )
    print(f"Loaded {len(materials)} materials, {len(shops)} shops, and {len(auths)} authorizations.")


if __name__ == "__main__":
    init_db()
