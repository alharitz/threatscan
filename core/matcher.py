# core/matcher.py

from utils.logger import setup_logger
from db.connection import get_db_connection
import psycopg2.pool
from psycopg2.extras import DictCursor
from packaging.version import Version, InvalidVersion
from typing import List, Dict, Set, Tuple, Any

import re
import os
import time

log = setup_logger()
log = log.getChild("matcher")

class Matcher:
    def __init__(self, db_pool: psycopg2.pool.SimpleConnectionPool = None):
        """
        Initializes the Matcher.
        1. Sets up the DB connection.
        2. Pre-loads known vendors into memory to make parsing smarter/faster.
        """
        self.db_pool = db_pool or get_db_connection()
        if not self.db_pool:
            log.error("Failed to initialize database connection pool.")
            raise ConnectionError("Database pool could not be initialized.")
        
        # Pre-load vendors to help distinguish "Adobe Reader" -> Vendor: Adobe
        self.known_vendors = self._load_known_vendors()

    def _load_known_vendors(self) -> Set[str]:
        """Fetch unique vendors from DB to assist in name splitting."""
        vendors = set()
        conn = None
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cur:
                # Based on your image: cpe_entries has a 'vendor' column
                cur.execute("SELECT DISTINCT vendor FROM cpe_entries WHERE vendor IS NOT NULL")
                for row in cur.fetchall():
                    if row[0]:
                        vendors.add(row[0].lower().strip())
            log.info(f"Loaded {len(vendors)} unique vendors for fuzzy matching.")
        except Exception as e:
            log.warning(f"Failed to load vendors: {e}")
        finally:
            if conn: self.db_pool.putconn(conn)
        return vendors

    def _extract_metadata(self, raw_name: str) -> Tuple[str, str]:
        """
        Heuristic: Splits 'Microsoft VSCode' into ('microsoft', 'vscode').
        Returns: (vendor_guess, product_guess)
        """
        if not raw_name:
            return "%", "%"

        # 1. Clean String: Lowercase, remove brackets, keep only alphanumeric + _
        clean = re.sub(r'[\(\[\{].*[\)\]\}]', '', raw_name).strip().lower()
        clean = re.sub(r'[^a-z0-9_ ]', '', clean)
        clean = clean.replace(' ', '_').replace('-', '_').strip('_')

        if not clean:
            return "%", "%"
        
        parts = clean.split('_')
        
        # 2. Smart Vendor Detection
        # Check first 1-3 words to see if they match a known vendor
        for i in range(1, min(4, len(parts) + 1)):
            candidate = "_".join(parts[:i])
            if candidate in self.known_vendors:
                vendor = candidate
                product = "_".join(parts[i:])
               
                if not product:
                    product = "%"
                else:
                    product = "%" + product + "%"
                return vendor, product

        # 3. Fallback: If no vendor found, assume the whole string is the product
        # and we will search ALL vendors.
        return "%", "%" + clean + "%"

    def _normalize_version(self, s: str) -> str:
        if not s: return ""

        s = s.strip().lower().lstrip("v")
        s = re.sub(r'^(\d+(?:\.\d+)*)([a-z]+)$', r'\1.\2', s)
        s = re.sub(r'[^0-9a-z\.\-\+]', '', s)

        return s

    def _s(self, x):
        return str(x) if x is not None else None

    def _is_version_vulnerable(self, scanned_ver_str: str, rule: Dict) -> bool:
        """
        Compares scanned version against the CVE range rules.
        """
        try:
            # Clean up version string (e.g., remove 'v' prefix if present)
            clean_ver = self._normalize_version(scanned_ver_str)
            v_scanned = Version(clean_ver)
        except (InvalidVersion, TypeError):
            # If version is garbage (e.g. "Unknown"), we can't mathematically compare it.
            return False

        # Extract rules from the DB row (keys match aliases in SQL query)
        start_incl = self._s(rule.get('v_start_inc'))
        start_excl = self._s(rule.get('v_start_exc'))
        end_incl   = self._s(rule.get('v_end_inc'))
        end_excl   = self._s(rule.get('v_end_exc'))
        exact_version = self._s(rule.get('exact_version'))

        has_range = any([start_incl, start_excl, end_incl, end_excl])

        if has_range:
            try:
                if start_incl and v_scanned < Version(start_incl): return False
                if start_excl and v_scanned <= Version(start_excl): return False
                if end_incl and v_scanned > Version(end_incl): return False
                if end_excl and v_scanned >= Version(end_excl): return False
                return True
            except (InvalidVersion, TypeError):
                return False

        if exact_version == '*': 
            return True
            
        if exact_version:
            try:
                # Compare as versions to handle 1.0 vs 1.0.0
                return v_scanned == Version(exact_version)
            except (InvalidVersion, TypeError):
                # Fallback to string comparison
                return clean_ver == exact_version
                
        return False

    def find_vulnerabilities(self, software_list: List[Dict]) -> List[Dict]:
        """
        Main Function:
        1. Groups software by product to reduce DB queries.
        2. Fetches potential CVEs from DB.
        3. Filters locally by version.
        """
        if not software_list:
            return []

        log.info(f"⚡ Analyzing {len(software_list)} items against Local Database...")

        # --- Step A: Grouping ---
        # We group items so if you have 10 versions of "Java", we only query the DB once for "Java".
        # Map: (vendor_guess, product_guess) -> List of indices in software_list
        grouped_items = {} 
        for idx, item in enumerate(software_list):
            v_guess, p_guess = self._extract_metadata(item['normalized_name'])
            key = (v_guess, p_guess)
            if key not in grouped_items:
                grouped_items[key] = []
            grouped_items[key].append(idx)

        conn = None
        try:
            conn = self.db_pool.getconn()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                
                # --- Step B: Batch Querying ---
                for (vendor_param, product_param), indices in grouped_items.items():
                    
                    # 1. The MASTER Query
                    # Matches the columns from your uploaded images exactly.
                    query = """
                        SELECT 
                            m.cve_id,
                            m.cpe_uri as m_cpe_uri,
                            e.cpe23uri as e_cpe23uri,
                            m.version_start_including::text as v_start_inc,
                            m.version_start_excluding::text as v_start_exc,
                            m.version_end_including::text as v_end_inc,
                            m.version_end_excluding::text as v_end_exc,
                            e.version::text as exact_version,
                            c.summary,
                            c.cvss_v3_base_score as severity,
                            c.base_severity as severity_level
                        FROM cpe_entries e
                        JOIN cve_cpe_entries m ON e.cpe23uri = m.cpe_uri
                        JOIN cve_entries c ON m.cve_id = c.cve_id
                        WHERE 
                            (%s = '%%' OR e.vendor = %s)
                            AND e.product ILIKE %s
                    """
                    
                    cur.execute(query, (vendor_param, vendor_param, product_param))
                    potential_cves = cur.fetchall()

                    # --- Step C: Python Version Filtering ---
                    if potential_cves:
                        if item['normalized_name'] == 'winrar':
                            log.info(f"row cve={cve_row['cve_id']} m_cpe={cve_row['m_cpe_uri']} e_cpe={cve_row['e_cpe23uri']} end_excl={cve_row['v_end_exc']} exact={cve_row['exact_version']}")
                        for idx in indices:
                            item = software_list[idx]
                            
                            if 'vulnerabilities' not in item:
                                item['vulnerabilities'] = []
                            
                            # Check every potential CVE against this specific item's version
                            for cve_row in potential_cves:
                                if self._is_version_vulnerable(item['normalized_version'], cve_row):
                                    # Deduplication check
                                    if not any(v['cve_id'] == cve_row['cve_id'] for v in item['vulnerabilities']):
                                        item['vulnerabilities'].append({
                                            "cve_id": cve_row['cve_id'],
                                            "summary": cve_row['summary'],
                                            "score": float(cve_row['severity']) if cve_row['severity'] else 0.0,
                                            "base_severity": cve_row['severity_level'],
                                            "status": "Analyzed"
                                        })

        except Exception as e:
            log.error(f"Error during matching process: {e}", exc_info=True)
        finally:
            if conn: self.db_pool.putconn(conn)

        return software_list