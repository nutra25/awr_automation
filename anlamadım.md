# AWR Otomasyon Projesi - Mimari Güncelleme Raporu

Bu belge, AWR Microwave Office otomasyon projesinde gerçekleştirilen yapısal değişiklikleri, modülerleşme adımlarını ve sistemin yeni çalışma mantığını detaylandırmaktadır. Yapılan güncellemeler, kodun sürdürülebilirliğini, okunabilirliğini ve farklı projelere entegrasyon kapasitesini artırmak amacıyla yazılım mühendisliği standartlarına uygun olarak tasarlanmıştır.

## 1. Yapısal Değişiklikler ve İyileştirmeler

### 1.1. Merkezi Veri Dışa Aktarım Modülü (DataExporter)
* **Bağımlılıkların Giderilmesi:** `main.py` içerisinde yer alan ve yalnızca spesifik AWR değişkenlerine bağımlı olarak çalışan hantal `ResultsLogger` sınıfı projeden tamamen kaldırılmıştır.
* **Evrensel Mimari:** Yerine, projenin iş mantığından (domain logic) tamamen izole edilmiş `DataExporter` modülü entegre edilmiştir. Bu modül; CSV, JSON, metin (HTML/XML) ve ikili (Binary - SVG, PNG) dosya formatlarını merkezi olarak diske yazma sorumluluğunu üstlenmiştir.
* **Dinamik Dosya Yönetimi:** Sınıf, başlatılma aşamasında yalnızca temel dizini (base directory) referans alarak, oluşturulacak dosya adlarını ve yollarını ilgili fonksiyon çağrılarından parametrik olarak kabul edecek şekilde yapılandırılmıştır.

### 1.2. Gelişmiş Loglama Altyapısı (Logger)
* **Dinamik Renk Ataması:** Log modülü, statik renk tanımlamalarından arındırılmıştır. Projeye eklenen her yeni dosya, isminin özet (hash) değerine göre atanmış sabit bir renkle log ekranında temsil edilmektedir.
* **Hassas Sütun Hizalaması:** Sütun genişlikleri, uzun dosya adlarını (örneğin `awr_configure_schematic_rf_frequency.py`) destekleyecek şekilde 45 karakter genişliğine sabitlenmiş ve terminal ekranındaki tablosal hizalama kusursuz hale getirilmiştir.
* **Çalıştırma (Run) Bazlı Kayıt:** Log kayıtlarının tek bir dizinde karmaşa yaratmasını engellemek amacıyla, her simülasyon başlangıcında log dosyası doğrudan o anki işleme ait `RUN [Tarih-Saat]` dizininin altındaki `logs` klasörüne yönlendirilmiştir.

### 1.3. Grafik Üretiminin İzole Edilmesi
* **Bellek İçi (In-Memory) Derleme:** `lp_iteration_point_selector.py` modülü, işletim sistemi üzerinde doğrudan dosya oluşturma (`plt.savefig` veya `fig.write_html`) yetkilerinden arındırılmıştır.
* **Veri Devri:** Matplotlib ile üretilen 2D SVG grafikleri bellekte bayt dizisine (`io.BytesIO`), Plotly ile üretilen 3D grafikler ise HTML metin formatına dönüştürülerek doğrudan `DataExporter` nesnesine devredilmiştir.

### 1.4. Kapsam ve Göreceli Dizin Yönetimi
* `main.py` içerisindeki `SimulationManager`, alt klasör yollarını (`export_subpath`) dinamik olarak oluşturup ilgili alt fonksiyonlara ve iterasyon adımlarına parametre olarak aktaracak şekilde güncellenmiştir. Bu sayede referans hataları (scope issues) tamamen giderilmiştir.

---

## 2. Yeni Çalışma Mantığı ve Veri Akışı

Mevcut sistemde tüm modüller yalnızca kendi tanımlı görevlerini icra etmekte olup, birbirlerinin sorumluluk alanlarına müdahale etmemektedir. Yeni veri akışı şu şekilde işlemektedir:

1.  **Başlatma ve Yapılandırma:** `main.py` (SimulationManager) simülasyon matrisini oluşturur, AWR sürücüsünü başlatır ve `DataExporter` nesnesini ana hedef dizin ile örneklendirir (instantiate).
2.  **Veri Üretimi:** AWR sürücüsü ve nokta seçici (point selector) modüller, simülasyon iterasyonlarını çalıştırır, matematiksel hesaplamaları yapar ve grafikleri yalnızca bellekte (RAM) üretir.
3.  **Dışa Aktarım (Delegasyon):** Elde edilen sonuçlar (ölçüm verileri, HTML metinleri veya SVG bayt dizileri), dosya adları ve göreceli dizin yollarıyla birlikte `DataExporter` nesnesine iletilir.
4.  **Kalıcı Kayıt (Persistence):** `DataExporter`, gelen verinin içeriğini analiz etmeksizin, aldığı formata uygun (CSV, text, binary) yazma fonksiyonunu kullanarak veriyi diske güvenle kaydeder.
5.  **İzlenebilirlik:** Tüm bu süreç, profesyonel İngilizce loglama standartlarına ve ağaç dalı (`├──`, `└──`) hiyerarşisine sadık kalınarak `simulation.log` dosyasına saniye saniye işlenir.

Bu modüler yaklaşım, projenin ilerleyen safhalarında yeni veri formatlarının veya farklı simülasyon sürücülerinin sisteme sorunsuz bir şekilde entegre edilebilmesini güvence altına almaktadır.