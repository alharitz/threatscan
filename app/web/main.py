# app/web/main.py

from flask import Flask, render_template, jsonify, abort, redirect, url_for, request
import os
import json
import sys
import time
import subprocess

# --- 1. Magic Pathing Biar Bisa Import dari Root! ---
# Ini nambahin folder 'vuln_scanner/' (induknya 'app/') ke path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# --- 2. Import Helper & API kita ---
from utils.paths import RESULT_STORAGE_DIR  # noqa: E402
# Path helper kita!
# Kita komen dulu import LLM-nya, sesuai permintaanmu
# import app.api.llm_api as main_api

app = Flask(
    __name__,
    # Pathing template-nya kita benerin pake PROJECT_ROOT
    template_folder=os.path.join(PROJECT_ROOT, 'app', 'templates'),
    static_folder=os.path.join(PROJECT_ROOT, 'app'),
    static_url_path='/app'
)

# --- 3. Helper Buat Ngebaca Laporan ---
def load_report():
    """Membaca file laporan JSON yang udah mateng."""
    report_path = os.path.join(RESULT_STORAGE_DIR, "vulnerability_report.json")
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Ambil waktu kapan file terakhir diubah
        last_modified_timestamp = os.path.getmtime(report_path)
        last_scan_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_timestamp))
        return data, last_scan_time # Kembalikan data DAN waktu scan
    except FileNotFoundError:
        app.logger.error(f"File laporan TIDAK DITEMUKAN di: {report_path}")
        return None, None # Balikin None kalo filenya gak ada
    except Exception as e:
        app.logger.error(f"Gagal ngebaca file laporan: {e}")
        return None, None

# --- 4. Rute Halaman Utama (index.html) ---
@app.route('/')
def home():
    # Cuma nampilin halaman welcome
    scan_log_path = os.path.join(RESULT_STORAGE_DIR, 'scan_log.json')
    scan_logs = []
    try:
        with open(scan_log_path, 'r', encoding='utf-8') as f:
            scan_logs = json.load(f)
    except FileNotFoundError:
        app.logger.warning(f"scan_log.json not found at: {scan_log_path}")
    except json.JSONDecodeError:
        app.logger.error(f"Failed to decode scan_log.json")

    results = []
    for scan_log in scan_logs:
        results.append({
            "scan_id": scan_log['scan_id'],
            "date_time": scan_log['date_time'],
            "vuln_count": scan_log['vuln_count'],
            "status": scan_log['status'],
            "report_url": "/result/" + str(scan_log['scan_id'])
        })

    return render_template('index.html', scan_logs=results)

# --- 5. Hapus /scan! ---
# Proses scan hanya via CLI 'python main.py'

@app.route('/scan')
def scan():
    """
    Triggers a new scan by running the main.py script in the background.
    """
    try:
        # Get the python executable from the current environment
        python_executable = sys.executable
        # Get the absolute path to main.py
        main_py_path = os.path.join(PROJECT_ROOT, 'main.py')
        
        # Run the scan in a separate process
        subprocess.Popen([python_executable, main_py_path])
        
        # Redirect to the results page
        return redirect(url_for('result'))
    except Exception as e:
        app.logger.error(f"Failed to start scan: {e}")
        return "Error: Failed to start scan.", 500

# --- 6. /result: Halaman Utama Laporan ---
@app.route('/result/<int:scan_id>')
def result(scan_id):
    vuln_report_path = os.path.join(RESULT_STORAGE_DIR, 'vulnerability_report'+ '_' + str(scan_id) + '.json')
    vuln_report = []

    try:
        with open(vuln_report_path, 'r', encoding='utf-8') as f:
            vuln_report = json.load(f)
    except FileNotFoundError:
        app.logger.warning(f"vulnerability_report.json not found at: {vuln_report_path}")
    except json.JSONDecodeError:
        app.logger.error(f"Failed to decode vulnerability_report.json")

    vulnerable_items = [item for item in vuln_report if item.get('vulnerabilities')]
    non_vulnerable_items = [item for item in vuln_report if not item.get('vulnerabilities')]

    def get_severity_class(severity):
        severity = severity.upper() if severity else 'NONE'
        if severity == 'CRITICAL':
            return 'bg-purple-600 text-white'
        elif severity == 'HIGH':
            return 'bg-red-600 text-white'
        elif severity == 'MEDIUM':
            return 'bg-orange-500 text-black'
        elif severity == 'LOW':
            return 'bg-yellow-400 text-black'
        else:
            return 'bg-gray-500 text-white'

    return render_template(
        'result.html', 
        scan_id=scan_id,
        vulnerable_items=vulnerable_items,
        non_vulnerable_items=non_vulnerable_items,
        get_severity_class=get_severity_class
    )

# --- 7. /detail/<scan_id>/<item_name>: Halaman Detail Item ---
@app.route('/detail/<int:scan_id>')
def detail(scan_id):
    item_name = request.args.get('item_name')
    if not item_name:
        abort(400, description="Item name must be provided as a query parameter.")
    vuln_report_path = os.path.join(RESULT_STORAGE_DIR, 'vulnerability_report'+ '_' + str(scan_id) + '.json')
    
    try:
        with open(vuln_report_path, 'r', encoding='utf-8') as f:
            vuln_report = json.load(f)
    except FileNotFoundError:
        abort(404, description=f"Report for scan ID '{scan_id}' not found.")
    except json.JSONDecodeError:
        abort(500, description="Failed to decode the report file.")

    found_item = None
    for item in vuln_report:
        if item.get("name") == item_name:
            found_item = item
            break

    if not found_item:
        abort(404, description=f"Item '{item_name}' not found in scan ID '{scan_id}'.")

    def get_severity_class(severity):
        severity = severity.upper() if severity else 'NONE'
        if severity == 'CRITICAL':
            return 'bg-purple-600 text-white'
        elif severity == 'HIGH':
            return 'bg-red-600 text-white'
        elif severity == 'MEDIUM':
            return 'bg-orange-500 text-black'
        elif severity == 'LOW':
            return 'bg-yellow-400 text-black'
        else:
            return 'bg-gray-500 text-white'

    return render_template('detail.html', item=found_item, scan_id=scan_id, get_severity_class=get_severity_class)

# --- 8. /cve/<cve_id>: Halaman Detail CVE ---
@app.route('/cve/<cve_id>')
def cve_detail(cve_id):
    # For now, this is a mock. We'll fetch real data later.
    # You would typically fetch the CVE data from your database
    # or an external API using the cve_id.
    return render_template('cve_detail.html', cve_id=cve_id)

# --- 8. API buat LLM (Udah Siap, Tinggal Un-comment) ---
@app.route('/api/mitigate/<cve_id>')
def api_mitigate(cve_id):
    report_data, _ = load_report()
    if report_data is None:
        return jsonify({"error": "Report file not found"}), 404

    summary = ""
    for item in report_data:
        for vuln in item.get("vulnerabilities", []):
            if vuln.get("cve_id", "").strip() == cve_id.strip():
                summary = vuln.get("summary")
                break
        if summary: 
            break # Keluar dari loop luar juga

    if not summary:
        return jsonify({"error": "CVE not found in report"}), 404

    try:
        # --- NANTI DI-UNCOMMENT KALAU LLM SIAP ---
        # mitigation_text = main_api.main(summary)
        # return jsonify({"mitigation": mitigation_text})
        # ----------------------------------------

        # --- UNTUK SEKARANG, KITA KASIH DUMMY DATA ---
        time.sleep(2) # Simulasi loading LLM
        return jsonify({"mitigation": f"Mitigation steps for {cve_id} (generated by AI):\n- Step 1\n- Step 2\n- Step 3 (This is dummy data)"})
        # --------------------------------------------

    except Exception as e:
        app.logger.error(f"LLM API error (dummy or real): {e}")
        return jsonify({"error": "Failed to get mitigation"}), 500

if __name__ == '__main__':
    # Pastiin port-nya 5000 (sesuai file main.py lama kamu)
    app.run(debug=True, port=5000)