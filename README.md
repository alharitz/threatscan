# ThreatScan

**ThreatScan** is a lightweight vulnerability scanning tool that integrates with Cloudflare Workers AI for threat intelligence. It scans your system environment and installed packages, then queries CVE databases to generate a comprehensive vulnerability report.

---

## 🚀 Features

- Scans OS, Python packages, Node.js/NPM packages, and more
- Retrieves Common Platform Enumerations (CPEs) for each software
- Queries CVE databases to fetch vulnerability details
- Generates a JSON vulnerability report
- Provides simple mitigation guidance

---

## 📦 Prerequisites

- Python 3.9 or higher
- A Cloudflare account with Workers AI access
- `pip` for managing Python dependencies

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/threatscan.git
   cd threatscan
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root (same level as `src/`) and add:
```bash
# Cloudflare API credentials
CLOUDFLARE_AUTH_TOKEN="your-token-here"
ACCOUNT_ID="your-account-id-here"
```

### Obtaining Your Cloudflare API Token
1. Sign up or log in to your Cloudflare account
2. In the dashboard, navigate to **AI > Workers AI > REST API**
3. Click **Create A Workers API Token**
4. Leave default permissions and create the token
5. Copy the token and your account ID into your `.env` file

---

## 🏃‍♂️ Running ThreatScan

From the project root, run:
```bash
# Ensure you're in the project root (contains src/)
cd threatscan/src

# Launch the scanner
python -m app.main
```

After completion, the vulnerability report will be saved to `data/reports/vulnerability_report.json`.

---

## 📤 Output

- **`vulnerability_report.json`**: Your main vulnerability report
- **`mitigation_results.json`**: Suggested mitigation steps for found CVEs

---

## 🧪 Testing

Run the test suite with:
```bash
pytest src/app/tests
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "feat: your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

