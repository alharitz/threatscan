from flask import Flask, render_template, jsonify
from .scanner import run_scan
from .parser import parse_scan_results

import os
import api.main_api as main_api
import json

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan')
def scan():
    app.logger.debug("scanning")
    try:
        raw_results = run_scan()
        app.logger.debug("parsing results")
        
        parsed_results = parse_scan_results(raw_results)
        
        # return render_template('scan.html', results=parsed_results)

        app.logger.debug("getting mitigation")
        with open("scan_results.json", "w") as f:
            json.dump(parsed_results, f, indent=2)
        
        mitigation_results = main_api.main(parsed_results)

        app.logger.debug("done!")
        return render_template('result.html', results=mitigation_results)
    except Exception as e:
        app.logger.error(f"Scan error: {e}")
        return f"Error during scan: {e}"
    
@app.route('/result')
def result():
    # with open('mitigation_results.json', 'r') as f:
    #     mitigation_data = json.load(f)
        
    return render_template('result.html')

@app.route('/detail')
def detail():
    return render_template('detail.html')

if __name__ == '__main__':
    app.run(debug=True)         