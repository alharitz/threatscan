import subprocess

def run_command(cmd):

    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        return None
    return result.stdout.strip()
    

def main():
    # Example command to run
    cmd = "fewffw"
    output = run_command(cmd)
    if output is None:
        print(True)
    print(False)

if __name__ == "__main__":
    main()