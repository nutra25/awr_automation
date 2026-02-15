# selectors.py
from abc import ABC, abstractmethod
from typing import Tuple, Any
import math
import heapq
from shapely.geometry import Polygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
import skrf as rf

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
    
# ----------------------------------------------------------------
# 4. STRATEJİ: BROADBAND OPTIMUM (Geniş Bant Kesişim Arama)
# ----------------------------------------------------------------
class BroadbandOptimumSelector(BasePointSelector):
    """
    Tüm frekansların PAE kontürlerini çeker.
    Max-Min Optimizasyonu ve BFS arama algoritması kullanarak
    tüm frekanslar için en dengeli kesişim alanını (Sweet Spot) bulur.
    Hedef olarak bu kesişim alanının merkezini (Centroid) döndürür.
    İsteğe bağlı olarak sonucu Smith Chart üzerinde görselleştirir.
    """

    def __init__(self, show_plot: bool = True):
        self.show_plot = show_plot

    def select_point(self, driver: Any, graph_name: str) -> Tuple[str, str, str]:
        # 1. Driver üzerinden tüm kontür verilerini al
        data_by_freq = driver.get_broadband_contours(graph_name)
        
        if not data_by_freq:
            print("[HATA] AWR'dan geçerli kontür verisi okunamadı.")
            return "0", "0", "0"

        # 2. Shapely Poligonlarına Dönüştürme
        freq_geoms = {}
        freqs = sorted(list(data_by_freq.keys()))
        
        for freq in freqs:
            sorted_contours = sorted(data_by_freq[freq], key=lambda x: x['pae'], reverse=True)
            geoms_list = []
            
            for contour in sorted_contours:
                polys = []
                for island in contour['islands']:
                    pts = list(zip(island['real'], island['imag']))
                    if len(pts) >= 3:
                        poly = Polygon(pts).buffer(0).simplify(0.0001)
                        polys.append(poly)
                        
                if polys:
                    unified_geom = unary_union(polys)
                    geoms_list.append({
                        'pae': contour['pae'],
                        'geom': unified_geom,
                        'islands': contour['islands']
                    })
            
            if geoms_list:
                freq_geoms[freq] = geoms_list

        freqs = [f for f in freqs if f in freq_geoms]
        num_freqs = len(freqs)
        
        if num_freqs == 0:
            return "0", "0", "0"

        # 3. KOTASIZ VE KESİN (EXACT) A* ARAMA ALGORİTMASI
        def get_metrics(state):
            current_paes = [freq_geoms[freqs[i]][state[i]]['pae'] for i in range(num_freqs)]
            min_pae = min(current_paes)
            drops = [freq_geoms[freqs[i]][0]['pae'] - current_paes[i] for i in range(num_freqs)]
            max_drop = round(max(drops), 4)
            sum_drop = round(sum(drops), 4)
            
            # Priority Queue en küçük değeri ilk çekeceği için, min_pae'yi eksi yapıyoruz.
            return -min_pae, max_drop, sum_drop

        initial_state = tuple([0] * num_freqs)
        queue = []
        heapq.heappush(queue, (*get_metrics(initial_state), initial_state))
        visited = set([initial_state])
        
        best_state = None
        best_intersection = None

        while queue:
            # DİKKAT: Artık len(queue) > 500 gibi bir kota yok!
            item = heapq.heappop(queue)
            state = item[-1]
            
            current_geom = freq_geoms[freqs[0]][state[0]]['geom']
            failed_index = -1 # Kesişimin koptuğu noktayı bulmak için ajan
            
            # Geometrileri sırayla kesiştir
            for i in range(1, num_freqs):
                current_geom = current_geom.intersection(freq_geoms[freqs[i]][state[i]]['geom'])
                if current_geom.is_empty:
                    failed_index = i # Çatışmayı çıkaran frekansı yakaladık!
                    break 
                    
            if failed_index == -1 and current_geom.area > 1e-6:
                # Kesişim başarılı! 
                # Priority Queue (Öncelik Kuyruğu) kullandığımız için bulduğumuz bu İLK sonuç 
                # MATEMATİKSEL OLARAK KESİN EN İYİ SONUÇTUR. Aramayı güvenle bitirebiliriz.
                best_state = state
                best_intersection = current_geom
                break
                
            # --- AKILLI BUDAMA (PRUNING) - DARBOĞAZI ÖNLEYEN MATEMATİK ---
            # Eğer kesişim 'failed_index' adımında koptuysa, ondan sonraki frekansları 
            # değiştirmek sonucu asla düzeltmez. Trilyonlarca ihtimali çöpe atıyoruz.
            # Sadece sorunu çıkaran 0 ile failed_index arasındaki frekansları feda etmeyi dene!
            branch_limit = failed_index + 1 if failed_index != -1 else num_freqs
            
            for i in range(branch_limit):
                if state[i] + 1 < len(freq_geoms[freqs[i]]):
                    next_state = list(state)
                    next_state[i] += 1
                    next_state = tuple(next_state)
                    
                    if next_state not in visited:
                        visited.add(next_state)
                        heapq.heappush(queue, (*get_metrics(next_state), next_state))

        # 4. Sonuçları Hesapla ve Döndür
        if best_state is None or best_intersection is None:
            print("[BAŞARISIZ] Geniş bant için ortak kesişim bulunamadı.")
            return "0", "0", "0"

        worst_case_pae = min([freq_geoms[freqs[i]][best_state[i]]['pae'] for i in range(num_freqs)])

        if best_intersection.geom_type in ['MultiPolygon', 'GeometryCollection']:
            geoms_to_plot = list(best_intersection.geoms)
        else:
            geoms_to_plot = [best_intersection]
            
        max_area = -1
        largest_poly = None
        for geom in geoms_to_plot:
            if geom.geom_type == 'Polygon' and geom.area > max_area:
                max_area = geom.area
                largest_poly = geom

        if largest_poly is not None:
            cx, cy = largest_poly.centroid.x, largest_poly.centroid.y
            mag = math.hypot(cx, cy)
            ang = math.degrees(math.atan2(cy, cx))
            
            print(f"[BAŞARILI] Optimum Kesişim Bulundu! Worst-Case PAE: {worst_case_pae}")
            print(f" -> Hedef Noktası: Mag = {mag:.4f}, Ang = {ang:.2f}°")

            # --- GÖRSELLEŞTİRME VE TAM EKRAN (FULL ZOOM) KAYIT EKLENTİSİ ---
            if self.show_plot:
                import os
                import time
                
                # 1. KANVAS AYARI: Lejantı sağa sığdırmak için genişlik (14) yükseklikten (12) fazla.
                fig = plt.figure(figsize=(14, 12), dpi=120)
                
                # Smith Chart ızgarasını çiz
                rf.plotting.smith(draw_labels=True)
                
                plt.title(f"{graph_name} - Broadband Optimum Target", fontsize=16, pad=15)

                # --- Kontür Çizim Döngüleri ---
                for i in range(num_freqs):
                    freq = freqs[i]
                    idx = best_state[i]
                    pae_val = freq_geoms[freq][idx]['pae']
                    islands = freq_geoms[freq][idx]['islands']
                    freq_ghz = freq / 1e9
                    
                    label_str = f"{freq_ghz:.2f} GHz (Hedef: {pae_val})"
                    first_island = True
                    trace_color = None
                    
                    for island in islands:
                        lbl = label_str if first_island else None
                        if first_island:
                            # GÜNCELLEME 1: Çizgi kalınlığı (linewidth) 1.5 yapıldı
                            p = plt.plot(island['real'], island['imag'], label=lbl, linewidth=0.2, alpha=0.99)
                            trace_color = p[0].get_color()
                            first_island = False
                        else:
                            # GÜNCELLEME 1: Çizgi kalınlığı (linewidth) 1.5 yapıldı
                            plt.plot(island['real'], island['imag'], linewidth=0.2, alpha=0.99, color=trace_color)

                for geom in geoms_to_plot:
                    if geom.geom_type == 'Polygon':
                        x, y = geom.exterior.xy
                        plt.fill(x, y, color='red', alpha=0.6, zorder=10)
                        # GÜNCELLEME 1: Kesişim sınır çizgisi inceltildi
                        plt.plot(x, y, color='black', linewidth=0.2, linestyle='--', zorder=11)
                
                # GÜNCELLEME 2: Hedef X işaretinin boyutu (markersize) 10'a düşürüldü
                plt.plot(cx, cy, marker='X', color='black', markersize=0.1, label='Optimum Target', zorder=15)
                # -------------------------------------------

                # 2. "FULL ZOOM" VE LEJANT AYARLARI
                # Smith Chart'ı sınırlara kilitle
                plt.xlim(-1.02, 1.02)
                plt.ylim(-1.02, 1.02)
                
                # Grafiğin kare formunu korumasını sağla
                plt.gca().set_aspect('equal', adjustable='box')

                # GÜNCELLEME 3: Lejant grafiği ezmemesi için DIŞARI (Sağ taraf) alındı.
                plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=10)
                
                # Kenar boşluklarını sıkılaştır
                plt.tight_layout()
                
                # 3. VEKTÖREL KAYIT (SVG)
                save_dir = "AWR_Plots"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                    
                timestamp = time.strftime("%H%M%S")
                filename = f"{save_dir}/{graph_name}_{timestamp}.svg"
                
                # bbox_inches='tight' ile dışarıdaki fazlalıkları kesip at
                plt.savefig(filename, bbox_inches='tight', format='svg')
                print(f" -> [VEKTÖREL GRAFİK KAYDEDİLDİ]: {filename}")
                
                plt.close()
            # --------------------------------

            return str(worst_case_pae), str(mag), str(ang)
        else:
            return "0", "0", "0"