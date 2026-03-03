import time
import pyawr.mwoffice as mwoffice


def get_all_data_for_single_point(app, graph_name, measurement_name):
    """
    Grafikteki ölçümü bulur ve ölçümün 1. noktasına ait
    tüm veri boyutlarındaki (DataDimension) Y değerlerini doğrudan çeker.
    """
    try:


        # 2. Grafiği bul
        graph = app.Project.Graphs.Item(graph_name)

        # 3. İstenen ölçümü KISMİ EŞLEŞME ile bul
        target_meas = None
        for i in range(1, graph.Measurements.Count + 1):
            meas = graph.Measurements.Item(i)
            if measurement_name in meas.Name:
                target_meas = meas
                print(f"Eşleşme bulundu: '{meas.Name}'")
                break

        if target_meas is None:
            print(f"Hata: İçinde '{measurement_name}' geçen ölçüm bulunamadı.")
            return None, None

        # 4. Veri noktası kontrolü
        if target_meas.XPointCount < 1:  # [3]
            print("Hata: Ölçümde hiç veri noktası yok (Simülasyon başarısız olmuş olabilir).")
            return None, None

        # Zaten tek noktamız olduğu için doğrudan 1. indeksteki X değerini alıyoruz
        single_x_val = target_meas.XValue(1)  # [3]

        # Bu noktaya ait kaç tane Y verisi (boyutu) olduğunu öğreniyoruz
        y_dimensions = target_meas.YDataDim  # [1]

        print(f"\nTek Nokta (X = {single_x_val}) İçin Tüm Veriler Çekiliyor...")
        print("-" * 50)

        all_y_values = []

        # 5. O noktaya ait tüm Y değerlerini çek
        for dim in range(1, y_dimensions + 1):
            # YValue(xIndex, DataDimension) kullanarak o noktadaki tüm verileri alıyoruz
            y_val = target_meas.YValue(1, dim)  # [2]
            all_y_values.append(y_val)

            print(f"Veri Boyutu [{dim}] ---> Y Değeri: {y_val}")

        print("-" * 50)

        # X noktasını ve ona ait tüm Y değerlerini liste olarak döndür
        return single_x_val, all_y_values

    except Exception as e:
        print(f"Veri çekme işlemi sırasında bir hata oluştu: {e}")
        return None, None


# ==========================================
# KULLANIM BÖLÜMÜ
# ==========================================
if __name__ == "__main__":
    app = mwoffice.CMWOffice()

    # Graph adını ve Measurement adını kendi projenize göre girin.
    x_noktasi, o_noktaya_ait_y_verileri = get_all_data_for_single_point(
        app=app,
        graph_name="it1_load_pull",
        measurement_name="G_LPCMMAX(PAE"
    )

    # Dilerseniz dönen bu ham verileri doğrudan yazdırabilir veya başka bir işleme sokabilirsiniz
    # print("Dönen Liste:", o_noktaya_ait_y_verileri)