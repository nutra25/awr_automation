Harika bir öngörü. İleride sisteme "Load and Match" veya tamamen farklı simülasyon tipleri eklemeyi planlıyorsanız, şu anki `SimulationManager`'ın Load-Pull mantığına sıkı sıkıya bağlı (tightly coupled) olması ciddi bir mimari engeldir.

Bu sorunu çözmek için yazılım mühendisliğinde sıkça başvurulan **Strategy Pattern** (Strateji Tasarım Deseni) veya modüler **Delegation** (Yetki Devri) yaklaşımını kullanmalıyız.

Bu yapıda `SimulationManager` sadece bir **Orkestratör** (yönetici) görevini üstlenmeli; durum (state) matrisini oluşturmalı, döngüleri döndürmeli ve dosya kayıtlarını yönetmelidir. İçeride dönen mühendislik hesabının (Load-Pull mu yoksa Load and Match mi olduğu) ne olduğunu bilmemelidir.

Aşağıda bu ayrımın nasıl yapılacağına dair hiyerarşik yapı ve akış şemasını sunuyorum:

### 1. Yeni Dosya ve Klasör Ağacı Görselleştirmesi

Load-Pull spesifik tüm iterasyon ve tuner hesaplamalarını `loadpull` klasörü altında yeni bir yönetici (sequence) dosyasına taşımalıyız.

```text
awr_automation/
│
├── main.py                     -> (Sadece Orkestrasyon: State döngüsü, loglama ve DataExporter)
│
├── loadpull/                   -> (Load-Pull Domain Klasörü)
│   ├── handlers.py             -> (Önceki adımda ayırdığımız StateHandler)
│   ├── sequence.py             -> [YENİ] LoadPullSequence Sınıfı (_run_iteration, _finalize_state vb.)
│   ├── tuner_utils.py          -> [YENİ] _build_tuner_params ve PullType Enum'ı
│   ├── lp_state_result_selector.py
│   └── lp_iteration_point_selector.py
│
└── ...

```

---

### 2. Sorumlulukların Bölünmesi (Separation of Concerns)

Kod yazmadan, mantıksal olarak hangi metodun nereye gideceğini şu şekilde özetleyebiliriz:

**A. `main.py` (SimulationManager Sınıfı)**
Görevleri sadece şunlar olmalıdır:

* State konfigürasyonlarını (VDS, VGS, Frekans vb.) okuyup matris oluşturmak.
* State başına yeni bir klasör (Graphs, EMP) yaratmak.
* `StateHandler` aracılığıyla state değişkenlerini devreye uygulamak.
* **[Kritik Nokta]:** İlgili analiz stratejisini (örneğin `LoadPullSequence`) çağırıp, "Bu state için işini yap ve bana sonuçları ver" demek.
* Gelen sonuçları CSV'ye yazmak ve projeyi kaydetmek.

**B. `loadpull/sequence.py` (LoadPullSequence Sınıfı)**
Şu an `main.py` içindeki yükü buraya alacağız. Görevleri:

* `_run_iteration` mantığını yürütmek (Source Pull ve Load Pull döngüleri).
* AWR Wizard opsiyonlarını (LP_MaxHarmonic, CenterMagnitude vb.) belirleyip çalıştırmak.
* Grafiklerden nokta seçimi için `POINT_SELECTOR`'ı tetiklemek.
* `_finalize_state` ile global maksimum noktalarını bulup devredeki Tuner'ları (Source ve Load) son hallerine getirmek ve ölçümleri alıp ana yöneticiye döndürmek.

**C. `loadpull/tuner_utils.py` (Yardımcı Araçlar)**

* `PullType` Enum yapısı ve `_build_tuner_params` metodu gibi sadece Load-Pull tuner formülleri üreten küçük yardımcı fonksiyonlar burada durmalıdır.

---

### 3. Mimari Akış Şeması (UML Akışı)

Sistem çalıştığında hiyerarşik akış tam olarak şu şekilde ilerleyecektir:

```text
[main.py] SimulationManager
   │
   ├── 1. State Kombinasyonunu Hazırla (VDS=40, Freq=13.0)
   ├── 2. Klasörleri Oluştur (State No 1)
   ├── 3. StateHandler'a Uygulat (VDS ayarlandı)
   │
   ├── 4. Stratejiyi Çalıştır ---> [loadpull/sequence.py] LoadPullSequence
   │                                 │
   │                                 ├── Iteration 1: Source Pull (Wizard -> Point Select)
   │                                 ├── Iteration 1: Load Pull (Wizard -> Point Select)
   │                                 ├── Iteration 2: Source Pull ...
   │                                 │
   │                                 └── Finalize State: Tuner'ları ayarla ve veriyi oku.
   │
   ├── 5. Sonuçları Geri Al <--------- (Ölçüm verileri döndü)
   ├── 6. DataExporter ile CSV'ye yaz.
   └── 7. EMP dosyasını kaydet.

```

### Sonraki Adım

Bu yapı sayesinde, ileride `LoadAndMatchSequence` adında yeni bir sınıf yazıp `main.py` içerisine sadece bir parametre olarak verebilirsiniz; ana iskeletiniz (döngüler, kayıtlar) hiç değişmemiş olur.

Bu mantıksal bölme planı kafanıza yattı mı? Onaylıyorsanız, bir sonraki aşamada bu iskelete uygun sınıfları yavaş yavaş oluşturmaya başlayabiliriz.