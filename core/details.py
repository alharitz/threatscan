import json
import requests
import psycopg2.pool
from psycopg2.extras import DictCursor
from typing import Dict, Any

from utils.logger import setup_logger
from db.connection import get_db_connection

log = setup_logger().getChild("details")

# ---------------------------------------------------------
# 🤖 OLLAMA CONFIGURATION
# ---------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:4b"

def ask_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Sends a request to the local Ollama instance.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['message']['content']
    except requests.exceptions.ConnectionError:
        log.error("❌ Could not connect to Ollama! Is it running? (ollama serve)")
        return None
    except Exception as e:
        log.error(f"❌ Ollama API Error: {e}")
        return None

class CveDetailProvider:
    def __init__(self, db_pool: psycopg2.pool.SimpleConnectionPool = None):
        self.db_pool = db_pool or get_db_connection()

    def get_full_details(self, cve_id: str) -> Dict[str, Any]:
        """
        The Master Method: Called when user clicks 'Show Details'.
        """
        log.info(f"Fetching full details for {cve_id}...")
        
        # 1. Fetch Raw Data from DB
        raw_data = self._fetch_db_data(cve_id)
        if not raw_data:
            return {"error": f"CVE {cve_id} not found in database"}

        # 2. Generate Friendly Advice (AI)
        ai_data = {"title": "Analysis Unavailable", "mitigation": []}
        try:
            generated = self._generate_ai_insight(raw_data)
            if generated:
                ai_data = generated
        except Exception as e:
            log.error(f"AI Generation logic failed: {e}")

        # 3. Combine & Return
        return {
            "cve_id": raw_data['cve_id'],
            "title": ai_data.get('title'),
            "description": raw_data['description'],
            "severity": raw_data['severity'],
            "score": float(raw_data['score']) if raw_data['score'] else None,
            "published_date": str(raw_data['published_at']),
            # 🌟 FIX: Use the correct key 'affected_software'
            "affected_software": raw_data['affected_software'], 
            "mitigation_steps": ai_data.get('mitigation', []),
            "references": raw_data['references']
        }

    def _fetch_db_data(self, cve_id: str) -> Dict:
        """Internal: Queries Postgres for facts."""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # A. Get Main Info
                query_main = """
                    SELECT cve_id, summary, details, cvss_v3_base_score, 
                           base_severity, published_at, references_data
                    FROM cve_entries 
                    WHERE cve_id = %s
                """
                cur.execute(query_main, (cve_id,))
                row = cur.fetchone()
                if not row: return None

                # Parse JSON references
                refs = []
                if row['references_data']:
                    ref_data = row['references_data']
                    if isinstance(ref_data, str): ref_data = json.loads(ref_data)
                    refs = [r.get('url') for r in ref_data if r.get('url')]

                # B. Get Affected Software with RANGES
                # We fetch the specific version rules
                query_soft = """
                    SELECT DISTINCT e.vendor, e.product, e.version, e.part,
                           m.version_start_including, m.version_start_excluding,
                           m.version_end_including, m.version_end_excluding
                    FROM cve_cpe_entries m
                    JOIN cpe_entries e ON m.cpe_uri = e.cpe23uri
                    WHERE m.cve_id = %s
                    LIMIT 20
                """
                cur.execute(query_soft, (cve_id,))
                soft_rows = cur.fetchall()
                
                # Format the ranges nicely
                affected_list = []
                for r in soft_rows:
                    name = f"{r['vendor']} {r['product']}"
                    
                    # 1. Build Range Rules
                    rules = []
                    if r['version_start_including']: rules.append(f">= {r['version_start_including']}")
                    if r['version_start_excluding']: rules.append(f"> {r['version_start_excluding']}")
                    if r['version_end_including']:   rules.append(f"<= {r['version_end_including']}")
                    if r['version_end_excluding']:   rules.append(f"< {r['version_end_excluding']}")
                    
                    # 2. Determine Display String
                    if rules:
                        # Case A: We have a range (e.g. "< 2.52")
                        range_str = " AND ".join(rules)
                    elif r['version'] and r['version'] not in ['*', '-']:
                        # Case B: Exact Match (e.g. "2.51.0")
                        range_str = f"Exact Version: {r['version']}"
                    else:
                        # Case C: Actually affects all versions (or data missing)
                        range_str = "All versions"
                    
                    affected_list.append({
                        "name": name,
                        "range": range_str,
                        "type": r['part']
                    })
                
                return {
                    "cve_id": row['cve_id'],
                    "description": row['details'] or row['summary'],
                    "score": row['cvss_v3_base_score'],
                    "severity": row['base_severity'],
                    "published_at": row['published_at'],
                    "references": refs,
                    "affected_software": affected_list 
                }
        finally:
            self.db_pool.putconn(conn)

    def _generate_ai_insight(self, data: Dict) -> Dict:
        """Internal: Constructs prompt and calls Ollama."""
        
        description = data['description']
        
        # Extract software names safely
        soft_list_names = []
        if data.get('affected_software'):
             soft_list_names = [item['name'] for item in data['affected_software'][:5]]
        soft_preview = ", ".join(soft_list_names)

        # 1. System Prompt
        system_prompt = """
        You are a smart cybersecurity consultant helping a regular user fix a specific vulnerability.
        
        YOUR GOAL:
        Provide concrete, actionable steps to fix the issue. Do not be vague.

        RULES:
        1. **Be Specific**: If the issue is about "NTP" or "WireGuard", mention them explicitly. Do not hide the software name.
        2. **Explain Simply**: If you use a technical term, explain it in parentheses or a short sentence.
           - BAD: "Disable unauthenticated NTP." (Too hard)
           - BAD: "Fix your clock settings." (Too vague)
           - GOOD: "Disable unauthenticated NTP (Network Time Protocol) to prevent attackers from manipulating your system clock."
        3. **Prioritize Updates**: If a software update fixes it, that is always Step 1.
        
        OUTPUT FORMAT (JSON ONLY):
        {
            "title": "Action-Oriented Title (Max 6 words)",
            "mitigation": [
                "Step 1: Specific action (Why it helps)",
                "Step 2: Specific action (Why it helps)",
                "Step 3: Verification step"
            ]
        }
        """

        # 2. User Prompt
        user_prompt = f"""
        Vulnerability Analysis Request:
        
        Software: {soft_preview}
        CVE ID: {data['cve_id']}
        Technical Description: {description}
        
        Task: Provide 3 specific steps to fix or mitigate this. 
        Focus on what the user needs to click, update, or change.
        """
        
        # 3. Call Ollama
        json_response_str = ask_llm(system_prompt, user_prompt)
        
        if not json_response_str:
            return None

        # 4. Parse JSON
        try:
            return json.loads(json_response_str)
        except json.JSONDecodeError:
            log.warning(f"Ollama returned invalid JSON: {json_response_str}")
            return {
                "title": "Update Required", 
                "mitigation": ["Update your software immediately.", "Contact IT support.", "Monitor for strange behavior."]
            }