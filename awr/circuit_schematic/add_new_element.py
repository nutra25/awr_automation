import pyawr.mwoffice as mwoffice
import logging

# Çıktıları ekranda düzgün görebilmek için standart loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(message)s')
LOGGER = logging.getLogger(__name__)


def replace_and_rewire_element(
        app_instance,
        schematic_title: str,
        target_designator: str,
        new_element_type: str,
        allow_partial_match: bool = False
) -> dict:
    LOGGER.info(
        f"İşlem Başlatıldı: Şematik='{schematic_title}', Hedef='{target_designator}', Yeni Element='{new_element_type}'")

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

        # İsim eşleşmezse, "ID" parametresine bakarak eşleştirmeyi dene
        if not is_match and candidate_element.Parameters.Exists("ID"):
            element_id_value = candidate_element.Parameters("ID").ValueAsString
            if element_id_value == target_designator:
                is_match = True

        if is_match:
            identified_element = candidate_element
            LOGGER.info(f" ├─ Hedef element bulundu: {identified_element.Name}")
            break

    if identified_element is None:
        LOGGER.warning(f" └─ UYARI: Element BULUNAMADI: '{target_designator}'")
        return {"success": False, "error": "Element bulunamadı"}

    # 3. Eski Bacak (Node) koordinatlarını ve merkez konumunu al
    old_node_coordinates = []
    try:
        # Bacakları tarayarak X ve Y koordinatlarını hafızaya al
        for idx, node in enumerate(identified_element.Nodes):
            # AWR API'sinde Node nesnesi üzerinden X ve Y koordinatları okunabilir
            old_node_coordinates.append((node.x, node.y))
            LOGGER.info(f" │  ├── Eski Bacak {idx + 1}: X={node.x}, Y={node.y}")
    except Exception as e:
        LOGGER.error(f" │  └── HATA: Bacak koordinatları okunamadı: {e}")
        return {"success": False, "error": "Bacaklar okunamadı"}

    elem_x = identified_element.x
    elem_y = identified_element.y
    old_name = identified_element.Name

    # 4. Eski Elementi Sil
    try:
        identified_element.Delete()
        LOGGER.info(f" ├─ Eski element '{old_name}' SİLİNDİ.")
    except Exception as e:
        LOGGER.error(f" └─ HATA: Element silinemedi: {e}")
        return {"success": False, "error": "Silme hatası"}

    # 5. Yeni Elementi Aynı Merkez Koordinatına Ekle
    try:
        # Kaynak: CSchematics.Elements.Add(Name, x, y)
        new_element = active_schematic.Elements.Add(new_element_type, elem_x, elem_y)
        LOGGER.info(f" ├─ Yeni element '{new_element.Name}' EKLENDİ.")
    except Exception as e:
        LOGGER.error(f" └─ HATA: Yeni element eklenemedi: {e}")
        return {"success": False, "error": "Ekleme hatası"}

    # 6. Eski bacak noktaları ile yeni bacak noktaları arasına kablo çek (Wiring)
    wire_count = 0
    try:
        new_node_coordinates = []
        for node in new_element.Nodes:
            new_node_coordinates.append((node.x, node.y))

        # Eski ve yeni elementin bacak sayıları farklı olabilir, minimum olan kadar eşleştirip kablo çekilir
        for i in range(min(len(old_node_coordinates), len(new_node_coordinates))):
            old_x, old_y = old_node_coordinates[i]
            new_x, new_y = new_node_coordinates[i]

            # Eğer eski bacak ile yeni bacak aynı noktada değilse (arada boşluk oluştuysa) kablo çiz
            if (old_x != new_x) or (old_y != new_y):
                # Kaynak: CSchematic.Wires.Add(x1, y1, x2, y2)
                active_schematic.Wires.Add(old_x, old_y, new_x, new_y)
                wire_count += 1
                LOGGER.info(f" │  ├── Kablo çekildi: ({old_x}, {old_y}) ---> ({new_x}, {new_y})")
            else:
                LOGGER.info(f" │  ├── Bacaklar kesişiyor, kabloya gerek yok: ({new_x}, {new_y})")

        LOGGER.info(f" └── İşlem başarıyla tamamlandı. Toplam çekilen kablo: {wire_count}")

    except Exception as e:
        LOGGER.error(f" └─ HATA: Kablo (Wire) çekilirken hata: {e}")
        return {"success": False, "error": "Kablolama hatası"}

    return {
        "success": True,
        "old_element": old_name,
        "new_element": new_element.Name,
        "wires_added": wire_count
    }


# ==========================================
# ANA ÇALIŞTIRMA BLOĞU (TEST)
# ==========================================
if __name__ == "__main__":
    try:
        # AWR uygulamasına bağlan
        app = mwoffice.CMWOffice()

        # --- KULLANICI AYARLARI ---
        hedef_sematik = "Load_Pull_Template"
        hedef_element = "CFH1"  # Silinecek eski element (örn: R1, C2)
        yeni_element_tipi = "GBJT"  # Yerine eklenecek yeni element (örn: transistör ise GBJT, kapasitör ise CAP)

        sonuc = replace_and_rewire_element(
            app_instance=app,
            schematic_title=hedef_sematik,
            target_designator=hedef_element,
            new_element_type=yeni_element_tipi,
            allow_partial_match=False
        )

        print("\nÖzet Rapor:", sonuc)

    except Exception as e:
        print(f"Uygulama başlatılamadı veya bir hata oluştu: {e}")