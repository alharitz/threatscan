from collectors.module.base_collector import BaseCollector
import wmi

class OSCollector(BaseCollector):

    def detect(self) -> bool:
        return True
    
    def collect(self) -> list[dict]:
        results = []
        c = wmi.WMI()
        for os in c.Win32_OperatingSystem():
            results.append({
                    "name": os.Caption,
                    "version": os.Version
                    })

        return results
