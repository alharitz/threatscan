import requests
import zipfile
import xml.etree.ElementTree as ET
import time
from db.db import insert_cpe

def get_cpe():
    print("Trying to sync CPE...")

    zipFilePath = "data/cpe/official-cpe-dictionary_v2.zip"
    extract_dir = "data/cpe"
    cpeFilePath = "data/cpe/official-cpe-dictionary_v2.3.xml"

    url = "https://nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.zip"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MyCPEFetcher/1.0)"}

    # # Download the CPE dictionary
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(zipFilePath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("✅ Downloaded successfully")
    else:
        print("❌ Download failed:", response.status_code)
        return

    # Extract the XML file
    print("Extracting CPE...")
    with zipfile.ZipFile(zipFilePath, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    # Parse the XML file
    tree = ET.parse(cpeFilePath)
    root = tree.getroot()

    # XML namespaces
    namespaces = {
        "default": "http://cpe.mitre.org/dictionary/2.0",
        "cpe-23": "http://scap.nist.gov/schema/cpe-extension/2.3",
    }

    # Extract CPE 2.3 entries
    cpe_list = []
    count = 0
    start_time = time.time()

    print("Proccessing CPE entries...")
    for item in root.findall("default:cpe-item", namespaces):
        cpe23_name = ""
        title = ""

        cpe23 = item.find("cpe-23:cpe23-item", namespaces)
        title_elem = item.find("default:title", namespaces)

        if cpe23 is not None and "name" in cpe23.attrib:
            cpe23_name = cpe23.attrib["name"]

        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()

        if cpe23_name:
            parts = cpe23_name.split(":")
            part = parts[2] if len(parts) > 2 else ""
            vendor = parts[3] if len(parts) > 3 else ""
            product = parts[4] if len(parts) > 4 else ""
            version = parts [5] if len(parts) > 5 else ""

            cpe_list.append((cpe23_name, title, part, vendor, product, version))
            count += 1
    insert_cpe(cpe_list)
    elapsed_time = time.time() - start_time
    print(f"✅ Completed: {count} entries inserted in {elapsed_time:.2f} s")
