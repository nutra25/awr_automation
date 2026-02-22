import pyawr.mwoffice as mwoffice
import logging

# Çıktıları ekranda düzgün görebilmek için standart loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(message)s')
LOGGER = logging.getLogger(__name__)


def delete_schematic_element(
        app_instance,
        schematic_title: str,
        target_designator: str,
        allow_partial_match: bool = False
) -> dict:
    LOGGER.info(f"Silme İşlemi Başlatıldı: Şematik='{schematic_title}', Element='{target_designator}'")

    # 1. Şematik Kontrolü
    try:
        project_reference = app_instance.Project
        active_schematic = project_reference.Schematics(schematic_title)
        LOGGER.info(f" ├─ Şematik bağlantısı kuruldu: {active_schematic.Name}")
    except Exception:
        LOGGER.error(f" └─ HATA: Şematik bulunamadı: '{schematic_title}'")
        return {"success": False, "error": "Şematik bulunamadı"}

    identified_element = None

    # 2. Elementi İsmine veya ID parametresine göre ara
    for candidate_element in active_schematic.Elements:
        element_identifier = candidate_element.Name
        is_match = False

        if allow_partial_match:
            if target_designator in element_identifier:
                is_match = True
        else:
            if target_designator == element_identifier:
                is_match = True

        # İsim eşleşmezse, "ID" parametresine bakarak eşleştirmeyi dene [1]
        if not is_match and candidate_element.Parameters.Exists("ID"):
            element_id_value = candidate_element.Parameters("ID").ValueAsString
            if element_id_value == target_designator:
                is_match = True

        # Eşleşme bulunduysa döngüden çık
        if is_match:
            identified_element = candidate_element
            LOGGER.info(f" ├─ Hedef element bulundu: {identified_element.Name}")
            break

    # Eşleşme bulunamadıysa işlemi durdur
    if identified_element is None:
        LOGGER.warning(f" └─ UYARI: Element BULUNAMADI: '{target_designator}'")
        return {"success": False, "error": "Element bulunamadı"}

    element_name = identified_element.Name

    # 3. Elementi Sil [2]
    try:
        delete_success = identified_element.Delete()

        if delete_success:
            LOGGER.info(f" └── Element '{element_name}' başarıyla SİLİNDİ.")
        else:
            LOGGER.error(f" └── HATA: Element '{element_name}' silinirken API 'False' döndürdü.")

    except Exception as e:
        LOGGER.error(f" └── HATA: Element silinirken bir istisna oluştu: {e}")
        delete_success = False

    # 4. Sonuç Raporunu Döndür
    return {
        "schematic_source": active_schematic.Name,
        "deleted_element_identifier": element_name,
        "success": delete_success
    }


# ==========================================
# ANA ÇALIŞTIRMA BLOĞU (TEST)
# ==========================================
if __name__ == "__main__":
    try:
        # AWR uygulamasına bağlan
        app = mwoffice.CMWOffice()

        # --- KULLANICI AYARLARI ---
        # İşlem yapılacak şematiğin ve silinecek elementin ismini buraya yazın
        hedef_sematik = "Load_Pull_Template"
        hedef_element = "CFH1"  # Örnek: "R1", "TL1" veya ID'si

        # Fonksiyonu çağır
        sonuc_raporu = delete_schematic_element(
            app_instance=app,
            schematic_title=hedef_sematik,
            target_designator=hedef_element,
            allow_partial_match=False
        )

        print("\nİşlem Sonucu Raporu:", sonuc_raporu)

    except Exception as e:
        print(f"Uygulama başlatılamadı veya bir hata oluştu: {e}")