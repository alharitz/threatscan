from flask import Flask, render_template, jsonify
import scanner.main_scanner as main_scanner
import os
import api.main_api as main_api
import json
import time

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
        start_time = time.time()
        scan_results = main_scanner.main()
        end_time = time.time()
        total_time = start_time - end_time
        app.logger.debug(f"Scan time: {total_time}")
        app.logger.debug("Parsing results")
        
        # Convert dict to JSON string before passing to main_api
        mitigation_results = main_api.main(scan_results)

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