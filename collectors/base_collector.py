# /collectors/module/base_collector.py

from abc import ABC, abstractmethod

class BaseCollector(ABC):
    """Abstract base class for all packages collectors."""

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def detect(self) -> bool:
        """Check if this language/environment is available in the system"""
        pass

    @abstractmethod
    def collect(self)-> list[dict]:
        """Collect and listing all global packages"""
        pass

    def safe_collect(self) -> list[dict]:
        """Safely collect packages; returns [] if not detected or on error."""
        if not self.detect():
            return []
        try:
            return self.collect()
        except Exception as e:
            print(f"[{self.name}] error during collection: {e}")
            return []

