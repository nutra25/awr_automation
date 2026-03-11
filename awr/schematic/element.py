from typing import Optional, Any, Dict

from fontTools.qu2cu.qu2cu import Union, List

from awr.awr_component import AWRComponent


class Element(AWRComponent):
    
    def add_element(self, schematic_name:str, x_pos:float, y_pos:float, element_name:Optional[str]=None, library_path:Optional[str]=None) -> Optional[Any]:
        if library_path:
            self.logger.info(f"├── Instantiating library element at ({x_pos}, {y_pos}) in '{schematic_name}'")
        elif element_name:
            self.logger.info(
                f"├── Instantiating standard element '{element_name}' at ({x_pos}, {y_pos}) in '{schematic_name}'")
        else:
            self.logger.error("└── Failed to add element: Must provide either 'element_name' or 'library_path'.")
            return None

        try:
            schematic = self.app.Project.Schematics(schematic_name)

            if library_path:
                new_element = schematic.Elements.AddLibraryElement(library_path, x_pos, y_pos)
            else:
                new_element = schematic.Elements.Add(element_name, x_pos, y_pos)

            self.logger.info(f"└── Successfully added element. Assigned Name: '{new_element.Name}'")
            return new_element
        except Exception as e:
            self.logger.error(f"└── Failed to add element. Details: {e}")
            return None

    def find_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> Union[Any, List[Any], None]:

        self.logger.info(f"├── Initiating element search sequence: Schematic='{schematic_name}', Target='{target_designator}'")
        self.logger.debug(f"│   ├── Mode: {'Partial Match (Bulk)' if allow_partial_match else 'Exact Match (Single)'}")

        try:
            active_schematic = self.app.Project.Schematics(schematic_name)
        except Exception:
            self.logger.error(f"└── Failed to locate schematic: '{schematic_name}'. Search sequence aborted.")
            return [] if allow_partial_match else None

        matched_elements = []

        for candidate_element in active_schematic.Elements:
            element_identifier = candidate_element.Name
            is_match = False

            if allow_partial_match:
                if target_designator in element_identifier:
                    is_match = True
            else:
                if target_designator == element_identifier:
                    is_match = True

            if not is_match and candidate_element.Parameters.Exists("ID"):
                element_id_value = candidate_element.Parameters("ID").ValueAsString
                if allow_partial_match:
                    if target_designator in element_id_value:
                        is_match = True
                else:
                    if element_id_value == target_designator:
                        is_match = True

            if is_match:
                if not allow_partial_match:
                    self.logger.debug(f"│   ├── Exact target element identified: {candidate_element.Name}")
                    self.logger.info(f"└── Search sequence completed successfully.")
                    return candidate_element
                else:
                    matched_elements.append(candidate_element)

        if allow_partial_match:
            if matched_elements:
                self.logger.info(f"└── Search sequence completed. Found {len(matched_elements)} matching element(s).")
                return matched_elements
            else:
                self.logger.warning(f"└── No elements found containing the substring '{target_designator}'.")
                return []

        self.logger.warning(f"└── Exact element '{target_designator}' could not be found in '{schematic_name}'.")
        return None

    def configure_element(self, schematic_name: str, target_designator: str, parameter_map: Dict[str, Any], allow_partial_match: bool = False) -> bool:

        self.logger.info(f"├── Initiating configuration sequence for '{target_designator}' in '{schematic_name}'")

        identified_element = self.find_element(schematic_name, target_designator, allow_partial_match)

        if identified_element is None:
            self.logger.warning(f"└── Configuration aborted: Target element reference could not be resolved.")
            return False

        element_name = identified_element.Name
        param_items = list(parameter_map.items())
        total_params = len(param_items)
        updates_made = 0

        self.logger.debug(f"├── Applying parameters to '{element_name}'...")

        for index, (param_key, param_value) in enumerate(param_items):
            is_last_item = (index == total_params - 1)
            tree_char = "└──" if is_last_item else "├──"

            if identified_element.Parameters.Exists(param_key):
                target_parameter = identified_element.Parameters(param_key)
                old_value = target_parameter.ValueAsString

                try:
                    target_parameter.ValueAsString = str(param_value)
                    self.logger.info(f"│   {tree_char} {param_key}: [{old_value}] -> [{param_value}]")
                    updates_made += 1
                except Exception as e:
                    self.logger.error(f"│   {tree_char} Failed to update '{param_key}'. Exception: {e}")
            else:
                self.logger.warning(f"│   {tree_char} Parameter '{param_key}' is missing on element '{element_name}'.")

        if updates_made > 0:
            self.logger.info(f"└── Successfully configured {updates_made} parameter(s) for '{element_name}'.")
            return True
        else:
            self.logger.warning(f"└── No parameters were updated for '{element_name}'.")
            return False

    def delete_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> bool:

        self.logger.info(f"├── Initiating deletion sequence for target '{target_designator}' in '{schematic_name}'")

        identified_element = self.find_element(schematic_name, target_designator, allow_partial_match)

        if identified_element is None:
            self.logger.warning(f"└── Deletion aborted: Target element reference could not be resolved.")
            return False

        element_name = identified_element.Name

        try:
            delete_success = identified_element.Delete()

            if delete_success:
                self.logger.info(f"└── Successfully DELETED element '{element_name}'.")
                return True
            else:
                self.logger.error(f"└── API returned False while attempting to delete '{element_name}'.")
                return False

        except Exception as e:
            self.logger.error(f"└── Encountered an exception during the deletion of '{element_name}': {e}")
            return False

    def get_element_node_positions(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> List[Dict[str, Any]]:

        self.logger.info(f"├── Initiating node extraction sequence for '{target_designator}' in '{schematic_name}'")

        identified_element = self.find_element(schematic_name, target_designator, allow_partial_match)

        if identified_element is None:
            self.logger.warning(f"└── Extraction aborted: Target element reference could not be resolved.")
            return []

        node_coordinates = []

        for pin_index, node in enumerate(identified_element.Nodes, start=1):
            net_num = node.NodeNumber
            x_pos = node.x
            y_pos = node.y

            node_coordinates.append({
                "PinNumber": pin_index,
                "NetNumber": net_num,
                "x": x_pos,
                "y": y_pos
            })

            self.logger.debug(f"│   ├── Extracted Pin {pin_index} (Assigned to Net {net_num}): X={x_pos}, Y={y_pos}")

        self.logger.info(f"└── Successfully extracted {len(node_coordinates)} node(s) for '{identified_element.Name}'.")
        return node_coordinates
    
    def replace_element(self, schematic_name: str, target_designator: str, node_mapping: Dict[int, Union[int, List[int]]], library_path: Optional[str] = None, element_name: Optional[str] = None) -> bool:

        self.logger.info(f"├── Initiating macro sequence: Replace & Rewire for '{target_designator}'")

        old_element = self.element_service.find_element(schematic_name, target_designator)
        if not old_element:
            self.logger.error(f"└── Sequence aborted: Target element '{target_designator}' not found.")
            return False

        center_x = old_element.x
        center_y = old_element.y
        old_nodes = self.element_service.get_element_node_positions(schematic_name, target_designator)

        if not self.element_service.delete_element(schematic_name, target_designator):
            self.logger.error("└── Sequence aborted: Failed to delete the target element.")
            return False

        new_element = None
        if library_path:
            self.logger.debug(f"│   ├── Attempting instantiation via library path: {library_path}")
            new_element = self.element_service.add_element(
                schematic_name, center_x, center_y, library_path=library_path
            )
        elif element_name:
            self.logger.debug(f"│   ├── Attempting instantiation via standard name: {element_name}")
            new_element = self.element_service.add_element(
                schematic_name, center_x, center_y, element_name=element_name
            )

        if not new_element:
            self.logger.error("└── Sequence aborted: No valid source provided or instantiation failed.")
            return False

        new_nodes = self.element_service.get_element_node_positions(schematic_name, new_element.Name)

        old_nodes_dict = {n["PinNumber"]: n for n in old_nodes}
        new_nodes_dict = {n["PinNumber"]: n for n in new_nodes}

        self.logger.info(f"├── Applying node wiring matrix for '{new_element.Name}'...")
        wire_count = 0

        for old_pin, target_pins in node_mapping.items():
            if old_pin not in old_nodes_dict:
                self.logger.warning(f"│   ├── Original pin {old_pin} does not exist. Skipping.")
                continue

            o_node = old_nodes_dict[old_pin]

            if not isinstance(target_pins, list):
                target_pins = [target_pins]

            for new_pin in target_pins:
                if new_pin not in new_nodes_dict:
                    self.logger.warning(f"│   ├── Target pin {new_pin} does not exist on new element. Skipping.")
                    continue

                n_node = new_nodes_dict[new_pin]

                if (o_node["x"] != n_node["x"]) or (o_node["y"] != n_node["y"]):

                    if self.add_wire(schematic_name, o_node["x"], o_node["y"], n_node["x"], n_node["y"]):
                        wire_count += 1
                else:
                    self.logger.debug(f"│   ├── Pins perfectly overlap (Old:{old_pin} -> New:{new_pin}). Wiring bypassed.")

        self.logger.info(f"└── Replacement sequence finalized. Total wires drawn: {wire_count}")
        return True
