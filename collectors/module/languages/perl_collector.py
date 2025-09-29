from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
import shutil
import subprocess

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("perl")

class PerlCollector(BaseCollector):

    def _perl_path(self):
        try:
            perl_path = shutil.which("perl")

            return perl_path

        except Exception as e:
            log.error(f"Failed collecting Perl Path: {e}", exc_info=True)
            return None


    def _perl_version(self):
        perl_path = self._perl_path()

        try:
            if perl_path is None:
                return  None
            
            version = subprocess.check_output(
                [perl_path, "-E", "say substr($^V,1)"],
                text=True
            ).strip()

            return version

        except Exception as e:
            log.error(f"Failed collecting Perl Version: {e}", exc_info=True)
            return None

    def detect(self) -> bool:
        return shutil.which("perl") is not None
    
    def collect(self) -> list[dict]:
        results = []

        perl_version = self._perl_version()
        perl_path = self._perl_path()

        try:
            packages = []
            if perl_path is not None:
                
                output = subprocess.check_output(
                    [
                        perl_path, "-MExtUtils::Installed", 
                        "-E", 'my $inst=ExtUtils::Installed->new; say "$_ " . $inst->version($_) for $inst->modules'
                    ],

                    text=True,
                    stderr=subprocess.STDOUT
                )

                for line in output.splitlines():
                    parts = line.strip().split(maxsplit=1)

                    if len(parts) :
                        name, version = parts
                        version = version.strip("v")

                        packages.append({
                            "name": name,
                            "version": version
                        })

            else:
                log.error("Failed collecting Perl Path")

            results.append({
                "language": "perl",
                "language_version": perl_version,
                "packages": packages
            })

            return results

        except Exception as e:
            log.error(f"Failed collecting Perl Modules: {e}", exc_info=True)
            return []