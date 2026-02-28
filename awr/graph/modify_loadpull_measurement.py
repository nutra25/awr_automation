import pyawr.mwoffice as mwoffice

def main():
    # 1. AWR Uygulamasına Bağlan
    # pyawr.mwoffice.CMWOffice() mevcut açık olan uygulamaya bağlanır.
    try:
        app = mwoffice.CMWOffice()
        print(f"AWR Versiyonuna Bağlandı: {app.Version}")
    except Exception as e:
        print("AWR uygulamasına bağlanılamadı. Lütfen AWR'ın açık olduğundan emin olun.")
        print(e)
        return

    # --- AYARLAR ---
    # Değişiklik yapmak istediğiniz Grafiğin adı (AWR'deki adıyla birebir aynı olmalı)
    TARGET_GRAPH_NAME = "it2_load_pull"

    # Hedeflediğiniz ölçüm türü (Örn: "G_LPCM" resimdeki ölçüm tipidir)
    # Eğer ölçümün tam adını biliyorsanız (legend'da yazar), doğrudan onu da aratabiliriz.
    MEASUREMENT_TYPE = "G_LPCM(PAE,0.5,12,50,0)[1,*]"

    # Yeni Değerler
    NEW_DATA_FILE_NAME = "load_data_2"  # Load Pull Data File Name
    NEW_CONTOUR_STEP = 0.7  # Contour Step (%)
    NEW_MAX_CONTOURS = 10  # Max number of contours
    # ---------------

    project = app.Project

    # 2. Grafiği Bul
    if not project.Graphs.Exists(TARGET_GRAPH_NAME):
        print(f"Hata: '{TARGET_GRAPH_NAME}' adında bir grafik bulunamadı.")
        return

    graph = project.Graphs.Item(TARGET_GRAPH_NAME)
    print(f"Grafik bulundu: {graph.Name}")

    # 3. Ölçümü Bul ve Güncelle
    # Grafikteki tüm ölçümleri tarayıp tipi 'G_LPCM' olanı buluyoruz.
    target_meas = None

    # Not: graph.Measurements koleksiyonu 1'den başlar (1-based index)
    for i in range(1, graph.Measurements.Count + 1):
        meas = graph.Measurements.Item(i)

        # Ölçüm isminde veya tipinde aradığımız ifade geçiyor mu?
        # meas.Type ölçümün kısaltmasını (G_LPCM gibi) döndürür.
        print (meas.Type)
        if meas.Type == MEASUREMENT_TYPE:
            target_meas = meas
            break

    if target_meas is None:
        print(f"Bu grafikte '{MEASUREMENT_TYPE}' tipinde bir ölçüm bulunamadı.")
        return

    print(f"Ölçüm bulundu: {target_meas.Name}")

    # 4. Parametreleri Değiştir
    # pyawr nesneleri sarmaladığı için (wrapper), alttaki COM nesnesine
    # erişmek için _get_inner() kullanıyoruz.
    raw_meas = target_meas._get_inner()

    # AWR API'de parametreler 'Parameters' koleksiyonunda tutulur.
    # Resimdeki sıralamaya göre indeksler (Genellikle):
    # Item(1): Load Pull Data File Name
    # Item(2): Data for contour(%)
    # Item(3): Contour Step (%)
    # Item(4): Max number of contours

    try:
        # Load Pull Data File Name (Parametre 1)
        print(f"Eski Dosya Adı: {raw_meas.Parameters.Item(1).Value}")
        raw_meas.Parameters.Item(1).Value = NEW_DATA_FILE_NAME
        print(f"Yeni Dosya Adı: {NEW_DATA_FILE_NAME}")

        # Contour Step (%) (Parametre 3)
        # API genellikle string olarak değer kabul eder, bu yüzden str() ile çeviriyoruz.
        raw_meas.Parameters.Item(3).Value = str(NEW_CONTOUR_STEP)
        print(f"Contour Step güncellendi: {NEW_CONTOUR_STEP}")

        # Max number of contours (Parametre 4)
        raw_meas.Parameters.Item(4).Value = str(NEW_MAX_CONTOURS)
        print(f"Max Contours güncellendi: {NEW_MAX_CONTOURS}")

        print("İşlem başarıyla tamamlandı.")

    except Exception as e:
        print("Parametreler güncellenirken hata oluştu.")
        print("Hata Detayı:", e)


if __name__ == "__main__":
    main()