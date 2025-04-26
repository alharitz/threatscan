from flask import Flask, render_template, jsonify
import scanner
import parser
import get_cpe
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan')
def scan():
    app.logger.debug("scanning")
    try:
        raw_results = scanner.run_scan()
        app.logger.debug("parsing results")
        
        parsed_results = parser.parse_scan_results(raw_results)
        app.logger.debug("getting mitigation")
        
        mitigation_results = get_cpe.main(parsed_results)
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