import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN")
MODEL_ID = "@cf/mistral/mistral-7b-instruct-v0.1"

def simplify_mitigation(cve_data, api_choice="mistral"):
    prompt_template = """Convert this cybersecurity vulnerability description into 
    simple, actionable steps for a non-technical user. Keep all critical security 
    information but remove technical jargon. Format as bullet points:
    
    {description}"""
    
    results = {}
    
    for software, vulns in cve_data.items():
        results[software] = []
        for vuln in vulns:
            try:
                # Build LLM prompt
                prompt = prompt_template.format(description=vuln["description"])
                
                # Choose API endpoint
                
                response = requests.post(
                    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL_ID}",
                    headers={
                        "Authorization": f"Bearer {AUTH_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    json={"prompt": prompt}
                )
                
                if response.ok:
                    # Parse response
                    mitigation = response.json()["result"]["response"]
                
                    # Store simplified explanation
                    results[software].append({
                        "cve_id": vuln["cve_id"],
                        "risk_level": categorize_risk(vuln["cvss_score"]),
                        "simple_steps": mitigation,
                        "original_score": vuln["cvss_score"]
                    })
                else:
                    print(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Error processing {vuln['cve_id']}: {str(e)}")
    
    return results

def categorize_risk(score):
    """Convert CVSS to simple categories"""
    if score >= 9: return "Critical Risk"
    elif score >=7: return "High Risk"
    elif score >=4: return "Medium Risk"
    return "Low Risk"