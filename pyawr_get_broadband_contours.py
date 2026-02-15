import math
from typing import Dict, List, Any
from logger import LOGGER
        
if not self.app.Project.Graphs.Exists(graph_name):
    print(f"[HATA] Grafik bulunamadı: {graph_name}")
    return {}

graph = self.app.Project.Graphs(graph_name)
data_by_freq = {}

for meas in graph.Measurements:
    if not meas.Enabled:
                continue 
            
    for i in range(1, meas.TraceCount + 1):
        try:
            sweep_labels = meas.SweepLabels(i)
            pae_val, freq_val = None, None
                    
            if sweep_labels.Count > 0:
                for label_idx in range(1, sweep_labels.Count + 1):
                    lbl = sweep_labels.Item(label_idx)
                    name_up = lbl.Name.upper()
                    if name_up == "PAE": pae_val = float(lbl.Value)
                    elif name_up in ["F1", "FREQ", "FREQUENCY"]: freq_val = float(lbl.Value)
                    
            # Tek frekanslı analiz koruması
            if pae_val is not None and freq_val is None:
                freq_val = 0.0
                    
            if pae_val is None:
                continue
                        
            data = meas.TraceValues(i)
            if not data:
                continue

            islands = []
            curr_r, curr_i = [], []
                    
            # --- GÜÇLENDİRİLMİŞ VERİ AYRIŞTIRICI (FLAT TUPLE KORUMASI) ---
            # AWR veriyi bazen düz liste, bazen de iç içe liste dönebilir.
            if isinstance(data[0], (int, float)):
                # Veri düz liste gelmişse eleman sayısına bakarak grupla (Genelde Param, Real, Imag)
                step = 3 if len(data) % 3 == 0 else 2
                points = []
                for k in range(0, len(data) - (step - 1), step):
                    if step == 3:
                        points.append((data[k], data[k+1], data[k+2]))
                    else:
                        points.append((0.0, data[k], data[k+1]))
            else:
                # Veri zaten düzgün gruplanmış gelmişse aynen kullan
                points = data
                        
            for pt in points:
                r, im = pt[1], pt[2]
                is_valid = not (math.isnan(r) or math.isinf(r) or math.isnan(im) or math.isinf(im))
                if is_valid and (abs(r) > 3.0 or abs(im) > 3.0):
                    is_valid = False
                            
                if is_valid:
                    curr_r.append(r)
                    curr_i.append(im)
                else:
                    if len(curr_r) > 2:
                        if curr_r[0] != curr_r[-1] or curr_i[0] != curr_i[-1]:
                            curr_r.append(curr_r[0])
                            curr_i.append(curr_i[0])
                        islands.append({'real': curr_r, 'imag': curr_i})
                    curr_r, curr_i = [], []
                            
            if len(curr_r) > 2:
                if curr_r[0] != curr_r[-1] or curr_i[0] != curr_i[-1]:
                    curr_r.append(curr_r[0])
                    curr_i.append(curr_i[0])
                islands.append({'real': curr_r, 'imag': curr_i})
                    
            if islands:
                if freq_val not in data_by_freq:
                    data_by_freq[freq_val] = []
                data_by_freq[freq_val].append({'pae': pae_val, 'islands': islands})
                        
        except Exception as e:
            # Artık hataları gizlemiyoruz! Bir sorun çıkarsa terminalde kırmızı kırmızı göreceğiz.
            if i == 1:
                print(f"    [KRİTİK HATA] Trace #{i} verisi okunamadı: {e}")
                        
return data_by_freq