# core/matcher.py

from utils.logger import setup_logger
from db.connection import get_db_connection
import psycopg2.pool
from psycopg2.extras import DictCursor
from packaging.version import Version, InvalidVersion

log = setup_logger()
log = log.getChild("matcher")

class Matcher:
    def __init__(self, db_pool: psycopg2.pool.SimpleConnectionPool = None):
        """
        Init matcher with pool
        """
        self.db_pool = db_pool or get_db_connection()
        if not self.db_pool:
            log.error("Failed to initialize database connection pool.")
            raise ConnectionError("Database pool could not be initialized.")

    def _is_version_vulnerable(self, software_version_str: str, rule: dict) -> bool:
        try:
            software_version = Version(software_version_str)

            has_start = rule.get("version_start_including") or rule.get("version_start_excluding")
            has_end = rule.get("version_end_including") or rule.get("version_end_excluding")

            if not has_start and not has_end:
                cpe_uri = rule.get("cpe23uri", "")
                if software_version_str in cpe_uri:
                    return True
                else:
                    return False

            start_incl = rule.get("version_start_including")
            start_excl = rule.get("version_start_excluding")

            if start_incl:
                if software_version < Version(start_incl):
                    return False
            elif start_excl:
                if software_version <= Version(start_excl):
                    return False

            end_incl = rule.get("version_end_including")
            end_excl = rule.get("version_end_excluding")

            if end_incl:
                if software_version > Version(end_incl):
                    return False
            elif end_excl:
                if software_version >= Version(end_excl):
                    return False

            return True
            
        except InvalidVersion:
            return False
        except TypeError:
            return False
        except ValueError as e:
            log.warning(f"Error parsing version string in rule: {e}")
            return False

    def find_vulnerabilities(self, software_list: list[dict]) -> list[dict]:
        """
        Fungsi utama: Menerima list software, mengembalikan list
        yang sama tapi udah ditambahin key 'vulnerabilities'.
        """
        if not software_list:
            log.warning("Software list is empty, nothing to match.")
            return []
            
        conn = None
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor(cursor_factory=DictCursor)
            
            search_terms = list(set(
                f"%{item['normalized_name']}%" for item in software_list
            ))
            
            # Query ini gabungin cpe_entries dan cve_cpe_entries!
            # Ini nyari semua 'aturan' (CVE-CPE match) yang 'product'-nya
            # mirip sama software yang kita scan.
            
            # Kita ambil product dari cpe_entries biar bisa ILIKE
            # Terus kita JOIN ke cve_cpe_entries
            
            # NOTE: Ini bisa di-improve lagi, tapi ini awal yg bagus
            query = """
                WITH matching_cpes AS (
                    SELECT cpe23uri
                    FROM cpe_entries
                    WHERE product ILIKE ANY(%s)
                )
                SELECT
                    e.product, e.cpe23uri,
                    m.cve_id, m.vulnerable,
                    m.version_start_including, m.version_start_excluding,
                    m.version_end_including, m.version_end_excluding
                FROM
                    matching_cpes mc
                JOIN
                    cve_cpe_entries m ON mc.cpe23uri = m.cpe_uri
                JOIN
                    cpe_entries e ON mc.cpe23uri = e.cpe23uri;
            """
            
            cur.execute(query, (search_terms,))
            all_matching_rules = cur.fetchall()
            
            log.info(f"Found {len(all_matching_rules)} potential vulnerability rules...")
            
            all_found_cve_ids = set()

            software_dict = {item['normalized_name']: item for item in software_list}

            vulnerability_map = {item['normalized_name']: set() for item in software_list}

            for rule in all_matching_rules:
                for sw_name in software_dict:
                    if sw_name == rule['product']:
                        
                        sw_item = software_dict[sw_name]
                        sw_version = sw_item['normalized_version']

                        if self._is_version_vulnerable(sw_version, rule):
                            log.debug(f"MATCH! {sw_name} {sw_version} is vulnerable to {rule['cve_id']}")
                            vulnerability_map[sw_name].add(rule['cve_id'])
                            all_found_cve_ids.add(rule['cve_id'])

            log.info(f"Found {len(all_found_cve_ids)} unique CVEs.")
            
            cve_details_map = {}
            if all_found_cve_ids:
                query_details = """
                    SELECT cve_id, summary, base_severity, cvss_v3_base_score
                    FROM cve_entries
                    WHERE cve_id IN %s;
                """
                cur.execute(query_details, (tuple(all_found_cve_ids),))
                cve_details_list = cur.fetchall()
                
                for cve in cve_details_list:
                    cve_details_map[cve['cve_id']] = dict(cve)
            
            final_results_list = []
            for item in software_list:
                sw_name = item['normalized_name']
                found_cves = vulnerability_map.get(sw_name, set())
                
                item['vulnerabilities'] = []
                
                for cve_id in found_cves:
                    if cve_id in cve_details_map:
                        item['vulnerabilities'].append(cve_details_map[cve_id])
                
                final_results_list.append(item)
            
            return final_results_list

        except Exception as e:
            log.error(f"Error during matching: {e}", exc_info=True)
            return software_list
        
        finally:
            if conn:
                self.db_pool.putconn(conn)