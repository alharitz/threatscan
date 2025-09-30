from abc import ABC, abstractmethod

class BaseCollector(ABC):
    """Abstarct base class for all packages collectors."""

    @abstractmethod
    def detect(self) -> bool:
        """Check if this language/environment is avaialable in the system"""
        pass

    @abstractmethod
    def collect(self)-> list[dict]:
        """Collect and listing all global packages"""
        pass

