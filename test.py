import scanner

software_list = [
    {"name": "npm", "version": "8.5.1"},         # CVE-2022-37599
    {"name": "node", "version": "16.14.2"},      # CVE-2022-32213
    {"name": "openssl", "version": "3.0.7"},      # CVE-2023-0286
    {"name": "python", "version": "3.10.6"}       # No CVE (test negative case)
]

def main():
    print(scanner.get_node_version_windows())
    
if __name__ == "__main__":
    main()