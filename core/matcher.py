# core/matcher.py

import datetime
import json
import requests
import re
import psycopg2.pool
import difflib

from utils.logger import setup_logger
from db.connection import get_db_connection
from psycopg2.extras import DictCursor
from packaging.version import Version, InvalidVersion
from typing import List, Dict, Tuple

log = setup_logger()
log = log.getChild("matcher")
class VersionMatcher:
    """
    Advanced version matching logic to reduce False Positives from 'Zombie CVEs'.
    """
    
    @staticmethod
    def get_cve_year(cve_id: str) -> int:
        """Extracts year from CVE-YYYY-NNNNN."""
        match = re.search(r'CVE-(\d{4})-', cve_id)
        return int(match.group(1)) if match else datetime.datetime.now().year

    @staticmethod
    def normalize(v_str: str) -> Version:
        """Attempts to parse messy version strings."""
        if not v_str or v_str == "*" or v_str == "-":
            return None
        
        try:
            # Remove leading 'v', generic cleanup
            clean = v_str.strip().lower().lstrip('v')
            # Handle "1.0.0.release" -> "1.0.0"
            clean = re.sub(r'[^0-9a-z\.]+', '', clean)
            return Version(clean)
        except (InvalidVersion, TypeError):
            return None
        
    @staticmethod
    def extract_version_from_cpe(cpe_uri: str) -> str:
        """
        Extracts version from 'cpe:2.3:a:vendor:product:VERSION:...'
        """
        if not cpe_uri: 
            return None
        parts = cpe_uri.split(':')
        # CPE 2.3 format: parts[5] is usually the version
        if len(parts) > 5:
            return parts[5]
        return None

    @staticmethod
    def is_vulnerable(scanned_ver: str, cve_row: Dict) -> bool:
        # 1. Parse Scanned Version
        v_scan = VersionMatcher.normalize(scanned_ver)
        if not v_scan: 
            return False 

        # 2. Check Explicit Ranges (Start/End columns)
        v_start = VersionMatcher.normalize(cve_row.get('v_start_inc'))
        v_end_inc = VersionMatcher.normalize(cve_row.get('v_end_inc'))
        v_end_exc = VersionMatcher.normalize(cve_row.get('v_end_exc'))

        has_range = (v_start or v_end_inc or v_end_exc)

        if has_range:
            # Standard Range Check
            if v_start and v_scan < v_start: 
                return False
            if v_end_inc and v_scan > v_end_inc: 
                return False
            if v_end_exc and v_scan >= v_end_exc: 
                return False
            return True

        # 3. No Range Columns? Check CPE URI for Specific Version
        # This handles cases where range is NULL but CPE says "cpe:...:python:3.6.8:..."
        cpe_version_str = VersionMatcher.extract_version_from_cpe(cve_row.get('cpe_uri'))
        v_cpe = VersionMatcher.normalize(cpe_version_str)

        if v_cpe:
            # If CPE targets a specific version (e.g., 3.6.8), we must match EXACTLY
            # (or be super conservative and say False if not equal)
            return v_scan == v_cpe
        
        # 4. "Wildcard" Logic (CPE has '*', Ranges are NULL)
        # This means "All Versions" OR "The database is messy".
        # Apply Zombie Logic here to be safe.
        
        cve_id = cve_row.get('cve_id', '')
        cve_year = VersionMatcher.get_cve_year(cve_id)
        age = datetime.datetime.now().year - cve_year

        if age > 4:
            # Old CVE + No Range + No Specific Version = Likely False Positive
            return False
            
        return True
        
class Matcher:
    def __init__(self, db_pool: psycopg2.pool.SimpleConnectionPool = None):
        """
        Initializes the Matcher.
        """
        self.db_pool = db_pool or get_db_connection()
        if not self.db_pool:
            log.error("[INIT] Failed to initialize database connection pool.")
            raise ConnectionError("Database pool could not be initialized.")
        
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model_name = "gemma3:4b"
        self.memory_cache = {}

        self.windows_base_url = "https://api.msrc.microsoft.com/cvrf/v2.0/cvrf"
        self.headers = {"Accept": "application/json"}
        self._init_db()

    def _init_db(self):
        """Creates the cache table automatically."""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cpe_cache (
                        software_name TEXT PRIMARY KEY,
                        vendor TEXT NOT NULL,
                        product TEXT NOT NULL,
                        trust_score INT DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
        finally:
            self.db_pool.putconn(conn)

    # Windows Logic (with MSRC)
    def windows_get_latest_updates(self):        
        now = datetime.datetime.now()        
        month_str = now.strftime("%Y-%b")
        url = f"{self.windows_base_url}/{month_str}"
        log.info(f"[MSRC] Fetching updates for: {month_str}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception: 
            pass
        return None
    
    def windows_find_product_id(self, cvrf_json, os_name, os_version):
        """
        Locates the specific 'ProductID' for the user's Windows version.
        Example: Maps 'Windows 11 23H2' -> ProductID '12345'
        """
        product_tree = cvrf_json.get("ProductTree", {}).get("FullProductName", [])
        target_name = f"{os_name} Version {os_version}"
        candidates = {}

        for item in product_tree:
            p_name = item.get("Value", "")
            p_id = item.get("ProductID")
            if "Windows" in p_name and os_version in p_name and "x64" in p_name:
                candidates[p_name] = p_id

        if not candidates:
            return None

        best_match_name = difflib.get_close_matches(target_name, candidates.keys(), n=1, cutoff=0.4)
        if best_match_name:
            found_name = best_match_name[0]
            log.info(f"[MSRC] Identified Variant: {best_match_name[0]} (ID: {candidates[best_match_name[0]]})")
            return candidates[found_name]
        
        return None
    
    def windows_get_cves(self, os_scan_result):
        """
        Fetches Windows CVEs.
        """
        cvrf = self.windows_get_latest_updates()
        if not cvrf:
            return []
        
        pid = self.windows_find_product_id(
            cvrf,
            os_scan_result['metadata'].get('family', 'Windows'),
            os_scan_result['version']
        )

        if not pid:
            log.warning(f"[MSRC] Could not map OS to Product ID: {os_scan_result['name']}")
            return []
        
        relevant_cves = []
        vulnerabilities = cvrf.get("Vulnerability", [])

        for vuln in vulnerabilities:
            product_statuses = vuln.get("ProductStatuses", [])
            if not product_statuses:
                continue

            # Check if this vuln affects our Product ID
            affected_ids = product_statuses[0].get("ProductID", [])
            
            if pid in affected_ids:
                cve_id = vuln.get("CVE")
                title = vuln.get("Title", {}).get("Value")

                max_score = 0.0
                cvss_sets = vuln.get("CVSSScoreSets", [])
                for score_set in cvss_sets:
                    # Some scores are specific to product IDs, but taking the max is a safe fallback
                    s = score_set.get("BaseScore", 0.0)
                    if s > max_score:
                        max_score = s
                
                relevant_cves.append({
                    "cve_id": cve_id,
                    "summary": title,
                    "score": float(max_score),
                    "base_severity": "HIGH" if max_score >= 7.0 else "MEDIUM",
                    "status": "Analyzed (MSRC)"
                })
                
        return relevant_cves
    
    # Apps Logic
    def _check_cache(self, raw_name: str) -> Tuple[str, str, int]:
        """
        Checks if we have already analyzed this software name.
        """
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT vendor, product, trust_score FROM cpe_cache WHERE software_name = %s", (raw_name,))
                res = cur.fetchone()
                if res: 
                    return res[0], res[1], res[2]
        finally:
            self.db_pool.putconn(conn)
        return None, None, 0
    
    def _save_to_cache(self, raw_name: str, vendor: str, product: str, score: int = 1):
        """
        Saves valid analysis to DB to speed up future runs.
        """
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cpe_cache (software_name, vendor, product, trust_score) 
                    VALUES (%s, %s, %s, %s) 
                    ON CONFLICT (software_name) DO NOTHING
                    """,
                    (raw_name, vendor, product, score)
                )
                conn.commit()
        finally:
            self.db_pool.putconn(conn)

    def _update_cache_score(self, raw_name: str, new_score: int):
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE cpe_cache SET trust_score = %s WHERE software_name = %s", (new_score, raw_name))
                conn.commit()
        finally:
            self.db_pool.putconn(conn)

    def _overwrite_cache(self, raw_name: str, new_vendor: str, new_product: str):
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE cpe_cache SET vendor = %s, product = %s, trust_score = 1 WHERE software_name = %s",
                    (new_vendor, new_product, raw_name)
                )
                conn.commit()
        finally:
            self.db_pool.putconn(conn)

    def _get_db_candidates(self, raw_name: str) -> List[str]:
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                # 1. Clean but keep spaces first: "Visual Studio Code" -> "visual studio code"
                clean_raw = re.sub(r'\d+(\.\d+)*', '', raw_name).lower()
                clean_raw = re.sub(r'[^a-z ]', '', clean_raw).strip()
                
                # Formats: "visual_studio_code"
                search_term = clean_raw.replace(" ", "_")
                if len(search_term) < 3: 
                    search_term = raw_name.lower()

                # --- STEP 1: Relaxed Fuzzy Search ---
                cur.execute("SET pg_trgm.similarity_threshold = 0.05;")
                
                # Use %% for the operator because we are in Python
                query = """
                    SELECT product FROM cpe_entries 
                    WHERE product %% %s 
                    GROUP BY product
                    ORDER BY MAX(similarity(product, %s)) DESC 
                    LIMIT 5
                """
                cur.execute(query, (search_term, search_term))
                results = [row[0] for row in cur.fetchall()]

               # Fallback: Last Word
                if not results and " " in clean_raw:
                    last_word = clean_raw.split(" ")[-1]
                    if len(last_word) > 3: 
                        cur.execute(query, (last_word, last_word))
                        results = [row[0] for row in cur.fetchall()]

                # Fallback: ILIKE
                if not results:
                    query_like = "SELECT product FROM cpe_entries WHERE product ILIKE %s LIMIT 5"
                    cur.execute(query_like, (f"%{search_term}%",))
                    results = [row[0] for row in cur.fetchall()]

                # --- LOGGING ---
                if results:
                    log.info(f"[OK] DB Matches for '{raw_name}': {results[:3]}")
                else:
                    log.warning(f"[!] ZERO matches for '{raw_name}' (Searched: '{search_term}')")
                    
                return results

        except Exception as e:
            log.error(f"[DB] Candidate Search Failed: {e}")
            return []
        finally:
            self.db_pool.putconn(conn)
    
    def _ask_ai_to_select_cpe(self, raw_name: str, candidates: List[str]) -> Tuple[str, str]:
        """Uses LLM to pick the best match from a list of valid candidates."""
        if not candidates: 
            return "%", "%"

        # Optimization: Exact string match check
        clean = raw_name.lower().replace(" ", "_")
        if clean in candidates:
            return self._get_vendor_for_product(clean)
        
        system_prompt = """You are a CPE Selector. 
        I will give you a Raw Software Name and a list of Database Candidates.
        Your job is to return the ONE candidate that matches the software.
        
        Rules:
        1. Return JSON: {"match": "candidate_name"} or {"match": null}
        2. Be strict. "Visual Studio 2022" != "Visual Studio Code".
        3. If the candidate list contains only garbage, return null.
        """
        
        user_prompt = f"""
        Raw Name: "{raw_name}"
        Candidates: {json.dumps(candidates)}
        """

        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.0} 
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=5)
            content = json.loads(response.json()["message"]["content"])
            best_match = content.get("match")
            
            if best_match and best_match in candidates:
                return self._get_vendor_for_product(best_match)
                
        except Exception as e:
            log.error(f"AI Selection Error: {e}")

        return "%", "%"
    
    def _get_vendor_for_product(self, product: str) -> Tuple[str, str]:
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT vendor FROM cpe_entries WHERE product = %s LIMIT 1", (product,))
                res = cur.fetchone()
                if res: 
                    return res[0], product
        finally:
            self.db_pool.putconn(conn)
        return "%", "%"
    
    def _is_version_vulnerable(self, scanned_ver_str: str, rule: Dict) -> bool:
        """
        Delegates to VersionMatcher for smart filtering.
        """
        return VersionMatcher.is_vulnerable(scanned_ver_str, rule)
    
    # Core Execution Flow 
    def find_vulnerabilities(self, software_list: List[Dict]) -> List[Dict]:
        if not software_list: 
            return []

        log.info(f"[SCAN] Analyzing {len(software_list)} items...")
        grouped_items = {}    

        for idx, item in enumerate(software_list):
            if idx % 10 == 0:
                print(f"[SCAN] Progress: {idx}/{len(software_list)} items processed...", flush=True)

            # 1. Windows OS
            if item.get("type") == "operating_system" and item.get("metadata", {}).get("family") == "windows":
                try:
                    item['vulnerabilities'] = self.windows_get_cves(item)
                except Exception as e:
                    log.error(f"[MSRC] Scan Error: {e}")
                continue

            # 2. Apps Logic
            raw_name = item['name']
            
            # Step A. Check Cache
            cached_vendor, cached_product, trust_score = self._check_cache(raw_name)
            final_vendor, final_product = cached_vendor, cached_product

            # Step B. Logic Tree
            if not cached_vendor or trust_score < 3:
                candidates = self._get_db_candidates(raw_name)

                if candidates:
                    clean_no_num = re.sub(r'\d+(\.\d+)*', '', raw_name).lower().strip().replace(" ", "_")

                    # Scenario 1: Exact Match
                    if clean_no_num in candidates:
                        ai_vendor, ai_product = self._get_vendor_for_product(clean_no_num)
                        log.info(f"[MATCH] Exact match: '{raw_name}' -> '{ai_product}'")
                        
                        if not cached_vendor:
                            self._save_to_cache(raw_name, ai_vendor, ai_product, score=3)
                        elif cached_product != ai_product:
                            self._overwrite_cache(raw_name, ai_vendor, ai_product)
                            self._update_cache_score(raw_name, 3)
                         
                        final_vendor, final_product = ai_vendor, ai_product

                    # Scenario 2: AI Audit
                    else:
                        log.info(f"[AI] Verifying '{raw_name}' (Score: {trust_score}/3)...")
                        ai_vendor, ai_product = self._ask_ai_to_select_cpe(raw_name, candidates)
                    
                    if ai_vendor != "%":
                             if not cached_vendor:
                                 self._save_to_cache(raw_name, ai_vendor, ai_product, score=1)
                                 final_vendor, final_product = ai_vendor, ai_product
                             else:
                                 if ai_product == cached_product:
                                     new_score = trust_score + 1
                                     log.info(f"[TRUST] Consensus reached. Score updated: {new_score}/3")
                                     self._update_cache_score(raw_name, new_score)
                                 else:
                                     log.warning(f"[WARN] Conflict detected for '{raw_name}'. Resetting score.")
                                     self._overwrite_cache(raw_name, ai_vendor, ai_product)
                                     final_vendor, final_product = ai_vendor, ai_product
                else:
                    pass

            # Step C. Grouping
            if final_vendor:
                key = (final_vendor, final_product)
                if key not in grouped_items: 
                    grouped_items[key] = []
                grouped_items[key].append(idx)

        # 3. Batch SQL Query
        if not grouped_items: 
            return software_list

        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:                
                for (vendor, product), indices in grouped_items.items():
                    # Construct search pattern
                    if vendor == "%":
                        search_pattern = f"%:{product}:%"
                    else:
                        search_pattern = f"%:{vendor}:{product}:%"
                    
                    query = """
                        SELECT 
                            m.cve_id, 
                            m.version_start_including as v_start_inc, 
                            m.version_end_including as v_end_inc, 
                            m.version_end_excluding as v_end_exc,
                            m.cpe_uri,
                            c.summary, 
                            c.cvss_v3_base_score as severity, 
                            c.base_severity as severity_level
                        FROM cve_cpe_entries m 
                        JOIN cve_entries c ON m.cve_id = c.cve_id
                        WHERE m.vulnerable = true AND m.cpe_uri ILIKE %s
                    """
                    cur.execute(query, (search_pattern,))
                    potential_cves = cur.fetchall()

                    if potential_cves:
                        for idx in indices:
                            item = software_list[idx]
                            if 'vulnerabilities' not in item: 
                                item['vulnerabilities'] = []
                            
                            for cve_row in potential_cves:
                                if self._is_version_vulnerable(item['normalized_version'], cve_row):
                                    if not any(v['cve_id'] == cve_row['cve_id'] for v in item['vulnerabilities']):
                                        item['vulnerabilities'].append({
                                            "cve_id": cve_row['cve_id'],
                                            "summary": cve_row['summary'],
                                            "score": float(cve_row['severity'] or 0),
                                            "base_severity": cve_row['severity_level'],
                                            "status": "Analyzed"
                                        })
        except Exception as e:
            log.error(f"[DB] SQL Batch Error: {e}")
        finally:
            if conn:
                self.db_pool.putconn(conn)

        return software_list