import src.app.scanner as scanner
import os
import requests
import json
import time
import api.llm_api as llm_api

software_list = [
    {"name": "npm", "version": "8.5.1"},         # CVE-2022-37599
    {"name": "node", "version": "16.14.2"},      # CVE-2022-32213
    {"name": "openssl", "version": "3.0.7"},      # CVE-2023-0286
    {"name": "python", "version": "3.10.6"}       # No CVE (test negative case)
]

def get_cpes(name, version):
    url = "https://services.nvd.nist.gov/rest/json/cpes/2.0"
    headers = {"Accept": "application/json"}
    
    # Vendor mapping for common software
    vendor_mapping = {
        "node": "nodejs",
        "python": "python_software_foundation",
        "npm": "nodejs"
    }
    
    params = {
        "keywordSearch": f"{vendor_mapping.get(name, name)} {version}",
        "resultsPerPage": 20,
        "startIndex": 0
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        valid_cpes = []
        for product in data.get("products", []):
            cpe = product["cpe"]["cpeName"]
            # Validate version match and proper format
            if f":{version}:" in cpe and cpe.startswith("cpe:2.3:a:"):
                valid_cpes.append(cpe)
        
        return valid_cpes[:3]  # Return max 3 relevant CPEs

    except Exception as e:
        print(f"CPE Error for {name}: {str(e)}")
        return []

def get_cves(cpe):
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {"cpeName": cpe}
    
    try:
        # NVD rate limits (5 requests/30 seconds)
        time.sleep(6)
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json().get("vulnerabilities", [])
    except Exception as e:
        print(f"CVE Error for {cpe}: {str(e)}")
        return []

def main():
    # node_json = result['node_version']
    # software_list = json.loads(node_json)
    # print(f"node version: {software_list}")
    results = {}
    
    for software in software_list:
        name = software["name"]
        version = software["version"]
        cpes = get_cpes(name, version)
        
        if not cpes:
            print(f"No CPEs found for {name} {version}")
            continue
            
        for cpe in cpes:
            vulnerabilities = get_cves(cpe)
            
            if not vulnerabilities:
                continue
                
            results.setdefault(f"{name} {version}", []).extend([
                {
                    "cve_id": vul["cve"]["id"],
                    "description": next(
                        (desc["value"] for desc in vul["cve"]["descriptions"] 
                        if desc["lang"] == "en"), ""
                    ),
                    "cvss_score": vul["cve"].get("metrics", {}).get("cvssMetricV31", [{}])[0]
                                  .get("cvssData", {}).get("baseScore", "N/A"),
                    "references": [
                        ref["url"] for ref in vul["cve"]["references"]
                        if "advisory" in ref["url"].lower() or "patch" in ref["url"].lower()
                    ]
                }
                for vul in vulnerabilities
            ])
    
    # Save results
    with open("vulnerability_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Vulnerability report generated successfully!")
    
    # Mitigation
    return llm_api.simplify_mitigation(results)
    
    # with open("mitigation_results.json", "w") as f:
    #     json.dump(results, f, indent=2)
        
    # print("Mitigation report generated successfully!")

if __name__ == "__main__":
    main()