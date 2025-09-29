from collectors import (
    PythonCollector,
    JavaScriptCollector,
    PHPCollector,
    RubyCollector,
    RustCollector,
    PerlCollector
)
from utils.logger import setup_logger
import json
import os

log = setup_logger()
log = log.getChild("testing")
log = log.getChild("languages_collector")


# PYTHON

def test_python_collector():
    collector = PythonCollector()
    assert isinstance(collector.detect(), bool)

    results = collector.collect()
    assert isinstance(results, list)

    assert all(isinstance(result, dict)
                and "path" in result
                and "python_version" in result
                and "packages" in result
                for result in results
                )

    for result in results:
        assert isinstance(result["path"], str)
        assert isinstance(result["python_version"], str)
        packages = result["packages"]
        assert isinstance(packages, list)

        assert all(isinstance(package, dict)
                    and "name" in package
                    and "version" in package
                    for package in packages
                    )
        
def save_python_collector():
    collector = PythonCollector()
    results = collector.collect()
    log.info(f"Python Detection: {collector.detect()}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/python_library.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved python packages list")
    except Exception as e:
        log.error(e)


# JS RUNTIMES
def test_js_collector():
    collector = JavaScriptCollector()
    results = collector.collect()

    assert isinstance(collector.detect(), bool)

    assert all(isinstance(result, dict) 
        and "runtime" in result
        and "version" in result
        and "packages" in result
        for result in results
        )

    for result in results:
        packages = result["packages"]
        assert isinstance(packages, list)
        
        assert all(isinstance(pkg, dict)
            and "name" in pkg
            and "version" in pkg
            for pkg in packages
            )


def save_js_collector():
    collector = JavaScriptCollector()
    results = collector.collect()
    
    log.info(f"JavaScript Detection: {collector.detect()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/javascript_packages.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved javascript packages list")
    except Exception as e:
        log.error(e)

def save_php_collector():
    collector = PHPCollector()
    results = collector.collect()
    
    log.info(f"PHP Detection: {collector.detect()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/php_packages.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved php packages list")
    except Exception as e:
        log.error(e)

def save_ruby_collector():
    collector = RubyCollector()
    results = collector.collect()
    
    log.info(f"Ruby Detection: {collector.detect()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/ruby_packages.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved ruby packages list")
    except Exception as e:
        log.error(e)


def save_rust_collector():
    collector = RustCollector()
    results = collector.collect()
    
    log.info(f"Rust Detection: {collector.detect()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/rust_packages.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved rust packages list")
    except Exception as e:
        log.error(e)

def save_perl_collector():
    collector = PerlCollector()
    results = collector.collect()
    
    log.info(f"Perl Detection: {collector.detect()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/perl_packages.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved perl packages list")
    except Exception as e:
        log.error(e)

if __name__ == "__main__":
    # test_python_collector()
    # save_python_collector()
    # save_js_collector()
    # save_php_collector()
    # save_ruby_collector()
    # save_rust_collector()
    save_perl_collector()
