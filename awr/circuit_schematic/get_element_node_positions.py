import pyawr.mwoffice as mwoffice
import logging

# Çıktıları ekranda düzgün görebilmek için standart loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(message)s')
LOGGER = logging.getLogger(__name__)


def get_element_node_positions(
        app_instance,
        schematic_title: str,
        target_designator: str,
        allow_partial_match: bool = False
) -> list:
    LOGGER.info(f"Bacak koordinatları aranıyor: Şematik='{schematic_title}', Element='{target_designator}'")

    # 1. Şematik Kontrolü
    try:
        project_reference = app_instance.Project
        active_schematic = project_reference.Schematics(schematic_title)
        LOGGER.info(f" ├─ Şematik bağlantısı kuruldu: {active_schematic.Name}")
    except Exception:
        LOGGER.error(f" └─ HATA: Şematik bulunamadı: '{schematic_title}'")
        return []

    identified_element = None

    # 2. Elementi İsmine veya ID parametresine göre ara (Gelişmiş Arama Mantığı)
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

        # Eşleşme bulunduysa döngüden çık [1]
        if is_match:
            identified_element = candidate_element
            LOGGER.info(f" ├─ Hedef element bulundu: {identified_element.Name}")
            break

    # Eşleşme bulunamadıysa işlemi durdur [1]
    if identified_element is None:
        LOGGER.warning(f" └─ UYARI: Element BULUNAMADI: '{target_designator}'")
        return []

    # 3. Bacak (Node) koordinatlarını al
    node_coordinates = []

    # Elementin bacaklarını (Nodes) döngüye al [2]
    for node in identified_element.Nodes:
        # AWR API'sinde Node nesnesi üzerinden X ve Y koordinatları okunabilir
        x_pos = node.x
        y_pos = node.y
        node_num = node.NodeNumber

        # Koordinatları listeye kaydet
        node_coordinates.append({
            "NodeNumber": node_num,
            "x": x_pos,
            "y": y_pos
        })

        LOGGER.info(f" ├── Bacak {node_num}: X={x_pos}, Y={y_pos}")

    LOGGER.info(f" └── İşlem başarıyla tamamlandı.")

    return node_coordinates


# ==========================================
# ANA ÇALIŞTIRMA BLOĞU (TEST)
# ==========================================
if __name__ == "__main__":
    try:
        # AWR uygulamasına bağlan
        app = mwoffice.CMWOffice()

        # --- KULLANICI AYARLARI ---
        hedef_sematik = "Load_Pull_Template"
        hedef_element = "CFH1"  # Örnek: "R1" veya ID'si (örn: "id_123")

        koordinatlar = get_element_node_positions(
            app_instance=app,
            schematic_title=hedef_sematik,
            target_designator=hedef_element,
            allow_partial_match=False  # Kısmi eşleşme istiyorsanız True yapın
        )

        if koordinatlar:
            print("\nKaydedilen Koordinatlar Listesi:")
            print(koordinatlar)

    except Exception as e:
        print(f"Uygulama başlatılamadı veya bir hata oluştu: {e}")