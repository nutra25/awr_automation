# selectors.py
from abc import ABC, abstractmethod
from typing import Tuple, Any
import math


# ----------------------------------------------------------------
# 1. SOYUT TEMEL SINIF (INTERFACE)
# ----------------------------------------------------------------
class BasePointSelector(ABC):
    """
    Tüm seçim stratejileri bu sınıftan türemelidir.
    Simülasyon yöneticisi sadece bu arayüzü (interface) bilir.
    """

    @abstractmethod
    def select_point(self, driver: Any, graph_name: str) -> Tuple[str, str, str]:
        """
        Geri dönüş formatı: (Value, Magnitude, Angle)
        Tüm değerler string olarak döner (AWR driver uyumluluğu için).
        """
        pass


# ----------------------------------------------------------------
# 2. STRATEJİ: TEK MARKER (Single Marker)
# ----------------------------------------------------------------
class MaxMarkerSelector(BasePointSelector):
    """
    En basit yöntem: Belirtilen marker (örn: m1) nerede ise orayı seçer.
    Genelde Max Power veya Max PAE noktası için kullanılır.
    """

    def __init__(self, marker_name: str = "m1"):
        self.marker_name = marker_name

    def select_point(self, driver: Any, graph_name: str) -> Tuple[str, str, str]:
        # Driver'dan veriyi çek: [Value, Mag, Ang]
        data = driver.get_marker_data(graph_name, self.marker_name)

        # Veri boşsa veya hata varsa güvenli çıkış
        if not data:
            return "0", "0", "0"

        return str(data[0]), str(data[1]), str(data[2])


# ----------------------------------------------------------------
# 3. STRATEJİ: TRADE-OFF (Örn: Power vs PAE)
# ----------------------------------------------------------------
class TradeOffSelector(BasePointSelector):
    """
    İki farklı marker okur ve bunların arasında ağırlıklı bir nokta belirler.
    weight=0.5 -> Tam orta nokta
    weight=0.8 -> Birinci marker'a %80 daha yakın
    """

    def __init__(self, marker1: str = "m1", marker2: str = "m2", weight: float = 0.5):
        self.m1 = marker1
        self.m2 = marker2
        self.weight = weight

    def select_point(self, driver: Any, graph_name: str) -> Tuple[str, str, str]:
        # İki marker verisini de al
        d1 = driver.get_marker_data(graph_name, self.m1)  # [Val, Mag, Ang]
        d2 = driver.get_marker_data(graph_name, self.m2)

        if not d1 or not d2:
            return "0", "0", "0"

        # Ağırlıklı Ortalama Hesapla
        w1 = self.weight
        w2 = 1.0 - self.weight

        # Magnitude (Genlik) Ortalaması
        avg_mag = (d1[1] * w1) + (d2[1] * w2)

        # Angle (Açı) Ortalaması
        # (Not: Basit aritmetik ortalama. Faz farkı çok büyükse vektörel toplama gerekebilir)
        avg_ang = (d1[2] * w1) + (d2[2] * w2)

        # Değer (Value) Ortalaması (Sembolik)
        avg_val = (d1[0] * w1) + (d2[0] * w2)

        return str(avg_val), str(avg_mag), str(avg_ang)