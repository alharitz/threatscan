import os
import shutil

def clean_project(root_dir='.'):
    for root, dirs, files in os.walk(root_dir):
        for d in dirs:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(root, d))
        for f in files:
            if f.endswith('.pyc') or f.endswith('.pyo'):
                os.remove(os.path.join(root, f))

if __name__ == '__main__':
    clean_project()
    print("Cleaned up all __pycache__ folders and .pyc files!")
