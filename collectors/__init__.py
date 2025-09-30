from .module.system.os_collector import OSCollector
from .module.system.processes_collector import ProcessCollector
from .module.system.programs_collector import ProgramsCollector

from .module.languages.python_collector import PythonCollector
from .module.languages.javascript_collector import JavaScriptCollector
from .module.languages.php_collector import PHPCollector
from .module.languages.perl_collector import PerlCollector
from .module.languages.ruby_collector import RubyCollector
from .module.languages.rust_collector import RustCollector

__all__ = [
    "OSCollector",
    "ProcessCollector",
    "ProgramsCollector",
    "PythonCollector",
    "JavaScriptCollector",
    "PHPCollector",
    "PerlCollector",
    "RubyCollector",
    "RustCollector"
]
