# core/context.py
from awr.awr_driver import AWRDriver
from core.dataexporter import DataExporter
from core.config import AppConfig

class AutomationContext:
    """
    Tüm projenin altyapı bağımlılıklarını ve global konfigürasyonunu tek bir
    çatı altında tutar. Modüller arası veri ve yetki taşıyıcısıdır.
    """
    def __init__(self, driver: AWRDriver, exporter: DataExporter, config: AppConfig):
        self.driver = driver
        self.exporter = exporter
        self.config = config