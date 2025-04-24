from flask import Flask, render_template, jsonify
import scanner
import parser

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan')
def scan():
    try:
        raw_results = scanner.run_scan()
        parsed_results = parser.parse_scan_results(raw_results)
        return render_template('scan.html', results=parsed_results)
    except Exception as e:
        return f"Error during scan: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)         