# /core/matcher.py

import json
from db import get_pool
from utils import normalize_name

def crosscheck(scan_results):
    """
    Compare scanned software list with entries in the CPE database.

    Args:
        scan_results (list[dict]): List of {"name": str, "version": str}
    Returns:
        list[dict]: Each result includes scanned app info + matched CPEs
    """

    pool = get_pool()
    conn = pool.getconn()
    cur = conn.cursor()

    results = []

    try:
        for app in scan_results:
            product_name = normalize_name(app["name"])
            version = app.get("version", "")
            matches = []

            # Search by product name and version
            cur.execute(
                """
                SELECT cpe23uri, vendor, product, version, title
                FROM cpe_entries
                WHERE product ILIKE %s
                AND (
                    version = %s OR
                    version ILIKE %s OR
                    version IS NULL OR
                    version = '*'
                )
                LIMIT 5;
                """,
                (f"%{product_name}%", version, f"%{version.split('.')[0]}%"),
            )

            rows = cur.fetchall()
            for row in rows:
                matches.append(
                    {
                        "cpe23uri": row[0],
                        "vendor": row[1],
                        "product": row[2],
                        "version": row[3],
                        "title": row[4],
                    }
                )

            results.append(
                {
                    "scanned_name": app["name"],
                    "scanned_version": version,
                    "matches": matches,
                }
            )

            if matches:
                print(f"✅ {app['name']} ({version}) matched {len(matches)} CPE(s)")
            else:
                print(f"⚠️  No CPE found for {app['name']} ({version})")

    except Exception as e:
        print("❌ Error during matching:", e)
    finally:
        cur.close()
        pool.putconn(conn)

    return results

def crosscheck_from_file(path: str):
    """
    Load scan result JSON file and crosscheck it against CPE database.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return crosscheck(data)