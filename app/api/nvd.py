import requests
import time
import json
import os

import api.llm as llm_api
from config.settings import settings

api_key = settings.NVD_API_KEY
if not api_key:
    raise ValueError("NVD_API_KEY environment variable not set")

def get_cpes(name, version):
    url = "https://services.nvd.nist.gov/rest/json/cpes/2.0"
    headers = {"apiKey": api_key, "Accept": "application/json"}

    # Vendor mapping for common software
    # TODO: add vendor mapping
    vendor_mapping = {
        "node": "nodejs",
        "python": "python_software_foundation",
        "npm": "nodejs",
    }

    params = {
        "keywordSearch": f"{vendor_mapping.get(name, name)} {version}",
        "resultsPerPage": 20,
        "startIndex": 0,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 404:
            print(f"No CPE data found for {name} {version}")
            return []
        if response.status_code == 404:
            print(f"No CPE data found for {name} {version}")
            return []
        response.raise_for_status()
        data = response.json()

        valid_cpes = []
        for product in data.get("products", []):
            cpe = product["cpe"]["cpeName"]
            # Validate version match and proper format
            if f":{version}:" in cpe and cpe.startswith("cpe:2.3:a:"):
                valid_cpes.append(cpe)

        return valid_cpes  # Return max 3 relevant CPEs

    except Exception as e:
        print(f"CPE Error for {name}: {str(e)}")
        return []


def get_cves(cpe):
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0/"
    params = {"cpeName": cpe}
    try:
        time.sleep(6)  # NVD API has rate limits of 5 requests/30 seconds
        time.sleep(6)  # NVD API has rate limits of 5 requests/30 seconds
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json().get("vulnerabilities", [])
    except Exception as e:
        print(f"CVE Error for {cpe}: {str(e)}")
        return []


def process_result(result):
    software_list = []

    for key, value in result.items():
        try:
            # parsed_value = json.loads(value)
            parsed_value = value
            # parsed_value = json.loads(value)
            parsed_value = value
        except json.JSONDecodeError:
            print(f"Skipping {key}, not a JSON structure.")
            continue

        print(f"Processing segment: {key}")

        # If it's a list (like node_version, installed_apps)
        if isinstance(parsed_value, list):
            for item in parsed_value:
                name = item.get("name")
                version = item.get("version")
                if name and version:
                    software_list.append({"name": name, "version": version})

    # print(f"\nFinal software list: {software_list}")
    return software_list


def main(result):
    software_list = process_result(result)
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

            results.setdefault(f"{name} {version}", []).extend(
                [
                    {
                        "cve_id": vul["cve"]["id"],
                        "description": next(
                            (
                                desc["value"]
                                for desc in vul["cve"]["descriptions"]
                                if desc["lang"] == "en"
                            ),
                            "",
                        ),
                        "cvss_score": vul["cve"]
                        .get("metrics", {})
                        .get("cvssMetricV31", [{}])[0]
                        .get("cvssData", {})
                        .get("baseScore", "N/A"),
                        "references": [
                            ref["url"]
                            for ref in vul["cve"]["references"]
                            if "advisory" in ref["url"].lower()
                            or "patch" in ref["url"].lower()
                        ],
                    }
                    for vul in vulnerabilities
                ]
            )

    # Save results
    with open("vulnerability_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Vulnerability report generated successfully!")

    # Mitigation
    return llm_api.simplify_mitigation(results)

    # with open("mitigation_results.json", "w") as f:
    #     json.dump(results, f, indent=2)

    # print("Mitigation report generated successfully!")
    #
