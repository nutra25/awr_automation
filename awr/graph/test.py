import pyawr.mwoffice as mwoffice


def change_measurement_source():
    # 1. MWOffice Uygulamasına Bağlan
    try:
        app = mwoffice.CMWOffice()
        print(f"Bağlanılan Proje: {app.Project.Name}\n")
    except Exception as e:
        print(f"MWOffice uygulamasına bağlanılamadı: {e}")
        return

    # Hedef Ölçüm Kriterleri (Eski Ayarlar)
    target_old_source = "load_data_1"
    target_type_keyword = "G_LPCM"
    target_param_keyword = "PAE"

    # Yeni Veri Kaynağı İsmi
    new_source_name = "load_data_2"

    found_meas = None

    # 2. Ölçümü Bul
    print("--- Ölçüm Aranıyor ---")
    for graph in app.Project.Graphs:
        for meas in graph.Measurements:
            # Kaynak, Tip ve Parametre kontrolü
            if (meas.Source == target_old_source and
                    target_type_keyword in meas.Name and
                    target_param_keyword in meas.Name):
                found_meas = meas
                print(f"HEDEF BULUNDU: {meas.Name}")
                break
        if found_meas:
            break

    if found_meas is None:
        print(f"Hata: '{target_old_source}' kaynağına sahip PAE ölçümü bulunamadı.")
        return

    # 3. Kaynağı Değiştir
    try:
        print(f"Mevcut Kaynak : {found_meas.Source}")

        # 'Source' özelliğine yeni dosya adını atıyoruz [1]
        found_meas.Source = new_source_name

        print(f"Yeni Kaynak   : {found_meas.Source}")
        print("\nİşlem başarılı. Grafik artık 'load_data_1' verisini kullanıyor.")

        # Değişikliğin grafiğe yansıması için simülasyonu tetikleyebiliriz
        if not found_meas.IsClean:
            print("Simülasyon güncelleniyor...")
            app.Project.Simulator.Analyze()

    except Exception as e:
        print(f"Kaynak değiştirilirken hata oluştu: {e}")
        print("Not: 'load_data_1' isimli veri dosyasının projede yüklü olduğundan emin olun.")


if __name__ == "__main__":
    change_measurement_source()