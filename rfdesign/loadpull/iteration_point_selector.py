"""
iteration_point_selector.py
Defines strategies for selecting the optimal point from load-pull contours.
Delegates all operations strictly to the central AutomationContext.
Utilizes embedded configuration nodes for strategy parameters.
"""

import os
import io
import math
from abc import ABC, abstractmethod
from typing import Tuple, Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pc
from shapely.geometry import Polygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
import skrf as rf
from core.logger import logger

# Pydantic V2 Importları
from pydantic import BaseModel, Field, ConfigDict


class PointSelectorConfig(BaseModel):
    """
    Configuration node containing parameters for all selection strategies.
    Pydantic V2 mimarisi kullanılarak veri doğrulama (validation) sağlanır.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    marker1_name: str = Field(default="m1")
    marker2_name: str = Field(default="m2")
    tradeoff_weight: float = Field(default=0.5)
    show_plot: bool = Field(default=True)

    # MaxMeasurementSelector için yeni eklenen merkezi ayar
    measurement_name: str = Field(
        default="G_LPCMMAX(PAE)",
        description="AWR grafiğinden verisi çekilecek ölçümün adı."
    )


class BasePointSelector(ABC):
    """
    Abstract base class defining the required interface for point selection strategies.
    """
    def __init__(self, config: PointSelectorConfig):
        self.config = config

    @abstractmethod
    def select_point(self, context: Any, graph_name: str, export_subpath: str = "") -> Tuple[str, str, str]:
        """
        Receives the global context instead of individual driver/exporter instances.
        """
        pass


class MaxMeasurementSelector(BasePointSelector):
    """
    Selection strategy that requests generic trace data from the AWR interface,
    parses it dynamically according to its structural dimensions, and calculates Gamma parameters.
    """

    def select_point(self, context: Any, graph_name: str, export_subpath: str = "") -> Tuple[str, str, str]:
        """
        Retrieves raw graph data, intelligently processes nested or flat arrays to extract the
        target measurement point, and computes polar coordinates.
        """
        logger.info(f"Initiating MaxMeasurementSelector algorithm for graph: {graph_name}")

        measurement_name = self.config.measurement_name

        try:
            y_data = context.driver.graph.get_single_measurement_data(graph_name, measurement_name)
        except AttributeError as e:
            logger.error(f"└── Context interface error: {e}")
            return "0", "0", "0"
        except Exception as e:
            logger.error(f"└── Unhandled exception during raw data retrieval: {e}")
            return "0", "0", "0"

        if not y_data:
            logger.warning(f"└── Insufficient data retrieved for '{measurement_name}'. Returning default origins.")
            return "0", "0", "0"

        try:
            logger.debug("├── Parsing trace data into load-pull parameters.")

            # Dynamically handle nested vs. flat data structures coming from AWR
            first_element = y_data[0]
            if isinstance(first_element, (list, tuple)):
                logger.debug("│   ├── Nested multidimensional data detected. Extracting the first coordinate point.")
                target_point = first_element
            else:
                logger.debug("│   ├── Flat one-dimensional data detected.")
                target_point = y_data

            if len(target_point) < 3:
                logger.error(
                    f"└── The extracted data point contains insufficient dimensions ({len(target_point)}). Minimum 3 required.")
                return "0", "0", "0"

            # Map the point indices to specific domain variables
            measurement_value = float(target_point[0])
            gamma_real = float(target_point[1])
            gamma_imag = float(target_point[2])

        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"└── Data parsing failed due to invalid format or typing: {e}")
            return "0", "0", "0"

        logger.debug("├── Executing mathematical transformations (Rectangular to Polar).")
        gamma_mag = math.hypot(gamma_real, gamma_imag)
        gamma_ang = math.degrees(math.atan2(gamma_imag, gamma_real))

        logger.info("└── Load-Pull Target Point Resolved:")
        logger.info(f"    ├── Target Measurement Value: {measurement_value:.4f}")
        logger.info(f"    ├── Gamma Magnitude: {gamma_mag:.4f}")
        logger.info(f"    └── Gamma Angle: {gamma_ang:.2f} deg")

        return str(measurement_value), str(gamma_mag), str(gamma_ang)


class TradeOffSelector(BasePointSelector):
    """
    Selection strategy that calculates a weighted central point between two distinct markers.
    """

    def select_point(self, context: Any, graph_name: str, export_subpath: str = "") -> Tuple[str, str, str]:
        logger.info(f"Initiating TradeOffSelector between markers '{self.config.marker1_name}' and '{self.config.marker2_name}'")

        d1 = context.driver.graph.get_marker_data(graph_name, self.config.marker1_name)
        d2 = context.driver.graph.get_marker_data(graph_name, self.config.marker2_name)

        if not d1 or not d2:
            logger.warning("└── Incomplete marker data retrieved. Returning default fallback values.")
            return "0", "0", "0"

        w1 = self.config.tradeoff_weight
        w2 = 1.0 - self.config.tradeoff_weight

        avg_mag = (d1[1] * w1) + (d2[1] * w2)
        avg_ang = (d1[2] * w1) + (d2[2] * w2)
        avg_val = (d1 * w1) + (d2 * w2)

        logger.info(f"└── Calculated weighted trade-off point: Magnitude={avg_mag:.4f}, Angle={avg_ang:.2f}")
        return str(avg_val), str(avg_mag), str(avg_ang)


class BroadbandOptimumSelector(BasePointSelector):
    """
    Advanced selection strategy to identify a generalized intersection area across multiple frequencies.
    """

    def select_point(self, context: Any, graph_name: str, export_subpath: str = "") -> Tuple[str, str, str]:
        logger.info(f"Initiating BroadbandOptimumSelector for graph: {graph_name}")

        freq_geoms, freqs, num_freqs = self._fetch_and_process_contours(context.driver, graph_name)

        if num_freqs == 0:
            return "0", "0", "0"

        best_intersection, best_state, worst_case_pae = self._find_best_intersection(freq_geoms, freqs, num_freqs)

        if best_state is None or best_intersection is None:
            logger.error("└── Failed to isolate a common broadband intersection area.")
            return "0", "0", "0"

        if best_intersection.geom_type in ['MultiPolygon', 'GeometryCollection']:
            geoms_to_plot = list(best_intersection.geoms)
        else:
            geoms_to_plot = [best_intersection]

        max_area = -1
        largest_poly = None
        for geom in geoms_to_plot:
            if geom.geom_type == 'Polygon' and geom.area > max_area:
                max_area = geom.area
                largest_poly = geom

        if largest_poly is not None:
            cx, cy = largest_poly.centroid.x, largest_poly.centroid.y
            mag = math.hypot(cx, cy)
            ang = math.degrees(math.atan2(cy, cx))

            logger.info(f"├── Optimal intersection identified with worst-case PAE threshold: {worst_case_pae}")
            logger.info(f"├── Target centroid calculated at Magnitude={mag:.4f}, Angle={ang:.2f}°")

            if self.config.show_plot and context.exporter:
                self._generate_plot(graph_name, freqs, num_freqs, freq_geoms, best_state, geoms_to_plot, cx, cy, context.exporter, export_subpath)
                self._generate_plot_3d_plotly(graph_name, freqs, num_freqs, freq_geoms, best_state, geoms_to_plot, cx, cy, context.exporter, export_subpath)
            elif self.config.show_plot and not context.exporter:
                logger.warning("└── Visualization is enabled, but no DataExporter was provided in context. Skipping plot generation.")
            else:
                logger.info("└── Visualization is disabled; skipping plot generation.")

            return str(worst_case_pae), str(mag), str(ang)
        else:
            logger.error("└── Failed to extract a valid polygon geometry from the intersection results.")
            return "0", "0", "0"

    def _fetch_and_process_contours(self, driver: Any, graph_name: str) -> Tuple[Dict, List[float], int]:
        logger.info("├── Retrieving broadband contour datasets from the application environment")

        data_by_freq = driver.graph.get_broadband_contours(graph_name)

        if not data_by_freq:
            logger.error("└── Aborting: Unreadable or empty contour data retrieved.")
            return {}, [], 0

        freq_geoms = {}
        freqs = sorted(list(data_by_freq.keys()))

        logger.info("├── Converting contour datasets into geometric polygon structures")

        num_processed = len(freqs)
        for idx, freq in enumerate(freqs):
            sorted_contours = sorted(data_by_freq[freq], key=lambda x: x['pae'], reverse=True)
            geoms_list = []

            for contour in sorted_contours:
                polys = []
                for island in contour['islands']:
                    pts = list(zip(island['real'], island['imag']))
                    if len(pts) >= 3:
                        poly = Polygon(pts).buffer(0).simplify(0.0001)
                        polys.append(poly)

                if polys:
                    unified_geom = unary_union(polys)
                    geoms_list.append({
                        'pae': contour['pae'],
                        'geom': unified_geom,
                        'islands': contour['islands']
                    })

            if geoms_list:
                freq_geoms[freq] = geoms_list

            prefix = "└──" if idx == num_processed - 1 else "├──"
            logger.debug(f"{prefix} Processed {len(geoms_list)} valid contours for {freq / 1e9:.2f} GHz")

        valid_freqs = [f for f in freqs if f in freq_geoms]
        return freq_geoms, valid_freqs, len(valid_freqs)

    def _find_best_intersection(self, freq_geoms: Dict, freqs: List[float], num_freqs: int) -> Tuple[Any, Optional[List[int]], float]:
        state = [0] * num_freqs
        best_state = None
        best_intersection = None
        step = 0

        logger.info("├── Executing intersection search algorithm")
        logger.debug("├── Phase 1: Establishing common baseline intersection area")

        while True:
            current_geom = freq_geoms[freqs[0]][state[0]]['geom']
            valid = True

            for i in range(1, num_freqs):
                next_geom = freq_geoms[freqs[i]][state[i]]['geom']
                cb = current_geom.bounds
                nb = next_geom.bounds
                if cb[0] > nb[2] or cb[2] < nb[0] or cb[1] > nb[3] or cb[3] < nb[1]:
                    valid = False
                    break

                current_geom = current_geom.intersection(next_geom)
                if current_geom.is_empty:
                    valid = False
                    break

            if valid and current_geom.area > 1e-6:
                best_intersection = current_geom
                best_state = list(state)
                min_base_pae = min([freq_geoms[freqs[i]][state[i]]['pae'] for i in range(num_freqs)])
                logger.debug(f"├── Common baseline discovered at iteration step {step} with minimum PAE of {min_base_pae}")
                break

            current_paes = []
            for i in range(num_freqs):
                if state[i] + 1 < len(freq_geoms[freqs[i]]):
                    current_paes.append((freq_geoms[freqs[i]][state[i]]['pae'], i))

            if not current_paes:
                logger.warning("├── Base intersection discovery exhausted all contour levels without success")
                break

            max_pae_in_current_state = max(current_paes, key=lambda x: x[0])[0]
            for pae_val, i in current_paes:
                if pae_val == max_pae_in_current_state:
                    state[i] += 1
            step += 1

        if best_intersection is not None:
            logger.debug("├── Phase 2: Applying limiter-biased optimization logic")
            pass_num = 1
            limiting_order = []
            for i in range(num_freqs):
                peak_pae = freq_geoms[freqs[i]][0]['pae']
                limiting_order.append((peak_pae, i))

            limiting_order.sort(key=lambda x: x[0])

            while True:
                improvement_in_this_pass = False
                for peak_pae, i in limiting_order:
                    if state[i] > 0:
                        test_state_idx = state[i] - 1
                        next_geom = freq_geoms[freqs[i]][test_state_idx]['geom']

                        cb = best_intersection.bounds
                        nb = next_geom.bounds
                        if cb[0] > nb[2] or cb[2] < nb[0] or cb[1] > nb[3] or cb[3] < nb[1]:
                            continue

                        test_intersection = best_intersection.intersection(next_geom)
                        if not test_intersection.is_empty and test_intersection.area > 1e-6:
                            best_intersection = test_intersection
                            state[i] = test_state_idx
                            best_state = list(state)
                            improvement_in_this_pass = True
                            freq_ghz = freqs[i] / 1e9
                            new_pae = freq_geoms[freqs[i]][state[i]]['pae']
                            logger.debug(f"├── [Iteration {pass_num}] Optimized {freq_ghz:.2f} GHz contour upward. Adjusted PAE: {new_pae}")

                if not improvement_in_this_pass:
                    logger.debug("├── Optimization process converged to a stable state")
                    break
                pass_num += 1

        worst_case_pae = min([freq_geoms[freqs[i]][best_state[i]]['pae'] for i in range(num_freqs)]) if best_state else 0.0
        return best_intersection, best_state, worst_case_pae

    def _generate_plot(self, graph_name: str, freqs: List[float], num_freqs: int, freq_geoms: Dict,
                       best_state: List[int], geoms_to_plot: List[Any], cx: float, cy: float,
                       exporter: Any, export_subpath: str):
        logger.info("├── Generating 2D vector graphic rendering of the intersection dataset")

        plt.figure(figsize=(14, 12), dpi=120)
        rf.plotting.smith(draw_labels=True)
        plt.title(f"{graph_name} - Broadband Optimum Target", fontsize=16, pad=15)

        for i in range(num_freqs):
            freq = freqs[i]
            idx = best_state[i]
            pae_val = freq_geoms[freq][idx]['pae']
            islands = freq_geoms[freq][idx]['islands']
            freq_ghz = freq / 1e9
            label_str = f"{freq_ghz:.2f} GHz (Target: {pae_val})"

            first_island = True
            trace_color = None
            for island in islands:
                lbl = label_str if first_island else None
                if first_island:
                    p = plt.plot(island['real'], island['imag'], label=lbl, linewidth=0.2, alpha=0.99)
                    trace_color = p[0].get_color()
                    first_island = False
                else:
                    plt.plot(island['real'], island['imag'], linewidth=0.2, alpha=0.99, color=trace_color)

        for geom in geoms_to_plot:
            if geom.geom_type == 'Polygon':
                x, y = geom.exterior.xy
                plt.fill(x, y, color='red', alpha=0.6, zorder=10)
                plt.plot(x, y, color='black', linewidth=0.2, linestyle='--', zorder=11)

        plt.plot(cx, cy, marker='X', color='black', markersize=0.1, label='Optimum Target', zorder=15)

        plt.xlim(-1.02, 1.02)
        plt.ylim(-1.02, 1.02)
        plt.gca().set_aspect('equal', adjustable='box')

        plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=10)
        plt.tight_layout()

        try:
            buf = io.BytesIO()
            plt.savefig(buf, bbox_inches='tight', format='svg')
            filename = os.path.join(export_subpath, f"{graph_name}_2D.svg")
            exporter.save_binary(filename, buf.getvalue())
        except Exception as e:
            logger.error(f"├── Encountered an error during 2D graphic memory serialization: {e}")
        finally:
            plt.close()
            buf.close()

    def _generate_plot_3d_plotly(self, graph_name: str, freqs: List[float], num_freqs: int, freq_geoms: Dict,
                                 best_state: List[int], geoms_to_plot: List[Any], cx: float, cy: float,
                                 exporter: Any, export_subpath: str):
        logger.info("├── Generating Advanced Interactive 3D Plotly rendering (Z-Axis = PAE)")

        fig = go.Figure()
        trace_metadata = []

        def push_trace(trace_obj, trace_type, f=None, p=None):
            fig.add_trace(trace_obj)
            trace_metadata.append({'type': trace_type, 'freq': f, 'pae': p})

        def get_max_decimals(val_list):
            max_d = 0
            for val in val_list:
                s = str(float(val))
                if '.' in s:
                    d = len(s.split('.')[1].rstrip('0'))
                    if d > max_d:
                        max_d = d
            return max_d if max_d > 0 else 1

        all_paes = [contour['pae'] for freq in freqs for contour in freq_geoms[freq]]
        freqs_ghz = [f / 1e9 for f in freqs]
        pae_dec = get_max_decimals(all_paes)
        freq_dec = get_max_decimals(freqs_ghz)

        z_min, z_max = min(all_paes), max(all_paes)
        if z_min == z_max:
            z_min -= 5.0
            z_max += 5.0

        worst_case_pae = min([freq_geoms[freqs[i]][best_state[i]]['pae'] for i in range(num_freqs)])

        smith_grp = "smith_chart_grp"
        theta = np.linspace(0, 2 * np.pi, 100)
        x_smith, y_smith = np.cos(theta), np.sin(theta)

        base_trace = go.Scatter3d(
            x=x_smith, y=y_smith, z=[z_min] * 100, mode='lines',
            line=dict(color='lightgray', dash='dash'),
            name='Smith Limits', legendgroup=smith_grp, showlegend=True
        )
        push_trace(base_trace, 'base')

        push_trace(go.Scatter3d(x=x_smith, y=y_smith, z=[z_max] * 100, mode='lines',
                                line=dict(color='lightgray', dash='dash'),
                                legendgroup=smith_grp, showlegend=False), 'base')

        for t in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
            push_trace(go.Scatter3d(x=[np.cos(t), np.cos(t)], y=[np.sin(t), np.sin(t)], z=[z_min, z_max],
                                    mode='lines', line=dict(color='lightgray', dash='dot'),
                                    legendgroup=smith_grp, showlegend=False), 'base')

        color_palette = pc.qualitative.Plotly
        for i in range(num_freqs):
            freq = freqs[i]
            f_ghz = freq / 1e9
            hex_color = color_palette[i % len(color_palette)].lstrip('#')
            r, g, b = tuple(int(hex_color[j:j + 2], 16) for j in (0, 2, 4))
            line_color = f'rgb({r},{g},{b})'

            sorted_contours = sorted(freq_geoms[freq], key=lambda x: x['pae'])
            first_group_entry = True

            for contour_idx, contour in enumerate(sorted_contours):
                pae_val = contour['pae']
                islands = contour['islands']

                pae_range = z_max - z_min
                normalized_pae = (pae_val - z_min) / pae_range if pae_range > 0 else 1.0
                dynamic_width = 1 + (6 * normalized_pae)

                legend_name = f"PAE: {pae_val:.{pae_dec}f}"
                freq_label = f"{f_ghz:.{freq_dec}f}"

                first_island = True
                for island in islands:
                    trace_line = go.Scatter3d(
                        x=island['real'], y=island['imag'], z=[pae_val] * len(island['real']),
                        mode='lines',
                        line=dict(color=line_color, width=dynamic_width),
                        name=legend_name,
                        legendgroup=f"grp_{f_ghz}",
                        showlegend=first_island
                    )

                    if first_group_entry and first_island:
                        trace_line.legendgrouptitle = dict(text=f"📻 {freq_label} GHz",
                                                           font=dict(size=16, color="black"))
                        first_group_entry = False

                    push_trace(trace_line, 'contour', f=f_ghz, p=pae_val)
                    first_island = False

        raw_intersection = None
        for freq in freqs:
            best_diff = float('inf')
            target_geom = None
            for contour in freq_geoms[freq]:
                diff = abs(contour['pae'] - worst_case_pae)
                if diff < best_diff:
                    best_diff = diff
                    target_geom = contour['geom']

            if raw_intersection is None:
                raw_intersection = target_geom
            else:
                raw_intersection = raw_intersection.intersection(target_geom)

        raw_geoms_to_plot = []
        if raw_intersection and not raw_intersection.is_empty:
            if raw_intersection.geom_type in ['MultiPolygon', 'GeometryCollection']:
                raw_geoms_to_plot = list(raw_intersection.geoms)
            else:
                raw_geoms_to_plot = [raw_intersection]

        raw_area_grp = "raw_area_grp"
        first_raw_geom = True
        for geom in raw_geoms_to_plot:
            if geom.geom_type == 'Polygon':
                x_geom, y_geom = geom.exterior.xy
                x_vals, y_vals = list(x_geom), list(y_geom)

                push_trace(go.Scatter3d(
                    x=x_vals, y=y_vals, z=[worst_case_pae] * len(x_vals),
                    mode='lines', surfaceaxis=2, surfacecolor='dodgerblue', opacity=0.3,
                    line=dict(color='blue', width=3, dash='dot'),
                    name='Raw Intersection Area (All Freqs)',
                    legendgroup=raw_area_grp, showlegend=first_raw_geom
                ), 'volume')
                first_raw_geom = False

        opt_area_grp = "opt_area_grp"
        first_opt_geom = True
        opt_z_height = worst_case_pae + 0.005

        for geom in geoms_to_plot:
            if geom.geom_type == 'Polygon':
                x_geom, y_geom = geom.exterior.xy
                x_vals, y_vals = list(x_geom), list(y_geom)

                push_trace(go.Scatter3d(
                    x=x_vals, y=y_vals, z=[opt_z_height] * len(x_vals),
                    mode='lines', surfaceaxis=2, surfacecolor='red', opacity=0.7,
                    line=dict(color='darkred', width=4),
                    name='Optimized Target Area (Biased)',
                    legendgroup=opt_area_grp, showlegend=first_opt_geom
                ), 'volume')
                first_opt_geom = False

        push_trace(go.Scatter3d(
            x=[cx, cx], y=[cy, cy], z=[z_min, worst_case_pae],
            mode='lines+markers', line=dict(color='black', width=6),
            marker=dict(size=4, color='black'),
            name=f'Optimum Axis (Limit: {worst_case_pae:.{pae_dec}f})'
        ), 'target')

        unique_freqs = sorted(list(set([m['freq'] for m in trace_metadata if m['type'] == 'contour'])))
        unique_paes = sorted(list(set([m['pae'] for m in trace_metadata if m['type'] == 'contour'])))

        def build_vis_array(filter_type, value, action="isolate"):
            vis = []
            for m in trace_metadata:
                if m['type'] in ['base', 'volume', 'target']:
                    vis.append(True)
                elif m['type'] == 'contour':
                    if action == "isolate":
                        vis.append(m[filter_type] == value)
                    elif action == "hide":
                        vis.append(m[filter_type] != value)
            return vis

        pae_buttons = [dict(label="👁️ Show All PAE", method="restyle", args=[{"visible": [True] * len(trace_metadata)}])]
        for p in unique_paes:
            pae_buttons.append(dict(label=f"🎯 Isolate PAE: {p:.{pae_dec}f}", method="restyle", args=[{"visible": build_vis_array('pae', p, 'isolate')}]))
        for p in unique_paes:
            pae_buttons.append(dict(label=f"🚫 Hide PAE: {p:.{pae_dec}f}", method="restyle", args=[{"visible": build_vis_array('pae', p, 'hide')}]))

        freq_buttons = [dict(label="👁️ Show All Freqs", method="restyle", args=[{"visible": [True] * len(trace_metadata)}])]
        for f in unique_freqs:
            freq_buttons.append(dict(label=f"🎯 Isolate {f:.{freq_dec}f} GHz", method="restyle", args=[{"visible": build_vis_array('freq', f, 'isolate')}]))
        for f in unique_freqs:
            freq_buttons.append(dict(label=f"🚫 Hide {f:.{freq_dec}f} GHz", method="restyle", args=[{"visible": build_vis_array('freq', f, 'hide')}]))

        fig.update_layout(
            title=dict(text=f"{graph_name} - 3D PAE Landscape & Dual Intersection Areas", font=dict(size=20)),
            scene=dict(
                xaxis_title='Real', yaxis_title='Imaginary', zaxis_title='PAE Limit',
                xaxis=dict(range=[-1.05, 1.05], backgroundcolor="white"),
                yaxis=dict(range=[-1.05, 1.05], backgroundcolor="white"),
                zaxis=dict(backgroundcolor="lightgray", range=[z_min, z_max]),
                aspectratio=dict(x=1, y=1, z=0.8)
            ),
            margin=dict(l=0, r=0, b=0, t=80),
            legend=dict(
                title=dict(text="Click Titles to Toggle Group", font=dict(size=14, color="gray")),
                font=dict(size=14, color="black"),
                yanchor="top", y=0.9, xanchor="left", x=1.05,
                itemsizing='constant', tracegroupgap=15,
                bgcolor="rgba(250, 250, 250, 0.9)",
                bordercolor="lightgray", borderwidth=2,
                groupclick="toggleitem"
            ),
            updatemenus=[
                dict(buttons=freq_buttons, direction="down", showactive=True, x=0.01, xanchor="left", y=1.08, yanchor="top", font=dict(size=13, color="black"), bgcolor="white", bordercolor="gray"),
                dict(buttons=pae_buttons, direction="down", showactive=True, x=0.25, xanchor="left", y=1.08, yanchor="top", font=dict(size=13, color="black"), bgcolor="white", bordercolor="gray")
            ]
        )

        fig.add_annotation(text="Frequency Filter:", x=0.01, y=1.12, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="black"), align="left")
        fig.add_annotation(text="PAE Filter:", x=0.25, y=1.12, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="black"), align="left")

        try:
            html_content = fig.to_html(include_plotlyjs='cdn', full_html=True)
            filename = os.path.join(export_subpath, f"{graph_name}_3D.html")
            exporter.save_text(filename, html_content)
        except Exception as e:
            logger.error(f"└── Encountered an error during 3D HTML text serialization: {e}")