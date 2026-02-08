from typing import List, Dict, Any
from config import SCHEMATIC_NAME
import time
import random
from logger import LOGGER


class TESTDriver:
    """
    Static interface wrapper for AWR Microwave Office API operations.
    Isolates direct API calls from the main simulation logic.
    """

    def configure_element(self, element_name: str, params: Dict[str, Any]) -> None:
        """Configures a schematic element with the provided parameters (MOCK MODE)."""

        # --- [MOCK] SİMÜLASYON MODU ---
        LOGGER.info(f"[MOCK] Configuring Element: '{element_name}' in '{SCHEMATIC_NAME}'")

        # Sanki şematik ve eleman bulunmuş gibi yapıyoruz
        LOGGER.debug(f"  ├─ [MOCK] Schematic found: {SCHEMATIC_NAME}")
        LOGGER.debug(f"  ├─ [MOCK] Element matched: {element_name}")

        param_items = list(params.items())
        total_params = len(param_items)

        for index, (key, value) in enumerate(param_items):
            # Rastgele eski bir değer uyduruyoruz (0 ile 100 arası)
            # Böylece loglarda "Eski Değer -> Yeni Değer" değişimi gerçekçi durur.
            mock_old_val = f"{random.uniform(0, 100):.2f}"

            # Ağaç yapısı loglaması
            is_last_item = (index == total_params - 1)
            tree_char = "└──" if is_last_item else "├──"

            LOGGER.info(f"  {tree_char} [MOCK] {key}: [{mock_old_val}] -> [{value}]")

        if not params:
            LOGGER.info(f"  └─ [MOCK] No parameters to update.")

    def set_frequency(self, freq: float) -> None:
        """Updates the system simulation frequency (MOCK MODE)."""

        # --- [MOCK] FREKANS AYARLAMA ---
        LOGGER.info(f"[MOCK] Configuring RF Frequencies: '{SCHEMATIC_NAME}'")

        # Sanki şematik bulundu ve bağlandık
        LOGGER.debug(f"  ├─ [MOCK] Connected to schematic: {SCHEMATIC_NAME}")

        # Proje varsayılanlarını kapatmış gibi yapıyoruz
        LOGGER.info(f"  ├── [MOCK] Project defaults disabled.")

        # Eski frekansları silmiş gibi yapıyoruz (Rastgele 1-10 arası eski nokta varmış gibi)
        old_count = random.randint(1, 10)
        LOGGER.debug(f"  ├─ [MOCK] Cleared {old_count} existing points.")

        # Yeni frekansı eklemiş gibi logluyoruz
        # Tek bir frekans geldiği için ağaç yapısının sonu (└──) olarak işaretliyoruz.
        LOGGER.info(f"  └── [MOCK] Added Frequency: {freq} GHz")

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """
        Retrieves numerical data from a graph marker (MOCK MODE).

        Returns:
             [Value1, Value2, Value3] (Random fake data)
        """

        # --- [MOCK] SİMÜLASYON VE VERİ OKUMA TAKLİDİ ---
        LOGGER.info(f"[MOCK] Retrieving Marker Data: '{marker}' from '{graph}'")

        # Sanki AWR'ye bağlandık, grafiği bulduk ve simülasyon yaptık
        if toggle_enable:
            LOGGER.debug(f"  ├─ [MOCK] Enabling measurements...")

        LOGGER.debug("  ├── [MOCK] Simulation (Analyze) running...")
        # Simülasyon süresi taklidi (istersen time.sleep(0.1) ekle)
        LOGGER.debug("  ├── [MOCK] Simulation Completed.")

        # --- RASTGELE VERİ ÜRETME ---
        # Genelde AWR'den [Mag, Ang] veya [dB, Phase] gibi değerler döner.
        # Simülasyonun çalıştığını görmek için rastgele sayılar dönüyoruz.

        val1 = round(random.uniform(-30.0, 0.0), 3)   # Örn: -15.420 dB
        val2 = round(random.uniform(0.0, 180.0), 2)   # Örn: 45.00 Derece
        val3 = round(random.uniform(0.0, 50.0), 2)    # Ekstra bir değer (opsiyonel)

        # "m1: -15.420 45.00 12.34" gibi bir çıktı gelmiş gibi davranıyoruz
        raw_output = f"{marker}: {val1} {val2} {val3}"
        LOGGER.info(f"  └── [MOCK] Value: {raw_output}")

        if toggle_enable:
            LOGGER.debug(f"  ├─ [MOCK] Disabling measurements...")

        # Zaten sayıları biz ürettik, direkt listeye çevirip dönüyoruz
        return [val1, val2, val3]

    def run_wizard(self, options: Dict[str, Any]) -> None:
        """Triggers the Load Pull Wizard with the specified configuration (MOCK MODE)."""

        # --- [MOCK] WIZARD SİMÜLASYONU ---
        LOGGER.info("[MOCK] Starting Load Pull Wizard Automation Sequence")

        # Sanki Wizard bulundu ve başlatıldı
        LOGGER.debug("  ├─ [MOCK] Wizard definition located.")
        LOGGER.info("  ├── [MOCK] Configuring Wizard Parameters:")

        success_count = 0
        fail_count = 0

        param_items = list(options.items())
        total_params = len(param_items)

        for index, (param_name, param_value) in enumerate(param_items):
            # Ağaç yapısı loglaması
            is_last = (index == total_params - 1)
            tree_char = "└──" if is_last else "├──"

            # Eski değer uyduruyoruz (loglarda değişim gözüksün diye)
            # Eğer değer True/False ise tersini, sayı ise farklı bir sayıyı "eski" diye gösterelim.
            if isinstance(param_value, bool):
                old_val_str = str(not param_value)
            elif isinstance(param_value, (int, float)):
                old_val_str = str(param_value * 0.5) # Yarısı eski değermiş gibi
            else:
                old_val_str = "Old_Value"

            # Değişimi logluyoruz
            if param_value is None:
                 LOGGER.debug(f"    {tree_char} [MOCK] {param_name}: SKIPPED (None)")
            else:
                LOGGER.info(f"    {tree_char} [MOCK] {param_name}: [{old_val_str}] -> [{param_value}]")
                success_count += 1

        LOGGER.info(f"  ├── [MOCK] Configuration Summary: {success_count} Success, {fail_count} Failed.")

        if success_count > 0:
            LOGGER.info("  ├── [MOCK] Triggering Load Pull Execution (Exec)...")

            # Simülasyon süresini taklit ediyoruz (0.5 saniye bekleme)
            LOGGER.debug("  │   [MOCK] Waiting for simulation to finish...")
            time.sleep(0.5)

            LOGGER.info("  └── [MOCK] Load Pull Process Completed Successfully.")
        else:
            LOGGER.warning("  └── [MOCK] Execution ABORTED: No parameters were configured.")