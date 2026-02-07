# strategies.py
from abc import ABC, abstractmethod
from typing import List
import objects  # PullResult nesnesini tanımak için


class BestResultStrategy(ABC):
    """
    Simülasyon sonuçları arasından 'en iyi' olanı seçmek için
    kullanılan temel soyut sınıf (Interface).
    """

    @abstractmethod
    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        pass


class MaxPointStrategy(BestResultStrategy):
    """
    Klasik Yöntem: 'point' değeri (Marker değeri) en yüksek olanı seçer.
    Genelde Max Power (dBm) için kullanılır.
    """

    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        if not results:
            raise ValueError("Sonuç listesi boş, en iyi sonuç seçilemiyor.")

        # point string geldiği için float'a çevirip karşılaştırıyoruz
        return max(results, key=lambda x: float(x.point))


class TargetPointStrategy(BestResultStrategy):
    """
    Örnek Alternatif: Belirli bir değere (örn: 40dBm) en yakın olanı seçer.
    Compression noktası bulmak için ideal olabilir.
    """

    def __init__(self, target_value: float):
        self.target = target_value

    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        # Hedef değere olan farkı (mutlak değer) en küçük olanı bul
        return min(results, key=lambda x: abs(float(x.point) - self.target))