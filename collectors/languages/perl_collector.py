# collectors/languages/perl_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.languages import perl_parser
import shutil
import subprocess
from utils.normalize import normalize_name, normalize_version 

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("perl")

class PerlCollector(BaseCollector):

    def detect(self) -> bool:
        return shutil.which("perl") is not None
    
    def collect(self) -> list[dict]:
        results = []
        
        perl_path = shutil.which("perl")
        if perl_path is None:
            return []

        try:
            perl_version = subprocess.check_output(
                [perl_path, "-E", "say substr($^V,1)"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()
        except Exception as e:
            log.error(f"Failed collecting Perl Version: {e}", exc_info=True)
            perl_version = "unknown"

        runtime_name = "Perl"
        
        results.append({
            "name": runtime_name,
            "version": perl_version,
            "normalized_name": normalize_name(runtime_name),
            "normalized_version": normalize_version(perl_version),
            "type": "language_runtime"
        })

        try:
            output = subprocess.check_output(
                [
                    perl_path, "-MExtUtils::Installed", 
                    "-E", 'my $inst=ExtUtils::Installed->new; say "$_ " . $inst->version($_) for $inst->modules'
                ],
                text=True,
                stderr=subprocess.STDOUT
            )

            packages = perl_parser.perlParser(output, log)

            for pkg in packages:
                name = pkg.get("name")
                version = pkg.get("version")
                
                if not name or not version:
                    continue
                    
                pkg['normalized_name'] = normalize_name(name)
                pkg['normalized_version'] = normalize_version(version)
                pkg['type'] = 'perl_package'
                pkg['parent_language_version'] = perl_version
                results.append(pkg)

        except Exception as e:
            log.error(f"Failed collecting Perl Modules: {e}", exc_info=True)
            
        return results