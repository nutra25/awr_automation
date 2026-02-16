# AWR Automation Modules
import pyawr.mwoffice as mwoffice
from awr.awr_get_marker_value import get_marker_value
from awr.awr_configure_schematic_element import configure_schematic_element
from awr.awr_loadpull_wizard import run_loadpull_wizard
from awr.awr_configure_schematic_rf_frequency import configure_schematic_rf_frequency
from awr.awr_get_broadband_contours import extract_graph_data

from typing import List, Dict, Any, Union
from config import SCHEMATIC_NAME
import re

from shapely.geometry import Polygon

class AWRDriver:
    """
    Static interface wrapper for AWR Microwave Office API operations.
    Isolates direct API calls from the main simulation logic.
    """

    def __init__(self):
        """Connecting to AWR"""
        try:
            self.app = mwoffice.CMWOffice()
        except Exception as e:
            raise

    def configure_element(self, element_name: str, params: Dict[str, Any]) -> None:
        """Configures a schematic element with the provided parameters."""
        configure_schematic_element(
            self.app,
            schematic_title=SCHEMATIC_NAME,
            target_designator=element_name,
            parameter_map=params,
        )

    def set_frequency(self, freq: Union[float, List[float]]) -> None:
        """Updates the system simulation frequency."""
        configure_schematic_rf_frequency(
            self.app,
            schematic_name=SCHEMATIC_NAME,
            frequencies=freq
        )

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """
        Retrieves numerical data from a graph marker.

        Returns:
            List[float]: Extracted numerical values (e.g., [Mag, Ang]).
                         Returns a list of zeros if retrieval fails.
        """
        raw_output = get_marker_value(
            self.app,
            graph_title=graph,
            marker_designator=marker,
            perform_simulation=True,
            toggle_enable=toggle_enable
        )

        if not raw_output:
            return [0.0, 0.0, 0.0]

        # Extract floating point numbers using regex
        numbers = re.findall(r"-?\d+\.?\d*", raw_output)
        return [float(n) for n in numbers]

    def run_wizard(self, options: Dict[str, Any]) -> None:
        """Triggers the Load Pull Wizard with the specified configuration."""
        run_loadpull_wizard(self.app, options)

    def get_broadband_contours(self, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:
        return extract_graph_data(self.app, graph_name)

    def modify_loadpull_measurement(self, graph_name: str, meas_name: str,
                                    data_file_name: str = None,
                                    contour_step: float = None,
                                    max_contours: int = None) -> None:
        """
        Load Pull ölçüm parametrelerini günceller.

        Args:
            graph_name (str): Ölçümün bulunduğu grafiğin adı.
            meas_name (str): Güncellenecek ölçümün tam adı veya imzası (örn: "G_LPCM(load_data_2,...)").
                             Eğer ölçüm adı tam bilinmiyorsa, grafikteki ilk ölçümü almak için mantık eklenebilir.
            data_file_name (str, optional): Yeni 'Load Pull Data File Name' değeri.
            contour_step (float, optional): Yeni 'Contour Step (%)' değeri.
            max_contours (int, optional): Yeni 'Max number of contours' değeri.
        """
        # 1. Grafiğe erişim
        if self.app.Project.Graphs.Exists(graph_name):
            graph = self.app.Project.Graphs.Item(graph_name)
        else:
            raise ValueError(f"Graph '{graph_name}' not found.")

        # 2. Ölçüme erişim
        # Not: AWR'de ölçüm isimleri parametreleri de içerdiği için (örn: "G_LPCM(...)")
        # tam ismi bilmek zor olabilir. Genellikle koleksiyonu taramak daha güvenlidir.
        target_meas = None

        # pyawr wrapper üzerinden 'Measurements' koleksiyonuna erişim
        measurements = graph.Measurements

        # İsimle doğrudan erişim deneniyor, yoksa arama yapılabilir
        if measurements.Exists(meas_name):
            target_meas = measurements.Item(meas_name)
        else:
            # Alternatif: Grafikteki ölçümler arasında ismi 'G_LPCM' ile başlayan veya
            # belirli bir ölçümü arayabilirsiniz. Örnek olarak ilk ölçümü alıyoruz:
            if measurements.Count > 0:
                target_meas = measurements.Item(1)
            else:
                raise ValueError(f"No measurements found in graph '{graph_name}'.")

        # 3. Altta yatan COM nesnesine erişim (_get_inner kullanarak)
        # pyawr CMeasurement sınıfı 'Parameters' özelliğini doğrudan sunmadığı için
        # ham COM nesnesini alıyoruz.
        raw_meas = target_meas._get_inner()

        # 4. Parametreleri güncelleme (AWR API'de parametre indeksleri 1 tabanlıdır)

        # Load Pull Data File Name (Genellikle 1. Parametre)
        if data_file_name is not None:
            # Parametre koleksiyonuna erişip değerini (Value) değiştiriyoruz
            raw_meas.Parameters.Item(1).Value = data_file_name

        # Contour Step (%) (Resimde 3. sırada)
        if contour_step is not None:
            raw_meas.Parameters.Item(3).Value = str(contour_step)

        # Max number of contours (Resimde 4. sırada)
        if max_contours is not None:
            raw_meas.Parameters.Item(4).Value = str(max_contours)

        print(f"Measurement '{meas_name}' updated successfully.")