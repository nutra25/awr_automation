import pyawr.mwoffice as mwoffice


def create_project_with_library():
    try:
        # MWOffice uygulamasına bağlan
        app = mwoffice.CMWOffice()
    except Exception as e:
        print(f"Uygulamaya bağlanılamadı: {e}")
        return

    # Kullanmak istediğiniz proses kütüphanesinin tam adı veya yolu
    # Örnek: Kendi sisteminizde yüklü olan bir kütüphane adı girin
    library_name = "MA_RFP"

    try:
        # YÖNTEM 1: Sadece Kütüphane adıyla yeni proje açmak [1]
        print(f"'{library_name}' kütüphanesi ile yeni proje oluşturuluyor...")
        app.NewWithProcessLibrary(library_name)

        print("Proje başarıyla oluşturuldu.")

        # --- ALTERNATİF YÖNTEM ---
        # YÖNTEM 2: Kütüphane adı ve spesifik bir versiyon numarası belirterek açmak [2]
        # library_version = "1.0"
        # app.NewWithProcessLibraryEx(library_name, library_version)

    except Exception as e:
        print(f"Proje oluşturulurken bir hata meydana geldi: {e}")


if __name__ == "__main__":
    create_project_with_library()